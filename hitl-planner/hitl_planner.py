"""Offline HITL Sample Size Planner. See docs/ for the immutable contract."""
import json
import csv
import io
import math
import datetime
import re
import http.client
import os
from pathlib import Path
import sys
import tempfile
import socket
import threading
import time
from contextlib import contextmanager
from html import escape
import webbrowser
from wsgiref.simple_server import make_server

from flask import Flask, jsonify, request, render_template_string

TOOL_NAME = 'HITL Sample Size Planner'
TOOL_VERSION = '1.0.0'
METHOD_VERSION = '1.0'
HOST = '127.0.0.1'
DEFAULT_PORT = 5062
Z = {0.90: 1.645, 0.95: 1.960, 0.99: 2.576}
FORMULAS = {
    'F1':'E = margin_input (absolute) or margin_input × p (relative)',
    'F2':'n0 = Z² × p × (1 − p) / E²',
    'F3':'n_cochran = ceil_safe(n0 / (1 + (n0 − 1) / N))',
    'F4':'n_assure = ceil_safe(ln(1 − C) / ln(1 − T))',
    'F5':'n = max(n_cochran, n_assure) if certify and n_assure ≤ N; else n_cochran',
    'F6':'DR = min(n, max(F, ceil_safe(s × n)))',
    'F7':'reviews = n + DR; hours = reviews × M / 60; capacity = S × H; FITS if hours ≤ capacity + 1e-9',
    'F8':'P = 1 − (1 − T)^n',
    'F9':'E_at(n) = Z × sqrt(p(1−p)/n × (N−n)/(N−1)); zero if n ≥ N',
    'F10':'T_at(n) = 1 − (1 − C)^(1/n); undefined if n = 0',
}
REFERENCES = [
    'Cochran, W. G. (1977). Sampling Techniques (3rd ed.). Wiley.',
    'Hanley, J. A., & Lippman-Hand, A. (1983). "If nothing goes wrong, is everything all right? Interpreting zero numerators." JAMA, 249(13), 1743–1745.',
    "This tool's answer key (§11.1).",
]
CSV_COLUMNS = ('plan_id,period_type,period_label,system,plan_version,saved_at,N,confidence,'
               'margin_mode,margin_input,E_effective,p,p_source,certify,threshold,smes,hours_per_sme,'
               'minutes_per_conversation,dr_share,dr_floor,n_cochran,n_assure,n_headline,binding,dr_count,'
               'reviews,hours,capacity,verdict,n_max_at_capacity,margin_at_capacity,threshold_at_capacity,'
               'detection_power,warnings,actuals_version,recorded_at,reviewed,issues,observed_rate,'
               'achieved_margin,certify_status,agreement,notes').split(',')
