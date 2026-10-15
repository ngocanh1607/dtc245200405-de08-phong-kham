import importlib.util
import os
import re
from datetime import datetime, timedelta
from pathlib import Path

import pytest
from sqlalchemy import text

@pytest.fixture(scope='module')
def module(tmp_path_factory):
    path = tmp_path_factory.mktemp('clinic')
    os.environ.update(SECRET_KEY='test-key-only', DATABASE_URL='sqlite:///'+str(path/'test.db'),
        LOG_DIR=str(path/'logs'), ADMIN_PASSWORD='StrongTestAdmin123',
        RECEPTION_PASSWORD='StrongTestReception123', ENABLE_DEMO='true')
    spec=importlib.util.spec_from_file_location('server', Path(__file__).resolve().parents[1]/'app/server.py')
    m=importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    m.app.root_path=str(Path(__file__).resolve().parents[1]/'app')
    sql=(Path(__file__).resolve().parents[1]/'db/01-init.sh').read_text()
    with m.engine.begin() as c:
        c.execute(text('PRAGMA foreign_keys=ON'))
        for line in sql.splitlines():
            if line.startswith(('CREATE TABLE','CREATE UNIQUE INDEX')):
                c.execute(text(line.replace('SERIAL PRIMARY KEY','INTEGER PRIMARY KEY AUTOINCREMENT')))
    with m.app.app_context():
        result=m.app.test_cli_runner().invoke(args=['seed'])
        assert result.exit_code == 0, result.output
    return m

def token(client):
    html=client.get('/login').get_data(as_text=True)
    return re.search(r'name="csrf_token" value="([^"]+)"',html)[1]

def login(client, username='admin'):
    csrf=token(client)
    password='StrongTestAdmin123' if username=='admin' else 'StrongTestReception123'
    result=client.post('/login',data={'username':username,'password':password,'csrf_token':csrf})
    assert result.status_code==302
    html=client.get('/').get_data(as_text=True)
    return re.search(r'name="csrf_token" value="([^"]+)"',html)[1]

def test_auth_csrf_and_roles(module):
    c=module.app.test_client()
    assert c.get('/').status_code==302
    assert c.post('/login',data={'username':'admin'}).status_code==400
    csrf=login(c,'letan')
    assert c.post('/doctors',data={'name':'Unauthorized','specialty':'X','csrf_token':csrf}).status_code==403
    assert c.post('/demo-error',data={'csrf_token':csrf}).status_code==403

def test_patient_validation_and_edit(module):
    c=module.app.test_client();csrf=login(c)
    c.post('/patients/save',data={'csrf_token':csrf,'name':'Invalid','phone':'abc','birth_date':'2000-01-01'})
    assert not module.rows("SELECT 1 FROM patients WHERE name='Invalid'")
    c.post('/patients/save',data={'csrf_token':csrf,'name':'New','phone':'0900000002','birth_date':'2000-01-01'})
    p=module.rows("SELECT * FROM patients WHERE phone='0900000002'")[0]
    c.post('/patients/save',data={'csrf_token':csrf,'id':p['id'],'name':'Changed','phone':'0900000002','birth_date':'2000-01-01'})
    assert module.rows('SELECT name FROM patients WHERE id=:id',id=p['id'])[0]['name']=='Changed'

def test_slot_conflict_and_cancel(module):
    c=module.app.test_client();csrf=login(c)
    at=(datetime.now()+timedelta(days=2)).replace(hour=9,minute=0,second=0,microsecond=0)
    data={'csrf_token':csrf,'patient_id':'1','doctor_id':'1','starts_at':at.strftime('%Y-%m-%dT%H:%M')}
    c.post('/appointments',data=data);c.post('/appointments',data=data)
    result=module.rows('SELECT * FROM appointments')
    assert len(result)==1
    # Reject same patient with another doctor at the same time.
    c.post('/appointments',data={**data,'doctor_id':'2'})
    assert len(module.rows('SELECT * FROM appointments'))==1
    c.post('/appointments/'+str(result[0]['id'])+'/status',data={'csrf_token':csrf,'status':'cancelled'})
    c.post('/appointments',data=data)
    assert len(module.rows("SELECT * FROM appointments WHERE status='booked'"))==1
    c.post('/patients/1/delete',data={'csrf_token':csrf})
    assert module.rows('SELECT 1 FROM patients WHERE id=1')

def test_metrics_demo_and_html_escaping(module):
    c=module.app.test_client();csrf=login(c)
    c.post('/doctors',data={'csrf_token':csrf,'name':'<script>alert(1)</script>','specialty':'Test'})
    html=c.get('/').get_data(as_text=True)
    assert '<script>alert(1)</script>' not in html
    assert '&lt;script&gt;' in html
    assert c.post('/demo-error',data={'csrf_token':csrf}).status_code==503
    assert b'clinic_http_requests_total' in c.get('/metrics').data
    assert c.get('/healthz').json['database']=='connected'
