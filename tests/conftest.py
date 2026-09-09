import os
import time
import uuid
import jwt
import pytest

# Never read developer credentials or call external LLMs during tests.
os.environ.update(APP_ENV='test', ALLOW_DEMO_AUTH='false', GEMINI_API_KEY='', GROQ_API_KEY='',
                  SUPABASE_URL='https://test.supabase.co', SUPABASE_JWT_SECRET='test-secret-' * 4)

@pytest.fixture(autouse=True)
def isolated_storage(tmp_path, monkeypatch):
    from backend.app import storage, config
    from backend.app.data_engine.dataset_manager import default_dataset_manager
    monkeypatch.setenv('DATABASE_URL', os.getenv('TEST_DATABASE_URL') or f'sqlite:///{(tmp_path / "test.db").as_posix()}')
    storage.engine.cache_clear()
    storage.initialize()
    with storage.engine().begin() as conn:
        conn.execute(storage.records.delete())
    raw = tmp_path / 'raw'; raw.mkdir()
    (raw / 'netflix_titles.csv').write_text('title,category,value\nA,Movie,10\nB,Show,20\n')
    monkeypatch.setattr(default_dataset_manager, 'raw_data_dir', raw)
    monkeypatch.setattr(default_dataset_manager, 'uploads_dir', tmp_path / 'uploads')
    monkeypatch.setattr(config, 'KNOWLEDGE_DIR', tmp_path / 'knowledge')
    from backend.app.api import routes
    monkeypatch.setattr(routes, 'KNOWLEDGE_DIR', tmp_path / 'knowledge')
    default_dataset_manager._cache.clear()
    default_dataset_manager._desc_cache.clear()
    routes._suggestions_cache.clear()
    yield
    storage.engine().dispose()
    storage.engine.cache_clear()

@pytest.fixture
def token():
    def make(user='alice', **claims):
        payload = dict(sub=user, email=f'{user}@example.com', role='authenticated',
                       iss='https://test.supabase.co/auth/v1', aud='authenticated',
                       iat=int(time.time()), exp=int(time.time()) + 3600)
        payload.update(claims)
        return jwt.encode(payload, os.environ['SUPABASE_JWT_SECRET'], algorithm='HS256')
    return make

@pytest.fixture
def client():
    from fastapi.testclient import TestClient
    from backend.app.main import app
    with TestClient(app, raise_server_exceptions=False) as client:
        yield client

@pytest.fixture
def auth(token):
    return {'Authorization': 'Bearer ' + token()}
