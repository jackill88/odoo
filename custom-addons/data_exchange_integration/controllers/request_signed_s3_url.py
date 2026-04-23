from odoo import http
from odoo.http import request

import boto3


class RequestSignedS3UrlController(http.Controller):
    @http.route(
        '/api/data-exchange/s3/config/<int:config_id>/signed-url',
        type='jsonrpc',
        auth='bearer',
        methods=['POST'],
        csrf=False,
    )
    def request_signed_upload_url(self, config_id):
        """Return a presigned URL for uploading an object to S3 valid for 48 hours."""
        payload = request.get_json_data() or {}

        bucket = payload.get('bucket')
        object_key = payload.get('object_key') or payload.get('key')
        content_type = payload.get('content_type')

        if not bucket:
            return {'error': 'bucket is required'}
        if not object_key:
            return {'error': 'object_key is required'}

        config = request.env['data.import.s3.config'].sudo().browse(config_id)
        if not config.exists():
            return {'error': f'Data import S3 config {config_id} not found'}

        s3 = boto3.client(
            's3',
            endpoint_url=config.endpoint,
            aws_access_key_id=config.access_key,
            aws_secret_access_key=config.secret_key,
        )

        presign_params = {
            'Bucket': bucket,
            'Key': object_key,
        }
        if content_type:
            presign_params['ContentType'] = content_type

        upload_url = s3.generate_presigned_url(
            ClientMethod='put_object',
            Params=presign_params,
            ExpiresIn=48 * 3600,
        )

        presign_params_download = {
            'Bucket': bucket,
            'Key': object_key,
        }
        download_url = s3.generate_presigned_url(
            ClientMethod='get_object',
            Params=presign_params_download, # no ContentType for GET action
            ExpiresIn=48 * 3600,
        )

        return {
            'data_import_s3_config_id': config.id,
            'bucket': bucket,
            'object_key': object_key,
            'endpoint_url': config.endpoint,
            'presigned_url': upload_url,
            'download_url': download_url,
            'expires_in': 48 * 3600,
            'content_type': content_type,
        }
