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