CONFIG_PATH = Path(__file__).resolve().with_name('config.json')
PAGE_HTML = r'''<!doctype html><html lang="en"><head><meta charset="utf-8">
<title>HITL Sample Size Planner</title>
<style>
*{box-sizing:border-box}body{font-family:system-ui,sans-serif;background:#f4f6f8;color:#18253a;margin:0;padding:24px}
main{max-width:1440px;margin:auto}h1{font-size:25px;margin:0 0 18px}h2{font-size:18px}h3{font-size:15px;margin:0 0 14px}
nav{display:flex;gap:8px;margin-bottom:18px}button{font:inherit;border:1px solid #bcc9d7;background:white;border-radius:6px;padding:9px 15px;cursor:pointer}
button.active{background:#183f69;color:white}button:disabled{opacity:.45;cursor:default}button:focus-visible,input:focus-visible,select:focus-visible{outline:3px solid #72a5d5;outline-offset:2px}
#quit{margin-left:auto}.columns{display:grid;grid-template-columns:390px minmax(0,1fr);gap:22px}.card{background:white;border:1px solid #e0e6ed;border-radius:10px;padding:20px;margin-bottom:16px}
.fields{display:grid;grid-template-columns:1fr 1fr;gap:13px}.wide{grid-column:1/-1}label{display:block;font-size:13px;font-weight:600;margin-bottom:5px}
input,select,textarea{font:inherit;width:100%;border:1px solid #aab8c9;border-radius:5px;padding:8px;background:white}input[type=checkbox]{width:auto}
.invalid{border-color:#bb3434;background:#fff9f9}.error{display:block;color:#ac2626;font-size:12px;margin-top:4px}.note{font-size:12px;color:#59687c}.muted{opacity:.45}small.tag{border:1px solid #d4deea;padding:2px 6px;border-radius:4px}
[hidden]{display:none!important}.segmented{display:flex;gap:4px}.segmented label{border:1px solid #c9d3df;padding:7px;border-radius:5px}.segmented input{width:auto}
#global-notices{margin-bottom:12px} .placeholder{color:#657389;padding:26px}.warning{border-left:4px solid #c6901c;background:#fff8de;padding:12px;margin-bottom:10px}.warning.red{border-color:#bf3333;background:#ffebeb}.badge{display:inline-block;padding:5px 10px;border-radius:5px;font-size:13px;font-weight:700}.badge.green{background:#e2f5e9;color:#146c40}.badge.red{background:#ffe5e5;color:#9c2525}li{margin:10px 0;line-height:1.5}table{width:100%;border-collapse:separate;border-spacing:5px;font-size:13px}th,td{text-align:left;padding:10px}td.green{background:#e2f5e9}td.red{background:#ffe5e5}td.selected{outline:2px solid #244c78;border-radius:3px}#assurance-card.red{border-color:#bf3333;background:#fff4f4}
</style></head><body><main><h1>HITL Sample Size Planner</h1>
<nav aria-label="Planner tabs"><button class="active" data-tab="plan">Plan</button><button data-tab="actuals">Actuals</button><button data-tab="history">History</button><button data-tab="method">Method</button><button id="quit">Quit</button></nav>
<div id="global-notices" role="alert"></div>
<section id="plan-tab"><div class="columns"><form id="plan-form" novalidate>
<div class="card"><h3>Identity</h3><div class="fields">
<div class="wide"><label>Period type</label><div class="segmented" id="period_type"><label><input type="radio" name="period_type" value="month" checked> Month</label><label><input type="radio" name="period_type" value="week"> Week</label></div></div>
<div class="wide"><label for="period_label">Period</label><input type="month" id="period_label" required></div>
<div class="wide"><label for="system">System / use case</label><input id="system" maxlength="60" list="systems" required autocomplete="off"><datalist id="systems"></datalist></div>
</div><div id="prefill-banner" class="note" hidden></div></div>
<div class="card"><h3>Population and precision</h3><div class="fields">
<div><label for="N">Population N</label><input type="number" id="N" min="1" step="1" required title="Total conversations the AI produced in this period. The sample is drawn from these."></div>
<div><label for="confidence">Confidence</label><select id="confidence" title="How sure you want to be that the true rate lies inside the margin. 95% is the convention."><option value="0.9">90%</option><option value="0.95" selected>95%</option><option value="0.99">99%</option></select></div>
<div class="wide"><label>Margin mode</label><div class="segmented" id="margin_mode" title="Absolute: ±5 percentage points. Relative: ±25% of the rate itself — use this when the expected rate is small."><label><input type="radio" name="margin_mode" value="absolute" checked> Absolute</label><label><input type="radio" name="margin_mode" value="relative"> Relative</label></div></div>
<div><label for="margin_preset">Margin</label><select id="margin_preset"><option value="3">±3%</option><option value="5" selected>±5%</option><option value="10">±10%</option><option value="custom">Custom</option></select></div>
<div id="custom-margin" hidden><label for="margin_input">Custom margin (%)</label><input type="number" id="margin_input" value="5" step="any"></div>
<div class="wide"><label for="p">Expected issue rate (%) <small class="tag" id="p-source">default</small></label><input type="number" id="p" min="0.1" max="99.9" step="any" value="50" title="Your best guess of the issue rate. Leave at 50% if unknown — that gives the largest (safest) sample."><p class="note">Leave at 50% if unknown — this gives the safest (largest) sample</p></div>
</div></div>
<div class="card"><h3>SME capacity</h3><div class="fields">
<div><label for="smes">Number of SMEs</label><input type="number" id="smes" min="1" step="1" required title="Net review time actually available this period; exclude calibration meetings and admin."></div>
<div><label for="hours_per_sme" id="hours-label">Hours per SME this month</label><input type="number" id="hours_per_sme" step="any" required title="Net review time actually available this period; exclude calibration meetings and admin."></div>
<div class="wide"><label for="minutes_per_conversation">Minutes per conversation review</label><input type="number" id="minutes_per_conversation" step="any" required title="Net review time actually available this period; exclude calibration meetings and admin."></div>
</div></div>
<div class="card"><h3>Double review and certify</h3><div class="fields">
<div><label for="dr_share">Double-review share (%)</label><input type="number" id="dr_share" min="0" max="100" step="any" value="15" title="Share of the sample reviewed independently by a second SME, so reviewer agreement can be measured. Never fewer than the floor, never more than the sample."></div>
<div><label for="dr_floor">Double-review floor</label><input type="number" id="dr_floor" min="0" step="1" value="50" title="Share of the sample reviewed independently by a second SME, so reviewer agreement can be measured. Never fewer than the floor, never more than the sample."></div>
<div class="wide"><label for="certify"><input type="checkbox" id="certify" checked> Certify below a threshold</label></div>
<div class="wide"><label for="threshold">Certify threshold (%)</label><input type="number" id="threshold" min="0.01" max="50" step="any" value="1" title="Also size the sample so that, if no issues are found, you can state the rate is below this threshold."></div>
</div></div></form>
<div><div id="results" class="muted" data-valid="false"><div class="card placeholder" id="result-placeholder">Complete the highlighted fields</div>
<div id="plan-output" hidden><div id="warnings" role="status"></div><div class="card"><h2 id="headline"></h2><span id="verdict" class="badge"></span><p id="reviews-subline"></p><p id="binding" class="note"></p></div>
<div class="card" id="tradeoff-panel" hidden><h2>What your capacity buys</h2><p id="tradeoff-summary"></p><label for="whatif-margin">What-if margin (%)</label><input id="whatif-margin" type="range" min="2" max="15" step="0.5"><p id="whatif-readout" aria-live="polite"></p><p id="assurance-floor" class="note"></p><button id="adopt-margin" disabled>Adopt this margin</button></div>
<div class="card"><h2>Sensitivity</h2><table id="sensitivity-grid"></table><p class="note">A: assurance sets the sample size.</p></div>
<div class="card" id="assurance-card"><h2>Assurance and detection</h2><p id="assurance-text"></p><p id="detection-text"></p></div>
<div class="card"><h2>What this sample can and can't say</h2><h3>Can say</h3><ol id="can-say"></ol><h3>Can't say</h3><ol id="cannot-say" start="4"></ol></div></div>
</div><button id="save-plan" disabled>Save plan</button><div id="save-toast" role="status"></div></div>
</div></section>
<section id="actuals-tab" hidden><div class="card"><label for="actuals-plan">Saved plan</label><select id="actuals-plan"><option value="">Choose a saved plan</option></select><div id="actuals-summary"></div><div id="actuals-existing" hidden></div><button id="record-again" hidden>Record again</button></div>
<form id="actuals-form" class="card" hidden novalidate><div class="fields"><div><label for="reviewed">Conversations reviewed</label><input id="reviewed" type="number" min="1" step="1"></div><div><label for="issues">Conversations with issues</label><input id="issues" type="number" min="0" step="1"></div><div><label for="agreement">Double-review agreement (%)</label><input id="agreement" type="number" min="0" max="100" step="any"></div><div class="wide"><label for="notes">Notes</label><textarea id="notes" rows="4"></textarea></div></div><p class="note">Record review totals and process notes. Do not enter conversation contents.</p></form>
<div id="actuals-results" class="card" hidden></div><button id="record-actuals" disabled hidden>Record actuals</button><div id="actuals-toast" role="status"></div></section>
<section id="history-tab" hidden><div class="card"><label for="history-filter">Filter by system</label><input id="history-filter" type="search"><div id="history-notice" role="status"></div><table id="history-table"></table></div></section>
<section id="method-tab" hidden><div class="card">Method view is not yet available.</div></section>
</main><script>
const initial={{ initial|tojson }};
const $=id=>document.getElementById(id);
const numeric=['N','confidence','margin_input','p','smes','hours_per_sme','minutes_per_conversation','dr_share','dr_floor','threshold'];
const percentages=new Set(['margin_input','p','dr_share','threshold']);
let pSource='default',timer,requestCounter=0,controller,currentResult=null;
function formInputs(){const data={};for(const id of numeric){const raw=$(id).value;data[id]=raw===''?null:Number(raw)/(percentages.has(id)?100:1);}data.period_type=document.querySelector('input[name=period_type]:checked').value;data.margin_mode=document.querySelector('input[name=margin_mode]:checked').value;data.period_label=$('period_label').value;data.system=$('system').value;data.certify=$('certify').checked;data.p_source=pSource;return data;}
function invalidate(){currentResult=null;$('results').classList.add('muted');$('results').dataset.valid='false';$('save-plan').disabled=true;$('result-placeholder').hidden=false;}
function showErrors(errors){for(const field of $('plan-form').querySelectorAll('.invalid'))field.classList.remove('invalid');for(const message of $('plan-form').querySelectorAll('.error'))message.remove();for(const [id,message] of Object.entries(errors)){const field=$(id);if(field){field.classList.add('invalid');const span=document.createElement('span');span.className='error';span.textContent=message;field.after(span);}}}
function textElement(tag,text,className=''){const element=document.createElement(tag);element.textContent=text;element.className=className;return element;}
function paintResult(data){currentResult=data;const o=data.outputs;$('results').classList.remove('muted');$('results').dataset.valid='true';$('result-placeholder').hidden=true;$('plan-output').hidden=false;$('headline').textContent=o.display.headline;$('reviews-subline').textContent=o.display.reviews_subline;$('binding').textContent=o.display.binding;$('verdict').textContent=o.verdict;$('verdict').className='badge '+(o.verdict==='FITS'?'green':'red');$('warnings').replaceChildren(...data.warnings.map(w=>textElement('div',w.message,'warning '+w.severity)));$('can-say').replaceChildren(...data.statements.slice(0,3).map(s=>textElement('li',s)));$('cannot-say').replaceChildren(...data.statements.slice(3).map(s=>textElement('li',s)));paintTradeoff(o);paintSensitivity(o);}
function paintSensitivity(o){const table=$('sensitivity-grid'),head=document.createElement('thead'),heading=document.createElement('tr');heading.append(textElement('th','Margin'),...o.display.grid_headers.map(h=>textElement('th',h)));head.append(heading);const body=document.createElement('tbody');for(let index=0;index<o.sensitivity.length;index+=3){const row=document.createElement('tr');row.append(textElement('th',o.sensitivity[index].margin_label));for(const cell of o.sensitivity.slice(index,index+3)){const td=textElement('td',cell.text,'sensitivity-cell '+(cell.fits?'green':'red')+(cell.selected?' selected':''));row.append(td);}body.append(row);}table.replaceChildren(head,body);$('assurance-text').textContent=o.display.assurance;$('detection-text').textContent=o.display.detection_sentence;$('assurance-card').classList.toggle('red',o.display.assurance_red);}
let whatifTimer,whatifCounter=0,whatifController,sliderContext=null;
function paintTradeoff(o){$('tradeoff-panel').hidden=o.tradeoff===null;if(o.tradeoff===null){sliderContext=null;whatifCounter++;return;}$('tradeoff-summary').textContent=o.display.tradeoff;const i=formInputs(),context=i.margin_mode+':'+i.margin_input;const settings=o.display.slider;for(const name of ['min','max','step'])$('whatif-margin')[name]=String(settings[name]);if(context!==sliderContext){$('whatif-margin').value=String(settings.value);sliderContext=context;}queueWhatif();}
function queueWhatif(){clearTimeout(whatifTimer);whatifController?.abort();$('adopt-margin').disabled=true;const ticket=++whatifCounter,base=requestCounter;whatifTimer=setTimeout(async()=>{if(!currentResult)return;whatifController=new AbortController();const candidate={...formInputs(),margin_input:Number($('whatif-margin').value)/100};try{const response=await fetch('/api/calc',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(candidate),signal:whatifController.signal});const data=await response.json();if(ticket!==whatifCounter||base!==requestCounter||!currentResult)return;if(response.ok){$('whatif-readout').textContent=data.outputs.display.whatif;$('assurance-floor').textContent=data.outputs.display.assurance_floor;$('adopt-margin').disabled=false;}}catch(error){if(error.name!=='AbortError')$('whatif-readout').textContent='Calculation unavailable.';}},150);}
$('whatif-margin').addEventListener('input',queueWhatif);
$('adopt-margin').onclick=()=>{if(!currentResult)return;$('margin_input').value=$('whatif-margin').value;$('margin_preset').value='custom';$('custom-margin').hidden=false;queueCalculation();};
async function performCalculation(ticket){controller=new AbortController();try{const response=await fetch('/api/calc',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(formInputs()),signal:controller.signal});const data=await response.json();if(ticket!==requestCounter)return;if(!response.ok){showErrors(data.errors||{});invalidate();return;}showErrors({});paintResult(data);}catch(error){if(error.name!=='AbortError'&&ticket===requestCounter){invalidate();$('global-notices').textContent='Calculation unavailable. Check that the local planner is running.';}}}
function queueCalculation(){clearTimeout(timer);invalidate();requestCounter++;controller?.abort();const ticket=requestCounter;timer=setTimeout(()=>performCalculation(ticket),150);}
let saving=false;
async function openSaved(kind,planId,target){try{const response=await fetch('/api/open-'+kind,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({plan_id:planId})});const data=await response.json();if(!response.ok||!data.ok){target.className='warning';target.append(textElement('p','Could not open automatically. Open this path: '+(data.path||data.error||planId)));}}catch(error){target.append(textElement('p','Opening unavailable. Check the local planner.'));}}
$('save-plan').onclick=async()=>{if(!currentResult||saving)return;saving=true;$('save-plan').disabled=true;const snapshot=formInputs();try{const response=await fetch('/api/plans',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(snapshot)});const data=await response.json();if(!response.ok){if(data.errors)showErrors(data.errors);$('save-toast').className='warning';$('save-toast').textContent=data.error||'Plan could not be saved. Check the highlighted inputs.';return;}const toast=$('save-toast');toast.className='card';toast.replaceChildren(textElement('p','Saved '+data.plan_id+' · version '+data.version));for(const kind of ['report','folder']){const button=textElement('button','Open '+kind);button.onclick=()=>openSaved(kind,data.plan_id,toast);toast.append(button);}}catch(error){$('save-toast').textContent='Save unavailable. Check the local planner.';}finally{saving=false;$('save-plan').disabled=!currentResult;}};
const paintCalculated=paintResult;paintResult=data=>{paintCalculated(data);if(!saving)$('save-plan').disabled=false;};
function setMarginMode(){const mode=document.querySelector('input[name=margin_mode]:checked').value;const values=mode==='absolute'?[3,5,10]:[10,25,50];$('margin_preset').replaceChildren(...values.map(value=>new Option('±'+value+'%',String(value))),new Option('Custom','custom'));$('margin_preset').value='custom';$('custom-margin').hidden=false;}
for(const id of numeric){const value=initial[id];$(id).value=value==null?'':String(value*(percentages.has(id)?100:1));}$('period_label').value=initial.period_label;
$('plan-form').addEventListener('submit',event=>event.preventDefault());
$('plan-form').addEventListener('input',event=>{if(event.target.id==='p'){pSource='manual';$('p-source').textContent=pSource;}queueCalculation();});
$('plan-form').addEventListener('change',event=>{if(event.target.name==='period_type'){const period=event.target.value;$('period_label').type=period==='month'?'month':'week';$('period_label').value=period==='month'?initial.period_label:{{ current_week|tojson }};$('hours-label').textContent='Hours per SME this '+period;}if(event.target.name==='margin_mode')setMarginMode();if(event.target.id==='margin_preset'){const custom=event.target.value==='custom';$('custom-margin').hidden=!custom;if(!custom)$('margin_input').value=event.target.value;}queueCalculation();});
for(const tab of document.querySelectorAll('[data-tab]'))tab.onclick=()=>{for(const other of document.querySelectorAll('[data-tab]')){other.classList.toggle('active',other===tab);$(other.dataset.tab+'-tab').hidden=other!==tab;}};
let historyRows=[];
function applyPlanInputs(data){for(const id of numeric){const value=data[id];$(id).value=value==null?'':String(value*(percentages.has(id)?100:1));}for(const name of ['period_type','margin_mode'])for(const radio of document.querySelectorAll('input[name='+name+']'))radio.checked=radio.value===data[name];$('period_label').type=data.period_type==='month'?'month':'week';$('period_label').value=data.period_label;$('system').value=data.system;$('certify').checked=data.certify;$('hours-label').textContent='Hours per SME this '+data.period_type;setMarginMode();const margin=String(data.margin_input*100);if([...$('margin_preset').options].some(o=>o.value===margin)){$('margin_preset').value=margin;$('custom-margin').hidden=true;}pSource=data.p_source;$('p-source').textContent=pSource;queueCalculation();}
async function loadSavedPlan(planId){try{const response=await fetch('/api/plans/'+encodeURIComponent(planId));const data=await response.json();if(!response.ok)throw new Error(data.error||'Saved plan unavailable.');const p=data.plan;applyPlanInputs({...p.inputs,period_type:p.plan.period_type,period_label:p.plan.period_label,system:p.plan.system});document.querySelector('[data-tab=plan]').click();$('prefill-banner').hidden=false;$('prefill-banner').textContent='Loaded '+p.plan.plan_id+' · version '+p.plan.version;}catch(error){$('history-notice').textContent=error.message;}}
function paintHistory(){const table=$('history-table'),heading=document.createElement('tr');for(const title of ['Period','System','Version','Saved at','Sample','Hours','Verdict','Warnings','Actuals','Observed rate','Achieved margin','Actions'])heading.append(textElement('th',title));const head=document.createElement('thead');head.append(heading);const body=document.createElement('tbody');const filter=$('history-filter').value.trim().toLocaleLowerCase();for(const plan of historyRows){if(filter&&!(plan.system||plan.plan_id).toLocaleLowerCase().includes(filter))continue;const row=document.createElement('tr');if(plan.unreadable){const cell=textElement('td',plan.plan_id+' · unreadable — '+plan.unreadable);cell.colSpan=12;row.append(cell);}else{const a=plan.actuals?.outputs;for(const value of [plan.period_label,plan.system,plan.version,plan.saved_at,plan.n_headline,plan.hours,plan.verdict,plan.warnings.join(';'),plan.actuals?'✔':'—',a?.display?.observed_rate||'—',a?.display?.achieved_margin||'—'])row.append(textElement('td',String(value)));const actions=document.createElement('td');const load=textElement('button','Load');load.onclick=()=>loadSavedPlan(plan.plan_id);actions.append(load);for(const kind of ['report','folder']){const button=textElement('button',kind==='report'?'Report':'Folder');button.onclick=()=>openSaved(kind,plan.plan_id,$('history-notice'));actions.append(button);}row.append(actions);}body.append(row);}table.replaceChildren(head,body);}
async function refreshHistory(){try{const response=await fetch('/api/plans');const data=await response.json();if(!response.ok)throw new Error(data.error||'History unavailable.');historyRows=data;paintHistory();}catch(error){$('history-notice').textContent=error.message;}}
$('history-filter').oninput=paintHistory;document.querySelector('[data-tab=history]').addEventListener('click',refreshHistory);
let prefilledFrom=null,prefillTicket=0,prefillTimer;
const baseFormInputs=formInputs;formInputs=()=>({...baseFormInputs(),prefilled_from:prefilledFrom});
async function refreshSystems(){try{const response=await fetch('/api/systems');if(response.ok)$('systems').replaceChildren(...(await response.json()).map(s=>new Option(s,s)));}catch(error){}}
function queuePrefill(){clearTimeout(prefillTimer);const ticket=++prefillTicket;prefilledFrom=null;const system=$('system').value;const snapshot=formInputs();prefillTimer=setTimeout(async()=>{try{const response=await fetch('/api/prefill?system='+encodeURIComponent(system));const data=await response.json();if(ticket!==prefillTicket||$('system').value!==system||!data.inputs)return;const current=formInputs(),merged={...current};for(const [key,value] of Object.entries(data.inputs)){if(key==='system'||key==='N'||key==='prefilled_from'||key==='p_source')continue;if(current[key]===snapshot[key])merged[key]=value;}merged.N=current.N;if(current.p===snapshot.p)merged.p_source=data.p_source;applyPlanInputs(merged);prefilledFrom=data.prefilled_from;$('prefill-banner').hidden=false;$('prefill-banner').textContent='Prefilled from '+data.prefilled_from+(data.actuals_recorded_at?' · p from actuals recorded '+data.actuals_recorded_at.slice(0,10):'');}catch(error){$('prefill-banner').hidden=false;$('prefill-banner').textContent='Previous settings could not be loaded.';}},150);}
$('system').addEventListener('input',queuePrefill);refreshSystems();
let selectedActualPlan=null,actualsTicket=0,actualsSelection=0,actualsTimer,actualsController,actualsValid=false,recordingActuals=false;
function actualsInputs(){const data={plan_id:selectedActualPlan?.plan.plan_id,plan_version:selectedActualPlan?.plan.version,notes:$('notes').value};for(const field of ['reviewed','issues','agreement'])data[field]=$(field).value===''?null:Number($(field).value)/(field==='agreement'?100:1);return data;}
function actualsErrors(errors){for(const e of $('actuals-form').querySelectorAll('.error'))e.remove();for(const e of $('actuals-form').querySelectorAll('.invalid'))e.classList.remove('invalid');for(const [field,message] of Object.entries(errors)){if(!['reviewed','issues','agreement','notes'].includes(field))continue;$(field).classList.add('invalid');$(field).after(textElement('span',message,'error'));}}
function paintActuals(data,target){const o=data.outputs;target.hidden=false;target.replaceChildren(textElement('h2','Review results'),textElement('p','Observed rate: '+o.display.observed_rate),textElement('p',o.display.achieved_margin),textElement('p','Certify: '+o.display.certify_status),textElement('p','Agreement: '+o.display.agreement));const table=document.createElement('table');const heading=document.createElement('tr');heading.append(...['Measure','Planned','Actual'].map(v=>textElement('th',v)));table.append(heading);for(const item of o.display.comparison){const row=document.createElement('tr');row.append(textElement('th',item.label),textElement('td',item.planned),textElement('td',item.actual));table.append(row);}target.append(table,...data.warnings.map(w=>textElement('div',w.message,'warning '+w.severity)));}
function queueActuals(){clearTimeout(actualsTimer);actualsController?.abort();actualsValid=false;$('record-actuals').disabled=true;$('actuals-results').classList.add('muted');const ticket=++actualsTicket,selection=actualsSelection;actualsTimer=setTimeout(async()=>{if(!selectedActualPlan)return;actualsController=new AbortController();try{const response=await fetch('/api/actuals/calc',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(actualsInputs()),signal:actualsController.signal});const data=await response.json();if(ticket!==actualsTicket||selection!==actualsSelection)return;if(!response.ok){actualsErrors(data.errors||{});$('actuals-toast').textContent=data.error||'';return;}actualsErrors({});paintActuals(data,$('actuals-results'));$('actuals-results').classList.remove('muted');actualsValid=true;$('record-actuals').disabled=recordingActuals;}catch(error){if(error.name!=='AbortError')$('actuals-toast').textContent='Calculation unavailable. Check the local planner.';}},150);}
async function selectActualPlan(){const ticket=++actualsSelection;actualsTicket++;actualsController?.abort();selectedActualPlan=null;actualsValid=false;for(const id of ['actuals-form','actuals-results','actuals-existing','record-again','record-actuals'])$(id).hidden=true;$('record-actuals').disabled=true;$('actuals-summary').replaceChildren();$('actuals-toast').textContent='';const id=$('actuals-plan').value;if(!id)return;try{const response=await fetch('/api/plans/'+encodeURIComponent(id));const data=await response.json();if(ticket!==actualsSelection)return;if(!response.ok)throw new Error(data.error||'Saved plan unavailable.');selectedActualPlan=data.plan;const p=data.plan,i=p.inputs,o=p.outputs;$('actuals-summary').append(textElement('p',p.plan.plan_id+' · plan version '+p.plan.version),textElement('p',o.display.headline),textElement('p','Planned sample '+o.display.n_headline+' · double reviews '+o.display.dr_count+' · margin '+o.display.E_effective+' · threshold '+o.display.threshold+' · expected rate '+o.display.expected_rate+' · population '+o.display.population));if(data.actuals){const a=data.actuals;paintActuals(a,$('actuals-existing'));$('actuals-existing').prepend(textElement('p','Actuals version '+a.version+' · recorded '+a.recorded_at+' · against plan version '+a.plan_version));$('actuals-existing').append(textElement('p',a.inputs.notes));$('record-again').hidden=false;}else openActualsForm();}catch(error){$('actuals-toast').textContent=error.message;}}
function openActualsForm(){for(const field of ['reviewed','issues','agreement','notes'])$(field).value='';$('actuals-existing').hidden=true;$('record-again').hidden=true;$('actuals-form').hidden=false;$('record-actuals').hidden=false;$('actuals-results').hidden=true;actualsErrors({});queueActuals();}
async function refreshActualPlans(){try{const response=await fetch('/api/plans');const data=await response.json();if(!response.ok)throw new Error(data.error||'Saved plans unavailable.');const value=$('actuals-plan').value;data.sort((a,b)=>(b.saved_at||'').localeCompare(a.saved_at||''));$('actuals-plan').replaceChildren(new Option('Choose a saved plan',''),...data.filter(p=>!p.unreadable).map(p=>new Option(p.plan_id+' · v'+p.version+' · '+p.verdict+' · '+p.saved_at,p.plan_id)));if(data.some(p=>p.plan_id===value))$('actuals-plan').value=value;await selectActualPlan();}catch(error){$('actuals-toast').textContent=error.message;}}
$('actuals-plan').onchange=selectActualPlan;document.querySelector('[data-tab=actuals]').addEventListener('click',refreshActualPlans);$('actuals-form').onsubmit=e=>e.preventDefault();$('actuals-form').oninput=queueActuals;$('record-again').onclick=openActualsForm;
$('record-actuals').onclick=async()=>{if(!selectedActualPlan||!actualsValid||recordingActuals)return;recordingActuals=true;$('record-actuals').disabled=true;const data=actualsInputs(),selection=actualsSelection;try{const response=await fetch('/api/plans/'+encodeURIComponent(data.plan_id)+'/actuals',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(data)});const result=await response.json();if(selection!==actualsSelection)return;if(!response.ok){actualsErrors(result.errors||{});$('actuals-toast').textContent=result.error||'Actuals could not be recorded.';return;}await selectActualPlan();const toast=$('actuals-toast');toast.replaceChildren(textElement('p','Recorded actuals version '+result.version+' for '+data.plan_id));const button=textElement('button','Open report');button.onclick=()=>openSaved('report',data.plan_id,toast);toast.append(button);}catch(error){$('actuals-toast').textContent='Recording unavailable. Check the local planner.';}finally{recordingActuals=false;$('record-actuals').disabled=!actualsValid;}};
$('quit').onclick=async()=>{try{const response=await fetch('/api/quit',{method:'POST'});if(response.ok)document.body.textContent='Planner stopped. You may close this tab.';}catch(error){$('global-notices').textContent='The local planner is unavailable.';}};
queueCalculation();
</script></body></html>'''


