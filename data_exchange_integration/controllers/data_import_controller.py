# controllers/data_import_controller.py

from odoo import http
from odoo.http import request


class DataImportController(http.Controller):

    @http.route('/api/data-exchange/process', type='jsonrpc', auth='bearer', methods=['POST'], csrf=False)
    def pull_file(self):
        """
        Examples:

        SFTP:
        {
            "source": "sftp",
            "config_key": "supplier_1",
            "filepath": "/exports/file.zip"
        }

        S3:
        {
            "source": "s3",
            "bucket": "imports",
            "key": "file.zip"
        }

        OR presigned URL:
        {
            "source": "url",
            "url": "https://s3/...signature..."
        }
        """
        payload = request.get_json_data()
        if not payload.get('source'):
            return {"error": "Missing source"}


        job = request.env['data.import.job'].sudo().create({
            'state': 'pending',
            'source_type': payload.get('source'),
            'payload': payload,
        })

        # ? optional: trigger immediate execution
        request.env.ref('data_exchange_integration.ir_cron_process_import_jobs')._trigger()

        return {
            "status": "accepted",
            "job_id": job.id
        }