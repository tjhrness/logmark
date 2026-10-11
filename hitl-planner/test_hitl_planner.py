import importlib
import json
import subprocess
import sys
import socket
import http.client
import time
from pathlib import Path

import pytest

import hitl_planner as hp


def test_log_failure_response_and_all_issue_prefill_boundary(tmp_path,monkeypatch):
    client=hp.create_app({'schema_version':1,'workspace':str(tmp_path),'port':5062}).test_client()
    info=hp.save_plan(tmp_path,scenario(system='All issues',N=100))
    hp.save_actuals(tmp_path,info['plan_id'],dict(reviewed=100,issues=100,agreement=1,notes=''))
    result=client.get('/api/prefill?system=All%20issues').json
    assert result['inputs']['p']==1
    assert client.post('/api/calc',json={**result['inputs'],'N':100}).status_code==400
    path=tmp_path/'plans_log.csv';before=path.read_bytes()
    replace=hp.os.replace
    def fail(source,target):
        if Path(target).name=='plans_log.csv':
            raise PermissionError('Excel has locked the CSV')
        return replace(source,target)
    monkeypatch.setattr(hp.os,'replace',fail)
    response=client.get('/api/log/rebuild')
    assert response.status_code==503 and response.is_json
    assert path.read_bytes()==before and not list(tmp_path.glob('*.tmp'))


def test_full_isolated_lifecycle_all_fifteen_endpoints(tmp_path,monkeypatch):
    import csv
    import threading
    config=hp.load_config(tmp_path/'config.json',home=tmp_path)
    config['port']=5062
    client=hp.create_app(config).test_client()
    assert client.get('/').status_code==200
    assert client.get('/api/health').json['workspace_ok']
    assert client.post('/api/calc',json=scenario()).json['outputs']['n_headline']==382
    v1=client.post('/api/plans',json=scenario()).json
    folder=Path(v1['folder']);original=(folder/'plan_v1.json').read_bytes()
    assert client.post('/api/plans',json=scenario()).json['version']==2
    assert (folder/'plan_v1.json').read_bytes()==original
    assert client.get('/api/plans').json[0]['version']==2
    detail=client.get('/api/plans/'+v1['plan_id']).json
    assert detail['plan']['plan']['version']==2
    assert client.get('/api/systems').json==['HR Helpdesk Bot']
    assert client.get('/api/prefill?system=HR%20Helpdesk%20Bot').json['inputs']['N'] is None
    data=dict(plan_id=v1['plan_id'],plan_version=2,reviewed=382,issues=11,agreement=.86,notes='Calibration, complete\n第二行')
    assert client.post('/api/actuals/calc',json=data).json['outputs']['display']['observed_rate']=='2.9%'
    assert client.post('/api/plans/'+v1['plan_id']+'/actuals',json=data).json['version']==1
    old_actuals=(folder/'actuals_v1.json').read_bytes()
    assert client.post('/api/plans/'+v1['plan_id']+'/actuals',json=data).json['version']==2
    assert (folder/'actuals_v1.json').read_bytes()==old_actuals
    assert '<h2>Actuals</h2>' in (folder/'report.html').read_text(encoding='utf-8')
    prefill=client.get('/api/prefill?system=hr%20helpdesk%20bot').json
    assert prefill['p_source']=='last_observed' and prefill['inputs']['p']==11/382
    rebuilt=client.get('/api/log/rebuild').json
    assert rebuilt['rows']==1 and Path(rebuilt['path']).read_bytes().startswith(b'\xef\xbb\xbf')
    with Path(rebuilt['path']).open(encoding='utf-8-sig',newline='') as stream:
        row=next(csv.DictReader(stream))
    assert row['plan_version']=='2' and row['actuals_version']=='2' and row['notes']==data['notes']
    opened=[];monkeypatch.setattr(hp.os,'startfile',lambda p:opened.append(p),raising=False)
    for endpoint in ('open-report','open-folder'):
        assert client.post('/api/'+endpoint,json={'plan_id':v1['plan_id']}).json['ok']
    assert opened==[v1['report_path'],v1['folder']]
    assert client.get('/api/method').json['integrity_check']=={'passed':11,'total':11}
    stopped=threading.Event();client.application.config['SHUTDOWN_CALLBACK']=stopped.set
    assert client.post('/api/quit').json=={'ok':True} and stopped.wait(1)
    assert set(config)=={'schema_version','workspace','port'}


def test_offline_assets_and_accessible_tab_contract(tmp_path):
    from html.parser import HTMLParser
    class Assets(HTMLParser):
        def __init__(self):
            super().__init__();self.external=[];self.tabs=[];self.panels=[]
        def handle_starttag(self,tag,attrs):
            attrs=dict(attrs)
            self.external.extend(v for k,v in attrs.items() if k in ('href','src','action') and v and v.startswith(('http:','https:','//')))
            if attrs.get('role')=='tab':
                self.tabs.append(attrs)
            if attrs.get('role')=='tabpanel':
                self.panels.append(attrs)
    client=hp.create_app({'schema_version':1,'workspace':str(tmp_path),'port':5062}).test_client()
    root=Assets();root.feed(client.get('/').text)
    assert not root.external and len(root.tabs)==4 and len(root.panels)==4
    assert {t['aria-controls'] for t in root.tabs}=={p['id'] for p in root.panels}
    info=hp.save_plan(tmp_path,scenario())
    report=Assets();report.feed(Path(info['report_path']).read_text(encoding='utf-8'))
    assert not report.external


def test_concurrent_plan_actuals_collision_and_statelessness(tmp_path):
    from concurrent.futures import ThreadPoolExecutor
    app=hp.create_app({'schema_version':1,'workspace':str(tmp_path),'port':5062})
    def save(system):
        with app.test_client() as client:
            response=client.post('/api/plans',json=scenario(system=system))
            assert response.status_code==200
            return response.json
    with ThreadPoolExecutor(max_workers=4) as pool:
        infos=list(pool.map(save,['A/B','A:B','A/B','A:B']))
    assert {i['plan_id'] for i in infos}=={'2026-10 - AB','2026-10 - AB (2)'}
    for folder in (tmp_path/'2026-10 - AB',tmp_path/'2026-10 - AB (2)'):
        assert len(list(folder.glob('plan_v*.json')))==2
    info=infos[0]
    original={p:p.read_bytes() for p in tmp_path.rglob('plan_v*.json')}
    def actual(count):
        with app.test_client() as client:
            response=client.post('/api/plans/'+info['plan_id']+'/actuals',json=dict(reviewed=382,issues=count,agreement=.86,notes=''))
            assert response.status_code==200
            return response.json['version']
    with ThreadPoolExecutor(max_workers=2) as pool:
        versions=list(pool.map(actual,[0,11]))
    assert sorted(versions)==[1,2]
    assert original=={p:p.read_bytes() for p in tmp_path.rglob('plan_v*.json')}
    with app.test_client() as client:
        a=client.post('/api/calc',json=scenario(system='First')).json
        client.post('/api/calc',json=scenario(system='Second',N=1))
        assert client.post('/api/calc',json=scenario(system='First')).json==a
    assert not (tmp_path/'.write-lock').exists() and not list(tmp_path.rglob('*.tmp'))


