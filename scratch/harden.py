from pathlib import Path
def edit(path, fn):
    p=Path(path); p.write_text(fn(p.read_text(encoding='utf-8')),encoding='utf-8')
p=Path('backend/app/auth/supabase_auth.py'); s=p.read_text(); s=s[:s.index('def _decode_jwt_token')]+'''from functools import lru_cache
@lru_cache
def _jwks(issuer):
    return jwt.PyJWKClient(issuer + '/.well-known/jwks.json', timeout=5)

def _decode_jwt_token(token: str) -> User:
    from backend.app.config import ALLOW_DEMO_AUTH
    if ALLOW_DEMO_AUTH and token in DEMO_USERS:
        return DEMO_USERS[token]
    try:
        if not SUPABASE_URL:
            raise ValueError('Authentication is not configured')
        issuer = SUPABASE_URL.rstrip('/') + '/auth/v1'
        if SUPABASE_JWT_SECRET:
            key, algorithms = SUPABASE_JWT_SECRET, ['HS256']
        else:
            key, algorithms = _jwks(issuer).get_signing_key_from_jwt(token).key, ['RS256', 'ES256']
        payload = jwt.decode(token, key, algorithms=algorithms, issuer=issuer,
            audience='authenticated', options={'require': ['exp', 'iat', 'sub', 'iss', 'aud']})
        from backend.app.paths import filename
        subject = filename(payload['sub'])
        if payload.get('role') != 'authenticated':
            raise ValueError('Invalid role')
        return User(id=subject, email=payload.get('email', ''), user_metadata=payload.get('user_metadata') or {})
    except Exception:
        raise HTTPException(status_code=401, detail='Invalid authentication credentials', headers={'WWW-Authenticate': 'Bearer'})

def get_current_user(credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)) -> User:
    if not credentials or not credentials.credentials:
        raise HTTPException(status_code=401, detail='Authentication required', headers={'WWW-Authenticate': 'Bearer'})
    user = _decode_jwt_token(credentials.credentials.strip())
    from backend.app import storage
    storage.put('users', user.id, user.id, user.model_dump())
    return user

get_optional_user = get_current_user
'''; p.write_text(s)
p=Path('backend/app/auth/quota_manager.py'); s=p.read_text(); a=s.index('        self.storage_path ='); b=s.index('    def check_quota',a)
s=s[:a]+'''        self.default_limit = default_limit

    def _today_utc(self):
        return datetime.now(timezone.utc).strftime('%Y-%m-%d')

    def _get_entry(self, user_id):
        from backend.app import storage
        return storage.get('quotas', user_id, self._today_utc()) or {'date': self._today_utc(), 'tokens_used': 0, 'daily_limit': self.default_limit}

'''+s[b:]; a=s.index('        entry = self._get_entry(user_id)',s.index('    def record_usage')); b=s.index('    def get_user_quota',a)
s=s[:a]+'''        from backend.app import storage
        day = self._today_utc()
        with storage.transaction('quotas', user_id, day) as conn:
            entry = storage.get('quotas', user_id, day, conn) or {'date': day, 'tokens_used': 0, 'daily_limit': self.default_limit}
            entry['tokens_used'] += tokens
            storage.put('quotas', user_id, day, entry, conn)
            return entry['tokens_used']

'''+s[b:];a=s.index('        today = self._today_utc()',s.index('    def reset_quota'));b=s.index('# Singleton instance',a)
s=s[:a]+'''        from backend.app import storage
        day = self._today_utc()
        storage.put('quotas', user_id, day, {'date': day, 'tokens_used': 0, 'daily_limit': self.default_limit})

'''+s[b:];p.write_text(s)
p=Path('backend/app/memory/session_store.py');s=p.read_text().replace('self._sessions: Dict[str, ChatSession] = {}','self._sessions = PersistentSessions()');pos=s.index('class SessionStore:')
s=s[:pos]+'''from collections.abc import MutableMapping
from backend.app import storage

def restore_session(row):
    session = ChatSession(row['session_id'], row['title'], row['dataset_name'], row['user_id'], row['created_at'])
    session.history, session.widgets, session.token_usage = row['history'], row['widgets'], row['token_usage']
    return session

class PersistentSessions(MutableMapping):
    def __getitem__(self, key):
        rows = [r for r in storage.list_records('sessions') if r['session_id'] == key]
        if not rows: raise KeyError(key)
        return restore_session(rows[0])
    def __setitem__(self, key, value):
        storage.put('sessions', value.user_id, key, vars(value))
    def __delitem__(self, key):
        value = self[key]
        storage.delete('sessions', value.user_id, key)
    def __iter__(self):
        return iter(r['session_id'] for r in storage.list_records('sessions'))
    def __len__(self):
        return len(storage.list_records('sessions'))

'''+s[pos:]
s=s.replace('    def ensure_default_session','    def save(self, session):\n        self._sessions[session.session_id] = session\n\n    def ensure_default_session')
s=s.replace('        session = self._sessions.get(session_id)',"        session = (restore_session(row) if (row := storage.get('sessions', user_id, session_id)) else None) if user_id else self._sessions.get(session_id)")
s=s.replace('return [s.to_dict() for s in self._sessions.values() if s.user_id == user_id]',"return [restore_session(r).to_dict() for r in storage.list_records('sessions', user_id)]")
s=s.replace('                session.title = truncated','                session.title = truncated\n            self.save(session)')
s=s.replace('    def update_tokens','            self.save(session)\n\n    def update_tokens')
s=s.replace('    def get_widgets','        self.save(session)\n\n    def get_widgets')
s=s.replace('        session.widgets.append(widget)\n        return widget','        session.widgets.append(widget)\n        self.save(session)\n        return widget')
s=s.replace('        return len(session.widgets) < initial_len','        self.save(session)\n        return len(session.widgets) < initial_len')
s=s.replace('        session.widgets = widgets\n        return True','        session.widgets = widgets\n        self.save(session)\n        return True');p.write_text(s)
edit('backend/app/agent/widget_engine.py',lambda s:s.replace('        session.widgets.append(widget)','        session.widgets.append(widget)\n        from backend.app.memory.session_store import default_session_store\n        default_session_store.save(session)').replace('        return session.widgets','        from backend.app.memory.session_store import default_session_store\n        default_session_store.save(session)\n        return session.widgets'))