class ConfigError(ValueError):
    pass


class ValidationError(ValueError):
    def __init__(self, errors):
        self.errors = errors
        super().__init__('Invalid inputs')


def system_key(value):
    return value.strip().casefold()


def initial_inputs(today=None):
    today = today or datetime.date.today()
    return {'period_type':'month', 'period_label':today.strftime('%Y-%m'), 'system':'',
            'N':None, 'confidence':.95, 'margin_mode':'absolute', 'margin_input':.05,
            'p':.5, 'p_source':'default', 'smes':None, 'hours_per_sme':None,
            'minutes_per_conversation':None, 'dr_share':.15, 'dr_floor':50,
            'certify':True, 'threshold':.01, 'prefilled_from':None}


def validate_plan(inputs):
    if not isinstance(inputs, dict):
        raise ValidationError({'inputs':'Expected an object.'})
    errors, normalized = {}, {}
    for key, choices in [('period_type', ('month','week')), ('margin_mode', ('absolute','relative'))]:
        if inputs.get(key) not in choices:
            errors[key] = 'Choose ' + ' or '.join(choices) + '.'
        else:
            normalized[key] = inputs[key]
    label = inputs.get('period_label')
    try:
        if not isinstance(label, str):
            raise ValueError
        if inputs.get('period_type') == 'month' and re.fullmatch(r'\d{4}-\d{2}', label):
            datetime.date.fromisoformat(label+'-01')
        elif inputs.get('period_type') == 'week' and re.fullmatch(r'\d{4}-W\d{2}', label):
            datetime.date.fromisocalendar(int(label[:4]), int(label[-2:]), 1)
        else:
            raise ValueError
        normalized['period_label'] = label
    except ValueError:
        errors['period_label'] = 'Choose a valid YYYY-MM month or ISO YYYY-Www week.'
    system = inputs.get('system')
    if not isinstance(system, str) or not 1 <= len(system.strip()) <= 60:
        errors['system'] = 'Enter a system name of 1–60 characters.'
    else:
        normalized['system'] = system.strip()
    for key, minimum in [('N',1),('smes',1),('dr_floor',0)]:
        value = inputs.get(key)
        if type(value) is not int or value < minimum:
            errors[key] = f'Enter an integer at least {minimum}.'
        else:
            normalized[key] = value
    margin_limits = (.05, .5) if inputs.get('margin_mode') == 'relative' else (.005, .25)
    for key, low, high in [('margin_input',*margin_limits),('p',.001,.999),('dr_share',0,1),('threshold',.0001,.5),
                           ('confidence',.9,.99),('hours_per_sme',0,None),('minutes_per_conversation',0,None)]:
        value = inputs.get(key)
        if type(value) not in (int,float) or not math.isfinite(value):
            errors[key] = 'Enter a finite number.'
        elif (high is None and value <= low) or (high is not None and not low <= value <= high):
            errors[key] = 'Enter a value greater than zero.' if high is None else f'Enter a decimal from {low} to {high}.'
        elif key == 'confidence' and value not in Z:
            errors[key] = 'Choose 90%, 95% or 99%.'
        else:
            normalized[key] = value
    if type(inputs.get('certify')) is not bool:
        errors['certify'] = 'Choose on or off.'
    else:
        normalized['certify'] = inputs['certify']
    source = inputs.get('p_source', 'default' if inputs.get('p') == .5 else 'manual')
    if source not in ('default','manual','last_observed','last_planned'):
        errors['p_source'] = 'Unknown rate source.'
    normalized['p_source'] = source
    prefilled = inputs.get('prefilled_from')
    if prefilled is not None and not isinstance(prefilled, str):
        errors['prefilled_from'] = 'Expected a plan name or null.'
    normalized['prefilled_from'] = prefilled
    if errors:
        raise ValidationError(errors)
    return normalized