def test_api_failure_resilience_workspace_recovery_and_json_errors(tmp_path,monkeypatch):
    app=hp.create_app({'schema_version':1,'workspace':str(tmp_path),'port':5062})
    client=app.test_client()
    assert client.get('/missing').status_code==404 and client.get('/missing').is_json
    assert client.post('/api/plans',data='{',content_type='application/json').status_code==400
    health=hp.workspace_health
    monkeypatch.setattr(hp,'workspace_health',lambda w:(False,'Drive is full: '+str(w)))
    response=client.get('/api/health')
    assert response.json['workspace_ok'] is False
    assert 'Drive is full' in client.get('/').text
    assert client.post('/api/plans',json=scenario()).status_code==503
    assert not list(tmp_path.rglob('plan_v*.json'))
    assert client.post('/api/calc',json=scenario()).status_code==200
    monkeypatch.setattr(hp,'workspace_health',health)
    assert client.get('/api/health').json['workspace_ok'] is True
    assert client.post('/api/plans',json=scenario()).status_code==200
    def fail(*args,**kwargs):
        raise RuntimeError('private traceback detail')
    monkeypatch.setattr(hp,'calculate_response',fail)
    response=client.post('/api/calc',json=scenario())
    assert response.status_code==500 and response.json=={'error':'Unexpected error','details':'RuntimeError'}
    assert 'Traceback' not in response.text and 'private traceback' not in response.text


def test_corrupt_record_types_and_invalid_config_schema(tmp_path):
    info=hp.save_plan(tmp_path,scenario())
    original=Path(info['folder'])/'plan_v1.json'
    record=json.loads(original.read_text(encoding='utf-8'))
    record['plan']['version']=2
    record['outputs']['n_headline']='bad'
    hp.write_json(Path(info['folder'])/'plan_v2.json',record,immutable=True)
    assert hp.list_plans(tmp_path)[0]['unreadable']
    config=tmp_path/'bad-config.json'
    hp.atomic_write(config,json.dumps(dict(schema_version=True,workspace=str(tmp_path),port=5062)))
    before=config.read_bytes()
    with pytest.raises(hp.ConfigError):
        hp.load_config(config)
    assert config.read_bytes()==before


def test_selftest_process_and_injected_failure_gate(tmp_path,monkeypatch,capsys):
    process=subprocess.run([sys.executable,str(Path(hp.__file__).resolve()),'--selftest'],cwd=tmp_path,capture_output=True,text=True,timeout=10)
    assert process.returncode==0 and process.stdout.count('PASS K')==11
    assert list(tmp_path.iterdir())==[]
    info=hp.save_plan(tmp_path,scenario())
    original=(Path(info['folder'])/'plan_v1.json').read_bytes()
    monkeypatch.setitem(hp.Z,.95,1.95996)
    assert hp.main(['--selftest'])==1
    assert 'FAIL K1' in capsys.readouterr().out
    client=hp.create_app({'schema_version':1,'workspace':str(tmp_path),'port':5062}).test_client()
    assert 'Answer key failed: cases' in client.get('/').text
    assert 'Results cannot be trusted; saving is disabled.' in client.get('/').text
    status=client.get('/api/method').json
    assert status['integrity_check']['passed']<11 and 'K1' in status['failed_cases']
    assert client.post('/api/plans',json=scenario()).status_code==503
    assert client.post('/api/plans/'+info['plan_id']+'/actuals',json=dict(reviewed=382,issues=0,agreement=.8,notes='')).status_code==503
    assert client.post('/api/calc',json=scenario()).status_code==200
    assert (Path(info['folder'])/'plan_v1.json').read_bytes()==original
    assert not list(tmp_path.rglob('actuals_v*.json'))


def test_method_api_and_live_trace_contract(tmp_path):
    client=hp.create_app({'schema_version':1,'workspace':str(tmp_path),'port':5062}).test_client()
    response=client.get('/api/method')
    assert response.status_code==200
    method=response.json
    assert method['constants']['Z']=={'0.90':1.645,'0.95':1.960,'0.99':2.576}
    assert set(method['formulas'])=={f'F{i}' for i in range(1,11)}
    assert method['method_version']=='1.0' and method['tool_version']=='1.0.0'
    assert method['integrity_check']=={'passed':11,'total':11}
    assert 'Cochran' in method['references'][0] and len(method['assumptions'])==6
    html=client.get('/').text
    for name in ('method-integrity','method-formulas','method-assumptions','method-arithmetic','method-references'):
        assert f'id="{name}"' in html
    absolute=client.post('/api/calc',json=scenario()).json
    assert any('382' in line for line in absolute['arithmetic'])
    relative=client.post('/api/calc',json=scenario(margin_mode='relative',margin_input=.25,p=.04)).json
    assert any('0.01' in line for line in relative['arithmetic'])


def test_history_csv_prefill_consistency_with_corrupt_actuals(tmp_path):
    import csv
    client=hp.create_app({'schema_version':1,'workspace':str(tmp_path),'port':5062}).test_client()
    valid=hp.save_plan(tmp_path,scenario(system='Valid'))
    hp.save_plan(tmp_path,scenario(system='Second'))
    hp.save_plan(tmp_path,scenario(system='Third'))
    hp.save_actuals(tmp_path,valid['plan_id'],dict(reviewed=382,issues=11,agreement=.86,notes=''))
    broken=hp.save_plan(tmp_path,scenario(system='Broken'))
    hp.atomic_write(Path(broken['folder'])/'actuals_v1.json','{')
    damaged=(Path(broken['folder'])/'actuals_v1.json').read_bytes()
    rows=client.get('/api/plans').json
    normal=next(r for r in rows if r['system']=='Valid')
    assert normal['warnings']==['W2','W9']
    assert normal['actuals']['outputs']['display']['observed_rate']=='2.9%'
    assert next(r for r in rows if r['plan_id']==broken['plan_id'])['unreadable']
    assert 'Broken' not in client.get('/api/systems').json
    assert client.get('/api/prefill?system=broken').json=={}
    rebuilt=client.get('/api/log/rebuild').json
    assert rebuilt['rows']==3
    with Path(rebuilt['path']).open(encoding='utf-8-sig',newline='') as stream:
        log=next(r for r in csv.DictReader(stream) if r['system']=='Valid')
    assert float(log['hours'])==normal['hours'] and int(log['n_headline'])==normal['n_headline']
    assert log['warnings']==';'.join(normal['warnings'])
    assert (Path(broken['folder'])/'actuals_v1.json').read_bytes()==damaged


