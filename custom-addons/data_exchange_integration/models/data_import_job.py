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

    locked_at = fields.Datetime()

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

        self.attempt_count += 1

        file_bytes, filename = self._download_file()

        self.write({
            'file_data': base64.b64encode(file_bytes),
            'file_name': filename,
        })

        self.process_file()

        if not self.state in ['discarded']:
            self.state = 'done'


    def _handle_failure(self, error):
        self.ensure_one()

        self.last_error = str(error)

        if self.attempt_count >= self.max_attempts:
            self.state = 'failed'
            return

        # exponential backoff
        delay_minutes = 2 ** self.attempt_count

        self.write({
            'state': 'pending',
            'next_attempt_at': fields.Datetime.now() + timedelta(minutes=delay_minutes),
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
    # Processing logic
    # =============================

    def process_file(self):
        z = zipfile.ZipFile(io.BytesIO(base64.b64decode(self.file_data)))

        dispatcher = FileDispatcher(self.env)

        file_map = defaultdict(list)

        for filename in z.namelist():
            if not filename.endswith('.json'):
                continue

            file_type = dispatcher._resolve_type(filename)

            if not file_type:
                self.add_log(f'Unsupported file type: {filename}')
                continue

            content = z.read(filename)
            file_map[file_type].append((filename, content))

        if not file_map:
            self.state = 'discarded'
            return

        ordered_types = resolve_import_order(list(file_map.keys()))

        for file_type in ordered_types:
            files = file_map[file_type]

            for filename, content in files:
                dispatcher.dispatch(
                    file_type,
                    content,
                    job=self
                )


    # =============================
    # MAIN ENTRYPOINT
    # =============================

    def process_pull(self):
        self.ensure_one()
        self.state = 'processing'

        try:
            file_bytes, filename = self._download_file()

            self.write({
                'file_data': base64.b64encode(file_bytes),
                'file_name': filename,
            })

            self.process_file()  # reuse your existing logic

            if not self.state in ['discarded']:
                self.state = 'done'

        except Exception:
            _logger.exception("Pull import failed")
            self.state = 'failed'

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
        