def calculate_validated(inputs, observed_history=False):
    return calculate_core(validate_plan(inputs), observed_history=observed_history)


def calculate_response(inputs, observed_history=False):
    outputs = calculate_validated(inputs, observed_history)
    warnings, statements, arithmetic = (outputs.pop(name) for name in ('warnings','statements','arithmetic'))
    trade = outputs.pop('trade_off')
    if trade is not None:
        trade['n_max'] = trade.pop('n_max_at_capacity')
        trade['margin_at_capacity_relative'] = trade.pop('relative_margin_at_capacity')
    outputs['tradeoff'] = trade
    for cell in outputs['sensitivity']:
        cell['n'] = cell.pop('n_headline')
        cell['margin'] = cell.pop('margin_input')
    return {'outputs':outputs, 'warnings':warnings, 'statements':statements, 'arithmetic':arithmetic}


def ceil_safe(value):
    return math.ceil(round(value, 9))


def precision_calc(N, confidence, margin_mode, margin_input, p):
    E = margin_input if margin_mode == 'absolute' else margin_input * p
    n0 = Z[confidence] ** 2 * p * (1-p) / E ** 2
    raw = n0 / (1+(n0-1)/N)
    return {'E_effective': E, 'n0': n0, 'n_cochran_raw': raw,
            'n_cochran': ceil_safe(raw)}


def assurance_calc(confidence, threshold):
    raw = math.log(1-confidence) / math.log(1-threshold)
    return {'n_assure_raw': raw, 'n_assure': ceil_safe(raw)}


def detection_power(n, threshold):
    return 1-(1-threshold) ** n


def reverse_margin(N, n, p, confidence):
    if n == 0:
        return None
    if n >= N or N == 1:
        return 0.0
    return Z[confidence] * math.sqrt(p*(1-p)/n * (N-n)/(N-1))


def inverse_threshold(n, confidence):
    return None if n == 0 else 1-(1-confidence) ** (1/n)


def fits(hours, capacity):
    return hours <= capacity + 1e-9


def review_effort(n, share, floor, minutes):
    dr = min(n, max(floor, ceil_safe(share*n)))
    return {'dr_count': dr, 'reviews': n+dr, 'hours': (n+dr)*minutes/60}


def capacity_max(N, capacity, share, floor, minutes):
    low, high = 0, min(N, math.floor(capacity*60/minutes + 1e-9))
    while low < high:
        middle = (low+high+1)//2
        if fits(review_effort(middle, share, floor, minutes)['hours'], capacity):
            low = middle
        else:
            high = middle-1
    return low


def trade_off_calc(i, capacity):
    n = capacity_max(i['N'], capacity, i['dr_share'], i['dr_floor'], i['minutes_per_conversation'])
    margin = reverse_margin(i['N'], n, i['p'], i['confidence'])
    return {**review_effort(n, i['dr_share'], i['dr_floor'], i['minutes_per_conversation']),
            'n_max_at_capacity': n, 'margin_at_capacity': margin,
            'relative_margin_at_capacity': margin/i['p'] if margin is not None and i['margin_mode'] == 'relative' else None,
            'threshold_at_capacity': inverse_threshold(n, i['confidence']),
            'no_reviews': n == 0}


def sensitivity_grid(inputs):
    margins = (.03, .05, .10) if inputs['margin_mode'] == 'absolute' else (.10, .25, .50)
    cells = []
    for margin in margins:
        for confidence in Z:
            out = calculate_core({**inputs, 'margin_input': margin, 'confidence': confidence}, include_sensitivity=False)
            cells.append({name: out[name] for name in ('n_headline', 'dr_count', 'hours', 'binding', 'verdict')})
            cells[-1].update(margin_input=margin, confidence=confidence,
                             fits=out['verdict'] == 'FITS', indicator='A' if out['binding'] == 'assurance' else '',
                             selected=inputs['confidence'] == confidence and inputs['margin_input'] == margin)
            cells[-1].update(text=f'{out["n_headline"]:,} · {format_hours(out["hours"])} h' + (' A' if out['binding'] == 'assurance' else ''),
                             margin_label=f'±{format_percent(margin)}' + (' relative' if inputs['margin_mode'] == 'relative' else ''))
    return cells


def format_percent(value, small_precision=False):
    if value is None:
        return 'n/a'
    places = 2 if small_precision and value < .01 else 1
    return f'{value*100:.{places}f}%'


def format_count(value):
    return f'{value:,}'


def format_hours(value):
    return f'{value:.1f}'