def test_csv_log_exact_schema_roundtrip_rebuild_and_failure(tmp_path,monkeypatch,capsys):
    import csv
    columns='plan_id,period_type,period_label,system,plan_version,saved_at,N,confidence,margin_mode,margin_input,E_effective,p,p_source,certify,threshold,smes,hours_per_sme,minutes_per_conversation,dr_share,dr_floor,n_cochran,n_assure,n_headline,binding,dr_count,reviews,hours,capacity,verdict,n_max_at_capacity,margin_at_capacity,threshold_at_capacity,detection_power,warnings,actuals_version,recorded_at,reviewed,issues,observed_rate,achieved_margin,certify_status,agreement,notes'.split(',')
    client=hp.create_app({'schema_version':1,'workspace':str(tmp_path),'port':5062}).test_client()
    a=hp.save_plan(tmp_path,scenario(system='日本語, A',period_label='2026-09'))
    hp.save_plan(tmp_path,scenario(system='Z',period_label='2026-10'))
    hp.save_plan(tmp_path,scenario(system='A',period_label='2026-10',N=40,margin_input=.005))
    assert (tmp_path/'plans_log.csv').is_file()
    notes='Calibration, notes\nSecond line 日本語'
    hp.save_actuals(tmp_path,a['plan_id'],dict(reviewed=382,issues=11,agreement=.86,notes=notes))
    result=client.get('/api/log/rebuild').json
    assert result=={'path':str(tmp_path/'plans_log.csv'),'rows':3}
    path=Path(result['path']);original=path.read_bytes()
    assert original.startswith(b'\xef\xbb\xbf')
    with path.open(encoding='utf-8-sig',newline='') as stream:
        reader=csv.DictReader(stream);rows=list(reader)
        assert reader.fieldnames==columns and len(columns)==43
    assert [r['system'] for r in rows]==['A','Z','日本語, A']
    assert len(rows)==3 and rows[2]['notes']==notes
    assert rows[0]['warnings']=='W2;W4;W5;W6;W7'
    assert rows[1]['actuals_version']=='' and rows[2]['actuals_version']=='1'
    assert client.get('/api/log/rebuild').json['rows']==3 and path.read_bytes()==original
    broken=tmp_path/'2026-11 - Broken';broken.mkdir();hp.atomic_write(broken/'plan_v1.json','{')
    assert client.get('/api/log/rebuild').json['rows']==3
    assert 'Skipped unreadable' in capsys.readouterr().out
    replace=hp.os.replace
    def fail_csv(source,target):
        if Path(target).name=='plans_log.csv':
            raise PermissionError('CSV locked')
        return replace(source,target)
    monkeypatch.setattr(hp.os,'replace',fail_csv)
    response=client.post('/api/plans',json=scenario(system='New'))
    assert response.status_code==503 and 'saved' in response.json['error']
    assert (tmp_path/'2026-10 - New'/'plan_v1.json').is_file()
    assert path.read_bytes()==original
    monkeypatch.setattr(hp.os,'replace',replace)
    assert client.get('/api/log/rebuild').json['rows']==4


def test_actuals_browser_contract_controls_and_server_display(tmp_path):
    client=hp.create_app({'schema_version':1,'workspace':str(tmp_path),'port':5062}).test_client()
    html=client.get('/').text
    for field in ('actuals-plan','actuals-summary','actuals-form','reviewed','issues','agreement','notes','actuals-results','record-actuals','record-again'):
        assert f'id="{field}"' in html
    assert 'actualsTicket' in html and '/api/actuals/calc' in html
    assert 'Number' in html and '/100' in html
    info=hp.save_plan(tmp_path,scenario())
    data=dict(plan_id=info['plan_id'],reviewed=382,issues=11,agreement=.86,notes='')
    o=client.post('/api/actuals/calc',json=data).json['outputs']
    assert o['display']['observed_rate']=='2.9%' and o['display']['achieved_margin']=='±1.7%'


def test_actuals_saves_versions_report_and_recoverable_failure(tmp_path,monkeypatch):
    client=hp.create_app({'schema_version':1,'workspace':str(tmp_path),'port':5062}).test_client()
    info=hp.save_plan(tmp_path,scenario())
    folder=Path(info['folder'])
    plan_bytes=(folder/'plan_v1.json').read_bytes()
    hp.save_plan(tmp_path,scenario(N=100))
    route='/api/plans/'+info['plan_id']+'/actuals'
    data=dict(reviewed=382,issues=11,agreement=.86,notes='<script>&,\n日本語',plan_version=1)
    first=client.post(route,json=data)
    assert first.status_code==200 and first.json['version']==1
    original=(folder/'actuals_v1.json').read_bytes()
    saved=json.loads(original)
    assert saved['plan_version']==1 and saved['outputs']['observed_rate']==11/382
    assert client.post(route,json={**data,'issues':0}).json['version']==2
    assert original==(folder/'actuals_v1.json').read_bytes()
    assert plan_bytes==(folder/'plan_v1.json').read_bytes()
    html=(folder/'report.html').read_text(encoding='utf-8')
    assert '<h2>Actuals</h2>' in html and '&lt;script&gt;&amp;' in html
    assert '<script>' not in html and 'below' in html
    assert 'Recorded against plan version 1' in html and 'Plan version 2' in html
    assert client.get('/api/plans/'+info['plan_id']).json['actuals']['version']==2
    assert client.post(route,json={**data,'issues':400}).status_code==400
    assert client.post('/api/plans/unknown/actuals',json=data).status_code==404
    replace=hp.os.replace
    def fail_report(source,target):
        if Path(target).name=='report.html':
            raise PermissionError('report locked')
        return replace(source,target)
    monkeypatch.setattr(hp.os,'replace',fail_report)
    response=client.post(route,json=data)
    assert response.status_code==503 and 'saved' in response.json['error']
    assert (folder/'actuals_v3.json').is_file() and (folder/'actuals_v1.json').read_bytes()==original
    assert not list(folder.glob('*.tmp'))


def test_actuals_api_stateless_and_saved_plan_authority(tmp_path):
    client = hp.create_app({'schema_version':1,'workspace':str(tmp_path),'port':5062}).test_client()
    info=hp.save_plan(tmp_path,scenario())
    data=dict(plan_id=info['plan_id'],reviewed=382,issues=11,agreement=.86,notes='',N=1,confidence=.9,threshold=.5)
    before={p:p.read_bytes() for p in tmp_path.rglob('*') if p.is_file()}
    for _ in range(3):
        response=client.post('/api/actuals/calc',json=data)
        assert response.status_code==200
        assert set(response.json)=={'outputs','warnings'}
        o=response.json['outputs']
        assert o['observed_rate']==11/382
        assert o['achieved_margin']==pytest.approx(.0167,abs=.0001)
        assert o['certify_status'].startswith('not applicable')
        assert [w['code'] for w in response.json['warnings']]==['W9']
    assert before=={p:p.read_bytes() for p in tmp_path.rglob('*') if p.is_file()}
    assert client.post('/api/actuals/calc',json={**data,'issues':0}).json['outputs']['bound_statement']
    assert client.post('/api/actuals/calc',json={**data,'notes':3}).status_code==400
    assert client.post('/api/actuals/calc',json={**data,'plan_id':'unknown'}).status_code==404
    hp.save_plan(tmp_path,scenario(N=100))
    assert client.post('/api/actuals/calc',json=data).status_code==400
    assert client.post('/api/actuals/calc',json={**data,'plan_version':1}).status_code==200


@pytest.mark.parametrize('issues,status',[(0,'met'),(1,'not applicable (issues found; report the observed rate)'),(400,'not applicable (issues found; report the observed rate)')])
def test_actuals_extremes_and_shared_formulas(tmp_path,issues,status):
    info = hp.save_plan(tmp_path,scenario())
    path = Path(info['folder'])/'plan_v1.json'
    original = path.read_bytes()
    plan = json.loads(original)
    out = hp.calculate_actuals(plan,{'reviewed':400,'issues':issues,'agreement':.8,'notes':'safe'})
    o=out['outputs']
    assert o['observed_rate'] == issues/400 and o['certify_status'] == status
    if issues in (0,400):
        assert o['achieved_margin'] is None and o['bound_statement']
        assert ('below' if issues==0 else 'above') in o['bound_statement']
    else:
        assert o['achieved_margin'] == hp.reverse_margin(50000,400,1/400,.95)
    assert path.read_bytes() == original


