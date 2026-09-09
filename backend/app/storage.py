"""Durable application records. PostgreSQL is required outside tests."""
import os
from contextlib import contextmanager
from functools import lru_cache
from sqlalchemy import create_engine, MetaData, Table, Column, String, JSON, select

metadata = MetaData()
records = Table('app_records', metadata,
    Column('kind', String, primary_key=True),
    Column('owner', String, primary_key=True),
    Column('key', String, primary_key=True),
    Column('payload', JSON, nullable=False))

@lru_cache
def engine():
    url = os.getenv('DATABASE_URL', '').strip()
    if not url:
        from backend.app.config import DATA_DIR
        DATA_DIR.mkdir(parents=True, exist_ok=True)
        db_path = (DATA_DIR / "visiq.db").as_posix()
        url = f"sqlite:///{db_path}"
    elif url.startswith('postgresql://'):
        url = url.replace('postgresql://', 'postgresql+psycopg://', 1)
    elif not url.startswith(('postgresql+psycopg://', 'sqlite://')):
        raise RuntimeError('Configure a PostgreSQL or SQLite DATABASE_URL')

    if url.startswith('sqlite://'):
        return create_engine(url)
    return create_engine(url, pool_pre_ping=True)

def initialize():
    metadata.create_all(engine())
    if engine().dialect.name == 'postgresql':
        from sqlalchemy import text
        with engine().begin() as conn:
            conn.execute(text('ALTER TABLE app_records ENABLE ROW LEVEL SECURITY'))
            conn.execute(text('REVOKE ALL ON app_records FROM PUBLIC'))
            for role in ('anon', 'authenticated'):
                if conn.execute(text('SELECT 1 FROM pg_roles WHERE rolname=:role'), {'role': role}).scalar():
                    conn.execute(text(f'REVOKE ALL ON app_records FROM {role}'))

@contextmanager
def transaction(kind, owner, key):
    """Serialize updates to a record, including first creation, across workers."""
    with engine().begin() as conn:
        if conn.dialect.name == 'postgresql':
            from sqlalchemy import text
            conn.execute(text('SELECT pg_advisory_xact_lock(hashtextextended(:key, 0))'),
                         {'key': f'{kind}:{owner}:{key}'})
        yield conn

def get(kind, owner, key, conn=None):
    stmt = select(records.c.payload).where(records.c.kind == kind, records.c.owner == owner, records.c.key == key)
    if conn is not None:
        return conn.execute(stmt).scalar_one_or_none()
    with engine().connect() as connection:
        return connection.execute(stmt).scalar_one_or_none()

def put(kind, owner, key, payload, conn=None):
    if conn is None:
        with transaction(kind, owner, key) as connection:
            return put(kind, owner, key, payload, connection)
    from sqlalchemy.dialects.postgresql import insert as pg_insert
    from sqlalchemy.dialects.sqlite import insert as sqlite_insert
    insert = pg_insert if conn.dialect.name == 'postgresql' else sqlite_insert
    stmt = insert(records).values(kind=kind, owner=owner, key=key, payload=payload)
    conn.execute(stmt.on_conflict_do_update(index_elements=['kind', 'owner', 'key'], set_={'payload': payload}))

def list_records(kind, owner=None):
    stmt = select(records.c.payload).where(records.c.kind == kind)
    if owner is not None:
        stmt = stmt.where(records.c.owner == owner)
    with engine().connect() as conn:
        return list(conn.execute(stmt).scalars())

def find(kind, key, owner=None):
    stmt = select(records.c.payload).where(records.c.kind == kind, records.c.key == key)
    if owner is not None:
        stmt = stmt.where(records.c.owner == owner)
    with engine().connect() as conn:
        return conn.execute(stmt).scalar_one_or_none()

def delete(kind, owner, key):
    with transaction(kind, owner, key) as conn:
        conn.execute(records.delete().where(records.c.kind == kind, records.c.owner == owner, records.c.key == key))

if __name__ == '__main__':
    from backend.app import config  # load local environment
    initialize()