def arithmetic_trace(i, o):
    return [
        f'Z: for {i["confidence"]*100:.0f}% = {Z[i["confidence"]]:.3f}',
        f'F1: E = {i["margin_input"]}' + (f' × {i["p"]}' if i['margin_mode'] == 'relative' else '') + f' = {o["E_effective"]!r}',
        f'F2: n0 = {Z[i["confidence"]]:.3f}² × {i["p"]!r} × (1 − {i["p"]!r}) / {o["E_effective"]!r}² = {o["n0"]!r}',
        f'F3: {o["n0"]!r} / (1 + ({o["n0"]!r} − 1) / {i["N"]}) = {o["n_cochran_raw"]!r}; ceil_safe → {o["n_cochran"]}',
        f'F4: ln(1 − {i["confidence"]!r}) / ln(1 − {i["threshold"]!r}) = {o["n_assure_raw"]!r}; ceil_safe → {o["n_assure"]}',
        f'F5: certify={i["certify"]}, assurance feasible={o["n_assure"] <= i["N"]}; n={o["n_headline"]}; binding={o["binding"]}',
        f'F6: min({o["n_headline"]}, max({i["dr_floor"]}, ceil_safe({i["dr_share"]!r} × {o["n_headline"]}))) = {o["dr_count"]}',
        f'F7 reviews: {o["n_headline"]} + {o["dr_count"]} = {o["reviews"]}',
        f'F7 hours: {o["reviews"]} × {i["minutes_per_conversation"]!r} / 60 = {o["hours"]!r} → {format_hours(o["hours"])}',
        f'F7 capacity: {i["smes"]} × {i["hours_per_sme"]!r} = {o["capacity"]!r} → {format_hours(o["capacity"])}',
        f'F7 verdict: {o["hours"]!r} <= {o["capacity"]!r} + 1e-9 → {o["verdict"]}',
        f'F8: 1 − (1 − {i["threshold"]!r})^{o["n_headline"]} = {o["detection_power"]!r} → {format_percent(o["detection_power"])}',
    ]


def plan_warnings(i, out, observed_history=False):
    E, p, n, N, F = out['E_effective'], i['p'], out['n_headline'], i['N'], i['dr_floor']
    rules = [
        ('W1', E > .10, 'yellow', 'Margin of error is above ±10%. The reported rate will be too imprecise for most governance decisions — tighten the margin or add SME hours.'),
        ('W2', p == .5 and not observed_history, 'yellow', "Expected issue rate is at the 50% default. This gives the largest sample; enter last cycle's rate if you have one."),
        ('W3', i['margin_mode'] == 'absolute' and E >= p, 'yellow', f'The margin (±{format_percent(E)}) is as large as the expected rate ({format_percent(p, True)}): the result could not tell the rate apart from zero. Switch to a relative margin, or rely on the certify claim.'),
        ('W4', out['dr_count'] < F, 'yellow', f'The sample ({n:,}) is smaller than the double-review floor ({F:,}); every conversation will be double-reviewed and agreement will rest on fewer than {F:,} items.'),
        ('W5', N < 200, 'yellow', 'Population is under 200 — consider reviewing every conversation instead of sampling.'),
        ('W6', n > .8*N, 'yellow', 'The sample is more than 80% of the population; review everything — sampling saves little here.'),
        ('W7', i['certify'] and out['n_assure'] > N, 'red', f'Cannot certify that the rate is below {format_percent(i["threshold"], True)} at this population: it would need {out["n_assure"]:,} clean reviews and only {N:,} conversations exist. Review everything and report the observed rate.'),
    ]
    return [{'code':code, 'severity':severity, 'message':message} for code, fired, severity, message in rules if fired]


def period_display(period_type, label):
    if period_type == 'week':
        return label
    year, month = label.split('-')
    return f'{("Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec")[int(month)-1]} {year}'


def plan_statements(i, o):
    E, p, T = format_percent(o['E_effective']), format_percent(i['p'], True), format_percent(i['threshold'], True)
    C, period, system = f'{i["confidence"]*100:.0f}%', period_display(i['period_type'], i['period_label']), i['system']
    n, N, assure = f'{o["n_headline"]:,}', f'{i["N"]:,}', f'{o["n_assure"]:,}'
    s1 = (f'The reported issue rate will be within ±{E} of the true rate for {system} in {period}, with {C} confidence.'
          if i['margin_mode'] == 'absolute' else
          f'The reported issue rate will be within ±{format_percent(i["margin_input"])} of its own value (±{E} absolute at the expected rate of {p}), with {C} confidence.')
    if not i['certify']:
        s2 = f"This plan is not sized to certify that the rate is below a threshold; a 'below {T}' claim would need {assure} clean reviews."
    elif o['n_assure'] > i['N']:
        s2 = f"The 'below {T}' claim cannot be made at this population: it would need {assure} clean reviews and only {N} conversations exist."
    else:
        s2 = f'If none of the {n} reviewed conversations shows the issue, you can state with {C} confidence that the true rate is below {T}.'
    return [s1, s2,
            f'If the true rate were {T}, this sample has a {format_percent(o["detection_power"])} chance of containing at least one such conversation.',
            f'It says nothing about conversations outside {period}, or about systems other than {system}.',
            f'The ±{E} applies to the overall rate only — not to any team, region or question type. Sub-groups need their own sample.',
            f'These claims assume the {n} conversations are picked at random from all {N}. Hand-picking, or reviewing only flagged conversations, voids them.',
            'It measures how often SMEs find issues, not how severe they are or why they happen.']


def calculate_core(inputs, include_sensitivity=True, observed_history=False):
    i = inputs
    out = precision_calc(i['N'], i['confidence'], i['margin_mode'], i['margin_input'], i['p'])
    out.update(assurance_calc(i['confidence'], i['threshold']))
    assurance_binds = i['certify'] and out['n_assure'] <= i['N'] and out['n_assure'] > out['n_cochran']
    n = out['n_assure'] if assurance_binds else out['n_cochran']
    out.update(n_headline=n, binding='assurance' if assurance_binds else 'cochran')
    out.update(review_effort(n, i['dr_share'], i['dr_floor'], i['minutes_per_conversation']))
    out['capacity'] = i['smes'] * i['hours_per_sme']
    out['verdict'] = 'FITS' if fits(out['hours'], out['capacity']) else 'DOES NOT FIT'
    out['detection_power'] = detection_power(n, i['threshold'])
    out['trade_off'] = trade_off_calc(i, out['capacity']) if out['verdict'] == 'DOES NOT FIT' else None
    if include_sensitivity:
        out['sensitivity'] = sensitivity_grid(i)
    out['warnings'] = plan_warnings(i, out, observed_history)
    out['statements'] = plan_statements(i, out)
    out['z'] = Z[i['confidence']]
    out['arithmetic'] = arithmetic_trace(i, out)
    out['display'] = {name: format_count(out[name]) for name in ('n_headline', 'n_cochran', 'n_assure', 'dr_count', 'reviews')}
    out['display'].update(hours=format_hours(out['hours']), capacity=format_hours(out['capacity']),
                          E_effective=format_percent(out['E_effective']), detection_power=format_percent(out['detection_power']),
                          population=format_count(i['N']),threshold=format_percent(i['threshold'],True),expected_rate=format_percent(i['p'],True))
    out['display'].update(
        headline=f'Review {n:,} conversations = {format_hours(out["hours"])} SME hours in {period_display(i["period_type"], i["period_label"])}',
        reviews_subline=f'{n:,} + {out["dr_count"]:,} double reviews = {out["reviews"]:,} reviews × {i["minutes_per_conversation"]:g} min · capacity {format_hours(out["capacity"])} h ({i["smes"]} SMEs × {i["hours_per_sme"]:g} h)',
        binding=(f'n set by the ±{format_percent(out["E_effective"])} precision target' if out['binding'] == 'cochran' else
                 f'n set by the \'below {format_percent(i["threshold"], True)}\' certify claim (precision alone would need {out["n_cochran"]:,})'))
    trade = out['trade_off']
    out['display']['tradeoff'] = None
    if trade is not None:
        maximum = trade['n_max_at_capacity']
        out['display']['tradeoff'] = ('Capacity allows no reviews at all.' if maximum == 0 else
            f'Your capacity allows {maximum:,} conversations ({maximum:,} + {trade["dr_count"]:,} double = {format_hours(trade["hours"])} h). '
            f'That buys ±{format_percent(trade["margin_at_capacity"])} precision'
            + (f' (±{format_percent(trade["relative_margin_at_capacity"])} relative)' if i['margin_mode'] == 'relative' else '')
            + f' and lets you certify below {format_percent(trade["threshold_at_capacity"], True)}.')
    out['display']['whatif'] = f'±{format_percent(i["margin_input"])}: {n:,} conversations + {out["dr_count"]:,} double reviews = {format_hours(out["hours"])} h · {out["verdict"]}'
    out['display']['assurance_floor'] = (f'With certify enabled, the sample cannot fall below {out["n_assure"]:,} clean reviews.'
        if i['certify'] and out['n_assure'] <= i['N'] else '')
    out['display']['slider'] = {'min':2 if i['margin_mode'] == 'absolute' else 5,
                              'max':15 if i['margin_mode'] == 'absolute' else 50,
                              'step':.5 if i['margin_mode'] == 'absolute' else 1,
                              'value':i['margin_input']*100}
    out['display']['grid_headers'] = [f'{confidence*100:.0f}%' for confidence in Z]
    out['display']['assurance'] = (f'Review {out["n_assure"]:,} conversations; if none shows the issue, you can state with {i["confidence"]*100:.0f}% confidence the true rate is below {format_percent(i["threshold"], True)}.'
        if out['n_assure'] <= i['N'] else plan_statements({**i,'certify':True}, out)[1])
    out['display']['assurance_red'] = i['certify'] and out['n_assure'] > i['N']
    out['display']['detection_sentence'] = out['statements'][2]
    return out


class PersistenceError(OSError):
    """A workspace operation failed without discarding existing records."""


@contextmanager
def workspace_lock(workspace):
    root = Path(workspace).resolve()
    lock = root / '.write-lock'
    acquired = False
    try:
        root.mkdir(parents=True, exist_ok=True)
        deadline = time.monotonic() + 5
        while not acquired:
            try:
                lock.mkdir()
                acquired = True
            except FileExistsError:
                if time.monotonic() >= deadline:
                    raise PersistenceError(f'Workspace is busy: {root}. Retry after the other save finishes.')
                time.sleep(.01)
        yield
    except OSError as exc:
        raise PersistenceError(f'Cannot save in {root}: {exc}') from exc
    finally:
        if acquired:
            lock.rmdir()