def test_actuals_boundaries_relative_and_validation(tmp_path):
    info=hp.save_plan(tmp_path,scenario(p=.1,margin_mode='relative',margin_input=.25))
    plan=json.loads((Path(info['folder'])/'plan_v1.json').read_text(encoding='utf-8'))
    def calc(reviewed=1000,issues=100,agreement=.8):
        return hp.calculate_actuals(plan,dict(reviewed=reviewed,issues=issues,agreement=agreement,notes=''))
    for count,expected in ((200,False),(201,True),(50,False),(49,True)):
        assert ('W9' in [w['code'] for w in calc(issues=count)['warnings']]) is expected
    assert 'W10' not in [w['code'] for w in calc()['warnings']]
    assert 'W10' in [w['code'] for w in calc(agreement=.799)['warnings']]
    n=plan['outputs']['n_headline']
    assert 'W8' not in [w['code'] for w in calc(reviewed=n,issues=1)['warnings']]
    assert 'W8' in [w['code'] for w in calc(reviewed=n-1,issues=1)['warnings']]
    o=calc()['outputs']
    assert o['achieved_margin_relative'] == o['achieved_margin']/.1
    assert calc(reviewed=1,issues=0)['outputs']['certify_status'].startswith('not met')
    plan['inputs']['certify']=False
    assert calc(issues=0)['outputs']['certify_status'] == 'not planned'
    for changes in ({'reviewed':0},{'reviewed':50001},{'reviewed':True},{'issues':1001},{'issues':-1},{'agreement':float('nan')},{'agreement':1.01},{'notes':None}):
        data=dict(reviewed=1000,issues=100,agreement=.8,notes='');data.update(changes)
        with pytest.raises(hp.ValidationError):
            hp.calculate_actuals(plan,data)
    plan['inputs']['N']=1
    assert hp.calculate_actuals(plan,dict(reviewed=1,issues=1,agreement=1,notes=''))['outputs']['achieved_margin'] is None


def test_system_prefill_timestamp_matching_and_observed_history(tmp_path):
    old = hp.save_plan(tmp_path,scenario(system='HR Bot',period_label='2026-09',p=.04))
    new = hp.save_plan(tmp_path,scenario(system='HR Bot',period_label='2026-08',p=.03))
    client = hp.create_app({'schema_version':1,'workspace':str(tmp_path),'port':5062}).test_client()
    assert client.get('/api/prefill?system=unknown').json == {}
    result = client.get('/api/prefill?system=%20hr%20bot%20').json
    assert result['inputs']['p'] == .03 and result['p_source'] == 'last_planned'
    assert result['inputs']['N'] is None and result['inputs']['period_label'] == hp.initial_inputs()['period_label']
    assert old['plan_id'] not in result['prefilled_from']
    assert client.get('/api/systems').json == ['HR Bot']
    actual = {'schema_version':1,'recorded_at':'2026-10-10T08:00:00+05:30','plan_id':old['plan_id'],
              'plan_version':1,'version':1,'inputs':{'reviewed':100,'issues':0,'agreement':.8,'notes':''},
              'outputs':{'observed_rate':0},'warnings':[]}
    hp.write_json(Path(old['folder'])/'actuals_v1.json',actual,immutable=True)
    result = client.get('/api/prefill?system=HR%20Bot').json
    assert result['inputs']['p'] == .001 and result['p_source'] == 'last_observed'
    actual['version'] = 2
    actual['outputs']['observed_rate'] = .5
    actual['inputs']['issues'] = 50
    hp.write_json(Path(old['folder'])/'actuals_v2.json',actual,immutable=True)
    assert 'W2' not in [w['code'] for w in client.post('/api/calc',json=scenario(system='HR Bot')).json['warnings']]
    assert 'prefillTicket' in client.get('/').text


def test_history_ui_and_calendar_period_sorting(tmp_path):
    hp.save_plan(tmp_path,scenario(system='September',period_label='2026-09'))
    hp.save_plan(tmp_path,scenario(system='Week',period_type='week',period_label='2026-W40'))
    hp.save_plan(tmp_path,scenario(system='October',period_label='2026-10'))
    client = hp.create_app({'schema_version':1,'workspace':str(tmp_path),'port':5062}).test_client()
    assert [r['system'] for r in client.get('/api/plans').json] == ['October','Week','September']
    html = client.get('/').text
    for control in ('history-filter','history-table','history-notice'):
        assert f'id="{control}"' in html
    assert 'async function loadSavedPlan' in html
    assert 'toLocaleLowerCase().includes' in html
    assert "encodeURIComponent(planId)" in html


def test_plan_read_model_numeric_latest_corruption_and_identity(tmp_path):
    app = hp.create_app({'schema_version':1,'workspace':str(tmp_path),'port':5062})
    client = app.test_client()
    a = hp.save_plan(tmp_path,scenario(system='Case Preserved',period_label='2026-08'))
    hp.save_plan(tmp_path,scenario(system='Other',period_label='2026-09'))
    hp.save_plan(tmp_path,scenario(system='Third',period_label='2026-10'))
    folder = Path(a['folder'])
    record = json.loads((folder/'plan_v1.json').read_text(encoding='utf-8'))
    for version in (9,10):
        record['plan']['version'] = version
        hp.write_json(folder/f'plan_v{version}.json',record,immutable=True)
    corrupt = tmp_path / '2026-11 - Broken'
    corrupt.mkdir()
    hp.atomic_write(corrupt/'plan_v1.json','{')
    before = {p:p.read_bytes() for p in tmp_path.rglob('*.json')}
    rows = client.get('/api/plans').json
    assert len(rows) == 4
    row = next(r for r in rows if r['plan_id']==a['plan_id'])
    assert row['version'] == 10 and row['system'] == 'Case Preserved'
    assert row['n_headline'] == 382 and row['actuals'] is None and row['unreadable'] is None
    assert next(r for r in rows if r['plan_id']==corrupt.name)['unreadable']
    detail = client.get('/api/plans/'+a['plan_id'])
    assert detail.json['plan']['plan']['version'] == 10
    assert detail.json['actuals'] is None
    assert client.get('/api/plans/missing').status_code == 404
    assert before == {p:p.read_bytes() for p in tmp_path.rglob('*.json')}


def test_save_ui_and_safe_open_actions(tmp_path,monkeypatch):
    app = hp.create_app({'schema_version':1,'workspace':str(tmp_path),'port':5062})
    client = app.test_client()
    html = client.get('/').text
    assert "$('save-plan').onclick" in html and "$('save-plan').disabled=false" in html
    info = client.post('/api/plans',json=scenario()).json
    opened = []
    monkeypatch.setattr(hp.os,'startfile',lambda path: opened.append(path),raising=False)
    for route in ('open-report','open-folder'):
        assert client.post('/api/'+route,json={'plan_id':info['plan_id']}).json == {'ok':True}
        assert client.post('/api/'+route,json={'plan_id':'missing'}).status_code == 404
        for bad in ('../outside','a/b','a\\b','..'):
            assert client.post('/api/'+route,json={'plan_id':bad}).status_code == 400
    assert opened == [info['report_path'],info['folder']]
    def fail(path):
        raise OSError('No association')
    monkeypatch.setattr(hp.os,'startfile',fail)
    assert client.post('/api/open-report',json={'plan_id':info['plan_id']}).json == {'ok':False,'path':info['report_path']}


