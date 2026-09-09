from pathlib import Path
import re
p=Path('backend/app/data_engine/dataset_manager.py');s=p.read_text();s=s.replace('import pandas as pd','import pandas as pd\nfrom backend.app.paths import inside, filename\nfrom backend.app import storage')
a=s.index('        if not name:',s.index('    def _resolve_path'));b=s.index('    def list_datasets',a)
s=s[:a]+'''        name = filename(name or DEFAULT_DATASET_PATH.name)
        if user_id:
            private = inside(self.uploads_dir, user_id, name)
            if private.exists(): return private
        shared = inside(self.raw_data_dir, name)
        if shared.exists(): return shared
        raise FileNotFoundError('Dataset not found')

    def _write_path(self, name, user_id):
        if not user_id: raise ValueError('User required for mutations')
        path = inside(self.uploads_dir, user_id, name or DEFAULT_DATASET_PATH.name)
        path.parent.mkdir(parents=True, exist_ok=True)
        return path

    def log_activity(self, dataset_name, action, description, details=None, user_id=None):
        from datetime import datetime, timezone
        import uuid
        user_id = user_id or (details or {}).get('user_id')
        if not user_id: raise ValueError('Activity owner required')
        entry = dict(id=str(uuid.uuid4()), dataset_name=dataset_name, action=action,
                     description=description, details=details or {}, timestamp=datetime.now(timezone.utc).isoformat())
        storage.put('activity', user_id, entry['id'], entry)
        path = self._resolve_path(dataset_name, user_id)
        df = load_data(path)
        storage.put('datasets', user_id, dataset_name, dict(name=dataset_name, rows=len(df),
            columns=len(df.columns), size_bytes=path.stat().st_size, modified_at=entry['timestamp'], is_private=True))
        return entry

    def get_activity_log(self, user_id):
        return sorted(storage.list_records('activity', user_id), key=lambda r:r['timestamp'], reverse=True)[:20]

'''+s[b:]
s=s.replace('user_dir = self.uploads_dir / user_id','user_dir = inside(self.uploads_dir, user_id)')
s=s.replace('        return datasets',"        for dataset in datasets:\n            storage.put('datasets', user_id or 'shared', dataset['name'], dataset)\n        return datasets")
# Always read fresh files; caches are not authoritative across workers.
s=s.replace('        if key not in self._cache:', '        if True:')
s=s.replace('        if key not in self._desc_cache:', '        if True:')
s=s.replace('str.contains(q, na=False)','str.contains(q, na=False, regex=False)')
# Only mutation methods get private output paths.
a=s.index('    def update_cells');s=s[:a]+s[a:].replace('self._resolve_path(name, user_id=user_id)','self._write_path(name, user_id)')
s=re.sub(r'(self.log_activity\(name, .*?)(\)\n)',r'\1, user_id=user_id\2',s)
p.write_text(s)
p=Path('backend/app/api/routes.py');s=p.read_text().replace('Depends(get_optional_user)','Depends(get_current_user)');s=s.replace('from fastapi import APIRouter, HTTPException, Depends','from fastapi import APIRouter, HTTPException, Depends, Query\nfrom backend.app.paths import inside\nfrom backend.app.config import MAX_UPLOAD_BYTES')
s=s.replace('filename = req.filename.strip()','filename = req.filename\n    if len(req.content.encode("utf-8")) > MAX_UPLOAD_BYTES:\n        raise HTTPException(413, "Upload exceeds size limit")')
s=s.replace('target_dir = default_dataset_manager.uploads_dir / current_user.id','target_dir = inside(default_dataset_manager.uploads_dir, current_user.id)').replace('target_path = target_dir / filename','target_path = inside(default_dataset_manager.uploads_dir, current_user.id, filename)')
s=s.replace('target_path = KNOWLEDGE_DIR / filename','target_path = inside(KNOWLEDGE_DIR, current_user.id, filename)').replace('KNOWLEDGE_DIR.mkdir(parents=True, exist_ok=True)','target_path.parent.mkdir(parents=True, exist_ok=True)').replace('default_retriever.refresh()','get_user_retriever(current_user.id).refresh()')
s=s.replace('from backend.app.rag.retriever import default_retriever','from backend.app.rag.retriever import get_user_retriever')
s=s.replace('def get_dataset_changes():','def get_dataset_changes(current_user: User = Depends(get_current_user)):').replace('return default_dataset_manager.get_activity_log()','return default_dataset_manager.get_activity_log(current_user.id)')
s=s.replace('user_sessions = [s for s in default_session_store._sessions.values() if s.user_id == current_user.id]', 'user_sessions = [default_session_store.get_session(s["session_id"], current_user.id) for s in default_session_store.list_sessions(current_user.id)]')
s=s.replace('page: int = 1','page: int = Query(1, ge=1)').replace('page_size: int = 50','page_size: int = Query(50, ge=1, le=200)').replace('sort_order: str = "asc"','sort_order: str = Query("asc", pattern="^(asc|desc)$")').replace('limit: int = 8','limit: int = Query(8, ge=1, le=100)')
s=s.replace('    session = default_session_store.create_session(', '    try:\n        default_dataset_manager._resolve_path(request.dataset_name, current_user.id)\n    except (ValueError, FileNotFoundError):\n        raise HTTPException(404, "Dataset not found")\n    session = default_session_store.create_session(')
s=re.sub(r'detail=f"[^"\n]*\{e\}[^"\n]*"', 'detail="Request could not be processed"', s)
p.write_text(s)
p=Path('backend/app/api/schemas.py');s=p.read_text().replace('from pydantic import BaseModel','from pydantic import BaseModel, Field, field_validator, ConfigDict\nfrom typing import Literal\nfrom backend.app.paths import filename as validate_filename\nfrom backend.app.config import MAX_UPLOAD_BYTES\n\nclass RequestModel(BaseModel):\n    model_config = ConfigDict(extra="forbid", str_strip_whitespace=False)')
for name in ['QuestionRequest','CreateSessionRequest','UploadDatasetRequest','CellUpdate','UpdateDatasetRequest','AddRowRequest','CreateWidgetRequest','PinWidgetRequest']:
    s=s.replace(f'class {name}(BaseModel):',f'class {name}(RequestModel):')