def integrity_check():
    checks = [
        precision_calc(1000000,.95,'absolute',.05,.5)['n_cochran'] == 385,
        precision_calc(5000,.95,'absolute',.05,.5)['n_cochran'] == 357,
        precision_calc(1000000,.99,'absolute',.03,.5)['n_cochran'] == 1840,
        assurance_calc(.95,.01)['n_assure'] == 299,
        round(detection_power(200,.01),4) == .8660,
        precision_calc(20000,.95,'relative',.25,.04)['n_cochran'] == 1374,
        round(reverse_margin(5000,357,.5,.95),4) == .0500,
        round(inverse_threshold(120,.95),4) == .0247,
        capacity_max(50000,24,.15,50,12) == 70 and
            round(reverse_margin(50000,70,.5,.95),4) == .1171 and
            round(inverse_threshold(70,.95),4) == .0419,
        review_effort(40,.15,50,12)['dr_count'] == 40,
        assurance_calc(.95,.001)['n_assure'] == 2995,
    ]
    return {'passed':sum(checks),'total':11}


def save_plan(workspace, inputs):
    inputs = validate_plan(inputs)
    calculated = calculate_response(inputs, observed_history=has_observed_history(workspace,inputs['system']))
    integrity = integrity_check()
    if integrity['passed'] != integrity['total']:
        raise PersistenceError('Integrity check failed. Plan was not saved.')
    with workspace_lock(workspace):
        folder = plan_folder(workspace, inputs['period_label'], inputs['system'])
        versions = [int(m[1]) for p in folder.iterdir()
                    if (m := re.fullmatch(r'plan_v(\d+)\.json', p.name))]
        version = max(versions, default=0) + 1
        record = {
            'schema_version':1,
            'tool':{'name':TOOL_NAME,'version':TOOL_VERSION,'method_version':METHOD_VERSION},
            'saved_at':datetime.datetime.now().astimezone().isoformat(),
            'plan':{'plan_id':folder.name,'period_type':inputs['period_type'],
                    'period_label':inputs['period_label'],'period_display':period_display(inputs['period_type'],inputs['period_label']),
                    'system':inputs['system'],'version':version},
            'inputs':{k:v for k,v in inputs.items() if k not in ('period_type','period_label','system')},
            'outputs':calculated['outputs'],'warnings':calculated['warnings'],
            'statements':calculated['statements'],
            'method':{'constants':{'Z':{f'{k:.2f}':v for k,v in Z.items()}},
                      'formulas':dict(FORMULAS),'arithmetic':calculated['arithmetic']},
            'integrity_check':integrity,
        }
        write_json(folder / f'plan_v{version}.json', record, immutable=True)
        report_path = folder / 'report.html'
        try:
            regenerate_report(folder, version)
            write_log(workspace)
        except PersistenceError as exc:
            raise PersistenceError(f'Plan version {version} saved in {folder}; report/log regeneration failed. Existing records are safe. Retry GET /api/log/rebuild for the log. {exc}') from exc
        return {'plan_id':folder.name,'version':version,'folder':str(folder),'report_path':str(report_path)}


def build_report(record, actuals=None):
    def text(value):
        return escape(str(value))
    def table(values):
        return '<table>' + ''.join('<tr><th>'+text(k)+'</th><td>'+text(v)+'</td></tr>' for k,v in values.items())+'</table>'
    def listing(values):
        return '<ol>'+''.join('<li>'+text(v)+'</li>' for v in values)+'</ol>'
    def section(name, content):
        return '<section><h2>'+name+'</h2>'+content+'</section>'
    plan, out = record['plan'], record['outputs']
    display = out['display']
    parts = ['<!doctype html><html lang="en"><head><meta charset="utf-8"><title>HITL Sampling plan</title><style>'
             'body{font:14px system-ui,sans-serif;color:#18253a;max-width:1000px;margin:24px auto;padding:16px}'
             'table{border-collapse:collapse;width:100%;margin:12px 0}td,th{border:1px solid #ccc;padding:7px;text-align:left}'
             'th{background:#f4f6f8}section{margin:24px 0}li{margin:8px 0;white-space:pre-wrap}'
             '.green{background:#e2f4e8}.red{background:#ffe4e4}.selected{outline:2px solid #365da6}'
             '@page{size:A4;margin:15mm}@media print{body{margin:0;padding:0;font-size:10pt}'
             'h2{break-after:avoid}tr,li{break-inside:avoid}thead{display:table-header-group}'
             'section{break-inside:auto}.method{break-before:page}*{print-color-adjust:exact}}'
             '</style></head><body><h1>HITL Sample Size Planner — Sampling plan</h1>',
             '<p>'+text(plan['plan_id'])+' · Plan version '+str(plan['version'])+'</p>',
             '<p>Saved at '+text(record['saved_at'])+' · Tool '+text(record['tool']['version'])
             +' · Method '+text(record['tool']['method_version'])+'</p>',
             section('Inputs',table({**{k:v for k,v in plan.items() if k!='version'},**record['inputs']})),
             section('Headline and verdict','<h3>'+text(display['headline'])+'</h3><p>'+text(out['verdict'])
                     +'</p><p>'+text(display['reviews_subline'])+'</p><p>'+text(display['binding'])+'</p>')]
    if out['tradeoff'] is not None:
        parts.append(section('Trade-off','<p>'+text(display['tradeoff'])+'</p>'))
    grid = '<table><thead><tr><th>Margin</th>'+''.join('<th>'+text(v)+'</th>' for v in display['grid_headers'])+'</tr></thead><tbody>'
    for index in range(0,9,3):
        cells = out['sensitivity'][index:index+3]
        grid += '<tr><th>'+text(cells[0]['margin_label'])+'</th>'
        for cell in cells:
            css = ('green' if cell['fits'] else 'red') + (' selected' if cell['selected'] else '')
            grid += '<td class="'+css+'">'+text(cell['text'])+'</td>'
        grid += '</tr>'
    parts.extend([
        section('Sensitivity grid',grid+'</tbody></table>'),
        section('Assurance and detection','<p>'+text(display['assurance'])+'</p><p>'+text(display['detection_sentence'])+'</p>'),
        section('Statements',listing(record['statements'])),
        section('Warnings',listing([w['code']+': '+w['message'] for w in record['warnings']]) if record['warnings'] else '<p>None</p>'),
        section('Arithmetic',listing(record['method']['arithmetic'])),
        section('Formulas and constants',table(record['method']['formulas'])+table(record['method']['constants']['Z'])),
        section('References',listing(REFERENCES)),
    ])
    if actuals is not None:
        actual_output = actuals['outputs']
        parts.append(section('Actuals',
            '<p>Actuals version '+str(actuals['version'])+' · Recorded at '+text(actuals['recorded_at'])
            +' · Recorded against plan version '+str(actuals['plan_version'])+'</p>'
            + table({'Observed rate':actual_output['display']['observed_rate'],
                     'Achieved margin or bound':actual_output['display']['achieved_margin'],
                     'Certify status':actual_output['certify_status'],
                     'Agreement':actual_output['display']['agreement']})
            + table(actual_output['planned_vs_actual'])+'<h3>Notes</h3><p style="white-space:pre-wrap">'
            +text(actuals['inputs']['notes'])+'</p>'
            +listing([w['code']+': '+w['message'] for w in actuals['warnings']])))
    parts.append('</body></html>')
    return ''.join(parts)


def regenerate_report(folder, version):
    path = Path(folder) / f'plan_v{version}.json'
    try:
        record = json.loads(path.read_text(encoding='utf-8'))
        atomic_write(Path(folder) / 'report.html', build_report(record, latest_record(folder,'actuals')))
    except (OSError, ValueError, KeyError, TypeError) as exc:
        raise PersistenceError(f'Cannot regenerate report from {path}: {exc}') from exc


def sanitise_system(system):
    clean = re.sub(r'[<>:"/\\|?*\x00-\x1f\x7f]', '', system)
    clean = re.sub(r'\s+', ' ', clean).strip(' .')[:60].rstrip(' .')
    if not clean:
        raise ValidationError({'system':'System must contain a usable folder name.'})
    if re.fullmatch(r'(?i:CON|PRN|AUX|NUL|COM[1-9]|LPT[1-9])', clean.split('.')[0]):
        clean += '_'
    return clean


def workspace_path(workspace, relative):
    root = Path(workspace).resolve()
    relative = Path(relative)
    if relative.is_absolute() or not relative.parts or '..' in relative.parts:
        raise PersistenceError('Requested path must stay inside the configured workspace.')
    path = (root / relative).resolve()
    if path == root or not path.is_relative_to(root):
        raise PersistenceError('Requested path must stay inside the configured workspace.')
    return path


def saved_folder(workspace, plan_id):
    if not isinstance(plan_id,str) or not plan_id or any(c in plan_id for c in '/\\:') or plan_id in ('.','..'):
        raise ValidationError({'plan_id':'Choose a saved plan.'})
    return workspace_path(workspace, plan_id)


def latest_record(folder, kind, requested_version=None):
    versions = [(int(m[1]),p) for p in Path(folder).iterdir()
                if (m := re.fullmatch(kind+r'_v(\d+)\.json', p.name))]
    if requested_version is not None:
        versions = [pair for pair in versions if pair[0]==requested_version]
    if not versions:
        return None
    version, path = max(versions)
    try:
        record = json.loads(path.read_text(encoding='utf-8'))
        if not isinstance(record,dict) or record.get('schema_version') != 1:
            raise ValueError('Unsupported or missing schema version')
        if kind == 'plan':
            plan = record['plan']
            validate_plan({**record['inputs'],**{k:plan[k] for k in ('system','period_type','period_label')}})
            if plan['version'] != version or plan['plan_id'] != Path(folder).name:
                raise ValueError('Plan identity/version does not match its record path')
            for key in ('n_headline','hours','verdict'):
                record['outputs'][key]
            record['saved_at']
            record['warnings']
        return record
    except (OSError, ValueError, KeyError, TypeError) as exc:
        raise PersistenceError(f'Unreadable record {path}: {exc}') from exc


