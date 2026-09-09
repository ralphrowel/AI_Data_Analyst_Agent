from backend.app import storage
from backend.app.memory.session_store import SessionStore
from backend.app.auth.quota_manager import QuotaManager

def test_upload_edit_sessions_and_ownership(client, auth, token):
    bob={'Authorization':'Bearer '+token('bob')}
    upload=client.post('/api/upload',headers=auth,json={'filename':'inventory.csv','content':'product,price\na,10\nb,20\n'})
    assert upload.status_code == 200, upload.text
    assert upload.json()['rows'] == 2
    session=client.post('/api/sessions',headers=auth,json={'dataset_name':'inventory.csv'}).json()
    sid=session['session_id']
    assert client.get(f'/api/sessions/{sid}',headers=bob).status_code == 404
    assert client.delete(f'/api/sessions/{sid}',headers=bob).status_code == 404
    assert client.get('/api/datasets/inventory.csv/rows',headers=bob).status_code == 400
    assert client.post('/api/datasets/inventory.csv/update',headers=auth,json={'updates':[{'row_index':0,'column':'price','value':15}]}).status_code == 200
    assert client.get('/api/datasets/inventory.csv/rows',headers=auth).json()['rows'][0]['price'] == 15
    assert client.post('/api/datasets/inventory.csv/rows/add',headers=auth,json={'row_data':{'product':'c','price':30}}).status_code == 200
    assert client.delete('/api/datasets/inventory.csv/rows/1',headers=auth).json()['success']
    assert client.get('/api/dataset-changes',headers=bob).json() == []
    assert len(client.get('/api/dataset-changes',headers=auth).json()) == 4
    assert storage.get('datasets','alice','inventory.csv')['rows'] == 2
    assert storage.get('users','alice','alice')['email'] == 'alice@example.com'
    assert client.delete(f'/api/sessions/{sid}',headers=auth).status_code == 200

def test_shared_sample_copy_on_write(client, auth, token):
    response=client.post('/api/datasets/netflix_titles.csv/update',headers=auth,
        json={'updates':[{'row_index':0,'column':'value','value':99}]})
    assert response.status_code == 200, response.text
    bob={'Authorization':'Bearer '+token('bob')}
    assert client.get('/api/datasets/netflix_titles.csv/rows',headers=bob).json()['rows'][0]['value'] == 10
    assert client.get('/api/datasets/netflix_titles.csv/rows',headers=auth).json()['rows'][0]['value'] == 99

def test_sessions_and_quota_survive_new_instances():
    first=SessionStore(); session=first.create_session(user_id='alice')
    first.add_turn(session.session_id,'user','hello')
    first.update_tokens(session.session_id,{'total_tokens':7,'prompt_tokens':5,'response_tokens':2},'groq')
    first.add_widget(session.session_id,{'id':'w','title':'Chart'})
    second=SessionStore(); restored=second.get_session(session.session_id,'alice')
    assert restored.history[0]['content'] == 'hello'
    assert restored.token_usage['total_tokens'] == 7
    assert restored.widgets[0]['id'] == 'w'
    QuotaManager().record_usage('alice',123)
    assert QuotaManager().get_user_quota('alice')['tokens_used'] == 123
    assert QuotaManager().get_user_quota('bob')['tokens_used'] == 0

def test_private_rag_upload(client,auth,token):
    from backend.app.tools.rag_tools import search_documents
    response=client.post('/api/upload',headers=auth,json={'filename':'secret.md','content':'# Alice\nQuasar proprietary inventory methodology.'})
    assert response.status_code == 200,response.text
    assert search_documents('Quasar',user_id='alice')
    assert search_documents('Quasar',user_id='bob') == []

def test_quota_guard(client,auth):
    from backend.app.auth.quota_manager import default_quota_manager
    default_quota_manager.record_usage('alice', default_quota_manager.default_limit)
    assert client.post('/api/ask',headers=auth,json={'question':'Count rows'}).status_code == 429