s=s.replace('    question: str','    question: str = Field(min_length=1, max_length=12000)').replace('    prompt: str','    prompt: str = Field(min_length=1, max_length=12000)').replace('    chart_theme: str = "light"','    chart_theme: Literal["light", "dark"] = "light"').replace('    provider: Optional[str] = None','    provider: Optional[Literal["groq", "gemini"]] = None').replace('    row_index: int','    row_index: int = Field(ge=0)').replace('    updates: List[CellUpdate]','    updates: List[CellUpdate] = Field(min_length=1, max_length=1000)').replace('    content: str','    content: str = Field(min_length=1, max_length=MAX_UPLOAD_BYTES)')
s=s.replace('class UploadResponse(BaseModel):','    @field_validator("filename")\n    @classmethod\n    def safe_filename(cls, value):\n        return validate_filename(value)\n\n\nclass UploadResponse(BaseModel):')
s=s.replace('class SessionResponse(BaseModel):','    @field_validator("dataset_name")\n    @classmethod\n    def safe_dataset(cls, value):\n        return validate_filename(value) if value is not None else value\n\n\nclass SessionResponse(BaseModel):')
p.write_text(s)
# Each retrieval uses a private index; no shared mutable vocabulary or stale cross-worker cache.
p=Path('backend/app/rag/retriever.py');s=p.read_text();s+='''
def get_user_retriever(user_id):
    from backend.app.config import KNOWLEDGE_DIR
    from backend.app.paths import inside
    return DocumentRetriever(DocumentIndexer(inside(KNOWLEDGE_DIR, user_id)))
''';p.write_text(s)
p=Path('backend/app/tools/rag_tools.py');s=p.read_text().replace('from backend.app.rag.retriever import default_retriever','from backend.app.rag.retriever import get_user_retriever').replace('top_k: int = 3)','top_k: int = 3, user_id: str = None)').replace('    return default_retriever.search(query, top_k=top_k)','    if not user_id:\n        raise ValueError("User required for retrieval")\n    return get_user_retriever(user_id).search(query, top_k=min(max(top_k, 1), 20))');p.write_text(s)
p=Path('backend/app/agent/coordinator.py');s=p.read_text().replace('raw_result = tool_fn(**params)','params.pop("user_id", None)\n                    raw_result = tool_fn(**params, user_id=session.user_id)').replace('rag_tool(query=question)','rag_tool(query=question, user_id=session.user_id)');p.write_text(s)