def read_plan(workspace, plan_id):
    folder = saved_folder(workspace, plan_id)
    if not folder.is_dir():
        return None
    plan = latest_record(folder, 'plan')
    if plan is None:
        return None
    return {'plan':plan,'actuals':latest_record(folder,'actuals')}


def list_plans(workspace):
    root = Path(workspace).resolve()
    if not root.exists():
        return []
    rows = []
    try:
        for folder in root.iterdir():
            if not folder.is_dir() or folder.name.startswith('.'):
                continue
            row = {'plan_id':folder.name,'version':None,'saved_at':None,'system':None,
                   'period_label':None,'verdict':None,'n_headline':None,'hours':None,
                   'warnings':[],'actuals':None,'unreadable':None}
            try:
                detail = read_plan(root,folder.name)
                if detail is None:
                    continue
                plan = detail['plan']
                row.update(version=plan['plan']['version'],saved_at=plan['saved_at'],
                           system=plan['plan']['system'],period_label=plan['plan']['period_label'],
                           verdict=plan['outputs']['verdict'],n_headline=plan['outputs']['n_headline'],
                           hours=plan['outputs']['hours'],warnings=[w['code'] for w in plan['warnings']],
                           actuals=detail['actuals'])
            except (OSError,ValueError,KeyError,TypeError) as exc:
                row['unreadable'] = str(exc)
            rows.append(row)
    except OSError as exc:
        raise PersistenceError(f'Cannot read workspace {root}: {exc}') from exc
    def period_start(row):
        label = row['period_label'] or ''
        if not label:
            return datetime.date.min
        if '-W' in label:
            year, week = label.split('-W')
            return datetime.date.fromisocalendar(int(year),int(week),1)
        return datetime.date.fromisoformat(label+'-01')
    rows.sort(key=lambda row:((row['system'] or '').casefold(),row['plan_id']))
    rows.sort(key=period_start,reverse=True)
    return rows


def system_history(workspace, system):
    plans, actuals = [], []
    for row in list_plans(workspace):
        if row['unreadable'] or system_key(row['system']) != system_key(system):
            continue
        detail = read_plan(workspace,row['plan_id'])
        plans.append(detail['plan'])
        actual = detail['actuals']
        if actual is not None:
            try:
                obs = actual['outputs']['observed_rate']
                if type(obs) not in (float,int) or not math.isfinite(obs) or not 0 <= obs <= 1:
                    continue
                datetime.datetime.fromisoformat(actual['recorded_at'])
                actuals.append(actual)
            except (ValueError,KeyError,TypeError):
                continue
    return plans, actuals


def has_observed_history(workspace, system):
    return bool(system_history(workspace,system)[1])


def prefill(workspace, system):
    plans, actuals = system_history(workspace,system)
    if not plans:
        return {}
    plan = max(plans,key=lambda p:datetime.datetime.fromisoformat(p['saved_at']))
    actual = max(actuals,key=lambda a:datetime.datetime.fromisoformat(a['recorded_at'])) if actuals else None
    source = 'last_observed' if actual else 'last_planned'
    defaults = initial_inputs()
    i = dict(plan['inputs'])
    i.update(N=None,system=plan['plan']['system'],period_type=plan['plan']['period_type'],
             p=max(actual['outputs']['observed_rate'],.001) if actual else i['p'],p_source=source)
    iso = datetime.date.today().isocalendar()
    i['period_label'] = defaults['period_label'] if i['period_type']=='month' else f'{iso.year:04d}-W{iso.week:02d}'
    provenance = f'{plan["plan"]["plan_id"]} (v{plan["plan"]["version"]})'
    i['prefilled_from'] = provenance
    return {'inputs':i,'prefilled_from':provenance,'p_source':source,
            'actuals_recorded_at':actual['recorded_at'] if actual else None}


def validate_actuals(plan, data):
    if not isinstance(data,dict):
        raise ValidationError({'actuals':'Enter actual review results.'})
    errors, normalized = {}, {}
    N = plan['inputs']['N']
    for field, minimum, maximum in [('reviewed',1,N),('issues',0,data.get('reviewed'))]:
        value = data.get(field)
        if type(value) is not int or type(maximum) is not int or not minimum <= value <= maximum:
            errors[field] = 'Enter an integer from 1 to population N.' if field=='reviewed' else 'Enter an integer from 0 to reviewed.'
        else:
            normalized[field] = value
    agreement = data.get('agreement')
    if type(agreement) not in (int,float) or not math.isfinite(agreement) or not 0 <= agreement <= 1:
        errors['agreement'] = 'Enter agreement from 0% to 100%.'
    else:
        normalized['agreement'] = agreement
    notes = data.get('notes','')
    if not isinstance(notes,str):
        errors['notes'] = 'Notes must be text.'
    else:
        normalized['notes'] = notes
    if errors:
        raise ValidationError(errors)
    return normalized


def plan_reference(workspace, data):
    if not isinstance(data,dict):
        raise ValidationError({'actuals':'Enter actual review results.'})
    folder = saved_folder(workspace,data.get('plan_id'))
    version = data.get('plan_version')
    if version is not None and (type(version) is not int or version < 1):
        raise ValidationError({'plan_version':'Choose a saved plan version.'})
    if not folder.is_dir():
        return None
    return latest_record(folder,'plan',version)


def save_actuals(workspace, plan_id, data):
    if not isinstance(data,dict):
        raise ValidationError({'actuals':'Enter actual review results.'})
    with workspace_lock(workspace):
        plan = plan_reference(workspace,{**data,'plan_id':plan_id})
        if plan is None:
            return None
        inputs = validate_actuals(plan,data)
        calculated = calculate_actuals(plan,inputs)
        folder = saved_folder(workspace,plan_id)
        versions = [int(m[1]) for p in folder.iterdir() if (m:=re.fullmatch(r'actuals_v(\d+)\.json',p.name))]
        version = max(versions,default=0)+1
        record = {'schema_version':1,'tool':dict(plan['tool']),
                  'recorded_at':datetime.datetime.now().astimezone().isoformat(),
                  'plan_id':plan_id,'plan_version':plan['plan']['version'],'version':version,
                  'inputs':inputs,**calculated}
        write_json(folder/f'actuals_v{version}.json',record,immutable=True)
        try:
            latest = latest_record(folder,'plan')
            regenerate_report(folder,latest['plan']['version'])
            write_log(workspace)
        except PersistenceError as exc:
            raise PersistenceError(f'Actuals version {version} saved in {folder}; report/log regeneration failed. Existing records are safe. Retry GET /api/log/rebuild for the log. {exc}') from exc
        return {'version':version,'report_path':str(folder/'report.html')}


def write_log(workspace):
    rows = []
    for summary in list_plans(workspace):
        if summary['unreadable']:
            print(f'Skipped unreadable {summary["plan_id"]}: {summary["unreadable"]}'.replace('\n',' ').replace('\r',' '))
            continue
        detail = read_plan(workspace,summary['plan_id'])
        p, actual = detail['plan'], detail['actuals']
        row = {**p['plan'],**p['inputs'],**p['outputs'],'plan_version':p['plan']['version'],'saved_at':p['saved_at']}
        trade = p['outputs']['tradeoff']
        row.update(n_max_at_capacity=trade['n_max'] if trade else None,
                   margin_at_capacity=trade['margin_at_capacity'] if trade else None,
                   threshold_at_capacity=trade['threshold_at_capacity'] if trade else None)
        warnings = [w['code'] for w in p['warnings']]
        if actual:
            row.update(actuals_version=actual['version'],recorded_at=actual['recorded_at'],
                       **actual['inputs'],**{k:actual['outputs'][k] for k in ('observed_rate','achieved_margin','certify_status')})
            warnings.extend(w['code'] for w in actual['warnings'])
        row['warnings'] = ';'.join(dict.fromkeys(warnings))
        rows.append(row)
    rows.sort(key=lambda r:(r['system'],r['plan_id']))
    rows.sort(key=lambda r:r['period_label'],reverse=True)
    stream = io.StringIO(newline='')
    writer = csv.DictWriter(stream,fieldnames=CSV_COLUMNS,extrasaction='ignore')
    writer.writeheader()
    writer.writerows(rows)
    path = Path(workspace).resolve()/'plans_log.csv'
    atomic_write(path,stream.getvalue(),encoding='utf-8-sig')
    return {'path':str(path),'rows':len(rows)}


def rebuild_log(workspace):
    with workspace_lock(workspace):
        return write_log(workspace)


def calculate_actuals(plan, data):
    a = validate_actuals(plan,data)
    i, planned = plan['inputs'], plan['outputs']
    reviewed, issues = a['reviewed'], a['issues']
    obs = issues / reviewed
    threshold = inverse_threshold(reviewed,i['confidence'])
    margin = reverse_margin(i['N'],reviewed,obs,i['confidence']) if 0 < obs < 1 else None
    relative = margin / obs if margin is not None and i['margin_mode']=='relative' else None
    bound = None
    if issues == 0:
        bound = f'No issues found — with {i["confidence"]*100:.0f}% confidence the true rate is below {format_percent(threshold,True)}.'
    elif issues == reviewed:
        bound = f'Every reviewed conversation showed the issue — with {i["confidence"]*100:.0f}% confidence the true rate is above {format_percent(1-threshold,True)}.'
    status = ('not planned' if not i['certify'] else
              'not applicable (issues found; report the observed rate)' if issues > 0 else
              'met' if threshold <= i['threshold'] else f'not met — can certify below {format_percent(threshold,True)} only')
    warnings = []
    def warn(code,message):
        warnings.append({'code':code,'severity':'yellow','message':message})
    if reviewed < planned['n_headline']:
        warn('W8',f'Fewer conversations were reviewed ({reviewed:,}) than planned ({planned["n_headline"]:,}). The achieved margin is ±{format_percent(margin)}, not the planned ±{format_percent(planned["E_effective"])}.')
    if obs > 2*i['p'] or obs < .5*i['p']:
        warn('W9',f'The observed rate ({format_percent(obs,True)}) is far from the planned expectation ({format_percent(i["p"],True)}). Next cycle\'s p will move; treat this cycle\'s precision claim with care.')
    if a['agreement'] < .8:
        warn('W10',f'Double-review agreement is {format_percent(a["agreement"])}, below 80%. Reviewer consistency is low — calibrate before relying on the rate.')
    outputs = {'observed_rate':obs,'achieved_margin':margin,'achieved_margin_relative':relative,
               'bound_statement':bound,'certify_status':status,
               'planned_vs_actual':{'n_planned':planned['n_headline'],'reviewed':reviewed,
                                    'margin_planned':planned['E_effective'],'margin_achieved':margin,
                                    'certify_planned':i['certify'],'certify_status':status,
                                    'dr_planned':planned['dr_count'],'agreement':a['agreement']},
               'display':{'observed_rate':format_percent(obs,True),
                          'achieved_margin':bound if bound else '±'+format_percent(margin)
                              + (f' (±{format_percent(relative)} relative)' if relative is not None else ''),
                          'certify_status':status,'agreement':format_percent(a['agreement'])}}
    outputs['display']['comparison'] = [
        {'label':'Conversations','planned':format_count(planned['n_headline']),'actual':format_count(reviewed)},
        {'label':'Margin','planned':'±'+format_percent(planned['E_effective']),
         'actual':outputs['display']['achieved_margin']},
        {'label':'Certify claim','planned':('Below '+format_percent(i['threshold'],True)) if i['certify'] else 'not planned','actual':status},
        {'label':'Double review / agreement','planned':format_count(planned['dr_count'])+' double reviews','actual':format_percent(a['agreement'])+' agreement'},
    ]
    return {'outputs':outputs,'warnings':warnings}


