import time
import jwt
import pytest

@pytest.mark.parametrize('path', ['/api/datasets','/api/sessions','/api/dataset-changes',
    '/api/recent-graphs','/api/user/quota','/api/auth/me','/api/suggestions'])
def test_private_routes_require_auth(client, path):
    assert client.get(path).status_code == 401
    assert client.get(path, headers={'Authorization':'Bearer demo_user_a'}).status_code == 401

@pytest.mark.parametrize('claims', [{'iss':'https://evil.test/auth/v1'}, {'aud':'wrong'},
    {'exp':1}, {'sub':'../alice'}, {'role':'service_role'}, {'iat':9999999999}])
def test_invalid_claims(client, token, claims):
    assert client.get('/api/auth/me', headers={'Authorization':'Bearer '+token(**claims)}).status_code == 401

def test_unsigned_and_wrong_key(client, token):
    for value in [jwt.encode({'sub':'alice'}, key='', algorithm='none'),
                  jwt.encode({'sub':'alice'}, 'wrong-secret-'*4, algorithm='HS256')]:
        assert client.get('/api/auth/me', headers={'Authorization':'Bearer '+value}).status_code == 401

def test_demo_flag_requires_development(client, monkeypatch):
    from backend.app import config
    assert config.ALLOW_DEMO_AUTH is False
    monkeypatch.setattr(config, 'ALLOW_DEMO_AUTH', True)
    assert client.get('/api/auth/me', headers={'Authorization':'Bearer demo_user_a'}).status_code == 200
    assert client.get('/api/auth/me', headers={'Authorization':'Bearer demo_arbitrary'}).status_code == 401

@pytest.mark.parametrize('name', ['../escape.csv', 'a/b.csv', 'a\\b.csv', 'C:\\a.csv',
    '/tmp/a.csv', '..', 'CON.csv', 'a.csv:stream', ' a.csv', 'a.csv\x00'])
def test_bad_upload_names(client, auth, name):
    assert client.post('/api/upload', headers=auth, json={'filename':name,'content':'a\n1'}).status_code == 422

def test_upload_size_and_request_validation(client, auth, monkeypatch):
    from backend.app.api import routes
    monkeypatch.setattr(routes, 'MAX_UPLOAD_BYTES', 4)
    assert client.post('/api/upload', headers=auth, json={'filename':'a.txt','content':'ééé'}).status_code == 413
    assert client.post('/api/ask', headers=auth, json={'question':'','provider':'evil'}).status_code == 422
    assert client.get('/api/datasets/a.csv/rows?page=-1', headers=auth).status_code == 422

def test_resolved_containment(tmp_path):
    from backend.app.paths import inside
    root=tmp_path/'root'; root.mkdir()
    other=tmp_path/'other'; other.mkdir()
    try:
        (root/'link').symlink_to(other, target_is_directory=True)
    except OSError:
        pytest.skip('Symlink creation unavailable on this Windows host')
    with pytest.raises(ValueError): inside(root,'link','escape.csv')

def test_generic_errors(client, auth, monkeypatch):
    from backend.app.api.routes import default_dataset_manager
    def fail(**kwargs): raise RuntimeError('secret-credential')
    monkeypatch.setattr(default_dataset_manager,'list_datasets',fail)
    response=client.get('/api/datasets',headers=auth)
    assert response.status_code == 500
    assert response.json() == {'detail':'Internal server error'}

def test_asymmetric_signature_and_trusted_jwks(client, monkeypatch):
    from cryptography.hazmat.primitives.asymmetric import rsa
    from types import SimpleNamespace
    from backend.app.auth import supabase_auth
    key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    now=int(time.time())
    claims=dict(sub='alice',email='alice@example.com',role='authenticated',
                iss='https://test.supabase.co/auth/v1',aud='authenticated',iat=now,exp=now+1000)
    token=jwt.encode(claims,key,algorithm='RS256',headers={'kid':'trusted'})
    monkeypatch.setattr(supabase_auth,'SUPABASE_JWT_SECRET','')
    def trusted_jwks(issuer):
        assert issuer == 'https://test.supabase.co/auth/v1'
        return SimpleNamespace(get_signing_key_from_jwt=lambda token:SimpleNamespace(key=key.public_key()))
    monkeypatch.setattr(supabase_auth,'_jwks',trusted_jwks)
    assert client.get('/api/auth/me',headers={'Authorization':'Bearer '+token}).status_code == 200
    bad_key=rsa.generate_private_key(public_exponent=65537,key_size=2048)
    forged=jwt.encode(claims,bad_key,algorithm='RS256')
    assert client.get('/api/auth/me',headers={'Authorization':'Bearer '+forged}).status_code == 401

def test_jwks_outage_fails_closed(client,token,monkeypatch):
    from backend.app.auth import supabase_auth
    monkeypatch.setattr(supabase_auth,'SUPABASE_JWT_SECRET','')
    def outage(*args): raise ConnectionError('offline')
    monkeypatch.setattr(supabase_auth,'_jwks',outage)
    assert client.get('/api/auth/me',headers={'Authorization':'Bearer '+token()}).status_code == 401

def test_raw_body_limit(client, auth, monkeypatch):
    from backend.app import http_security
    monkeypatch.setattr(http_security,'MAX_UPLOAD_BYTES',1)
    assert client.post('/api/upload',headers=auth,content=b'x'*66000).status_code == 413

def test_invalid_csv_preserves_existing_upload(client,auth):
    assert client.post('/api/upload',headers=auth,json={'filename':'a.csv','content':'col\n1\n'}).status_code == 200
    assert client.post('/api/upload',headers=auth,json={'filename':'a.csv','content':'\n'}).status_code == 422
    assert client.get('/api/datasets/a.csv/rows',headers=auth).json()['rows'][0]['col'] == 1