def test_standalone_report_escaped_complete_latest(tmp_path):
    from html import escape
    info = hp.save_plan(tmp_path,scenario(system='<Bot>&'))
    html = Path(info['report_path']).read_text(encoding='utf-8')
    assert '<style>' in html and '@media print' in html and 'size:A4' in html
    assert '<script' not in html and 'http://' not in html and 'https://' not in html
    assert '&lt;Bot&gt;&amp;' in html and '<Bot>' not in html
    saved = json.loads((Path(info['folder'])/'plan_v1.json').read_text(encoding='utf-8'))
    assert all(escape(s) in html for s in saved['statements'])
    headings = ['Inputs','Headline and verdict','Trade-off','Sensitivity grid','Assurance and detection',
                'Statements','Warnings','Arithmetic','Formulas and constants','References']
    positions = [html.index('<h2>'+h+'</h2>') for h in headings]
    assert positions == sorted(positions)
    assert 'Actuals' not in html
    hp.save_plan(tmp_path,scenario(system='<Bot>&',N=100))
    html = Path(info['report_path']).read_text(encoding='utf-8')
    assert 'Plan version 2' in html and 'value="100"' not in html


def test_plan_save_route_versions_recalculate_and_schema(tmp_path):
    import datetime
    client = hp.create_app({'schema_version':1,'workspace':str(tmp_path),'port':5062}).test_client()
    inputs = scenario(outputs={'n_headline':1}, integrity_check={'passed':0})
    first = client.post('/api/plans',json=inputs)
    assert first.status_code == 200
    info = first.json
    assert set(info) == {'plan_id','version','folder','report_path'}
    path = Path(info['folder']) / 'plan_v1.json'
    original = path.read_bytes()
    record = json.loads(original)
    assert record['outputs'] == client.post('/api/calc',json=scenario()).json['outputs']
    assert record['outputs']['n_headline'] == 382
    assert datetime.datetime.fromisoformat(record['saved_at']).utcoffset() is not None
    assert record['integrity_check'] == {'passed':11,'total':11}
    assert len(record['method']['formulas']) == 10 and len(record['statements']) == 7
    assert Path(info['report_path']).is_file()
    second = client.post('/api/plans',json=inputs)
    assert second.json['version'] == 2 and path.read_bytes() == original
    assert client.post('/api/plans',json=scenario(N=0)).status_code == 400
    warning = client.post('/api/plans',json=scenario(N=2000,threshold=.001))
    assert warning.status_code == 200
    saved = json.loads((Path(warning.json['folder']) / 'plan_v3.json').read_text(encoding='utf-8'))
    assert 'W7' in [w['code'] for w in saved['warnings']]


def test_concurrent_plan_requests_preserve_distinct_versions(tmp_path):
    from concurrent.futures import ThreadPoolExecutor
    app = hp.create_app({'schema_version':1,'workspace':str(tmp_path),'port':5062})
    def save(_):
        with app.test_client() as client:
            return client.post('/api/plans',json=scenario()).json
    with ThreadPoolExecutor(max_workers=2) as pool:
        records = list(pool.map(save,range(2)))
    assert sorted(r['version'] for r in records) == [1,2]
    assert len(list(tmp_path.rglob('plan_v*.json'))) == 2


def test_safe_names_and_workspace_containment(tmp_path):
    assert hp.sanitise_system('A/B: "C"') == 'AB C'
    assert hp.sanitise_system(' .CON. ') == 'CON_'
    assert hp.sanitise_system('a\x00\x1fb\t  c') == 'ab c'
    assert hp.sanitise_system('x'*61) == 'x'*60
    for text in ('...', '\x00/:'):
        with pytest.raises(hp.ValidationError):
            hp.sanitise_system(text)
    for text in ('..', '../outside', 'nested/../../outside', str(tmp_path.parent)):
        with pytest.raises(hp.PersistenceError):
            hp.workspace_path(tmp_path, text)


def test_persistence_slice_unicode_collisions_and_immutability(tmp_path):
    workspace = tmp_path / 'missing'
    folder = hp.plan_folder(workspace, '2026-10', 'A/B')
    assert folder.name == '2026-10 - AB'
    path = folder / 'plan_v1.json'
    hp.write_json(path, {'inputs':{'system':'A/B'}, 'note':'日本語'}, immutable=True)
    original = path.read_bytes()
    assert json.loads(original)['note'] == '日本語'
    assert '日本語' in path.read_text(encoding='utf-8')
    assert hp.plan_folder(workspace, '2026-10', 'a/b') == folder
    assert hp.plan_folder(workspace, '2026-10', 'A:B').name == '2026-10 - AB (2)'
    with pytest.raises(hp.PersistenceError):
        hp.write_json(path, {'changed':True}, immutable=True)
    with pytest.raises(hp.PersistenceError):
        hp.atomic_write(path, 'changed')
    assert path.read_bytes() == original


def test_atomic_failure_preserves_old_and_cleans_temporary(tmp_path, monkeypatch):
    path = tmp_path / 'report.html'
    hp.atomic_write(path, 'original')
    def fail(*args):
        raise PermissionError('locked')
    monkeypatch.setattr(hp.os, 'replace', fail)
    with pytest.raises(hp.PersistenceError, match='locked'):
        hp.atomic_write(path, 'new')
    assert path.read_text() == 'original'
    assert list(tmp_path.iterdir()) == [path]


def test_import_has_no_disk_or_browser_side_effects(tmp_path, monkeypatch):
    monkeypatch.setattr(hp.webbrowser, 'open', lambda *a: pytest.fail('browser opened'))
    monkeypatch.chdir(tmp_path)
    importlib.reload(hp)
    assert list(tmp_path.iterdir()) == []


def test_first_config_and_workspace(tmp_path):
    config_path = tmp_path / 'config.json'
    config = hp.load_config(config_path, home=tmp_path)
    assert config == {'schema_version': 1, 'workspace': str(tmp_path / 'Documents' / 'HITL Planner'), 'port': 5062}
    assert json.loads(config_path.read_text(encoding='utf-8')) == config
    app = hp.create_app(config)
    assert Path(config['workspace']).is_dir()
    client = app.test_client()
    root = client.get('/')
    assert root.status_code == 200
    assert 'HITL Sample Size Planner' in root.text
    assert 'not yet available' in root.text
    assert 'https://' not in root.text and 'http://' not in root.text
    assert client.get('/api/health').json == {'tool': hp.TOOL_NAME, 'version': '1.0.0', 'workspace_ok': True}
    assert not list(tmp_path.rglob('*.tmp'))


def test_config_preserved(tmp_path):
    path = tmp_path / 'config.json'
    config = {'schema_version': 1, 'workspace': str(tmp_path / 'custom'), 'port': 54321}
    data = json.dumps(config).encode()
    path.write_bytes(data)
    assert hp.load_config(path) == config
    assert path.read_bytes() == data


@pytest.mark.parametrize('bad', ['{', '{}', '[]', '{"schema_version": 1, "workspace": "", "port": 5062}', '{"schema_version": 1, "workspace": "C:/data", "port": true}'])
def test_bad_config_preserved_exit2(tmp_path, bad, monkeypatch, capsys):
    path = tmp_path / 'config.json'
    path.write_text(bad, encoding='utf-8')
    monkeypatch.setattr(hp, 'CONFIG_PATH', path)
    assert hp.main([]) == 2
    assert len(capsys.readouterr().out.splitlines()) == 1
    assert path.read_text(encoding='utf-8') == bad


def test_unreadable_config(tmp_path, monkeypatch):
    path = tmp_path / 'config.json'
    path.mkdir()
    with pytest.raises(hp.ConfigError):
        hp.load_config(path)


def test_workspace_failure_reported(tmp_path):
    workspace = tmp_path / 'file'
    workspace.write_text('keep')
    app = hp.create_app({'schema_version': 1, 'workspace': str(workspace), 'port': 5062})
    assert app.test_client().get('/api/health').json['workspace_ok'] is False
    assert workspace.read_text() == 'keep'