def plan_folder(workspace, period, system):
    if not re.fullmatch(r'\d{4}-(?:\d{2}|W\d{2})', period):
        raise PersistenceError('Invalid period for plan folder.')
    base = f'{period} - {sanitise_system(system)}'
    suffix = 1
    while True:
        folder = workspace_path(workspace, base + (f' ({suffix})' if suffix > 1 else ''))
        try:
            if not folder.exists():
                folder.mkdir(parents=True)
                return folder
            versions = [(int(m[1]), p) for p in folder.iterdir()
                        if (m := re.fullmatch(r'plan_v(\d+)\.json', p.name))]
            if not versions:
                return folder
            saved = json.loads(max(versions)[1].read_text(encoding='utf-8'))
            saved_system = saved['plan']['system'] if 'plan' in saved else saved['inputs']['system']
            if system_key(saved_system) == system_key(system):
                return folder
        except (OSError, ValueError, KeyError, TypeError) as exc:
            raise PersistenceError(f'Cannot use plan folder {folder}: {exc}') from exc
        suffix += 1


def write_json(path, record, immutable=False):
    atomic_write(path, json.dumps(record, ensure_ascii=False, indent=2), immutable=immutable)


def atomic_write(path, text, encoding='utf-8', immutable=False):
    path = Path(path)
    temporary = None
    try:
        if path.exists() and (immutable or re.fullmatch(r'(?:plan|actuals)_v\d+\.json', path.name)):
            raise PersistenceError(f'Record already exists: {path}. Save a new version.')
        with tempfile.NamedTemporaryFile(mode='w', encoding=encoding, dir=path.parent,
                                         prefix=path.name + '.', suffix='.tmp', delete=False, newline='') as stream:
            temporary = Path(stream.name)
            stream.write(text)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
    except OSError as exc:
        raise PersistenceError(f'Cannot write {path}: {exc}') from exc
    finally:
        if temporary is not None and temporary.exists():
            temporary.unlink()


def validate_config(config):
    if not isinstance(config, dict) or config.get('schema_version') != 1:
        raise ConfigError('schema_version must be 1')
    if not isinstance(config.get('workspace'), str) or not config['workspace'].strip():
        raise ConfigError('workspace must be a nonempty path')
    if not Path(config['workspace']).is_absolute():
        raise ConfigError('workspace must be an absolute path')
    if type(config.get('port')) is not int or not 1 <= config['port'] <= 65535:
        raise ConfigError('port must be an integer from 1 to 65535')
    return config


def load_config(path=None, home=None):
    path = Path(path if path is not None else CONFIG_PATH)
    try:
        if path.exists():
            return validate_config(json.loads(path.read_text(encoding='utf-8')))
        config = {'schema_version': 1, 'workspace': str((Path(home) if home else Path.home()) / 'Documents' / 'HITL Planner'), 'port': DEFAULT_PORT}
        atomic_write(path, json.dumps(config, ensure_ascii=False, indent=2))
        return config
    except (OSError, ValueError) as exc:
        raise ConfigError(f'{path}: {exc}') from exc


def workspace_health(workspace):
    try:
        workspace = Path(workspace)
        workspace.mkdir(parents=True, exist_ok=True)
        with tempfile.NamedTemporaryFile(dir=workspace, prefix='.health-', suffix='.tmp'):
            pass
        return True, None
    except OSError as exc:
        return False, f'{workspace}: {exc}'


def create_app(config=None):
    config = validate_config(config if config is not None else load_config())
    app = Flask(__name__)
    app.config['PLANNER_CONFIG'] = dict(config)
    workspace_health(config['workspace'])

    @app.get('/')
    def index():
        iso = datetime.date.today().isocalendar()
        return render_template_string(PAGE_HTML, initial=initial_inputs(), current_week=f'{iso.year:04d}-W{iso.week:02d}')

    @app.get('/api/health')
    def health():
        ok, _ = workspace_health(config['workspace'])
        return jsonify(tool=TOOL_NAME, version=TOOL_VERSION, workspace_ok=ok)

    @app.post('/api/quit')
    def quit_app():
        callback = app.config.get('SHUTDOWN_CALLBACK')
        if callback is not None:
            threading.Thread(target=callback, daemon=True).start()
        return jsonify(ok=True)

    @app.errorhandler(ValidationError)
    def validation_error(error):
        return jsonify(errors=error.errors), 400

    @app.errorhandler(PersistenceError)
    def persistence_error(error):
        return jsonify(error=str(error)), 503

    @app.post('/api/plans')
    def save():
        return jsonify(save_plan(config['workspace'], request.get_json(silent=True)))

    @app.get('/api/plans')
    def plans():
        return jsonify(list_plans(config['workspace']))

    @app.get('/api/systems')
    def systems():
        names = {}
        for row in list_plans(config['workspace']):
            if not row['unreadable']:
                names.setdefault(system_key(row['system']),row['system'])
        return jsonify(sorted(names.values(),key=system_key))

    @app.get('/api/prefill')
    def prefill_system():
        return jsonify(prefill(config['workspace'],request.args.get('system','')))

    @app.get('/api/plans/<plan_id>')
    def plan_detail(plan_id):
        detail = read_plan(config['workspace'], plan_id)
        if detail is None:
            return jsonify(error='Saved plan was not found.'), 404
        return jsonify(detail)

    @app.post('/api/actuals/calc')
    def actuals_calc():
        data = request.get_json(silent=True)
        plan = plan_reference(config['workspace'],data)
        if plan is None:
            return jsonify(error='Saved plan version was not found.'), 404
        return jsonify(calculate_actuals(plan,data))

    @app.post('/api/plans/<plan_id>/actuals')
    def record_actuals(plan_id):
        result = save_actuals(config['workspace'],plan_id,request.get_json(silent=True))
        if result is None:
            return jsonify(error='Saved plan version was not found.'), 404
        return jsonify(result)

    @app.get('/api/log/rebuild')
    def log_rebuild():
        return jsonify(rebuild_log(config['workspace']))

    def open_resource(kind):
        data = request.get_json(silent=True)
        folder = saved_folder(config['workspace'], data.get('plan_id') if isinstance(data,dict) else None)
        path = folder / 'report.html' if kind == 'report' else folder
        if not folder.is_dir() or not any(folder.glob('plan_v*.json')) or not path.exists():
            return jsonify(error='Saved plan was not found.'), 404
        try:
            os.startfile(str(path))
            return jsonify(ok=True)
        except (OSError, AttributeError):
            return jsonify(ok=False,path=str(path))

    @app.post('/api/open-report')
    def open_report():
        return open_resource('report')

    @app.post('/api/open-folder')
    def open_folder():
        return open_resource('folder')

    @app.post('/api/calc')
    def calc():
        inputs = validate_plan(request.get_json(silent=True))
        return jsonify(calculate_response(inputs,observed_history=has_observed_history(config['workspace'],inputs['system'])))

    return app


def read_health(port):
    connection = http.client.HTTPConnection(HOST, port, timeout=0.6)
    try:
        connection.request('GET', '/api/health')
        response = connection.getresponse()
        if response.status != 200:
            return None
        return json.loads(response.read(4096))
    except (OSError, ValueError, http.client.HTTPException):
        return None
    finally:
        connection.close()


def probe_instance(port):
    health = read_health(port)
    if isinstance(health, dict) and health.get('tool') == TOOL_NAME:
        return 'same'
    # Windows can silently drop connections to closed ports. An exclusive bind
    # distinguishes that timeout from a foreign listener; launch handles races.
    try:
        with socket.socket() as probe:
            if hasattr(socket, 'SO_EXCLUSIVEADDRUSE'):
                probe.setsockopt(socket.SOL_SOCKET, socket.SO_EXCLUSIVEADDRUSE, 1)
            probe.bind((HOST, port))
        return 'free'
    except OSError:
        return 'foreign'


def launch(config, browser_open=None):
    browser_open = browser_open or webbrowser.open
    url = f'http://{HOST}:{config["port"]}/'
    state = probe_instance(config['port'])
    if state == 'same':
        browser_open(url)
        return 0
    if state == 'foreign':
        print(f'Port {config["port"]} is in use; check {CONFIG_PATH}.')
        return 2
    try:
        app = create_app(config)
        server = make_server(HOST, config['port'], app)
    except OSError:
        print(f'Port {config["port"]} is unavailable; check {CONFIG_PATH}.')
        return 2
    app.config['SHUTDOWN_CALLBACK'] = server.shutdown
    try:
        browser_open(url)
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
    return 0


def main(argv=None):
    try:
        config = load_config()
    except ConfigError as exc:
        print(f'Config error: {str(exc).replace(chr(10), " ").replace(chr(13), " ")}')
        return 2
    return launch(config)


if __name__ == '__main__':
    sys.exit(main())
