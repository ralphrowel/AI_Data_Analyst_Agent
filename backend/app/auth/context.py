from contextvars import ContextVar

request_user_id = ContextVar('request_user_id', default=None)