def test_port_probe_free_foreign_and_same_tool(monkeypatch):
    with socket.socket() as listener:
        listener.bind((hp.HOST, 0))
        port = listener.getsockname()[1]
    assert hp.probe_instance(port) == 'free'
    with socket.socket() as listener:
        listener.bind((hp.HOST, port))
        listener.listen()
        monkeypatch.setattr(hp, 'read_health', lambda port: {'tool': 'Other'})
        assert hp.probe_instance(port) == 'foreign'
        monkeypatch.setattr(hp, 'read_health', lambda port: {'tool': hp.TOOL_NAME})
        assert hp.probe_instance(port) == 'same'


@pytest.mark.parametrize('kind,expected', [('same', 0), ('foreign', 2)])
def test_launcher_occupied(tmp_path, monkeypatch, capsys, kind, expected):
    config = {'schema_version': 1, 'workspace': str(tmp_path), 'port': 12345}
    opened = []
    monkeypatch.setattr(hp, 'probe_instance', lambda port: kind)
    assert hp.launch(config, browser_open=opened.append) == expected
    if kind == 'same':
        assert opened == ['http://127.0.0.1:12345/']
    else:
        assert not opened
        assert '12345' in capsys.readouterr().out


def test_launcher_binding_and_keyboard_interrupt(tmp_path, monkeypatch):
    calls = []
    class Server:
        def serve_forever(self):
            raise KeyboardInterrupt
        def server_close(self):
            calls.append('closed')
        def shutdown(self):
            calls.append('shutdown')
    monkeypatch.setattr(hp, 'probe_instance', lambda port: 'free')
    monkeypatch.setattr(hp, 'make_server', lambda host, port, app: (calls.append((host, port)) or Server()))
    assert hp.launch({'schema_version': 1, 'workspace': str(tmp_path), 'port': 12345}, browser_open=calls.append) == 0
    assert calls == [(hp.HOST, 12345), 'http://127.0.0.1:12345/', 'closed']


