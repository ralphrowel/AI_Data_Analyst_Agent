"""Deterministic replacements for scratch steps 4–7 and embedding discovery."""
import json
from types import SimpleNamespace as NS
import pytest

def reply(text):
    return NS(choices=[NS(message=NS(content=text))], usage=NS(prompt_tokens=5, completion_tokens=2, total_tokens=7)), 'groq'

@pytest.mark.parametrize('question,expected', [
    ('How many rows?', 'structured'), ('What does rating mean?', 'rag'),
    ('Count ratings and explain the methodology', 'hybrid')])
def test_router_fallback(monkeypatch, question, expected):
    from backend.app.agent import router
    def unavailable(*args, **kwargs): raise RuntimeError('offline')
    monkeypatch.setattr(router,'call_llm',unavailable)
    assert router.QueryRouter().route(question) == expected

def test_router_llm(monkeypatch):
    from backend.app.agent import router
    monkeypatch.setattr(router,'call_llm',lambda *a,**k:reply('{"route":"hybrid"}'))
    assert router.QueryRouter().route('Compare and explain') == 'hybrid'

@pytest.mark.parametrize('route,decision', [
    ('structured', {'tool':'get_unique_values','parameters':{'column':'category'}}),
    ('rag', None),
    ('hybrid', {'tool':'get_unique_values','parameters':{'column':'category'}}),
    ('structured', {'tool':'unsupported','parameters':{'reason':'Unavailable data'}}),
])
def test_analysis_pipeline(client,auth,monkeypatch,route,decision):
    from backend.app.agent.coordinator import default_coordinator
    from backend.app.llm import client as llm
    monkeypatch.setattr(default_coordinator.router,'route',lambda *a,**k:route)
    responses = ([reply(json.dumps(decision))] if decision else [])
    if not decision or decision['tool'] != 'unsupported': responses += [reply('The dataset has one movie and one show.')]
    pending=iter(responses)
    monkeypatch.setattr(llm,'_call_llm',lambda *a,**k:next(pending))
    sid=client.post('/api/sessions',headers=auth,json={}).json()['session_id']
    response=client.post('/api/ask',headers=auth,json={'question':'Count categories','session_id':sid,'provider':'groq'})
    assert response.status_code == 200,response.text
    result=response.json()
    assert result['summary']
    details=client.get(f'/api/sessions/{sid}',headers=auth).json()
    assert len(details['history']) == 2
    assert details['token_usage']['total_tokens'] == len(responses)*7
    assert client.get('/api/user/quota',headers=auth).json()['tokens_used'] == len(responses)*7
    if decision and decision['tool'] == 'get_unique_values':
        assert result['chart_base64']
        assert '<svg' in result['chart_svg']

def test_widget_persistence_and_recompute(client,auth,monkeypatch):
    from backend.app.llm import client as llm
    monkeypatch.setattr(llm,'_call_llm',lambda *a,**k:reply(json.dumps({
        'title':'Categories','tool_name':'get_unique_values',
        'parameters':{'column':'category'},'chart_type':'bar'})))
    sid=client.post('/api/sessions',headers=auth,json={}).json()['session_id']
    response=client.post(f'/api/sessions/{sid}/widgets',headers=auth,json={'prompt':'Count categories'})
    assert response.status_code == 200,response.text
    widget=response.json()
    assert widget['chart_base64']
    assert client.get(f'/api/sessions/{sid}/widgets',headers=auth).json()[0]['id'] == widget['id']
    assert client.post(f'/api/sessions/{sid}/widgets/recompute',headers=auth).status_code == 200
    assert client.get('/api/user/quota',headers=auth).json()['tokens_used'] == 7
    assert client.delete(f'/api/sessions/{sid}/widgets/{widget["id"]}',headers=auth).status_code == 200

def test_tfidf_vectors(tmp_path):
    import numpy as np
    from backend.app.rag.indexer import DocumentIndexer
    from backend.app.rag.retriever import DocumentRetriever
    (tmp_path/'guide.md').write_text('# Ratings\nRatings classify audience suitability.\n\n# Stock\nInventory counts available products.')
    indexer=DocumentIndexer(tmp_path)
    retriever=DocumentRetriever(indexer)
    assert len(indexer.chunks) == 2
    assert all(np.isclose(np.linalg.norm(c.vector),1) for c in indexer.chunks)
    assert retriever.search('audience ratings')[0]['title'] == 'Ratings'
    assert retriever.search('unmatchableword') == []

def test_suggestions_are_metered(client,auth,monkeypatch):
    from backend.app.llm import client as llm
    monkeypatch.setattr(llm,'_call_llm',lambda *a,**k:reply('["Count rows", "Sum value", "List titles", "Compare categories"]'))
    assert len(client.get('/api/suggestions',headers=auth).json()) == 4
    assert client.get('/api/user/quota',headers=auth).json()['tokens_used'] == 7

@pytest.mark.postgres
def test_postgres_concurrent_quota():
    import os
    if not os.getenv('TEST_DATABASE_URL'): pytest.skip('PostgreSQL service required')
    from concurrent.futures import ThreadPoolExecutor
    from backend.app.auth.quota_manager import QuotaManager
    with ThreadPoolExecutor(max_workers=8) as pool:
        list(pool.map(lambda _:QuotaManager().record_usage('alice',1),range(32)))
    assert QuotaManager().get_user_quota('alice')['tokens_used'] == 32
