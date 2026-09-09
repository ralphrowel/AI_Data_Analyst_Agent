"""Bound request bodies before JSON parsing; emit credential-free request logs."""
import json
import logging
import time
import uuid
from starlette.responses import JSONResponse
from backend.app.config import MAX_UPLOAD_BYTES

logger = logging.getLogger('visiq.http')

class JsonFormatter(logging.Formatter):
    def format(self, record):
        return json.dumps({'level': record.levelname, 'logger': record.name,
                           'message': record.getMessage(), **getattr(record, 'fields', {})}, ensure_ascii=True)

class RequestBoundary:
    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope['type'] != 'http':
            return await self.app(scope, receive, send)
        request_id = uuid.uuid4().hex
        started = time.monotonic()
        status = 500
        # JSON can encode a UTF-8 character as six ASCII escape bytes.
        limit = MAX_UPLOAD_BYTES * 6 + 65536
        body = bytearray()
        while True:
            message = await receive()
            if message['type'] == 'http.disconnect': return
            body.extend(message.get('body', b''))
            if len(body) > limit:
                return await JSONResponse({'detail': 'Request exceeds size limit'}, 413)(scope, receive, send)
            if not message.get('more_body', False): break
        sent = False
        async def replay():
            nonlocal sent
            if not sent:
                sent = True
                return {'type': 'http.request', 'body': bytes(body), 'more_body': False}
            return await receive()
        async def response(message):
            nonlocal status
            if message['type'] == 'http.response.start':
                status = message['status']
                message['headers'].append((b'x-request-id', request_id.encode()))
            await send(message)
        try:
            await self.app(scope, replay, response)
        finally:
            logger.info('request_completed', extra={'fields': {'request_id': request_id,
                'method': scope['method'], 'status': status,
                'duration_ms': round((time.monotonic()-started)*1000)}})