def test_real_subprocess_launch_and_quit(tmp_path):
    with socket.socket() as listener:
        listener.bind((hp.HOST, 0))
        port = listener.getsockname()[1]
    config = {'schema_version': 1, 'workspace': str(tmp_path), 'port': port}
    script = f'import hitl_planner as h; raise SystemExit(h.launch({config!r}, browser_open=lambda url: None))'
    process = subprocess.Popen([sys.executable, '-c', script], cwd=Path(hp.__file__).parent, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    try:
        deadline = time.monotonic() + 10
        while True:
            try:
                conn = http.client.HTTPConnection(hp.HOST, port, timeout=0.5)
                conn.request('GET', '/api/health')
                result = json.loads(conn.getresponse().read())
                conn.close()
                break
            except OSError:
                if time.monotonic() >= deadline or process.poll() is not None:
                    pytest.fail('launcher never became ready')
                time.sleep(0.03)
        assert result['tool'] == hp.TOOL_NAME
        conn = http.client.HTTPConnection(hp.HOST, port, timeout=3)
        conn.request('POST', '/api/quit')
        assert json.loads(conn.getresponse().read()) == {'ok': True}
        conn.close()
        stdout, stderr = process.communicate(timeout=5)
        assert process.returncode == 0, (stdout, stderr)
        assert hp.probe_instance(port) == 'free'
    finally:
        if process.poll() is None:
            process.terminate()
            process.communicate(timeout=5)


@pytest.mark.parametrize('N,C,mode,margin,p,expected', [
    (1000000, .95, 'absolute', .05, .5, 385),
    (5000, .95, 'absolute', .05, .5, 357),
    (1000000, .99, 'absolute', .03, .5, 1840),
    (20000, .95, 'relative', .25, .04, 1374),
])
def test_cochran_answer_key(N, C, mode, margin, p, expected):
    output = hp.precision_calc(N, C, mode, margin, p)
    assert output['n_cochran'] == expected
    E = margin if mode == 'absolute' else margin * p
    n0 = hp.Z[C] ** 2 * p * (1-p) / E ** 2
    assert output['E_effective'] == E
    assert output['n0'] == pytest.approx(n0, abs=1e-10)
    assert output['n_cochran_raw'] == pytest.approx(n0 / (1+(n0-1)/N), abs=1e-10)


def test_precision_constants_rounding_and_census():
    assert hp.Z == {.90:1.645, .95:1.960, .99:2.576}
    assert hp.ceil_safe(356.0000000004) == 356
    assert hp.ceil_safe(356.0000001) == 357
    assert hp.precision_calc(1, .95, 'absolute', .05, .5)['n_cochran'] == 1
    assert hp.precision_calc(20000, .95, 'absolute', .01, .04) == hp.precision_calc(20000, .95, 'relative', .25, .04)
    for N in (1, 2, 10, 100):
        assert 1 <= hp.precision_calc(N, .99, 'absolute', .005, .5)['n_cochran'] <= N


def test_assurance_reverse_answer_keys():
    assert hp.assurance_calc(.95, .01)['n_assure'] == 299
    assert round(hp.detection_power(200, .01), 4) == .8660
    assert round(hp.reverse_margin(5000, 357, .5, .95), 4) == .0500
    assert round(hp.inverse_threshold(120, .95), 4) == .0247
    assert hp.assurance_calc(.95, .001)['n_assure'] == 2995
    assert hp.assurance_calc(.95, .001)['n_assure'] > 2000


def test_assurance_reverse_edges_and_monotonicity():
    assert hp.reverse_margin(1, 1, .5, .95) == 0
    assert hp.reverse_margin(100, 100, .5, .95) == 0
    assert hp.reverse_margin(100, 120, .5, .95) == 0
    assert hp.reverse_margin(100, 0, .5, .95) is None
    assert hp.inverse_threshold(0, .95) is None
    assert hp.detection_power(0, .01) == 0
    assert hp.detection_power(200, .01) > hp.detection_power(100, .01)
    assert hp.inverse_threshold(200, .95) < hp.inverse_threshold(100, .95)


def scenario(**changes):
    data = dict(period_type='month', period_label='2026-10', system='HR Helpdesk Bot',
                N=50000, confidence=.95, margin_mode='absolute', margin_input=.05,
                p=.5, p_source='default', smes=3, hours_per_sme=8,
                minutes_per_conversation=12, dr_share=.15, dr_floor=50,
                certify=True, threshold=.01)
    data.update(changes)
    return data


def test_review_counts_contract_and_capacity():
    assert hp.review_effort(40, .15, 50, 12)['dr_count'] == 40
    assert hp.review_effort(400, .15, 50, 12)['dr_count'] == 60
    assert hp.review_effort(400, 0, 0, 12)['dr_count'] == 0
    assert hp.fits(24, 24)
    assert hp.fits(24+5e-10, 24)
    assert not hp.fits(24+2e-9, 24)
    out = hp.calculate_core(scenario())
    assert (out['n_headline'], out['dr_count'], out['reviews'], out['hours'], out['capacity']) == (382, 58, 440, 88, 24)
    assert out['binding'] == 'cochran'
    assert out['verdict'] == 'DOES NOT FIT'


@pytest.mark.parametrize('certify,N,threshold,binding,n', [
    (True, 50000, .01, 'assurance', 299),
    (False, 50000, .01, 'cochran', 43),
    (True, 2000, .001, 'cochran', 42),
    (True, 1, .01, 'cochran', 1),
])
def test_headline_binding(certify, N, threshold, binding, n):
    out = hp.calculate_core(scenario(certify=certify, N=N, threshold=threshold, margin_input=.15))
    assert out['binding'] == binding
    assert out['n_headline'] == n
    assert out['dr_count'] <= n


def test_headline_tie_is_cochran(monkeypatch):
    monkeypatch.setattr(hp, 'assurance_calc', lambda *args: {'n_assure':382, 'n_assure_raw':381.5})
    assert hp.calculate_core(scenario())['binding'] == 'cochran'


def test_capacity_max_answer_key_and_shared_hours():
    trade = hp.calculate_core(scenario())['trade_off']
    assert (trade['n_max_at_capacity'], trade['dr_count'], trade['reviews'], trade['hours']) == (70, 50, 120, 24)
    assert round(trade['margin_at_capacity'], 4) == .1171
    assert round(trade['threshold_at_capacity'], 4) == .0419
    assert not hp.fits(hp.review_effort(71, .15, 50, 12)['hours'], 24)
    assert hp.calculate_core(scenario(hours_per_sme=100))['trade_off'] is None
    relative = hp.calculate_core(scenario(margin_mode='relative', margin_input=.25))['trade_off']
    assert relative['relative_margin_at_capacity'] == pytest.approx(relative['margin_at_capacity']/.5)


@pytest.mark.parametrize('N,capacity,share,floor,minutes', [
    (10,0,.15,50,12), (10,.1,.15,50,12), (10,1000,1,1000,12),
    (1000000,24,.15,50,12), (1,1,0,0,60), (50,1,.01,0,1),
])
def test_capacity_max_boundaries(N, capacity, share, floor, minutes):
    n = hp.capacity_max(N, capacity, share, floor, minutes)
    assert 0 <= n <= N
    assert hp.fits(hp.review_effort(n, share, floor, minutes)['hours'], capacity)
    if n < N:
        assert not hp.fits(hp.review_effort(n+1, share, floor, minutes)['hours'], capacity)
    if capacity == 0:
        assert n == 0
    assert hp.calculate_core(scenario(hours_per_sme=.001))['trade_off']['margin_at_capacity'] is None


@pytest.mark.parametrize('mode,margin,certify', [('absolute',.05,True),('relative',.25,True),('absolute',.06,False)])
def test_sensitivity_grid(mode, margin, certify):
    data = scenario(margin_mode=mode, margin_input=margin, certify=certify)
    grid = hp.sensitivity_grid(data)
    assert len(grid) == 9
    margins = [.03,.05,.10] if mode == 'absolute' else [.10,.25,.50]
    assert [(c['margin_input'], c['confidence']) for c in grid] == [(m,c) for m in margins for c in [.9,.95,.99]]
    assert sum(c['selected'] for c in grid) == (0 if margin == .06 else 1)
    for cell in grid:
        result = hp.calculate_core({**data, 'margin_input':cell['margin_input'], 'confidence':cell['confidence']})
        for name in ['n_headline','dr_count','hours','binding','verdict']:
            assert cell[name] == result[name]
        assert cell['indicator'] == ('A' if cell['binding'] == 'assurance' else '')
        if not certify:
            assert not cell['indicator']
    assert hp.calculate_core(data)['sensitivity'] == grid


@pytest.mark.parametrize('code,inside,outside', [
    ('W1', {'E_effective':.1001}, {'E_effective':.1}),
    ('W3', {'E_effective':.5}, {'E_effective':.4999}),
    ('W4', {'dr_count':49}, {'dr_count':50}),
    ('W6', {'n_headline':40001}, {'n_headline':40000}),
    ('W7', {'n_assure':50001}, {'n_assure':50000}),
])
def test_warning_output_boundaries(code, inside, outside):
    data = scenario()
    base = hp.calculate_core(data)
    assert code in {w['code'] for w in hp.plan_warnings(data, {**base, **inside}, False)}
    assert code not in {w['code'] for w in hp.plan_warnings(data, {**base, **outside}, False)}


def test_warning_history_population_mode_and_structure():
    default = hp.calculate_core(scenario())
    assert 'W2' in {w['code'] for w in default['warnings']}
    assert 'W2' not in {w['code'] for w in hp.plan_warnings(scenario(p_source='manual'), default, True)}
    assert 'W2' in {w['code'] for w in hp.plan_warnings(scenario(p_source='last_observed'), default, False)}
    assert 'W2' not in {w['code'] for w in hp.plan_warnings(scenario(p=.4999), default, False)}
    assert 'W3' not in {w['code'] for w in hp.plan_warnings(scenario(margin_mode='relative'), {**default,'E_effective':.5}, False)}
    assert 'W5' in {w['code'] for w in hp.calculate_core(scenario(N=199))['warnings']}
    assert 'W5' not in {w['code'] for w in hp.calculate_core(scenario(N=200))['warnings']}
    warnings = hp.calculate_core(scenario(N=1))['warnings']
    codes = [w['code'] for w in warnings]
    assert 'W5' in codes and 'W6' in codes and 'W7' in codes
    assert len(codes) == len(set(codes))
    assert all(set(w) == {'code','severity','message'} for w in warnings)
    assert next(w for w in warnings if w['code'] == 'W7')['severity'] == 'red'
    assert 'W7' not in {w['code'] for w in hp.calculate_core(scenario(N=1,certify=False))['warnings']}


@pytest.mark.parametrize('mode,certify,N', [('absolute',True,50000),('relative',True,50000),('absolute',True,1),('absolute',False,50000)])
def test_seven_statements_variants(mode, certify, N):
    data = scenario(margin_mode=mode, margin_input=.25 if mode == 'relative' else .05, certify=certify, N=N, threshold=.0025)
    output = hp.calculate_core(data)
    statements = output['statements']
    assert len(statements) == 7
    assert statements == hp.plan_statements(data, output)
    assert '0.25%' in statements[1] and '0.25%' in statements[2]
    assert ('of its own value' in statements[0]) == (mode == 'relative')
    assert 'Oct 2026' in statements[3] and 'HR Helpdesk Bot' in statements[3]
    assert f'all {N:,}' in statements[5] and 'picked at random' in statements[5]
    assert statements[6] == 'It measures how often SMEs find issues, not how severe they are or why they happen.'
    if not certify:
        assert 'not sized to certify' in statements[1]
    elif N == 1:
        assert 'claim cannot be made' in statements[1]
    else:
        assert f"{output['n_headline']:,} reviewed" in statements[1]
    week = scenario(period_type='week', period_label='2026-W41', system='<A&B>')
    assert '<A&B>' in hp.calculate_core(week)['statements'][0]
    assert '2026-W41' in hp.calculate_core(week)['statements'][3]


def test_display_formatting_and_arithmetic_trace():
    assert hp.format_percent(.0025, True) == '0.25%'
    assert hp.format_percent(.0288, True) == '2.9%'
    assert hp.format_count(12345) == '12,345'
    assert hp.format_hours(88) == '88.0'
    o = hp.calculate_core(scenario())
    assert len(o['arithmetic']) == 12
    assert [s.split(':')[0] for s in o['arithmetic']] == ['Z','F1','F2','F3','F4','F5','F6','F7 reviews','F7 hours','F7 capacity','F7 verdict','F8']
    assert repr(o['n_cochran_raw']) in o['arithmetic'][3]
    assert '382' in o['arithmetic'][3]
    assert o['z'] == 1.960
    assert o['display']['hours'] == '88.0'
    boundary = hp.calculate_core(scenario(hours_per_sme=(88-1e-5)/3))
    assert boundary['display']['hours'] == boundary['display']['capacity']
    assert boundary['verdict'] == 'DOES NOT FIT'


@pytest.mark.parametrize('field,value', [
    ('N',0),('N',True),('N',1.5),('N','1'),('smes',0),('smes',False),
    ('hours_per_sme',0),('minutes_per_conversation',-1),('dr_floor',-1),('dr_floor',1.5),
    ('confidence',.96),('margin_input',.0049),('margin_input',.2501),
    ('p',.0009),('p',.9991),('dr_share',-.0001),('dr_share',1.0001),
    ('threshold',.00009),('threshold',.5001),('certify','true'),
    ('period_type','day'),('period_label','2026-13'),('period_label','2026-1'),
    ('system',' '),('system','a'*61),('margin_mode','other'),
])
def test_plan_validation_invalid_fields(field, value):
    original = scenario(**{field:value})
    with pytest.raises(hp.ValidationError) as error:
        hp.validate_plan(original)
    assert field in error.value.errors
    assert original[field] == value


@pytest.mark.parametrize('field', ['N','smes','hours_per_sme','minutes_per_conversation','dr_floor','confidence','margin_input','p','dr_share','threshold'])
@pytest.mark.parametrize('value', [float('nan'),float('inf'),float('-inf'),True,None])
def test_nonfinite_and_bool_numbers_refused(field, value):
    with pytest.raises(hp.ValidationError) as error:
        hp.validate_plan(scenario(**{field:value}))
    assert field in error.value.errors


def test_validation_limits_dates_defaults_and_no_mutation(monkeypatch):
    import datetime
    for changes in [dict(N=1,smes=1,hours_per_sme=.001,minutes_per_conversation=.001,dr_floor=0),
                    dict(margin_input=.005,p=.001,dr_share=0,threshold=.0001),
                    dict(margin_input=.25,p=.999,dr_share=1,threshold=.5),
                    dict(margin_mode='relative',margin_input=.05),dict(margin_mode='relative',margin_input=.5)]:
        assert hp.validate_plan(scenario(**changes))['N'] >= 1
    with pytest.raises(hp.ValidationError):
        hp.validate_plan(scenario(margin_mode='relative',margin_input=.5001))
    with pytest.raises(hp.ValidationError):
        hp.validate_plan(scenario(margin_mode='relative',margin_input=.0499))
    with pytest.raises(hp.ValidationError):
        hp.validate_plan(scenario(period_type='week',period_label='2025-W53'))
    assert hp.validate_plan(scenario(period_type='week',period_label='2020-W53'))['period_label'] == '2020-W53'
    original = scenario(system='  A&B  ', unknown='ignored')
    normalized = hp.validate_plan(original)
    assert normalized['system'] == 'A&B' and 'unknown' not in normalized
    assert original['system'] == '  A&B  '
    assert hp.system_key(' AbC ') == hp.system_key('abc')
    defaults = hp.initial_inputs(datetime.date(2026,10,10))
    assert defaults['period_label'] == '2026-10'
    assert all(defaults[field] is None for field in ('N','smes','hours_per_sme','minutes_per_conversation'))
    assert defaults['p'] == .5 and defaults['certify'] is True
    monkeypatch.setattr(hp, 'calculate_core', lambda *a, **k: pytest.fail('invalid data reached math'))
    with pytest.raises(hp.ValidationError):
        hp.calculate_validated({})


def test_plan_api_success_errors_and_statelessness(tmp_path):
    app = hp.create_app({'schema_version':1,'workspace':str(tmp_path),'port':5062})
    client = app.test_client()
    before = {p.relative_to(tmp_path):p.read_bytes() for p in tmp_path.rglob('*') if p.is_file()}
    for _ in range(20):
        response = client.post('/api/calc', json=scenario())
        assert response.status_code == 200
        result = response.json
        assert set(result) == {'outputs','warnings','statements','arithmetic'}
        o = result['outputs']
        assert (o['n_headline'],o['dr_count'],o['hours'],o['verdict']) == (382,58,88,'DOES NOT FIT')
        assert o['tradeoff']['n_max'] == 70
        assert len(result['statements']) == 7 and len(o['sensitivity']) == 9
    after = {p.relative_to(tmp_path):p.read_bytes() for p in tmp_path.rglob('*') if p.is_file()}
    assert before == after
    response = client.post('/api/calc', json=scenario(N=0,smes=0))
    assert response.status_code == 400 and {'N','smes'} <= set(response.json['errors'])
    response = client.post('/api/calc',data='{',content_type='application/json')
    assert response.status_code == 400 and 'errors' in response.json
    assert client.post('/api/calc',json=[]).status_code == 400


def test_plan_form_offline_controls_and_debounce(tmp_path):
    html = hp.create_app({'schema_version':1,'workspace':str(tmp_path),'port':5062}).test_client().get('/').text
    for field in ['period_type','period_label','system','N','confidence','margin_mode','margin_input','p','smes','hours_per_sme','minutes_per_conversation','dr_share','dr_floor','certify','threshold']:
        assert f'id="{field}"' in html
    for tab in ('Plan','Actuals','History','Method'):
        assert f'>{tab}</button>' in html
    assert 'AbortController' in html and ',150)' in html
    assert 'ticket!==requestCounter' in html
    assert 'Complete the highlighted fields' in html
    assert '<script src' not in html and '<link' not in html
    assert 'Math.sqrt' not in html and 'Math.log' not in html


def test_headline_ui_response_mapping(tmp_path):
    html = hp.create_app({'schema_version':1,'workspace':str(tmp_path),'port':5062}).test_client().get('/').text
    for name in ['warnings','headline','verdict','binding','can-say','cannot-say']:
        assert f'id="{name}"' in html
    o = hp.calculate_core(scenario())
    assert o['display']['headline'] == 'Review 382 conversations = 88.0 SME hours in Oct 2026'
    assert o['display']['binding'] == 'n set by the ±5.0% precision target'
    assert 'certify claim' in hp.calculate_core(scenario(margin_input=.15))['display']['binding']


def test_whatif_contract_and_ui(tmp_path):
    client = hp.create_app({'schema_version':1,'workspace':str(tmp_path),'port':5062}).test_client()
    html = client.get('/').text
    assert 'id="whatif-margin"' in html and 'id="adopt-margin"' in html
    assert 'id="tradeoff-panel"' in html
    on = client.post('/api/calc',json=scenario(margin_input=.15)).json['outputs']
    off = client.post('/api/calc',json=scenario(margin_input=.15,certify=False)).json['outputs']
    assert (on['n_headline'],on['reviews'],on['hours']) == (299,349,69.8)
    assert (off['n_headline'],off['dr_count'],off['reviews'],off['hours'],off['verdict']) == (43,43,86,17.2,'FITS')


def test_sensitivity_and_assurance_ui(tmp_path):
    html = hp.create_app({'schema_version':1,'workspace':str(tmp_path),'port':5062}).test_client().get('/').text
    assert 'id="sensitivity-grid"' in html and 'id="assurance-card"' in html
    o = hp.calculate_core(scenario(N=2000,threshold=.001))
    assert o['display']['assurance_red'] is True
    assert 'cannot be made' in o['display']['assurance']
    off = hp.calculate_core(scenario(certify=False))
    assert off['display']['detection_sentence'] == off['statements'][2]
    assert all('text' in c for c in off['sensitivity'])
