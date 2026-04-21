# models/data_import_job.py
from collections import defaultdict
from datetime import timedelta
import paramiko
import base64
import io
import requests


from odoo import models, fields

import boto3
import zipfile

import logging

from ..services.file_dispatcher import FileDispatcher
from ..services.master_import_registry import resolve_import_order

_logger = logging.getLogger(__name__)


class DataImportJob(models.Model):
    _name = 'data.import.job'

    state = fields.Selection([
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('done', 'Done'),
        ('failed', 'Failed'),
        ('discarded', 'Discarded'),
    ], default='pending')
    log = fields.Text()

    source_type = fields.Char()
    payload = fields.Json()

    file_data = fields.Binary()
    file_name = fields.Char()

    attempt_count = fields.Integer(default=0)
    max_attempts = fields.Integer(default=3)
    next_attempt_at = fields.Datetime(index=True)
    last_error = fields.Text()

    processed_files = fields.Json(default=list)

    locked_at = fields.Datetime()

    BATCH_SIZE_DEFAULT = 5

    # =========================
    # keeping the log
    # ========================
    def add_log(self, message):
        self.ensure_one()

        existing = self.log or ""
        self.log = f"{existing}\n{message}" if existing else message

    # =========================
    # Cron
    # =========================

    def _acquire_jobs(self, limit=5):
        self.env.cr.execute("""
            SELECT id
            FROM data_import_job
            WHERE state = 'pending'
            AND (next_attempt_at IS NULL OR next_attempt_at <= NOW())
            ORDER BY create_date
            FOR UPDATE SKIP LOCKED
            LIMIT %s
        """, (limit,))

        job_ids = [row[0] for row in self.env.cr.fetchall()]
        jobs = self.browse(job_ids)

        now = fields.Datetime.now()

        jobs.write({
            'state': 'processing',
            'locked_at': now,
        })

        return jobs
    

    def _process_one(self):
        self.ensure_one()

        entries = self._ensure_processed_files()
        if not entries:
            return

        dispatcher = FileDispatcher(self.env)
        zip_bytes = self._ensure_archive_bytes()
        batch_limit = self._get_batch_size()
        processed = 0

        while processed < batch_limit:
            entry = self._get_next_pending_entry(entries)
            if entry is None:
                break

            try:
                content = self._read_entry_content(entry['filename'], zip_bytes)
                dispatcher.dispatch(entry['file_type'], content, job=self)

                if self.state == 'discarded':
                    entry['state'] = 'failed'
                    entry['attempts'] = self.max_attempts
                    entry['error'] = 'Discarded by importer'
                    self._persist_processed_files(entries, {'locked_at': False})
                    self.env.cr.commit()
                    return

            except Exception as exc:
                entry['state'] = 'failed'
                entry['attempts'] = (entry.get('attempts') or 0) + 1
                entry['error'] = str(exc)
                self.last_error = str(exc)
                extra = {'locked_at': False, 'last_error': self.last_error}
                if entry['attempts'] >= self.max_attempts:
                    extra.update({
                        'state': 'failed',
                        'attempt_count': self.max_attempts,
                        'next_attempt_at': False,
                    })
                self._persist_processed_files(entries, extra)
                self.env.cr.commit()
                raise

            entry['state'] = 'done'
            entry['error'] = None
            entry['attempts'] = 0

            self.add_log(f"Imported {entry['file_type']} file {entry['filename']}")
            self._persist_processed_files(entries)
            self.env.cr.commit()
            processed += 1

            if not self._has_pending_entries(entries):
                break

        next_state = 'done' if not self._has_pending_entries(entries) else 'pending'
        self._persist_processed_files(entries, {
            'state': next_state,
            'locked_at': False,
            'attempt_count': 0,
            'next_attempt_at': False,
        })


    def _handle_failure(self, error):
        self.ensure_one()

        self.last_error = str(error)

        if self.state == 'failed':
            self.write({'last_error': self.last_error, 'locked_at': False})
            return

        self.attempt_count += 1

        if self.attempt_count >= self.max_attempts:
            self.write({
                'state': 'failed',
                'attempt_count': self.attempt_count,
                'next_attempt_at': False,
                'locked_at': False,
                'last_error': self.last_error,
            })
            return

        delay_minutes = 2 ** self.attempt_count

        self.write({
            'state': 'pending',
            'attempt_count': self.attempt_count,
            'next_attempt_at': fields.Datetime.now() + timedelta(minutes=delay_minutes),
            'locked_at': False,
            'last_error': self.last_error,
        })


    def _release_stale_jobs(self, timeout_minutes=30):
        limit_time = fields.Datetime.now() - timedelta(minutes=timeout_minutes)

        stuck_jobs = self.search([
            ('state', '=', 'processing'),
            ('locked_at', '<', limit_time)
        ])

        stuck_jobs.write({
            'state': 'pending',
            'locked_at': False,
        })


    def _cron_process_jobs(self):
        self._release_stale_jobs()
        jobs = self._acquire_jobs(limit=10)

        for job in jobs:
            self.env.cr.commit()  # isolate each job

            try:
                job._process_one()
                self.env.cr.commit()

            except Exception as e:
                self.env.cr.rollback()
                job._handle_failure(e)
                self.env.cr.commit()


    # =============================
    # Processing helpers
    # =============================

    def _ensure_archive_bytes(self):
        if not self.file_data:
            file_bytes, filename = self._download_file()
            self.write({
                'file_data': base64.b64encode(file_bytes),
                'file_name': filename,
            })
            return file_bytes

        try:
            return base64.b64decode(self.file_data)
        except Exception as exc:
            raise ValueError("Stored archive is corrupted") from exc


    def _get_batch_size(self):
        payload = self.payload or {}
        batch_from_payload = payload.get('batch_size')

        try:
            batch_value = int(batch_from_payload)
        except (TypeError, ValueError):
            batch_value = self.BATCH_SIZE_DEFAULT

        if batch_value < 1:
            batch_value = self.BATCH_SIZE_DEFAULT

        return batch_value


    def _ensure_processed_files(self):
        if self.processed_files:
            return self.processed_files

        zip_bytes = self._ensure_archive_bytes()
        dispatcher = FileDispatcher(self.env)
        file_map = defaultdict(list)

        with zipfile.ZipFile(io.BytesIO(zip_bytes)) as z:
            for filename in z.namelist():
                if not filename.endswith('.json'):
                    continue

                file_type = dispatcher._resolve_type(filename)

                if not file_type:
                    self.add_log(f'Unsupported file type: {filename}')
                    continue

                file_map[file_type].append(filename)

        if not file_map:
            self.add_log('Archive did not contain any supported JSON files.')
            self._persist_processed_files([], {
                'state': 'discarded',
                'locked_at': False,
            })
            return []

        try:
            ordered_types = resolve_import_order(list(file_map.keys()))
        except Exception as exc:
            self.last_error = str(exc)
            self.state = 'failed'
            self.write({
                'state': 'failed',
                'locked_at': False,
                'last_error': self.last_error,
            })
            raise

        entries = []
        for file_type in ordered_types:
            for filename in file_map[file_type]:
                entries.append({
                    'filename': filename,
                    'file_type': file_type,
                    'state': 'pending',
                    'attempts': 0,
                    'error': None,
                })

        self._persist_processed_files(entries)
        return entries


    def _persist_processed_files(self, entries, extra=None):
        payload = {'processed_files': entries}
        if extra:
            payload.update(extra)
        self.write(payload)
        self.processed_files = entries


    def _get_next_pending_entry(self, entries):
        for entry in entries:
            attempts = entry.get('attempts', 0)
            if entry['state'] in ('pending', 'failed') and attempts < self.max_attempts:
                return entry
        return None


    def _has_pending_entries(self, entries):
        return any(
            entry['state'] in ('pending', 'failed') and entry.get('attempts', 0) < self.max_attempts
            for entry in entries
        )


    def _read_entry_content(self, filename, zip_bytes=None):
        zip_bytes = zip_bytes or self._ensure_archive_bytes()
        with zipfile.ZipFile(io.BytesIO(zip_bytes)) as z:
            return z.read(filename)


    # =============================
    # MAIN ENTRYPOINT
    # =============================

    def process_pull(self):
        self.ensure_one()
        self.write({
            'state': 'processing',
            'locked_at': fields.Datetime.now(),
        })

        try:
            self._process_one()
            self.env.cr.commit()

        except Exception as exc:
            _logger.exception("Pull import failed")
            self.env.cr.rollback()
            self._handle_failure(exc)
            self.env.cr.commit()

    # =============================
    # TRANSPORT ROUTER
    # =============================

    def _download_sftp(self):
        payload = self.payload

        config = self.env['data.import.sftp.config'].search([
            ('key', '=', payload.get('config_key'))
        ], limit=1)

        if not config:
            raise ValueError("SFTP config not found")

        transport = paramiko.Transport((config.host, config.port or 22))
        transport.connect(
            username=config.username,
            password=config.password
        )

        sftp = paramiko.SFTPClient.from_transport(transport)

        filepath = payload['filepath']

        with sftp.open(filepath, 'rb') as f:
            file_bytes = f.read()

        sftp.close()
        transport.close()

        filename = filepath.split('/')[-1]

        return file_bytes, filename
    
    def _download_s3(self):
        payload = self.payload

        config = self.env['data.import.s3.config'].search([
            ('key', '=', payload.get('config_key'))
        ], limit=1)

        if not config:
            raise ValueError("S3 config not found")

        s3 = boto3.client(
            's3',
            endpoint_url=config.endpoint,
            aws_access_key_id=config.access_key,
            aws_secret_access_key=config.secret_key,
        )

        bucket = payload['bucket']
        key = payload['object_key']

        obj = s3.get_object(Bucket=bucket, Key=key)
        file_bytes = obj['Body'].read()

        filename = key.split('/')[-1]

        return file_bytes, filename

    def _download_url(self):
        payload = self.payload

        url = payload['url']

        response = requests.get(url, timeout=300)
        response.raise_for_status()

        content_disposition = response.headers.get('Content-Disposition')
        filename = "download.zip"

        if content_disposition and 'filename=' in content_disposition:
            filename = content_disposition.split('filename=')[-1].strip('"')

        return response.content, filename

    def _download_file(self):
        source = self.source_type

        if source == 'sftp':
            return self._download_sftp()
        elif source == 's3':
            return self._download_s3()
        elif source == 'url':
            return self._download_url()
        else:
            raise ValueError(f"Unsupported source: {source}")
