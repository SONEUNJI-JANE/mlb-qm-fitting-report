import json

from src.service.mlb_qm_fitting_report.xlsx_source import LABEL_OFFSETS

_TEMPLATE = """<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>MLB QM Fitting 주간 보고</title>
<style>

:root{color-scheme:light;--bg:#fafaf9;--surface:#fff;--soft:#f4f4f2;--ink:#0b0b0b;--ink2:#52514e;--muted:#8b8a85;
--line:#ececea;--line2:#dcdcd8;--good:#0f7a4d;--bad:#c4314b;--warn:#a96a00;--accent:#2a78d6}
@media (prefers-color-scheme:dark){:root:not([data-theme=light]){color-scheme:dark;--bg:#111110;--surface:#1a1a19;--soft:#232322;
--ink:#fff;--ink2:#c3c2b7;--muted:#8d8c85;--line:#2b2b29;--line2:#3a3a37;--good:#4cd49a;--bad:#ff7d95;--warn:#e8b04a;--accent:#3987e5}}
:root[data-theme=dark]{color-scheme:dark;--bg:#111110;--surface:#1a1a19;--soft:#232322;
--ink:#fff;--ink2:#c3c2b7;--muted:#8d8c85;--line:#2b2b29;--line2:#3a3a37;--good:#4cd49a;--bad:#ff7d95;--warn:#e8b04a;--accent:#3987e5}
*{box-sizing:border-box}
body{margin:0;background:var(--bg);color:var(--ink);font:14px/1.5 "Pretendard","Malgun Gothic","Apple SD Gothic Neo",system-ui,sans-serif}
button,select,input{font:inherit;color:inherit}
.hdr{height:52px;border-bottom:1px solid var(--line);background:var(--surface);color:var(--ink);display:flex;align-items:center;gap:12px;padding:0 24px;position:sticky;top:0;z-index:5}
.hdr h1{font-size:15px;margin:0;font-weight:700}
.hdr .sp{flex:1}
.ib{width:34px;height:34px;border:1px solid var(--line);border-radius:8px;background:var(--surface);cursor:pointer}
select{padding:6px 10px;border-radius:6px;border:1px solid var(--line2);font-size:12px}
.content{padding:20px;max-width:1100px;margin:0 auto}
/* 분석 탭만 넓게 - 차트와 협력사 표가 1100에서는 잘린다. 요약은 기존 폭 유지. */
#analysis-tab{max-width:1680px}
table{width:100%;table-layout:fixed;border-collapse:collapse;background:var(--surface);border-radius:8px;overflow:hidden;margin-bottom:16px}
th,td{padding:6px 10px;border-bottom:1px solid var(--line);text-align:left;font-size:12px}
th{background:var(--soft);color:var(--ink2);font-weight:700}
.grp-th{text-align:center;border-left:1px solid var(--line)}
.num-th,.num-td{text-align:center;font-variant-numeric:tabular-nums;width:90px}
.num-td.pct{font-weight:700}
.owner-col{width:64px;text-align:center}
.stage-col{width:64px;text-align:center}
.act-col{width:60px;text-align:center}
.status-col{text-align:left;vertical-align:middle;padding:6px 12px;font-size:13px}
.remark-col{width:280px;text-align:center;vertical-align:middle;padding:6px}
.remark-input{border:1px solid transparent;background:transparent}
.remark-input:not([readonly]){border-color:var(--line2);background:var(--surface)}
.grp-a{background:var(--soft)}
.grp-b{background:var(--soft)}
th.grp-a,th.grp-th:first-of-type{border-left:1px solid var(--line)}
.season-title{font-weight:700;font-size:15px;margin:20px 0 8px;padding-bottom:4px;border-bottom:2px solid var(--line2)}
.quarter-title{font-weight:700;font-size:12px;color:var(--ink2);margin:14px 0 4px}
.season-title:first-child{margin-top:0}
.btn{padding:3px 8px;border-radius:4px;border:1px solid var(--line2);background:var(--surface);font-size:11px;cursor:pointer}
.btn:hover{background:var(--soft)}
.edit-cell{display:inline-flex;align-items:center;gap:3px;white-space:nowrap}
.edit-cell input{width:40px;padding:2px 3px;font-size:11px}
.num-td.pct.grp-a:has(.edit-cell){overflow:visible;position:relative}
.override-bar{position:sticky;bottom:0;background:var(--ink);color:var(--surface);padding:10px 20px;display:none;align-items:center;gap:12px;font-size:12px}
.override-bar.show{display:flex}
.override-bar .btn{background:var(--accent);color:#fff;border:none}
.settings-bar{background:var(--surface);border:1px solid var(--line);border-radius:8px;margin:0 auto 12px;max-width:1100px;padding:12px 16px;font-size:12px}
.settings-bar summary{cursor:pointer;font-weight:700;color:var(--ink)}
.settings-bar .row{display:flex;flex-wrap:wrap;align-items:center;gap:8px;margin-top:10px}
.settings-bar label{color:var(--ink2);white-space:nowrap}
.settings-bar input,.settings-bar select{padding:4px 6px;font-size:11px;border:1px solid var(--line2);border-radius:4px}
.settings-bar .desc{color:var(--muted);font-size:11px;margin:4px 0 0}
.settings-btn{background:var(--surface);border:1px solid var(--line);border-radius:6px;padding:6px 12px;font-size:12px;font-weight:700;color:var(--ink);cursor:pointer}
.th-table{width:100%;border-collapse:collapse;margin-top:10px}
.th-table th,.th-table td{padding:5px 8px;border-bottom:1px solid var(--line);font-size:11px;text-align:left}
.th-table th{color:var(--muted);font-weight:700}
.th-table td:first-child{color:var(--ink2)}
.th-table input{width:36px;text-align:right}
.tabs{display:flex;gap:4px}
.tab-btn{padding:6px 16px;border-radius:6px 6px 0 0;border:none;background:rgba(255,255,255,0.12);color:#fff;font-size:12px;font-weight:700;cursor:pointer}
.tab-btn.active{background:var(--soft);color:var(--ink)}
.analysis-section{background:var(--surface);border-radius:8px;padding:16px 20px;margin-bottom:16px}
.analysis-section h3{font-size:14px;margin:0 0 4px}
.analysis-section .sub{color:var(--muted);font-size:11px;margin:0 0 12px}
.donut-grid{display:flex;flex-wrap:wrap;gap:16px}
.donut-cell{display:flex;flex-direction:column;align-items:center;width:88px}
.donut-cell .name{font-size:10px;color:var(--ink2);text-align:center;margin-top:4px;line-height:1.3}
.big-stat{display:flex;align-items:center;gap:20px}
.big-stat .num{font-size:36px;font-weight:700}
.big-stat .detail{color:var(--muted);font-size:12px}
</style>
</head>
<body>
<div class="hdr">
  <h1>MLB QM Weekly Analysis</h1>
  <select id="week-select" onchange="onWeekChange()"></select>
  <div class="tabs">
    <button class="tab-btn active" id="tab-btn-main" onclick="switchTab('main')">요약</button>
    <button class="tab-btn" id="tab-btn-analysis" onclick="switchTab('analysis')">분석</button>
  </div>
  <span class="sp"></span>
  <button class="ib" onclick="toggleTheme()" title="밝게/어둡게">◐</button>
</div>
<div id="main-tab">
<div style="max-width:1100px;margin:16px auto 0;display:flex;justify-content:flex-end">
  <button class="settings-btn" onclick="switchTab('settings')">⚙ 설정</button>
</div>
<div class="content" id="seasons"></div>
<div class="override-bar" id="override-bar">
  <span id="override-count"></span>
  <span id="override-status"></span>
  <button class="btn" onclick="downloadOverrides()">오버라이드 파일 다운로드(백업용)</button>
</div>
</div>
<div class="content" id="analysis-tab" style="display:none">
  <div style="margin-bottom:12px">
    <label style="font-weight:700;margin-right:8px">시즌</label><select id="analysis-season-select" onchange="renderAnalysis()"></select>
  </div>
  <div id="analysis-body"></div>
</div>
<div class="content" id="settings-tab" style="display:none">
  <div style="max-width:1100px;margin:0 auto">
    <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:12px">
      <h2 style="margin:0">설정</h2>
      <button class="btn" onclick="switchTab('main')">닫기</button>
    </div>
    <details class="settings-bar">
      <summary>기준일 설정 (시즌별)</summary>
      <p class="desc">전체 스타일 수 기준 = 완료 / 전체. Due Date 기준 = as_of_date까지 due date 지난 것 중 완료 / 지난 것 전체(계획 대비 실적).<br>이번 주(라이브)는 항상 오늘 날짜 기준. 특정 날짜로 보고 싶을 때만 아래에 지정(시즌마다 따로 가능).</p>
      <div id="as-of-rows"></div>
      <div class="row"><button class="btn" onclick="applySettings()">적용</button><span id="settings-status"></span></div>
    </details>
    <div id="due-offset-panels"></div>
  </div>
</div>
<script id="snapshot-data" type="application/json">__SNAPSHOT_JSON__</script>
<script id="settings-data" type="application/json">__SETTINGS_JSON__</script>
<script id="due-offsets-data" type="application/json">__DUE_OFFSETS_JSON__</script>
<script>
// 화면 테마: 저장해둔 값이 있으면 그걸, 없으면 OS 설정을 따른다.
try {
  const savedTheme = localStorage.getItem('mlb_qm_theme');
  if (savedTheme) document.documentElement.dataset.theme = savedTheme;
} catch (e) { /* 저장소를 못 쓰는 환경이면 OS 설정 그대로 */ }

function toggleTheme() {
  const cur = document.documentElement.dataset.theme
    || (window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light');
  const next = cur === 'dark' ? 'light' : 'dark';
  document.documentElement.dataset.theme = next;
  try { localStorage.setItem('mlb_qm_theme', next); } catch (e) { /* 무시 */ }
}

const DATA = JSON.parse(document.getElementById('snapshot-data').textContent);
const SETTINGS = JSON.parse(document.getElementById('settings-data').textContent);
const DUE_OFFSETS = JSON.parse(document.getElementById('due-offsets-data').textContent);
const weekIds = Object.keys(DATA.weeks).sort().reverse();
const sel = document.getElementById('week-select');
// 가장 최근 수요일 18시(수요일 18시를 넘겨야 그 수요일이 기준일) — resolveAsOfDate()의 기본값과
// 같은 공식. 데이터가 최신인 날짜(라이브)랑 due date 판단 기준일을 한 표시로 맞추려고 씀.
// server의 current_live_as_of()와 동일 규칙(AS_OF_WEEKDAY=수, AS_OF_HOUR=18).
function mostRecentAsOfStr() {
  const today = new Date();
  let daysSinceAsOf = (today.getDay() - 3 + 7) % 7;  // JS: Sun=0..Wed=3
  if (daysSinceAsOf === 0 && today.getHours() < 18) daysSinceAsOf = 7;
  const d = new Date(today.getFullYear(), today.getMonth(), today.getDate() - daysSinceAsOf);
  const mm = String(d.getMonth() + 1).padStart(2, '0');
  const dd = String(d.getDate()).padStart(2, '0');
  return `${d.getFullYear()}-${mm}-${dd}`;
}
weekIds.forEach((w, i) => {
  const asOf = i === 0 ? mostRecentAsOfStr() : DATA.weeks[w].as_of_date; // i===0: 최신(라이브) 주
  const o = document.createElement('option');
  o.value = w;
  o.textContent = w + ' (기준일 ' + asOf + ')';
  sel.appendChild(o);
});

const seasons = weekIds.length ? Object.keys(DATA.weeks[weekIds[0]].raw || {}).sort() : [];
const asOfBySeason = SETTINGS.as_of_by_season || {};

const asOfRowsEl = document.getElementById('as-of-rows');
seasons.forEach(season => {
  const s = asOfBySeason[season] || {};
  const row = document.createElement('div');
  row.className = 'row';
  row.dataset.season = season;
  row.innerHTML = `<label style="min-width:48px;font-weight:700">${esc(season)}</label>` +
    `<label>특정 날짜로 고정(선택)</label><input type="date" data-field="override">` +
    `<span class="as-of-badge" style="margin-left:8px;color:#4a65a9;font-weight:700"></span>`;
  row.querySelector('[data-field="override"]').value = s.as_of_date_override || '';
  asOfRowsEl.appendChild(row);
});

function updateAsOfBadges() {
  seasons.forEach(season => {
    const row = asOfRowsEl.querySelector(`[data-season="${season}"]`);
    if (!row) return;
    row.querySelector('.as-of-badge').textContent = `→ ${resolveAsOfDate(season)} 기준으로 계산 중`;
  });
}

asOfRowsEl.querySelectorAll('select,input').forEach(el => el.addEventListener('input', () => { updateAsOfBadges(); refresh(); }));

function resolveAsOfDate(season) {
  // 매주 "지난 한 주(수요일 18시 마감)"를 분석하는 기준 — due date 지났는지 판단하는
  // 기준일은 "가장 최근 수요일 18시". override가 있으면 우선.
  // (데이터 자체는 오늘까지 반영된 최신 상태 — 여기서 정하는 건 그중 어디까지를 "이번 판단
  // 대상"으로 볼지의 기준일일 뿐. server의 current_live_as_of()와 동일한 공식.)
  const row = asOfRowsEl.querySelector(`[data-season="${season}"]`);
  const override = row ? row.querySelector('[data-field="override"]').value : '';
  if (override) return override;
  return mostRecentAsOfStr();
}

function dueOffsetsKey(season) { return `mlb_qm_fitting_due_offsets_${season}`; }
function dueOffsetBodyId(season) { return `due-offset-table-${season}`.replace(/[^\\w-]/g, '_'); }

const duePanelsEl = document.getElementById('due-offset-panels');
seasons.forEach(season => {
  const panel = document.createElement('details');
  panel.className = 'settings-bar';
  const bodyId = dueOffsetBodyId(season);
  panel.innerHTML = `<summary>${esc(season)} DUE DATE 설정 기준</summary>
    <table class="th-table">
      <thead><tr><th>구분</th><th>워시기준</th><th>수량기준</th><th style="text-align:right">QC(FIT)</th><th style="text-align:right">PP</th><th style="text-align:right">TOP</th></tr></thead>
      <tbody id="${bodyId}"></tbody>
    </table>
    <div class="row"><button class="btn" onclick="applyDueOffsets('${season}')">적용</button><button class="btn" onclick="resetDueOffsets('${season}')">초기화</button><span id="due-offset-status-${bodyId}"></span></div>`;
  duePanelsEl.appendChild(panel);

  const body = panel.querySelector(`#${bodyId}`);
  DUE_OFFSETS.forEach(row => {
    const tr = document.createElement('tr');
    tr.dataset.label = row.label;
    tr.dataset.category = row.category;
    tr.dataset.wash = row.wash;
    tr.dataset.qtyTier = row.qty_tier;
    tr.innerHTML = `<td>${esc(row.category)}</td><td>${esc(row.wash)}</td><td>${esc(row.qty_tier)}</td>` +
      `<td style="text-align:right"><input type="number" data-stage="FIT" value="${row.FIT}"> 일 전</td>` +
      `<td style="text-align:right"><input type="number" data-stage="PP" value="${row.PP}"> 일 전</td>` +
      `<td style="text-align:right"><input type="number" data-stage="TOP" value="${row.TOP}"> 일 전</td>`;
    body.appendChild(tr);
  });
  body.querySelectorAll('input[data-stage]').forEach(inp => inp.addEventListener('input', () => refresh()));
});

function dueOffsetBody(season) { return document.getElementById(dueOffsetBodyId(season)); }

function currentOffsets(season) {
  const m = {};
  const body = dueOffsetBody(season);
  if (!body) return m;
  body.querySelectorAll('tr').forEach(tr => {
    const e = {};
    tr.querySelectorAll('input[data-stage]').forEach(inp => { e[inp.dataset.stage] = parseInt(inp.value, 10) || 0; });
    m[tr.dataset.label] = e;
  });
  return m;
}

function remarkKey(season, owner, stage) { return `${season}|${owner}|${stage}`; }
function remarkSettingsKey(weekId) { return `mlb_qm_remark_${weekId}`; }

function unlockRemark(domId) {
  const input = document.getElementById(domId);
  input.readOnly = false;
  input.focus();
  input.select();
}

async function saveRemarkValue(weekId, domId, storageKey) {
  const input = document.getElementById(domId);
  if (input.readOnly) return; // dblclick으로 잠금 해제 안 한 상태에서 blur만 지나가는 경우
  const text = input.value;
  try {
    // 같은 주의 다른 칸 비고를 덮어쓰지 않게, 저장된 값을 먼저 읽어와서 이 칸만 바꿔 합친다.
    const readResp = await fetch(`${SETTINGS.supabase_url}/rest/v1/settings?select=value&key=eq.${remarkSettingsKey(weekId)}`, {
      headers: {'apikey': SETTINGS.supabase_anon_key, 'Authorization': `Bearer ${SETTINGS.supabase_anon_key}`},
    });
    const rows = await readResp.json();
    const current = (rows[0] && rows[0].value) ? JSON.parse(rows[0].value) : {};
    current[storageKey] = text;
    const saveResp = await fetch(`${SETTINGS.supabase_url}/rest/v1/settings`, {
      method: 'POST',
      headers: {
        'apikey': SETTINGS.supabase_anon_key,
        'Authorization': `Bearer ${SETTINGS.supabase_anon_key}`,
        'Content-Type': 'application/json',
        'Prefer': 'resolution=merge-duplicates',
      },
      body: JSON.stringify({key: remarkSettingsKey(weekId), value: JSON.stringify(current)}),
    });
    if (!saveResp.ok) throw new Error(await saveResp.text());
    if (DATA.weeks[weekId]) DATA.weeks[weekId].remarks = current;
  } catch (e) {
    alert('비고 저장 실패: ' + e.message);
  } finally {
    input.readOnly = true;
  }
}

async function saveRemark(weekId, season, owner, stage) {
  const domId = `remark-${weekId}-${season}-${owner}-${stage}`.replace(/[^\\w-]/g, '_');
  await saveRemarkValue(weekId, domId, remarkKey(season, owner, stage));
}

async function saveOverdueRemark(weekId, season, styleCode, stage) {
  const domId = `overdue-${weekId}-${season}-${styleCode}-${stage}`.replace(/[^\\w-]/g, '_');
  await saveRemarkValue(weekId, domId, overdueRemarkKey(season, styleCode, stage));
}

async function applyDueOffsets(season) {
  const body = dueOffsetBody(season);
  const value = {};
  body.querySelectorAll('tr').forEach(tr => {
    const entry = {category: tr.dataset.category, wash: tr.dataset.wash, qty_tier: tr.dataset.qtyTier};
    tr.querySelectorAll('input[data-stage]').forEach(inp => { entry[inp.dataset.stage] = parseInt(inp.value, 10); });
    value[tr.dataset.label] = entry;
  });

  const statusEl = document.getElementById(`due-offset-status-${dueOffsetBodyId(season)}`);
  statusEl.textContent = '저장 중...';
  try {
    const resp = await fetch(`${SETTINGS.supabase_url}/rest/v1/settings`, {
      method: 'POST',
      headers: {
        'apikey': SETTINGS.supabase_anon_key,
        'Authorization': `Bearer ${SETTINGS.supabase_anon_key}`,
        'Content-Type': 'application/json',
        'Prefer': 'resolution=merge-duplicates',
      },
      body: JSON.stringify({key: dueOffsetsKey(season), value: JSON.stringify(value)}),
    });
    if (!resp.ok) throw new Error(await resp.text());
    statusEl.textContent = '저장됨 (이 화면엔 이미 반영됨, 다음 실행 기본값으로도 저장)';
  } catch (e) {
    statusEl.textContent = '저장 실패: ' + e.message;
  }
}

async function loadSavedAsOfSettings() {
  try {
    const resp = await fetch(`${SETTINGS.supabase_url}/rest/v1/settings?select=value&key=eq.mlb_qm_fitting_report_config`, {
      headers: {'apikey': SETTINGS.supabase_anon_key, 'Authorization': `Bearer ${SETTINGS.supabase_anon_key}`},
    });
    if (!resp.ok) throw new Error(await resp.text());
    const rows = await resp.json();
    if (rows.length && rows[0].value) {
      const saved = JSON.parse(rows[0].value).as_of_by_season || {};
      asOfRowsEl.querySelectorAll('[data-season]').forEach(row => {
        const s = saved[row.dataset.season];
        if (!s) return;
        row.querySelector('[data-field="override"]').value = s.as_of_date_override || '';
      });
    }
  } catch (e) {
    // 저장된 값 조회 실패해도 서버에 마지막으로 구운 기본값으로 화면은 뜬다 (fail open)
  }
}

async function loadSavedDueOffsets(season) {
  const body = dueOffsetBody(season);
  if (!body) return;
  try {
    const resp = await fetch(`${SETTINGS.supabase_url}/rest/v1/settings?select=value&key=eq.${dueOffsetsKey(season)}`, {
      headers: {'apikey': SETTINGS.supabase_anon_key, 'Authorization': `Bearer ${SETTINGS.supabase_anon_key}`},
    });
    if (!resp.ok) throw new Error(await resp.text());
    const rows = await resp.json();
    if (rows.length && rows[0].value) {
      const saved = JSON.parse(rows[0].value);
      body.querySelectorAll('tr').forEach(tr => {
        const s = saved[tr.dataset.label];
        if (!s) return;
        tr.querySelectorAll('input[data-stage]').forEach(inp => {
          if (s[inp.dataset.stage] !== undefined) inp.value = s[inp.dataset.stage];
        });
      });
    }
  } catch (e) {
    // 저장된 값 조회 실패해도 코드 기본값(DUE_OFFSETS)으로 화면은 뜬다 (fail open)
  }
}

function resetDueOffsets(season) {
  const body = dueOffsetBody(season);
  DUE_OFFSETS.forEach(row => {
    const tr = [...body.children].find(t => t.dataset.label === row.label);
    if (!tr) return;
    tr.querySelectorAll('input[data-stage]').forEach(inp => { inp.value = row[inp.dataset.stage]; });
  });
  document.getElementById(`due-offset-status-${dueOffsetBodyId(season)}`).textContent = '기본값으로 초기화됨(저장하려면 적용 누르기)';
  refresh();
}

async function applySettings() {
  const as_of_by_season = {};
  asOfRowsEl.querySelectorAll('[data-season]').forEach(row => {
    as_of_by_season[row.dataset.season] = {
      as_of_date_override: row.querySelector('[data-field="override"]').value || null,
    };
  });
  const value = JSON.stringify({as_of_by_season});

  const statusEl = document.getElementById('settings-status');
  statusEl.textContent = '저장 중...';
  try {
    const resp = await fetch(`${SETTINGS.supabase_url}/rest/v1/settings`, {
      method: 'POST',
      headers: {
        'apikey': SETTINGS.supabase_anon_key,
        'Authorization': `Bearer ${SETTINGS.supabase_anon_key}`,
        'Content-Type': 'application/json',
        'Prefer': 'resolution=merge-duplicates',
      },
      body: JSON.stringify({key: 'mlb_qm_fitting_report_config', value}),
    });
    if (!resp.ok) throw new Error(await resp.text());
    statusEl.textContent = '저장됨 (이 화면엔 이미 실시간 반영됨, 다음 실행 기본값으로도 저장)';
  } catch (e) {
    statusEl.textContent = '저장 실패: ' + e.message;
  }
}

function pct(done, all) { return all > 0 ? Math.round(done / all * 1000) / 10 : 0; }

function esc(s) {
  return String(s).replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
}

let edits = {}; // key `${season}|${owner}|${stage}` -> {season, stage, owner_type, override_numerator, override_denominator}

function editKey(season, owner, stage) { return `${season}|${owner}|${stage}`; }

function overridesSettingsKey(week) { return `mlb_qm_fitting_overrides_${week}`; }

async function loadOverridesForWeek(week) {
  edits = {};
  try {
    const resp = await fetch(`${SETTINGS.supabase_url}/rest/v1/settings?select=value&key=eq.${overridesSettingsKey(week)}`, {
      headers: {'apikey': SETTINGS.supabase_anon_key, 'Authorization': `Bearer ${SETTINGS.supabase_anon_key}`},
    });
    if (!resp.ok) throw new Error(await resp.text());
    const rows = await resp.json();
    if (rows.length && rows[0].value) {
      JSON.parse(rows[0].value).forEach(o => { edits[editKey(o.season, o.owner_type, o.stage)] = o; });
    }
  } catch (e) {
    // 조회 실패해도 화면은 원래 값으로 보여준다 (fail open)
  }
  const bar = document.getElementById('override-bar');
  const count = Object.keys(edits).length;
  bar.classList.toggle('show', count > 0);
  document.getElementById('override-count').textContent = count ? `수정 ${count}건 적용됨` : '';
}

async function refreshRemarksForWeek(weekId) {
  // 비고는 서버 응답 캐시(5분)에 갇히면 방금 저장한 값이 새로고침 시 안 보일 수 있어서,
  // 화면 그리기 직전에 항상 Supabase에서 직접 최신값을 받아온다(진행률/raw는 그대로 캐시된 값 사용).
  if (!DATA.weeks[weekId]) return;
  try {
    const resp = await fetch(`${SETTINGS.supabase_url}/rest/v1/settings?select=value&key=eq.${remarkSettingsKey(weekId)}`, {
      headers: {'apikey': SETTINGS.supabase_anon_key, 'Authorization': `Bearer ${SETTINGS.supabase_anon_key}`},
    });
    const rows = await resp.json();
    DATA.weeks[weekId].remarks = (rows[0] && rows[0].value) ? JSON.parse(rows[0].value) : {};
  } catch (e) {
    // 실패해도 페이지 로드 자체를 막을 필요는 없음 — 서버가 같이 내려준 값 그대로 둔다.
  }
}

async function onWeekChange() {
  await loadOverridesForWeek(sel.value);
  await refreshRemarksForWeek(sel.value);
  refresh();
}

async function applyEdit(season, owner, stage) {
  const key = editKey(season, owner, stage);
  const done = parseInt(document.getElementById(`in-done-${key}`).value, 10);
  const all = parseInt(document.getElementById(`in-all-${key}`).value, 10);
  edits[key] = {season, stage, owner_type: owner, override_numerator: done, override_denominator: all};
  refresh();
  const bar = document.getElementById('override-bar');
  bar.classList.add('show');
  document.getElementById('override-count').textContent = `수정 ${Object.keys(edits).length}건 적용됨`;

  const statusEl = document.getElementById('override-status');
  statusEl.textContent = '저장 중...';
  try {
    const resp = await fetch(`${SETTINGS.supabase_url}/rest/v1/settings`, {
      method: 'POST',
      headers: {
        'apikey': SETTINGS.supabase_anon_key,
        'Authorization': `Bearer ${SETTINGS.supabase_anon_key}`,
        'Content-Type': 'application/json',
        'Prefer': 'resolution=merge-duplicates',
      },
      body: JSON.stringify({key: overridesSettingsKey(sel.value), value: JSON.stringify(Object.values(edits))}),
    });
    if (!resp.ok) throw new Error(await resp.text());
    statusEl.textContent = '저장됨';
  } catch (e) {
    statusEl.textContent = '저장 실패: ' + e.message;
  }
}

function downloadOverrides() {
  const payload = Object.values(edits);
  const blob = new Blob([JSON.stringify(payload, null, 2)], {type: 'application/json'});
  const a = document.createElement('a');
  a.href = URL.createObjectURL(blob);
  a.download = `${sel.value}.json`;
  a.click();
}

const OWNER_BY_STAGE = {FIT: 'TD', PP: 'QA', TOP: 'QA'};
const STAGES = ['FIT', 'PP', 'TOP'];

// row.fit_due/pp_due/top_due: DUE_DATA(2) 또는 Supabase 고정 due(ISO 문자열)면 그걸 그대로 씀(offset표 무관).
// 없고 row.label/row.etd(26FW만 있음)가 있으면 지금 화면의 DUE DATE 설정 기준표로 즉석 계산.
// 기준표에 label이 그대로 없을 때 폴백. DENIM은 기준표에 "워싱일반" 한 줄뿐이라(사용자 제공 표
// 기준), DENIM인데 논워싱으로 찍힌 극소수 예외 건은 DENIM워싱일반 기준을 그대로 쓴다.
function offsetLookupLabel(label, offsets) {
  if (label && offsets[label]) return label;
  if (label && label.startsWith('DENIM논워싱')) {
    const alt = 'DENIM워싱' + label.slice('DENIM논워싱'.length);
    if (offsets[alt]) return alt;
  }
  return null;
}

function resolveDue(row, stage, offsets) {
  const fixed = row[`${stage.toLowerCase()}_due`];
  if (fixed) return fixed;
  const lookupLabel = offsetLookupLabel(row.label, offsets);
  if (lookupLabel && row.etd) {
    const etd = new Date(row.etd + 'T00:00:00');
    etd.setDate(etd.getDate() - offsets[lookupLabel][stage]);
    return etd.toISOString().slice(0, 10);
  }
  return null;
}

function shortDate(iso) {
  if (!iso) return '';
  const parts = iso.split('-');
  if (parts.length !== 3) return iso;
  return `${parseInt(parts[1], 10)}/${parseInt(parts[2], 10)}`;
}

function ordinalRound(round) {
  if (round === null || round === undefined || round === '') return '';
  if (typeof round === 'number') return ['1ST', '2ND', '3RD', '4TH', '5TH'][round - 1] || `${round}TH`;
  return round;
}

const VENDOR_ALIASES = {
  '(주) 약진통상': '약진통상',
  '(주)기도산업': '기도산업',
  '(주)다인지아이씨': '다인',
  '(주)팬코': '팬코',
  '(주)포마트코퍼레이션': '포마트',
  'BOSIDENG INTERNATIONAL FASHION(SIGNAPORE)PTE.LTD.': 'BOSIDENG',
  'DONGGUAN OUTIN TRADE Co., LTD': 'OUTIN',
  'DONGGUAN TONGFA KNITWEARS CO., LTD.': 'TONGFA',
  'ESQUEL ENTERPRISES LIMITED': 'ESQUEL',
  'HONGKONG KING TIDE FASHION CO.,LIMITED': 'KING TIDE',
  'HONGYING GARMENT CO., LTD': 'HONGYING',
  'Hongying garment CO., LTD': 'HONGYING',
  'ITOCHU TEXTILE(CHINA)CO.,LTD.': 'ITOCHU',
  'SUNRISE(Henan Shengtai Knitting Co.,LTD)': 'SUNRISE',
  '㈜노브랜드': '노브랜드',
  '㈜노브랜드(우븐)': '노브랜드(우븐)',
  '원전교역': '원전',
  '주식회사 거림씨앤에프': '거림',
  '주식회사 에이엠지엠브이': 'AM GMV',
  '티피나디아㈜': '나디아',
  '한솔섬유 (주)': '한솔',
};

function vendorAlias(v) {
  if (!v) return v;
  const trimmed = v.trim();
  return VENDOR_ALIASES[trimmed] || trimmed;
}

// 현재 stage가 아직 접수 전이면, 이전 stage(보정<FIT<PP<TOP 순)에서 가장 최근 전달된 회차를 찾는다.
// {label: "2ND FIT", date: "2026-07-05", reason: "..."} 형태. 아무 이전 활동도 없으면 null.
function recentActivityBefore(row, stage) {
  const order = ['보정', 'FIT', 'PP', 'TOP'];
  const idx = order.indexOf(stage);
  for (let i = idx - 1; i >= 0; i--) {
    const s = order[i];
    const d = (row.detail && row.detail[s]) || {};
    if (d.confirm_date) return {label: `${ordinalRound(d.round)} ${s}`.trim(), date: d.confirm_date, reason: d.reason || null};
  }
  return null;
}

// iso(YYYY-MM-DD)부터 refIso(기준일, 보통 위에서 지정한 as_of_date)까지 주말 뺀 영업일수. iso가 refIso 이후면 0.
function businessDaysSince(iso, refIso) {
  if (!iso || !refIso) return null;
  const start = new Date(iso + 'T00:00:00');
  const end = new Date(refIso + 'T00:00:00');
  let count = 0;
  const cur = new Date(start);
  while (cur < end) {
    cur.setDate(cur.getDate() + 1);
    const day = cur.getDay();
    if (day !== 0 && day !== 6) count++;
  }
  return count;
}

function computeProgressFromRaw(rawRows, asOfDate, offsets) {
  const result = {TD: {}, QA: {}};
  for (const row of rawRows) {
    for (const stage of STAGES) {
      const isDone = row[`${stage.toLowerCase()}_done`];
      const due = resolveDue(row, stage, offsets);
      // due date를 못 구했어도(라벨/ETD 누락 등) 이미 완료된 건은 "Due Date 기준"에서 완료로 잡는다.
      // 안 그러면 그 스타일은 어느 쪽 통계에도 안 잡히고 조용히 빠져버림.
      const isDue = !!(due && due <= asOfDate) || (!due && isDone);
      const owner = OWNER_BY_STAGE[stage];
      const bucket = result[owner][stage] || (result[owner][stage] = {total_done: 0, total_all: 0, baseline_done: 0, baseline_all: 0, overdue: []});
      bucket.total_all++;
      if (isDone) bucket.total_done++;
      if (isDue) {
        bucket.baseline_all++;
        if (isDone) {
          bucket.baseline_done++;
        } else {
          const d = (row.detail && row.detail[stage]) || {};
          // 기도산업은 2ND TOP을 보지 않는다 - TOP을 이미 한 번 낸 뒤라면 리젝이 나도 다음
          // 회차가 없어서 납기에 영향이 없다. 완료율(Due%/전체%)엔 그대로 미완료로 잡고,
          // 챙길 대상을 추리는 미완료 상세 리스트에서만 뺀다.
          // TOP을 아직 접수조차 안 한 건(회차 기록 없음)은 여전히 챙겨야 하므로 남긴다.
          if (stage === 'TOP' && vendorAlias(row.vendor) === '기도산업' && d.round) continue;
          let confirmRawDate = d.confirm_date || null;
          let confirmStage = d.confirm_date ? `${ordinalRound(d.round)} ${stage}`.trim() : null;
          let confirmReason = d.confirm_date ? (d.reason || null) : null;
          if (!confirmRawDate) {
            const recent = recentActivityBefore(row, stage);
            if (recent) { confirmRawDate = recent.date; confirmStage = recent.label; confirmReason = recent.reason; }
          }
          // 납기(ETD) 영향 여부: due~ETD 사이 원래 버퍼(영업일)보다 이미 초과한 일수가 많거나
          // 같으면 그 버퍼를 다 까먹은 것 -> 영향 있음. ETD가 없으면 판단 불가로 null.
          const overdueDays = businessDaysSince(due, asOfDate);
          const etdBufferDays = (due && row.etd) ? businessDaysSince(due, row.etd) : null;
          const impactsDelivery = etdBufferDays == null ? null : overdueDays >= etdBufferDays;
          bucket.overdue.push({
            style_code: row.style_code, vendor: row.vendor || null, due, status: d.status || '접수 전',
            confirm_stage: confirmStage, confirm_date: confirmRawDate ? shortDate(confirmRawDate) : null,
            elapsed_days: businessDaysSince(confirmRawDate, asOfDate), overdue_days: overdueDays,
            etd: row.etd || null, etd_buffer_days: etdBufferDays, impacts_delivery: impactsDelivery,
            reason: confirmReason,
          });
        }
      }
    }
  }
  return result;
}

// 펼쳐둔 상세표가 어떤 것들인지 기억해둔다 - 정렬하면 화면을 다시 그리는데,
// 기억 안 하면 눌러둔 표가 도로 접혀버린다.
const overdueOpen = new Set();
// 상세표별 정렬 상태: overdueId -> {key, dir(1=오름차순, -1=내림차순)}
const overdueSort = {};

function toggleOverdue(id) {
  const el = document.getElementById(id);
  if (!el) return;
  const willOpen = el.style.display === 'none';
  el.style.display = willOpen ? 'block' : 'none';
  if (willOpen) overdueOpen.add(id); else overdueOpen.delete(id);
}

function sortOverdue(id, key) {
  const cur = overdueSort[id];
  overdueSort[id] = (cur && cur.key === key) ? {key, dir: -cur.dir} : {key, dir: 1};
  overdueOpen.add(id);
  render();
}

// 값 없는 칸은 방향과 상관없이 항상 뒤로 보낸다(빈칸이 위에 쌓이면 보기 나쁨).
function compareOverdueValues(a, b) {
  const aEmpty = a == null || a === '';
  const bEmpty = b == null || b === '';
  if (aEmpty || bEmpty) return aEmpty && bEmpty ? 0 : (aEmpty ? 1 : -1);
  if (typeof a === 'number' && typeof b === 'number') return a - b;
  if (typeof a === 'boolean' || typeof b === 'boolean') return (a ? 1 : 0) - (b ? 1 : 0);
  return String(a).localeCompare(String(b), 'ko');
}

function sortedOverdue(overdue, overdueId) {
  const st = overdueSort[overdueId];
  if (!st) return overdue;
  const pick = o => st.key === 'vendor' ? (vendorAlias(o.vendor) || '') : o[st.key];
  return [...overdue].sort((x, y) => {
    const c = compareOverdueValues(pick(x), pick(y));
    return c === 0 ? 0 : c * st.dir;
  });
}

let activeTab = 'main';

function switchTab(tab) {
  activeTab = tab;
  document.getElementById('main-tab').style.display = tab === 'main' ? '' : 'none';
  document.getElementById('analysis-tab').style.display = tab === 'analysis' ? '' : 'none';
  document.getElementById('settings-tab').style.display = tab === 'settings' ? '' : 'none';
  document.getElementById('tab-btn-main').classList.toggle('active', tab === 'main');
  document.getElementById('tab-btn-analysis').classList.toggle('active', tab === 'analysis');
  if (tab === 'analysis') renderAnalysis();
}

function refresh() {
  render();
  if (activeTab === 'analysis') renderAnalysis();
}

// ==== 분석 탭 ====

function colorForPct(pct) {
  if (pct >= 100) return '#2e9e5b';
  if (pct >= 70) return '#e0a72e';
  return '#d9534f';
}

function escSvg(s) { return esc(String(s == null ? '' : s)); }

function hBarChart(items, opts) {
  opts = opts || {};
  const width = opts.width || 460;
  const barHeight = opts.barHeight || 20;
  const gap = opts.gap != null ? opts.gap : 8;
  const labelWidth = opts.labelWidth || 100;
  const unit = opts.unit || '';
  const color = opts.color || '#4a65a9';
  const max = opts.maxValue || Math.max(1, ...items.map(i => i.value));
  const chartWidth = width - labelWidth - 44;
  const height = items.length * (barHeight + gap);
  let bars = '';
  items.forEach((it, i) => {
    const y = i * (barHeight + gap);
    const w = Math.max(2, (it.value / max) * chartWidth);
    bars += `<text x="${labelWidth - 8}" y="${y + barHeight / 2}" text-anchor="end" dominant-baseline="central" font-size="11" fill="var(--ink2)">${escSvg(it.label)}</text>` +
      `<rect x="${labelWidth}" y="${y + 2}" width="${w.toFixed(1)}" height="${barHeight - 4}" rx="4" fill="${it.color || color}">` +
      `<title>${escSvg(it.label)} ${escSvg(it.value)}${escSvg(unit)}</title></rect>` +
      `<text x="${labelWidth + w + 6}" y="${y + barHeight / 2}" dominant-baseline="central" font-size="11" fill="var(--ink)">${escSvg(it.value)}${unit}</text>`;
  });
  return `<svg width="${width}" height="${Math.max(height, 1)}">${bars}</svg>`;
}

// 그룹 막대그래프: 기간(주/월)마다 여러 series(주차별/누적 등)를 나란히. values는 periods와 같은 길이,
// 없는 기간은 null.
function groupedBarChart(periods, series, opts) {
  opts = opts || {};
  const width = opts.width || 900, height = opts.height || 240;
  const unit = opts.unit != null ? opts.unit : '%';
  // showValues: 막대 위에 값을 세로로 적는다(막대가 얇아 가로로는 안 들어간다).
  // rotateLabels: x축 이름이 길어 겹칠 때 비스듬히 눕힌다.
  const showValues = !!opts.showValues;
  const rotateLabels = !!opts.rotateLabels;
  const padL = 34, padR = 10, padT = showValues ? 26 : 10, padB = rotateLabels ? 64 : 30;
  const chartW = width - padL - padR, chartH = height - padT - padB;
  const n = Math.max(periods.length, 1);
  const groupW = chartW / n;
  const barCount = Math.max(series.length, 1);
  const barW = Math.max(1, (groupW - 2) / barCount);
  // Y축 최대값: 값이 100 넘는 게 있으면(조기완료 누적처럼) 그만큼 자동으로 늘어난다.
  const dataMax = Math.max(0, ...series.flatMap(s => s.values.filter(v => v != null)));
  const yMax = opts.yMax || Math.max(100, Math.ceil(dataMax / 50) * 50);
  const ticks = [0, 0.25, 0.5, 0.75, 1].map(t => Math.round(yMax * t));
  let out = '';
  ticks.forEach(v => {
    const y = padT + chartH - (v / yMax) * chartH;
    out += `<line x1="${padL}" y1="${y.toFixed(1)}" x2="${width - padR}" y2="${y.toFixed(1)}" stroke="var(--line)"/>` +
      `<text x="${padL - 6}" y="${(y + 3).toFixed(1)}" text-anchor="end" font-size="9" fill="var(--muted)">${v}</text>`;
  });
  periods.forEach((p, gi) => {
    const gx = padL + gi * groupW;
    series.forEach((s, si) => {
      const v = s.values[gi];
      if (v == null) return;
      const bh = Math.max(0, (Math.min(v, yMax) / yMax) * chartH);
      const x = gx + si * barW + 1;
      const y = padT + chartH - bh;
      // <title>은 브라우저 기본 툴팁 - 커서를 올리면 "주차 · 시리즈 · 값"이 그대로 뜬다.
      out += `<rect x="${x.toFixed(1)}" y="${y.toFixed(1)}" width="${Math.max(1, barW - 1).toFixed(1)}" height="${bh.toFixed(1)}" fill="${s.color}" opacity="${s.opacity != null ? s.opacity : 1}">` +
        `<title>${escSvg(p)} · ${escSvg(s.name)} ${escSvg(v)}${escSvg(unit)}</title></rect>`;
      if (showValues) {
        // 가로로 적는다. 막대가 얇아 글자가 서로 붙을 수 있어 막대 폭에 맞춰 글씨를 줄인다.
        const fs = Math.max(6, Math.min(9, barW * 0.62));
        out += `<text x="${(x + barW / 2).toFixed(1)}" y="${(y - 3).toFixed(1)}" text-anchor="middle" ` +
          `font-size="${fs.toFixed(1)}" fill="var(--ink2)">${escSvg(v)}</text>`;
      }
    });
    const groupTip = series.map(s => s.values[gi] == null ? null : `${s.name} ${s.values[gi]}${unit}`)
      .filter(Boolean).join('  /  ');
    out += `<rect x="${gx.toFixed(1)}" y="${padT}" width="${groupW.toFixed(1)}" height="${chartH}" fill="transparent">` +
      `<title>${escSvg(p)}${groupTip ? ' - ' + escSvg(groupTip) : ''}</title></rect>`;
    const lx = (gx + groupW / 2).toFixed(1);
    out += rotateLabels
      ? `<text x="${lx}" y="${(padT + chartH + 10).toFixed(1)}" transform="rotate(-35 ${lx} ${(padT + chartH + 10).toFixed(1)})" ` +
        `text-anchor="end" font-size="9" fill="var(--muted)">${escSvg(p)}</text>`
      : `<text x="${lx}" y="${height - 8}" text-anchor="middle" font-size="9" fill="var(--muted)">${escSvg(p)}</text>`;
  });
  const legend = series.map((s, i) =>
    `<span style="display:inline-flex;align-items:center;gap:4px;margin-right:14px;font-size:11px;color:var(--ink2)">` +
    `<span style="width:10px;height:10px;border-radius:2px;background:${s.color};opacity:${s.opacity != null ? s.opacity : 1};display:inline-block"></span>${esc(s.name)}</span>`
  ).join('');
  // responsive면 폭을 컨테이너에 맞춰 줄인다(viewBox라 내부 좌표는 그대로, 넘치지 않는다).
  const svgAttrs = opts.responsive
    ? `width="100%" viewBox="0 0 ${width} ${height}" preserveAspectRatio="xMidYMin meet" style="max-width:${width}px;height:auto"`
    : `width="${width}" height="${height}"`;
  return `<div style="margin-bottom:6px">${legend}</div><svg ${svgAttrs}>${out}</svg>`;
}

const CATEGORIES = ['KNIT', 'SWEATER', 'WOVEN', 'DENIM'];

const GROUP_LABELS = {vendor: '협력사', item: '아이템', td: 'TD', qa: 'QA'};

// 특정 값으로 좁히는 건 위쪽 전체 필터(Quarter/Item/TD/QA/Vendor 체크박스, 이미 교집합 적용됨)가
// 담당하고, 여기는 그 결과를 어느 기준으로 묶어서 차트에 뿌릴지만 고른다.
function groupKeyForRow(row, groupBy) {
  if (groupBy === 'item') return row.item || '미상';
  if (groupBy === 'td') return row.td || '미배정';
  if (groupBy === 'qa') return row.qa || '미배정';
  return vendorAlias(row.vendor) || '미상';
}

// ISO 8601 주차 라벨 (예: "2026-W35"). 목요일 기준 계산이라 연말/연초 경계도 정확함.
function isoWeekLabel(iso) {
  const d = new Date(iso + 'T00:00:00');
  const target = new Date(d.valueOf());
  const dayNr = (d.getDay() + 6) % 7;
  target.setDate(target.getDate() - dayNr + 3);
  const firstThursday = new Date(target.getFullYear(), 0, 4);
  const diff = target - firstThursday;
  const week = 1 + Math.round(diff / (7 * 24 * 3600 * 1000));
  return `${target.getFullYear()}-W${String(week).padStart(2, '0')}`;
}

// "2026-W35" -> 그 ISO 주의 수요일 날짜(Date). 기준일이 수요일인 것과 맞춤.
function isoWeekLabelToAsOfDay(weekStr) {
  const [y, w] = weekStr.split('-W').map(Number);
  const jan4 = new Date(y, 0, 4);
  const jan4Day = (jan4.getDay() + 6) % 7;
  const monday = new Date(jan4);
  monday.setDate(jan4.getDate() - jan4Day + (w - 1) * 7);
  const asOfDay = new Date(monday);
  asOfDay.setDate(monday.getDate() + 2);
  return asOfDay;
}

function periodShortLabel(key, period) {
  if (period === 'month') return key.slice(5);
  const f = isoWeekLabelToAsOfDay(key);
  return `${f.getMonth() + 1}/${f.getDate()}`;
}

function periodLabel(iso, period) {
  return period === 'month' ? iso.slice(0, 7) : isoWeekLabel(iso);
}

// FIT이 보정에서 바로 PP로 넘어가서(생략) 자체 회차가 아예 없는 경우, 보정 승인일을
// FIT의 실제 승인일로 쳐준다 — 이미 그 시점에 승인된 상태였던 거라 "날짜 기록 없음=미준수"로 잡으면 안 됨.
function effectiveConfirmDate(row, stage) {
  const d = (row.detail && row.detail[stage]) || {};
  if (d.confirm_date) return d.confirm_date;
  if (stage === 'FIT' && d.round == null) {
    const prep = (row.detail && row.detail['보정']) || {};
    if (prep.confirm_date) return prep.confirm_date;
  }
  return null;
}

// 단계 전환 리드타임: 이전 단계가 Approved된 시점(confirm_date) → 다음 단계 1회차 접수일(first_received)까지
// 영업일수. 이전 단계가 승인 안 됐거나 다음 단계가 아직 접수 전이면 그 스타일은 그 전환에서 뺀다.
const WITHIN_STAGE_PIPELINE = ['보정', 'FIT', 'PP', 'TOP'];

// 회차 단위 리드타임: 각 회차의 status(Approved/Rejected/Int Rej 등)가 확정된 시점(confirm_date)부터
// "다음 이벤트"까지 영업일수. 다음 이벤트는 같은 단계의 다음 회차 접수일이거나(재작업), 그 회차가
// 그 단계의 마지막 Approved 회차면 다음 단계 1회차 접수일(핸드오프, 보정→FIT 생략 시 PP로 직행).
// 회차·사유 구분 없이 스테이지·상태 단위로 뭉치되, 어디로 넘어갔는지(다음 단계/회차)는 뱃지로 남긴다.
// stage -> status -> {days:[...], next:{label: count, ...}}
const NEXT_STAGE_OF = {'보정': 'FIT', 'FIT': 'PP', 'PP': 'TOP', 'TOP': null};

// 원본 엑셀 status 표기가 대소문자·부가텍스트("Rejected--LA LOGO...", "int rej" 등)로 흔들려서
// 같은 상태가 별도 행으로 쪼개지는 걸 막는다 — 대표 라벨로 정규화.
function canonStatus(raw) {
  const s = (raw || '').trim();
  if (!s) return '미상';
  const low = s.toLowerCase();
  if (low.startsWith('approved')) return 'Approved';
  if (low.startsWith('int rej')) return 'Int Rej';
  if (low.startsWith('rejected')) return 'Rejected';
  if (low.startsWith('go to')) return 'Go to FIT';
  return s;
}

// 그룹 한 줄을 눌러서 접었다 폈다 하는 링크 + 그 안에 들어갈 상태별 분해 표.
// 단계 평균(예: FIT 22.6일)만으로는 "승인 후 다음 단계 착수(28.7일)"와 "리젝 재작업(14.2일)"이
// 뭉개져서, 어느 쪽이 느린 건지 구분이 안 된다 - 펼치면 그 분해가 나온다.
// 시즌 끝나고 쓰는 협력사 평가: 단계마다 "샘플 제작 수 / 스타일 수" 비율을 내고, 아래 기준표로
// 점수(3/2/1/0)를 매긴 뒤 QC·PP·TOP 점수를 평균해 총점을 낸다. 기준은 QM 평가 양식 그대로다.
// (샘플 제작 수 = 그 단계 회차 수, 스타일 수 = 그 단계 샘플이 한 번이라도 들어온 스타일 수)
const EVAL_BANDS_DEFAULT = {
  QC: [1.5, 2, 2.5],        // 이 값 미만이면 각각 3점 / 2점 / 1점, 그 이상은 0점
  PP: [1.25, 1.5, 1.75],
  TOP: [1.25, 1.5, 1.75],
};
// 배점 기준은 화면에서 고쳐 Supabase에 저장한다(저장값 없으면 위 기본값).
const EVAL_BANDS_SETTING_KEY = 'mlb_qm_eval_bands';
let EVAL_BANDS = JSON.parse(JSON.stringify(EVAL_BANDS_DEFAULT));
try {
  const saved = (typeof SETTINGS !== 'undefined') && SETTINGS.eval_bands;
  if (saved && saved.QC && saved.PP && saved.TOP) EVAL_BANDS = saved;
} catch (e) { /* 저장값이 깨졌으면 기본값 그대로 */ }

function evalBandsPanelHtml() {
  const row = (kind) => `<tr><td style="padding:3px 8px;font-weight:700">${kind}</td>` +
    EVAL_BANDS[kind].map((v, i) =>
      `<td style="padding:3px 6px">&lt; <input type="number" step="0.01" min="0" style="width:62px" ` +
      `data-eval-kind="${kind}" data-eval-idx="${i}" value="${v}"> → ${3 - i}점</td>`).join('') +
    `<td style="padding:3px 8px;color:var(--muted)">그 이상 0점</td></tr>`;
  return `<details class="settings-bar" style="margin:0 0 10px">` +
    `<summary>배점 기준 수정</summary>` +
    `<p class="desc">비율(샘플 제작 수 ÷ 스타일 수)이 각 값보다 작으면 그 점수를 줍니다. 저장하면 모두에게 적용됩니다.</p>` +
    `<table class="th-table"><tbody>${row('QC')}${row('PP')}${row('TOP')}</tbody></table>` +
    `<div class="row"><button class="btn" onclick="applyEvalBands()">적용</button>` +
    `<button class="btn" onclick="resetEvalBands()">기본값</button>` +
    `<span id="eval-bands-status"></span></div></details>`;
}

async function applyEvalBands() {
  const next = {QC: [...EVAL_BANDS.QC], PP: [...EVAL_BANDS.PP], TOP: [...EVAL_BANDS.TOP]};
  document.querySelectorAll('[data-eval-kind]').forEach(inp => {
    const v = parseFloat(inp.value);
    if (!isNaN(v)) next[inp.dataset.evalKind][parseInt(inp.dataset.evalIdx, 10)] = v;
  });
  const statusEl = document.getElementById('eval-bands-status');
  if (statusEl) statusEl.textContent = '저장 중...';
  try {
    const resp = await fetch(`${SETTINGS.supabase_url}/rest/v1/settings`, {
      method: 'POST',
      headers: {
        'apikey': SETTINGS.supabase_anon_key,
        'Authorization': `Bearer ${SETTINGS.supabase_anon_key}`,
        'Content-Type': 'application/json',
        'Prefer': 'resolution=merge-duplicates',
      },
      body: JSON.stringify({key: EVAL_BANDS_SETTING_KEY, value: JSON.stringify(next)}),
    });
    if (!resp.ok) throw new Error(await resp.text());
    EVAL_BANDS = next;
    renderAnalysis();
    const el = document.getElementById('eval-bands-status');
    if (el) el.textContent = '저장됨';
  } catch (e) {
    const el = document.getElementById('eval-bands-status');
    if (el) el.textContent = '저장 실패: ' + e.message;
  }
}

function resetEvalBands() {
  EVAL_BANDS = JSON.parse(JSON.stringify(EVAL_BANDS_DEFAULT));
  renderAnalysis();
}
const EVAL_CATEGORY_ORDER = ['KNIT', 'SWEATER', 'WOVEN', 'DENIM', '미분류'];

function evalScore(kind, ratio) {
  if (ratio == null || !isFinite(ratio) || ratio <= 0) return null;
  const limits = EVAL_BANDS[kind] || EVAL_BANDS_DEFAULT[kind];
  for (let i = 0; i < limits.length; i++) if (ratio < limits[i]) return 3 - i;
  return 0;
}

// 완료/미완료를 한 줄 막대로. div 두 개라 테마(다크모드)를 알아서 따라간다.
function progressBarHtml(done, total, color) {
  const ratio = total ? done / total * 100 : 0;
  return `<div style="height:10px;border-radius:5px;background:var(--line);overflow:hidden">` +
    `<div style="width:${ratio.toFixed(1)}%;height:100%;background:${color}"></div></div>`;
}

// 차트가 주인공, 숫자는 필요할 때만. 표를 접어서 아래에 둔다.
function collapsedTableHtml(label, tableHtml) {
  return `<details style="margin-top:10px"><summary style="cursor:pointer;color:var(--muted);font-size:11px">${esc(label)}</summary>` +
    `<div style="margin-top:8px">${tableHtml}</div></details>`;
}

function leadDetailId(rowId) { return `lead-detail-${rowId}`; }

function leadToggleLink(rowId, label) {
  return `<a href="#" onclick="toggleOverdue('${leadDetailId(rowId)}');return false" ` +
    `style="color:#4a65a9;text-decoration:none">${esc(label)} <span style="font-size:9px">▾</span></a>`;
}

// byStageStatus: {stage: {status: {days:[...], next:{label:count}}}}
function leadDetailRow(rowId, byStageStatus, colspan) {
  const lines = [];
  WITHIN_STAGE_PIPELINE.forEach(stage => {
    const byStatus = (byStageStatus && byStageStatus[stage]) || {};
    Object.keys(byStatus).sort((a, b) => {
      if (a === 'Approved') return -1;
      if (b === 'Approved') return 1;
      return a.localeCompare(b, 'ko');
    }).forEach(status => {
      const bucket = byStatus[status];
      if (!bucket.days.length) return;
      const avg = Math.round(bucket.days.reduce((a, b) => a + b, 0) / bucket.days.length * 10) / 10;
      const nextLabel = Object.entries(bucket.next).sort((a, b) => b[1] - a[1])[0][0];
      lines.push(`<tr><td style="padding:3px 10px;color:${STAGE_COLORS[stage] || '#555'};font-weight:700">${esc(stage)}</td>` +
        `<td style="padding:3px 10px">${esc(status)}</td>` +
        `<td style="padding:3px 10px;color:var(--muted)">→ ${esc(nextLabel)}</td>` +
        `<td style="padding:3px 10px;text-align:right;font-weight:700">${avg}일</td>` +
        `<td style="padding:3px 10px;text-align:right;color:var(--muted)">${bucket.days.length}건</td></tr>`);
    });
  });
  const body = lines.length ? lines.join('') : `<tr><td colspan="5" style="padding:4px 10px;color:var(--muted)">분해할 데이터 없음</td></tr>`;
  return `<tr><td colspan="${colspan}" style="padding:0">` +
    `<div id="${leadDetailId(rowId)}" style="display:none;padding:6px 10px 10px 24px;background:var(--soft)">` +
    `<table style="font-size:10px;border-collapse:collapse"><tbody>${body}</tbody></table></div></td></tr>`;
}

function computeRoundLeadTimes(rawRows, groupBy) {
  const stages = {};
  WITHIN_STAGE_PIPELINE.forEach(stage => { stages[stage] = {}; });
  // 그룹(협력사/아이템/TD/QA)별 왕복 리드타임. response = 우리가 결과를 내보낸 뒤 다음 샘플이
  // 들어오기까지(상대가 들고 있던 기간), review = 샘플이 들어온 뒤 결과를 내보내기까지(우리가 들고 있던 기간).
  const groups = {};
  const groupBucket = g => groups[g] || (groups[g] = {response: [], review: [], byStage: {}, byStageStatus: {}, counts: {}, styles: 0});

  for (const row of rawRows) {
    if (!row.detail) continue;
    const group = groupKeyForRow(row, groupBy);
    // 날짜 기입과 무관하게 "몇 스타일을 몇 회차 봤는지"를 따로 센다 - 리드타임은 접수일·전달일이
    // 다 있어야 계산되지만, 회차 수는 기록만 있으면 셀 수 있다(스타일당 몇 번 봤나 = rounds/styles).
    {
      const gb = groupBucket(group);
      gb.styles++;
      WITHIN_STAGE_PIPELINE.forEach(stage => {
        const rs = (row.detail[stage] && row.detail[stage].rounds) || [];
        if (!rs.length) return;
        const c = gb.counts[stage] || (gb.counts[stage] = {styles: 0, rounds: 0});
        c.styles++;
        c.rounds += rs.length;
      });
    }
    WITHIN_STAGE_PIPELINE.forEach(stage => {
      const rounds = (row.detail[stage] && row.detail[stage].rounds) || [];
      rounds.forEach((r, i) => {
        // 우리가 들고 있던 기간: 접수 -> 전달. 둘 다 찍힌 회차만 센다.
        if (r.received && r.confirm_date && r.confirm_date >= r.received) {
          const reviewDays = businessDaysSince(r.received, r.confirm_date);
          if (reviewDays != null) groupBucket(group).review.push(reviewDays);
        }
        if (!r.confirm_date) return;
        const status = canonStatus(r.status);
        let nextDate = null;
        let nextStageLabel = null;
        if (status === 'Go to FIT') {
          // "Go to FIT"는 보정에서 FIT으로 바로 넘어간다는 상태 그 자체라, 같은 단계에 우연히
          // 남은 회차 기록이 있어도 무시하고 무조건 FIT 접수일을 다음 이벤트로 본다.
          const nextDetail = row.detail['FIT'];
          nextDate = nextDetail && nextDetail.first_received;
          nextStageLabel = 'FIT';
        } else if (i < rounds.length - 1) {
          // 같은 단계 안에서 다음 회차로 넘어간 재작업.
          nextDate = rounds[i + 1].received;
          nextStageLabel = stage;
        } else if (status === 'Approved') {
          // 그 단계의 마지막 승인 회차 → 다음 단계로 핸드오프(보정→FIT 생략 시 PP로 직행).
          let nextStage = NEXT_STAGE_OF[stage];
          let nextDetail = nextStage ? row.detail[nextStage] : null;
          if (nextStage === 'FIT' && nextDetail && nextDetail.round == null) { nextDetail = row.detail['PP']; nextStage = 'PP'; }
          if (nextStage) {
            nextDate = nextDetail && nextDetail.first_received;
            nextStageLabel = nextStage;
          }
        }
        if (!nextDate || nextDate < r.confirm_date || !nextStageLabel) return;
        const days = businessDaysSince(r.confirm_date, nextDate);
        if (days == null) return;
        const bucket = stages[stage][status] || (stages[stage][status] = {days: [], next: {}});
        bucket.days.push(days);
        bucket.next[nextStageLabel] = (bucket.next[nextStageLabel] || 0) + 1;
        const gb = groupBucket(group);
        gb.response.push(days);
        (gb.byStage[stage] || (gb.byStage[stage] = [])).push(days);
        // 접었다 폈을 때 보여줄 상태별 분해(Approved→PP 28.7일 / Rejected→FIT 14.2일 식).
        const byStatus = gb.byStageStatus[stage] || (gb.byStageStatus[stage] = {});
        const sb = byStatus[status] || (byStatus[status] = {days: [], next: {}});
        sb.days.push(days);
        sb.next[nextStageLabel] = (sb.next[nextStageLabel] || 0) + 1;
      });
    });
  }
  return {stages, groups};
}

let analysisPeriod = 'week';
let analysisGroupBy = 'vendor';
// 그룹 표에 뭘 띄울지: 'days'=평균 소요일, 'rounds'=스타일당 회차 수.
let analysisLeadMetric = 'days';
// 그룹 표를 숫자표로 볼지 가로막대 차트로 볼지.
let analysisLeadView = 'chart';
// 지연 분석 카드들이 보는 단계(FIT/PP/TOP). 세그먼트 버튼으로 고른다.
let analysisDelayStage = 'FIT';

function setDelayStage(st) { analysisDelayStage = st; renderAnalysis(); }
// 차트로 볼 때 한 차트에 같이 띄울 칸들. 체크박스로 켜고 끈다(표의 열 = 막대 한 줄).
let analysisLeadStages = ['보정', 'FIT', 'PP', 'TOP'];

function toggleLeadStage(key) {
  const i = analysisLeadStages.indexOf(key);
  if (i >= 0) analysisLeadStages.splice(i, 1);
  else analysisLeadStages.push(key);
  renderAnalysis();
}
let complianceChartStage = 'FIT';
const STAGE_COLORS = {보정: '#8e6bbf', FIT: '#4a65a9', PP: '#e0a72e', TOP: '#2e9e5b'};

// dim -> 선택된 값 배열(여러 개 선택 가능) | []면 전체.
const analysisFilters = {quarter: [], item: [], td: [], qa: [], vendor: []};
const FILTER_DIM_LABELS = {quarter: 'Quarter', item: 'Item', td: 'TD', qa: 'QA', vendor: 'Vendor'};

// 벤더 필터만 구분(KNIT/WOVEN/SWEATER/DENIM)별로 묶어서 보여준다(사용자가 알려준 매핑).
const VENDOR_CATEGORY = {
  '약진통상': 'KNIT', '팬코': 'KNIT', 'ESQUEL': 'KNIT', 'SUNRISE': 'KNIT', '노브랜드': 'KNIT', '한솔': 'KNIT',
  '기도산업': 'WOVEN', '포마트': 'WOVEN', 'BOSIDENG': 'WOVEN', 'ITOCHU': 'WOVEN', '노브랜드(우븐)': 'WOVEN', '원전': 'WOVEN', '거림': 'WOVEN', '나디아': 'WOVEN',
  '다인': 'SWEATER', 'OUTIN': 'SWEATER', 'TONGFA': 'SWEATER',
  'KING TIDE': 'DENIM', 'HONGYING': 'DENIM', 'AM GMV': 'DENIM',
};

function filterFieldValue(row, dim) {
  if (dim === 'vendor') return vendorAlias(row.vendor) || '미상';
  return row[dim] || '미상';
}

let lastFilterSeason = null;

// 시즌이 바뀌면 이전 시즌 필터값이 안 맞을 수 있어서 초기화.
function resetFiltersIfSeasonChanged(season) {
  if (lastFilterSeason === season) return;
  lastFilterSeason = season;
  Object.keys(analysisFilters).forEach(dim => { analysisFilters[dim] = []; });
}

function toggleFilterValue(dim, value, checked) {
  const arr = analysisFilters[dim];
  if (checked) { if (!arr.includes(value)) arr.push(value); }
  else { analysisFilters[dim] = arr.filter(v => v !== value); }
  renderAnalysis();
}

function resetAnalysisFilters() {
  Object.keys(analysisFilters).forEach(dim => { analysisFilters[dim] = []; });
  renderAnalysis();
}

function clearFilterDim(dim) {
  analysisFilters[dim] = [];
  renderAnalysis();
}

// 열려있는 필터 드롭다운(한 번에 하나만). 문서 아무데나 클릭하면 닫힘.
let openFilterDim = null;
function toggleFilterDropdown(dim, ev) {
  ev.stopPropagation();
  openFilterDim = openFilterDim === dim ? null : dim;
  renderAnalysis();
}
document.addEventListener('click', () => { if (openFilterDim) { openFilterDim = null; renderAnalysis(); } });

// 검색창은 전체 재렌더 없이 목록만 로컬로 숨기고 보여준다(재렌더하면 입력 포커스가 날아감).
function filterDropdownSearch(dim, term) {
  const t = term.trim().toLowerCase();
  document.querySelectorAll(`#filter-list-${dim} label.fv`).forEach(el => {
    el.style.display = !t || (el.dataset.value || '').toLowerCase().includes(t) ? '' : 'none';
  });
}

function filterCheckboxesHtml(rows, dim) {
  const values = [...new Set(rows.map(r => filterFieldValue(r, dim)))].sort();
  const cur = analysisFilters[dim];
  const cb = v => `<label class="fv" data-value="${escSvg(v)}" style="display:block;font-weight:400;white-space:nowrap">` +
    `<input type="checkbox" value="${escSvg(v)}"${cur.includes(v) ? ' checked' : ''} onchange="toggleFilterValue('${dim}', this.value, this.checked)"> ${esc(v)}</label>`;
  if (dim !== 'vendor') return values.map(cb).join('');
  const byCat = {};
  values.forEach(v => { const cat = VENDOR_CATEGORY[v] || '기타'; (byCat[cat] || (byCat[cat] = [])).push(v); });
  return ['KNIT', 'WOVEN', 'SWEATER', 'DENIM', '기타'].filter(c => byCat[c])
    .map(cat => `<div style="font-weight:700;color:var(--ink2);margin-top:4px">${esc(cat)}</div>${byCat[cat].map(cb).join('')}`).join('');
}

// 필터 = 칸마다 작은 드롭다운 버튼("전체" 또는 "N개 선택") + 클릭하면 검색창·전체·값 목록 팝업.
function filterRowHtml(rows) {
  return `<div style="display:flex;gap:8px;flex-wrap:wrap;align-items:flex-start;margin-bottom:10px">` +
    Object.keys(FILTER_DIM_LABELS).map(dim => {
      const cur = analysisFilters[dim];
      const summary = cur.length ? `${cur.length}개 선택` : '전체';
      const isOpen = openFilterDim === dim;
      return `<span style="font-size:11px;position:relative" onclick="event.stopPropagation()">` +
        `<label style="font-weight:700;color:var(--muted);display:block;margin-bottom:2px">${esc(FILTER_DIM_LABELS[dim])}</label>` +
        `<button class="btn" style="min-width:88px;text-align:left;display:flex;justify-content:space-between;gap:6px" onclick="toggleFilterDropdown('${dim}', event)">` +
        `<span>${esc(summary)}</span><span>▾</span></button>` +
        (isOpen ? `<div style="position:absolute;top:100%;left:0;z-index:50;margin-top:2px;background:var(--surface);border:1px solid #e5e7eb;border-radius:6px;padding:6px;min-width:160px;max-height:220px;overflow-y:auto;box-shadow:0 4px 14px rgba(0,0,0,0.12)">` +
          `<input type="text" placeholder="검색..." oninput="filterDropdownSearch('${dim}', this.value)" style="width:100%;box-sizing:border-box;padding:4px 6px;font-size:11px;border:1px solid #ccc;border-radius:4px;margin-bottom:6px">` +
          `<label style="display:block;font-weight:700;white-space:nowrap;margin-bottom:2px">` +
          `<input type="checkbox"${cur.length ? '' : ' checked'} onchange="clearFilterDim('${dim}')"> 전체</label>` +
          `<div id="filter-list-${dim}">${filterCheckboxesHtml(rows, dim)}</div>` +
          `</div>` : '') +
        `</span>`;
    }).join('') +
    `<span style="font-size:11px;align-self:flex-end">` +
    `<button class="btn" onclick="resetAnalysisFilters()">초기화</button></span>` +
    `</div>`;
}

function applyAnalysisFilters(rows) {
  return rows.filter(r => Object.keys(analysisFilters).every(dim => {
    const sel = analysisFilters[dim];
    return !sel.length || sel.includes(filterFieldValue(r, dim));
  }));
}

function renderAnalysis() {
  const seasonSelect = document.getElementById('analysis-season-select');
  const weekSeasonsAll = weekIds.length ? Object.keys(DATA.weeks[weekIds[0]].raw || {}).sort() : [];
  if (!seasonSelect.options.length) {
    weekSeasonsAll.forEach(s => { const o = document.createElement('option'); o.value = s; o.textContent = s; seasonSelect.appendChild(o); });
  }
  const season = seasonSelect.value || weekSeasonsAll[0];
  const period = analysisPeriod;
  const groupBy = analysisGroupBy;
  const container = document.getElementById('analysis-body');
  container.innerHTML = '';
  if (!season) return;

  const week = DATA.weeks[sel.value];
  if (!week) return;
  const allRows = (week.raw && week.raw[season]) || [];
  if (!allRows.length) { container.innerHTML = '<p class="sub">이 시즌은 아직 raw 데이터가 없음</p>'; return; }
  resetFiltersIfSeasonChanged(season);
  const rows = applyAnalysisFilters(allRows);
  const offsets = currentOffsets(season);
  const asOfDate = (sel.value === weekIds[0]) ? resolveAsOfDate(season) : week.as_of_date;
  const groupByHtml = `<label style="font-weight:700;margin-right:8px;font-size:12px">그룹 기준</label>` +
    `<select onchange="analysisGroupBy=this.value;renderAnalysis()" style="margin-right:16px">` +
    Object.entries(GROUP_LABELS).map(([k, v]) => `<option value="${k}"${groupBy === k ? ' selected' : ''}>${v}</option>`).join('') +
    `</select>`;

  // 우리가 정한 DUE 대비 지금 어디가 밀렸는지. 요약 탭의 미완료 상세와 같은 계산(computeProgressFromRaw)을
  // 그대로 써서 두 화면 숫자가 어긋나지 않게 한다.
  const prog = computeProgressFromRaw(rows, asOfDate, offsets);
  const bucketOf = st => ((OWNER_BY_STAGE[st] === 'TD' ? prog.TD : prog.QA)[st]) ||
    {total_all: 0, total_done: 0, baseline_all: 0, baseline_done: 0, overdue: []};

  // 카드 1 - 이번 주 한눈에: 단계별 due 도래 / 미완료 / 정시율 / 납기영향. 필터도 여기 붙인다.
  {
    const secTop = document.createElement('div');
    secTop.className = 'analysis-section';
    const tile = st => {
      const b = bucketOf(st);
      const late = b.baseline_all - b.baseline_done;
      const onTime = b.baseline_all ? Math.round(b.baseline_done / b.baseline_all * 1000) / 10 : null;
      const impacted = (b.overdue || []).filter(o => o.impacts_delivery).length;
      const color = STAGE_COLORS[st] || 'var(--accent)';
      return `<div style="flex:1;min-width:220px;border:1px solid var(--line);border-radius:10px;padding:14px 16px">` +
        `<div style="display:flex;align-items:baseline;gap:8px">` +
        `<span style="font-weight:700;font-size:12px;color:${color}">${esc(st)}</span>` +
        `<span style="font-size:28px;font-weight:700">${onTime == null ? '-' : onTime + '%'}</span></div>` +
        `<div style="margin:8px 0 6px">${progressBarHtml(b.baseline_done, b.baseline_all, color)}</div>` +
        `<div style="font-size:11px;color:var(--muted)">DUE 도래 ${b.baseline_all} · 완료 ${b.baseline_done} · ` +
        `미완료 <b style="color:var(--ink)">${late}</b></div>` +
        `<div style="margin-top:6px;font-size:11px;color:${impacted ? 'var(--bad)' : 'var(--muted)'};` +
        `font-weight:${impacted ? 700 : 400}">${impacted ? `납기영향 ${impacted}건` : '납기영향 없음'}</div></div>`;
    };
    secTop.innerHTML = `<h3>이번 주 한눈에 · 기준일 ${esc(asOfDate)}</h3>` +
      `<p class="sub">우리가 정한 DUE 대비 지금 상태입니다. 아래 필터는 이 탭 전체에 적용됩니다.</p>` +
      filterRowHtml(allRows) +
      `<div style="display:flex;gap:12px;flex-wrap:wrap">${STAGES.map(tile).join('')}</div>`;
    container.appendChild(secTop);
  }

  // 지연 카드 3종(협력사 / 사유 / 납기영향)은 한 단계를 같이 본다.
  const delayStage = analysisDelayStage;
  const stageSegHtml = `<span style="font-weight:700;font-size:12px;margin-right:8px">단계</span>` +
    STAGES.map(st => `<button onclick="setDelayStage('${st}')" style="margin-right:4px;padding:4px 12px;border-radius:6px;cursor:pointer;` +
      `border:1px solid ${delayStage === st ? (STAGE_COLORS[st] || '#4a65a9') : '#ddd'};` +
      `background:${delayStage === st ? (STAGE_COLORS[st] || '#4a65a9') : '#fff'};` +
      `color:${delayStage === st ? '#fff' : '#555'};font-size:11px">${esc(st)}</button>`).join('');
  const od = bucketOf(delayStage).overdue || [];
  const avgOfArr = a => a.length ? Math.round(a.reduce((x, y) => x + y, 0) / a.length * 10) / 10 : null;

  // 카드 2 - 어떤 협력사가 늦나: 미완료 건수 / 평균·최대 초과일 / 납기영향.
  {
    const byVendor = {};
    od.forEach(o => {
      const v = vendorAlias(o.vendor) || '미상';
      const b = byVendor[v] || (byVendor[v] = {late: 0, days: [], impacted: 0, worst: null});
      b.late++;
      if (o.overdue_days != null) b.days.push(o.overdue_days);
      if (o.impacts_delivery) b.impacted++;
      if (!b.worst || (o.overdue_days || 0) > (b.worst.overdue_days || 0)) b.worst = o;
    });
    const list = Object.entries(byVendor)
      .map(([v, b]) => ({vendor: v, late: b.late, avg: avgOfArr(b.days), max: b.days.length ? Math.max(...b.days) : null,
                         impacted: b.impacted, worst: b.worst}))
      .sort((a, b) => b.late - a.late || (b.avg || 0) - (a.avg || 0));
    const secV = document.createElement('div');
    secV.className = 'analysis-section';
    const tdc = 'padding:4px 10px;text-align:center';
    secV.innerHTML = `<h3>어떤 협력사가 늦나 · ${esc(delayStage)}</h3>` +
      `<p class="sub">DUE가 지났는데 아직 승인 안 난 건을 협력사별로 모았습니다. 초과일수는 영업일 기준입니다.</p>` +
      `<div style="margin-bottom:10px">${stageSegHtml}</div>` +
      (list.length
        ? hBarChart(list.map(r => ({label: r.vendor, value: r.late,
            color: r.impacted ? 'var(--bad)' : (STAGE_COLORS[delayStage] || 'var(--accent)')})),
            {unit: '건', width: 880, labelWidth: 120, barHeight: 18, gap: 6}) +
          `<p class="sub" style="margin-top:6px">붉은 막대는 납기영향 건이 섞인 협력사입니다.</p>` +
          collapsedTableHtml('숫자로 보기 (평균·최대 초과일, 납기영향, 가장 오래 밀린 스타일)',
          `<table style="font-size:11px;border-collapse:collapse">` +
          `<thead><tr style="color:var(--muted)"><th style="padding:4px 10px;text-align:left">협력사</th>` +
          `<th style="${tdc}">미완료</th><th style="${tdc}">평균 초과</th><th style="${tdc}">최대 초과</th>` +
          `<th style="${tdc}">납기영향</th><th style="padding:4px 10px;text-align:left">가장 오래 밀린 스타일</th></tr></thead><tbody>` +
          list.map(r => `<tr style="border-top:1px solid var(--line)">` +
            `<td style="padding:4px 10px">${esc(r.vendor)}</td>` +
            `<td style="${tdc};font-weight:700">${r.late}건</td>` +
            `<td style="${tdc}">${r.avg == null ? '-' : '+' + r.avg + '일'}</td>` +
            `<td style="${tdc}">${r.max == null ? '-' : '+' + r.max + '일'}</td>` +
            `<td style="${tdc};color:${r.impacted ? '#c0392b' : '#888'};font-weight:${r.impacted ? 700 : 400}">${r.impacted}건</td>` +
            `<td style="padding:4px 10px;color:var(--ink2)">${r.worst ? `${esc(r.worst.style_code)} (+${r.worst.overdue_days}일, ${esc(r.worst.status)})` : '-'}</td>` +
            `</tr>`).join('') + `</tbody></table>`)
        : `<p class="sub">이 단계는 지금 미완료가 없습니다.</p>`);
    container.appendChild(secV);
  }

  // 카드 3 - 사유: 기입된 사유를 묶어서 센다. 기입률이 낮으면 그 자체가 먼저 할 일이라 같이 보여준다.
  {
    const byReason = {};
    od.forEach(o => {
      const key = (o.reason || '').trim() || '(사유 미기입)';
      const b = byReason[key] || (byReason[key] = {n: 0, vendors: {}});
      b.n++;
      const v = vendorAlias(o.vendor) || '미상';
      b.vendors[v] = (b.vendors[v] || 0) + 1;
    });
    const filled = od.filter(o => (o.reason || '').trim()).length;
    const list = Object.entries(byReason).map(([reason, b]) => ({reason, n: b.n,
      top: Object.entries(b.vendors).sort((x, y) => y[1] - x[1]).slice(0, 3).map(([v, n]) => `${v} ${n}`).join(', ')}))
      .sort((a, b) => b.n - a.n);
    const secR = document.createElement('div');
    secR.className = 'analysis-section';
    secR.innerHTML = `<h3>사유 · ${esc(delayStage)}</h3>` +
      `<p class="sub">미완료 ${od.length}건 중 사유가 적힌 건 <b>${filled}건</b> (${pct(filled, od.length)}). ` +
      `사유 칸이 비어 있으면 아래 "(사유 미기입)"으로 잡힙니다.</p>` +
      (od.length
        ? hBarChart(list.map(r => ({label: r.reason, value: r.n,
            color: r.reason === '(사유 미기입)' ? 'var(--line2)' : (STAGE_COLORS[delayStage] || 'var(--accent)')})),
            {unit: '건', width: 760, labelWidth: 160, barHeight: 18, gap: 6}) +
          collapsedTableHtml('숫자로 보기 (비중·많은 협력사)',
          `<table style="font-size:11px;border-collapse:collapse">` +
          `<thead><tr style="color:var(--muted)"><th style="padding:4px 10px;text-align:left">사유</th>` +
          `<th style="padding:4px 10px;text-align:center">건수</th><th style="padding:4px 10px;text-align:center">비중</th>` +
          `<th style="padding:4px 10px;text-align:left">많은 협력사</th></tr></thead><tbody>` +
          list.map(r => `<tr style="border-top:1px solid var(--line)">` +
            `<td style="padding:4px 10px;color:${r.reason === '(사유 미기입)' ? '#aaa' : '#1a1a2e'}">${esc(r.reason)}</td>` +
            `<td style="padding:4px 10px;text-align:center;font-weight:700">${r.n}</td>` +
            `<td style="padding:4px 10px;text-align:center;color:var(--muted)">${pct(r.n, od.length)}</td>` +
            `<td style="padding:4px 10px;color:var(--ink2)">${esc(r.top)}</td></tr>`).join('') +
          `</tbody></table>`)
        : `<p class="sub">이 단계는 지금 미완료가 없습니다.</p>`);
    container.appendChild(secR);
  }

  // 카드 4 - 납기영향: DUE~ETD 사이 버퍼를 이미 다 까먹은 건(impacts_delivery)만 추린다.
  {
    const impacted = od.filter(o => o.impacts_delivery);
    const byVendor = {};
    impacted.forEach(o => {
      const v = vendorAlias(o.vendor) || '미상';
      const b = byVendor[v] || (byVendor[v] = {n: 0, styles: []});
      b.n++; b.styles.push(o);
    });
    const list = Object.entries(byVendor).map(([v, b]) => ({vendor: v, n: b.n,
      styles: b.styles.sort((x, y) => (y.overdue_days || 0) - (x.overdue_days || 0))})).sort((a, b) => b.n - a.n);
    const secI = document.createElement('div');
    secI.className = 'analysis-section';
    secI.innerHTML = `<h3>납기영향 · ${esc(delayStage)}</h3>` +
      `<p class="sub">DUE에서 ETD까지 원래 있던 여유(영업일)를 이미 다 써버린 건입니다 - 지금 속도면 선적이 밀립니다. ` +
      `미완료 ${od.length}건 중 <b style="color:#c0392b">${impacted.length}건</b> (${pct(impacted.length, od.length)}).</p>` +
      (impacted.length
        ? hBarChart(list.map(r => ({label: r.vendor, value: r.n})),
            {unit: '건', color: 'var(--bad)', width: 760, labelWidth: 120, barHeight: 18, gap: 6}) +
          collapsedTableHtml('어떤 스타일인지 보기',
          `<table style="font-size:11px;border-collapse:collapse">` +
          `<thead><tr style="color:var(--muted)"><th style="padding:4px 10px;text-align:left">협력사</th>` +
          `<th style="padding:4px 10px;text-align:center">납기영향</th><th style="padding:4px 10px;text-align:left">스타일 (초과일 · ETD)</th></tr></thead><tbody>` +
          list.map(r => `<tr style="border-top:1px solid var(--line)">` +
            `<td style="padding:4px 10px;font-weight:700">${esc(r.vendor)}</td>` +
            `<td style="padding:4px 10px;text-align:center;color:#c0392b;font-weight:700">${r.n}건</td>` +
            `<td style="padding:4px 10px;color:var(--ink2)">` +
            r.styles.slice(0, 6).map(o => `${esc(o.style_code)} <span style="color:var(--muted)">(+${o.overdue_days}일 · ${esc(shortDate(o.etd))})</span>`).join(', ') +
            (r.styles.length > 6 ? ` 외 ${r.styles.length - 6}건` : '') + `</td></tr>`).join('') +
          `</tbody></table>`)
        : `<p class="sub">납기에 영향 주는 건은 없습니다.</p>`);
    container.appendChild(secI);
  }

  // 단계별(보정/FIT/PP/TOP) 소요일수: 단계마다 표를 따로 만들고, 그 안에서 상태(APPROVED가
  // 맨 위, 나머지는 이름순) → 회차(1ST/2ND/3RD/4TH/5TH) 순으로 묶어서 보여준다.
  {
    const roundLead = computeRoundLeadTimes(rows, groupBy);
    const avgOf = days => days.length ? Math.round(days.reduce((a, b) => a + b, 0) / days.length * 10) / 10 : null;

    const sec5 = document.createElement('div');
    sec5.className = 'analysis-section';
    let html = `<div style="margin-bottom:10px">${groupByHtml}</div>`;

    // 같은 섹션 아래에 그룹별 분해: 위 Stage 표와 같은 "내보냄→들어옴"을 단계별로 쪼개고,
    // 맨 끝에 "들어옴→내보냄"(우리가 들고 있던 기간)을 붙여 공이 어느 쪽에 있었는지 가른다.
    const groupRows = Object.entries(roundLead.groups)
      .map(([name, b]) => ({name, resp: avgOf(b.response), respN: b.response.length,
                            rev: avgOf(b.review), revN: b.review.length,
                            byStage: b.byStage, byStageStatus: b.byStageStatus,
                            counts: b.counts, styles: b.styles}))
      .filter(g => g.respN || g.revN)
      .sort((a, b) => (b.resp == null ? -1 : b.resp) - (a.resp == null ? -1 : a.resp));
    const allResp = Object.values(roundLead.groups).flatMap(b => b.response);
    const allRev = Object.values(roundLead.groups).flatMap(b => b.review);
    const allByStage = {}, allCounts = {};
    WITHIN_STAGE_PIPELINE.forEach(st => {
      allByStage[st] = Object.values(roundLead.groups).flatMap(b => b.byStage[st] || []);
      allCounts[st] = Object.values(roundLead.groups).reduce((acc, b) => {
        const c = b.counts[st];
        return c ? {styles: acc.styles + c.styles, rounds: acc.rounds + c.rounds} : acc;
      }, {styles: 0, rounds: 0});
    });
    // 단계 구분 없는 합계(맨 오른쪽 두 칸용): 스타일 수는 그룹의 스타일 수, 회차는 전 단계 합.
    const sumCounts = cs => WITHIN_STAGE_PIPELINE.reduce(
      (acc, st) => cs[st] ? {styles: acc.styles, rounds: acc.rounds + cs[st].rounds} : acc, {styles: 0, rounds: 0});
    const allStyles = Object.values(roundLead.groups).reduce((n, b) => n + b.styles, 0);
    const metric = analysisLeadMetric;
    // 한 칸에 두 줄: 윗줄은 고른 지표(평균 소요일 또는 스타일당 회차), 아랫줄은 모수
    // (회차 건수·스타일 수). 괄호 안 숫자가 스타일 수인 줄 알고 헷갈리는 일이 없게 둘 다 적는다.
    // 한 줄로: 값 + 스타일 수만. 모수(회차 건수)는 커서를 올리면 title로 뜬다.
    const cell = (days, daysN, c) => {
      const counts = c || {styles: 0, rounds: 0};
      const head = metric === 'rounds'
        ? (counts.styles ? `${Math.round(counts.rounds / counts.styles * 10) / 10}회` : null)
        : (days == null ? null : `${days}일`);
      if (head == null && !counts.rounds) return '<span style="color:var(--line2)">-</span>';
      const tip = metric === 'rounds'
        ? `회차 ${counts.rounds}건 ÷ 스타일 ${counts.styles}개`
        : `평균을 낸 회차 ${daysN}건 · 스타일 ${counts.styles}개`;
      return `<span title="${esc(tip)}"><b>${head == null ? '-' : head}</b>` +
        `<span style="color:var(--muted);font-weight:400"> · ${counts.styles}sty</span></span>`;
    };
    // 차트에서 고를 수 있는 칸 = 표의 열. 회차 지표일 땐 "들어옴→내보냄"(우리 검토 소요일)이
    // 의미가 없어서 뺀다.
    const leadChartOptions = [
      ...WITHIN_STAGE_PIPELINE.map(st => ({key: st, label: st, color: STAGE_COLORS[st]})),
      {key: 'resp', label: '내보냄→들어옴 (상대가 들고 있던 기간)', color: '#c0392b'},
      ...(metric === 'days' ? [{key: 'rev', label: '들어옴→내보냄 (우리가 들고 있던 기간)', color: '#2e9e5b'}] : []),
    ];
    const metricHtml = `<label style="font-weight:700;margin-right:8px;font-size:12px">지표</label>` +
      `<select onchange="analysisLeadMetric=this.value;renderAnalysis()">` +
      `<option value="days"${metric === 'days' ? ' selected' : ''}>평균 소요일</option>` +
      `<option value="rounds"${metric === 'rounds' ? ' selected' : ''}>스타일당 회차 수</option></select>` +
      `<label style="font-weight:700;margin:0 8px 0 16px;font-size:12px">보기</label>` +
      `<select onchange="analysisLeadView=this.value;renderAnalysis()">` +
      `<option value="table"${analysisLeadView === 'table' ? ' selected' : ''}>표</option>` +
      `<option value="chart"${analysisLeadView === 'chart' ? ' selected' : ''}>차트</option></select>` +
      (analysisLeadView === 'chart'
        ? `<span style="margin-left:16px;font-weight:700;font-size:12px">차트에 띄울 칸</span> ` +
          leadChartOptions.map(o =>
            `<label style="margin-left:10px;font-size:11px;color:${o.color || '#555'};white-space:nowrap">` +
            `<input type="checkbox" onchange="toggleLeadStage('${o.key}')"` +
            `${analysisLeadStages.includes(o.key) ? ' checked' : ''}> ${esc(o.label)}</label>`).join('')
        : '');

    // 차트용 값: 고른 지표를 그룹별 숫자 하나로 환산한다(없으면 제외).
    const metricValue = (days, counts) => {
      if (metric === 'rounds') {
        const c = counts || {styles: 0, rounds: 0};
        return c.styles ? Math.round(c.rounds / c.styles * 10) / 10 : null;
      }
      return days;
    };
    const chartUnit = metric === 'rounds' ? '회' : '일';
    const th = `padding:4px 10px;text-align:center`;
    const colspan = WITHIN_STAGE_PIPELINE.length + 3;

    html += `<h3 style="margin:0 0 4px">${esc(GROUP_LABELS[groupBy])}별 ` +
      `${metric === 'rounds' ? '회차 수' : '소요일 수 (영업일)'}</h3>` +
      `<p class="sub">단계 칸 = 내보냄→들어옴(결과를 보낸 뒤 다음 샘플이 들어오기까지, 상대가 들고 있던 기간). ` +
      `맨 오른쪽 "들어옴→내보냄"은 샘플 접수 뒤 결과를 보내기까지 우리가 들고 있던 기간입니다. ` +
      `${esc(GROUP_LABELS[groupBy])} 이름을 누르면 상태별(Approved/Rejected/Int Rej) 분해가 펼쳐집니다.<br>` +
      (metric === 'rounds'
        ? `윗줄 = 스타일 1개를 평균 몇 회차 봤는지(회차 ÷ 스타일). 아랫줄 = 그 모수(총 회차 · 스타일 수).`
        : `윗줄 = 평균 소요일. 아랫줄 = 그 모수(평균을 낸 <b>회차 건수</b> · <b>스타일 수</b>) — ` +
          `한 스타일이 1차·2차·3차를 거치면 회차는 그만큼 여러 번 셉니다.`) +
      ` 소요일은 접수일·전달일이 기입된 회차만, 회차 수는 기록이 있는 회차를 다 셉니다.</p>` +
      `<div style="margin-bottom:8px">${metricHtml}</div>`;

    let tableHtml = `<table style="font-size:11px;border-collapse:collapse">` +
      `<thead><tr style="color:var(--muted)"><th style="padding:4px 10px;text-align:left">${esc(GROUP_LABELS[groupBy])}</th>` +
      WITHIN_STAGE_PIPELINE.map(st => `<th style="${th};color:${STAGE_COLORS[st] || '#888'}">${esc(st)}</th>`).join('') +
      `<th style="${th}">내보냄→들어옴</th><th style="${th};border-left:1px solid var(--line)">들어옴→내보냄</th>` +
      `</tr></thead><tbody>` +
      `<tr style="font-weight:700;background:var(--soft)">` +
      `<td style="padding:4px 10px">${leadToggleLink('all', '전체 평균')}</td>` +
      WITHIN_STAGE_PIPELINE.map(st => `<td style="${th}">${cell(avgOf(allByStage[st]), allByStage[st].length, allCounts[st])}</td>`).join('') +
      `<td style="${th}">${cell(avgOf(allResp), allResp.length, {...sumCounts(allCounts), styles: allStyles})}</td>` +
      `<td style="${th};border-left:1px solid var(--line)">${cell(avgOf(allRev), allRev.length, {...sumCounts(allCounts), styles: allStyles})}</td></tr>` +
      leadDetailRow('all', roundLead.stages, colspan);
    if (!groupRows.length) {
      tableHtml += `<tr><td colspan="${WITHIN_STAGE_PIPELINE.length + 3}" style="padding:6px;color:var(--muted)">데이터 없음</td></tr>`;
    }
    groupRows.forEach(g => {
      const rowId = `lead-${groupBy}-${g.name}`.replace(/[^\\w-]/g, '_');
      tableHtml += `<tr style="border-top:1px solid var(--line)">` +
        `<td style="padding:4px 10px">${leadToggleLink(rowId, g.name)}</td>` +
        WITHIN_STAGE_PIPELINE.map(st => {
          const d = g.byStage[st] || [];
          return `<td style="${th}">${cell(avgOf(d), d.length, g.counts[st])}</td>`;
        }).join('') +
        `<td style="${th};font-weight:700">${cell(g.resp, g.respN, {...sumCounts(g.counts), styles: g.styles})}</td>` +
        `<td style="${th};border-left:1px solid var(--line)">${cell(g.rev, g.revN, {...sumCounts(g.counts), styles: g.styles})}</td></tr>` +
        leadDetailRow(rowId, g.byStageStatus, colspan);
    });
    tableHtml += `</tbody></table>`;

    if (analysisLeadView === 'chart') {
      // 체크한 칸들을 한 차트에 묶음 막대로 겹쳐 그린다(x축 = 그룹, 막대 = 칸).
      // 위쪽 "주차별 일정 준수 현황"과 같은 groupedBarChart를 쓴다.
      const picked = leadChartOptions.filter(o => analysisLeadStages.includes(o.key));
      const valueOf = (g, key) => {
        if (key === 'resp') return metricValue(g.resp, {...sumCounts(g.counts), styles: g.styles});
        if (key === 'rev') return g.rev;
        return metricValue(avgOf(g.byStage[key] || []), g.counts[key]);
      };
      const names = groupRows.map(g => g.name);
      const series = picked.map(o => ({
        name: o.label.split(' (')[0],
        color: o.color || '#4a65a9',
        values: groupRows.map(g => valueOf(g, o.key)),
      }));
      const dataMax = Math.max(0, ...series.flatMap(x => x.values.filter(v => v != null)));
      html += (picked.length && names.length
        ? groupedBarChart(names, series, {
            width: 1240, height: 340, unit: chartUnit,
            yMax: Math.max(1, Math.ceil(dataMax * 1.1)),
            showValues: true, rotateLabels: names.length > 8, responsive: true,
          })
        : `<p class="sub">${picked.length ? '데이터 없음' : '띄울 칸을 하나 이상 체크하세요'}</p>`);
    } else {
      html += tableHtml;
    }

    sec5.innerHTML = html;
    container.appendChild(sec5);

    // 시즌 말 협력사 평가는 성격이 달라서(점수·배점) 소요일 섹션 아래 별도 칸으로 뺀다.
    {
      let evalHtml = '';

      // 평가표는 늘 협력사 기준이다(그룹 기준 선택과 무관). QC = FIT 단계.
      const ev = computeRoundLeadTimes(rows, 'vendor').groups;
      const KINDS = [['QC', 'FIT'], ['PP', 'PP'], ['TOP', 'TOP']];
      const byCat = {};
      Object.entries(ev).forEach(([vendor, b]) => {
        const cat = VENDOR_CATEGORY[vendor] || '미분류';
        const cells = KINDS.map(([kind, stage]) => {
          const c = b.counts[stage] || {styles: 0, rounds: 0};
          const ratio = c.styles ? c.rounds / c.styles : null;
          return {kind, styles: c.styles, rounds: c.rounds, ratio, score: evalScore(kind, ratio)};
        });
        const scored = cells.filter(c => c.score != null);
        if (!scored.length) return;
        const total = scored.reduce((a, c) => a + c.score, 0) / scored.length;
        (byCat[cat] || (byCat[cat] = [])).push({vendor, cells, total});
      });
      const tdc = 'padding:4px 8px;text-align:center';
      evalHtml += `<h3 style="margin:0 0 4px">협력사 평가 (샘플 제작 수 ÷ 스타일 수)</h3>` +
        `<p class="sub">단계마다 "샘플 제작 수 ÷ 스타일 수"를 내고 기준표로 점수를 매긴 뒤, QC·PP·TOP 점수를 평균해 총점을 냅니다. ` +
        `현재 기준 — QC: ${EVAL_BANDS.QC.map((v, i) => `~${v} ${3 - i}점`).join(' / ')} / 그 이상 0점, ` +
        `PP·TOP: ${EVAL_BANDS.PP.map((v, i) => `~${v} ${3 - i}점`).join(' / ')} / 그 이상 0점. ` +
        `샘플이 한 번도 안 들어온 단계는 총점 평균에서 뺍니다. 위쪽 필터(Quarter/Item/TD/QA/Vendor)가 그대로 적용됩니다.</p>` +
                evalBandsPanelHtml() +
        `<table style="font-size:11px;border-collapse:collapse">` +
        `<thead><tr style="color:var(--muted)"><th style="padding:4px 8px;text-align:left">협력사</th>` +
        KINDS.map(([kind]) => `<th colspan="4" style="${tdc};border-left:1px solid var(--line)">${kind}</th>`).join('') +
        `<th style="${tdc};border-left:1px solid var(--line)">총점</th></tr>` +
        `<tr style="color:#bbb"><th></th>` +
        KINDS.map(() => `<th style="${tdc};border-left:1px solid var(--line)">스타일</th><th style="${tdc}">샘플</th>` +
          `<th style="${tdc}">비율</th><th style="${tdc}">점수</th>`).join('') +
        `<th style="${tdc};border-left:1px solid var(--line)"></th></tr></thead><tbody>`;
      EVAL_CATEGORY_ORDER.filter(cat => byCat[cat]).forEach(cat => {
        evalHtml += `<tr><td colspan="${KINDS.length * 4 + 2}" style="padding:6px 8px;font-weight:700;background:var(--soft)">&lt;${esc(cat)}&gt;</td></tr>`;
        byCat[cat].sort((a, b) => b.total - a.total).forEach(r => {
          evalHtml += `<tr style="border-top:1px solid var(--line)"><td style="padding:4px 8px">${esc(r.vendor)}</td>` +
            r.cells.map(c => `<td style="${tdc};border-left:1px solid var(--line)">${c.styles || '-'}</td>` +
              `<td style="${tdc}">${c.rounds || '-'}</td>` +
              `<td style="${tdc}">${c.ratio == null ? '-' : (Math.round(c.ratio * 100) / 100).toFixed(2)}</td>` +
              `<td style="${tdc};font-weight:700;color:${c.score == null ? '#ccc' : (c.score >= 3 ? '#2e9e5b' : c.score === 0 ? '#c0392b' : '#1a1a2e')}">` +
              `${c.score == null ? '-' : c.score}</td>`).join('') +
            `<td style="${tdc};border-left:1px solid var(--line);font-weight:700">${(Math.round(r.total * 100) / 100).toFixed(2)}</td></tr>`;
        });
      });
      if (!Object.keys(byCat).length) html += `<tr><td colspan="${KINDS.length * 4 + 2}" style="padding:6px;color:var(--muted)">데이터 없음</td></tr>`;
      evalHtml += `</tbody></table>`;

      const secEval = document.createElement('div');
      secEval.className = 'analysis-section';
      secEval.innerHTML = evalHtml;
      container.appendChild(secEval);
    }
  }
}

const QUARTER_ORDER = ['Main TS', '2nd TS', 'Spot', 'After TS', '기타'];

function normalizeQuarter(raw) {
  const s = (raw || '').trim();
  if (!s) return '기타';
  if (s.toLowerCase() === 'spot') return 'Spot';
  return QUARTER_ORDER.includes(s) ? s : '기타';
}

function statusTextHtml(m) {
  const extraApproved = m.total_done - m.baseline_done;
  return `총 <b>${m.total_all}sty</b> 가운데 due date 도래 <b>${m.baseline_all}sty</b> 중 <b>${m.baseline_done}sty</b> 완료` +
    (extraApproved > 0 ? ` (+<b>${extraApproved}sty</b> Approved)` : '');
}

function overdueRemarkKey(season, styleCode, stage) { return `od|${season}|${styleCode}|${stage}`; }

function overdueDetailRowHtml(overdue, overdueId, colspan, weekId, season, stage, remarks) {
  if (!overdue.length) return '';
  const impacted = overdue.filter(o => o.impacts_delivery).length;
  const impactedPct = pct(impacted, overdue.length);
  const impactedNote = ` <span style="color:${impacted > 0 ? '#c0392b' : '#888'};font-weight:700">(납기영향 ${impacted}건, ${impactedPct}%)</span>`;
  return `<tr><td colspan="${colspan}" style="background:var(--soft);padding:0">` +
    `<div style="padding:4px 10px"><a href="#" onclick="toggleOverdue('${overdueId}');return false" style="font-size:11px;color:#4a65a9">미완료 ${overdue.length}건 상세 ▾</a>${impactedNote}</div>` +
    `<div id="${overdueId}" style="display:${overdueOpen.has(overdueId) ? 'block' : 'none'};padding:0 10px 8px;overflow-x:hidden">` +
    `<table style="width:auto;min-width:100%;table-layout:auto;overflow:visible;font-size:10px;border-collapse:collapse;white-space:nowrap">` +
    `<thead><tr style="color:var(--muted)">` +
    // 머리글을 누르면 그 칸으로 정렬, 다시 누르면 반대 방향. 비고(메모)는 정렬 대상이 아니다.
    [['스타일', 'style_code', 'center'], ['협력사', 'vendor', 'center'], ['DUE DATE', 'due', 'center'],
     ['납기(ETD)', 'etd', 'center'], ['초과일수', 'overdue_days', 'center'], ['현재 status', 'status', 'left'],
     ['이전 Stage', 'confirm_stage', 'center'], ['전달일', 'confirm_date', 'center'], ['사유', 'reason', 'center'],
     ['소요일', 'elapsed_days', 'center'], ['납기영향', 'impacts_delivery', 'center']]
      .map(([label, key, align]) => {
        const st = overdueSort[overdueId];
        const arrow = st && st.key === key ? (st.dir === 1 ? ' ▲' : ' ▼') : '';
        return `<th style="text-align:${align};padding:4px 10px;cursor:pointer;user-select:none"` +
          ` onclick="sortOverdue('${overdueId}','${key}')" title="눌러서 정렬">${esc(label)}${arrow}</th>`;
      }).join('') +
      `<th style="text-align:center;padding:4px 10px">비고</th></tr></thead>` +
    `<tbody>` + sortedOverdue(overdue, overdueId).map(o => {
      const remarkDomId = `overdue-${weekId}-${season}-${o.style_code}-${stage}`.replace(/[^\\w-]/g, '_');
      const remarkText = remarks[overdueRemarkKey(season, o.style_code, stage)] || '';
      return `<tr style="border-top:1px solid var(--line)${o.impacts_delivery ? ';background:#fdeceb' : ''}">` +
      `<td style="padding:4px 10px;text-align:center">${esc(o.style_code)}</td><td style="padding:4px 10px;text-align:center">${esc(vendorAlias(o.vendor) || '-')}</td><td style="padding:4px 10px;text-align:center">${esc(shortDate(o.due))}</td>` +
      `<td style="padding:4px 10px;text-align:center">${o.etd ? esc(shortDate(o.etd)) : '-'}</td>` +
      `<td style="padding:4px 10px;text-align:center">${o.overdue_days != null ? esc('+' + o.overdue_days) : '-'}</td>` +
      `<td style="padding:4px 10px;text-align:left">${esc(o.status)}</td>` +
      `<td style="padding:4px 10px;text-align:center">${esc(o.confirm_stage || '-')}</td><td style="padding:4px 10px;text-align:center">${esc(o.confirm_date || '-')}</td>` +
      `<td style="padding:4px 10px;text-align:center">${esc(o.reason || '-')}</td>` +
      `<td style="padding:4px 10px;text-align:center">${o.elapsed_days != null ? esc(String(o.elapsed_days)) : '-'}</td>` +
      `<td style="padding:4px 10px;text-align:center" title="${o.etd ? `ETD ${esc(shortDate(o.etd))}, 원래 버퍼 ${o.etd_buffer_days}영업일` : ''}">` +
      `${o.impacts_delivery == null ? '판단불가' : (o.impacts_delivery ? 'O' : 'X')}</td>` +
      `<td style="padding:4px 10px;text-align:center"><input type="text" class="remark-input" id="${remarkDomId}" value="${esc(remarkText)}" readonly ` +
      `ondblclick="unlockRemark('${remarkDomId}')" onblur="saveOverdueRemark('${weekId}','${season}','${o.style_code}','${stage}')" ` +
      `style="width:220px;font-size:10px;padding:2px 4px;text-align:left" title="더블클릭해서 수정"></td></tr>`;
    }).join('') +
    `</tbody></table></div></td></tr>`;
}

// 담당/단계 하나의 한 행(전체 또는 quarter 하나) — 현황(pct+문장) + 미완료 상세 토글 + (전체 행일 때만) 비고.
function progressRowHtml(label, m, key, suffix, weekId, season, owner, stage, remarkText, showRemark, remarksBlob) {
  const overdue = m.overdue || [];
  const overdueId = `overdue-${key}-${suffix}`.replace(/[^\\w-]/g, '_');
  const remarkCell = showRemark
    ? (() => {
        const remarkDomId = `remark-${weekId}-${season}-${owner}-${stage}`.replace(/[^\\w-]/g, '_');
        return `<td class="remark-col" style="display:flex;align-items:center;justify-content:flex-start">` +
          `<input type="text" class="remark-input" id="${remarkDomId}" value="${esc(remarkText)}" readonly ` +
          `ondblclick="unlockRemark('${remarkDomId}')" onblur="saveRemark('${weekId}','${season}','${owner}','${stage}')" ` +
          `style="width:220px;font-size:11px;padding:2px 4px;text-align:left" title="더블클릭해서 수정"></td>`;
      })()
    : `<td class="remark-col"></td>`;
  const rowHtml = `<tr><td class="owner-col">${esc(label)}</td>` +
    `<td class="status-col" id="cell-${key}-${esc(suffix)}">${statusTextHtml(m)}</td>` +
    `<td class="num-td pct">${pct(m.baseline_done, m.baseline_all)}%</td>` +
    `<td class="num-td pct">${pct(m.total_done, m.total_all)}%</td>` +
    `${remarkCell}</tr>` + overdueDetailRowHtml(overdue, overdueId, 5, weekId, season, stage, remarksBlob);
  return {html: rowHtml, overdueId};
}

// stage(FIT/PP/TOP) 하나: "전체" 행(quarter 다 합친 값) + 클릭하면 펼쳐지는 quarter별 세부 행.
function renderStageTable(stage, owner, season, quarters, quarterProgress, overallProgress, weekId, remarks) {
  const table = document.createElement('table');
  table.innerHTML = `<thead>
    <tr><th class="owner-col">Quarter</th>
      <th class="status-col">현황</th>
      <th class="num-th">Due%</th><th class="num-th">전체%</th>
      <th class="remark-col">비고</th></tr>
    </thead><tbody></tbody>`;
  const tbody = table.querySelector('tbody');
  const key = editKey(season, owner, stage);
  let overallM = (overallProgress[owner] || {})[stage];
  if (!overallM) return table;
  if (edits[key]) overallM = {...overallM, total_done: edits[key].override_numerator, total_all: edits[key].override_denominator};
  const remarkText = remarks[remarkKey(season, owner, stage)] || '';
  const detailId = `qbreakdown-${key}`.replace(/[^\\w-]/g, '_');
  const canExpand = quarters.length > 1;
  const {html: overallRowHtml} = progressRowHtml(
    canExpand ? `▾ 전체 (quarter별 보기)` : '전체', overallM, key, '전체', weekId, season, owner, stage, remarkText, true, remarks);
  const overallRow = document.createElement('template');
  overallRow.innerHTML = overallRowHtml;
  if (canExpand) {
    const labelTd = overallRow.content.querySelector('td.owner-col');
    labelTd.innerHTML = `<a href="#" onclick="toggleOverdue('${detailId}');return false" style="color:var(--ink);font-weight:700">▾ 전체</a>`;
  }
  tbody.append(...overallRow.content.childNodes);

  if (canExpand) {
    const detailRow = document.createElement('tr');
    let inner = '';
    quarters.forEach(q => {
      const progress = quarterProgress[q];
      let m = (progress[owner] || {})[stage];
      if (!m) return;
      const {html} = progressRowHtml(q, m, key, q, weekId, season, owner, stage, remarkText, false, remarks);
      inner += html;
    });
    detailRow.innerHTML = `<td colspan="5" style="background:var(--soft);padding:0">` +
      `<div id="${detailId}" style="display:none">` +
      `<table style="width:100%;border-collapse:collapse">${inner}</table></div></td>`;
    tbody.appendChild(detailRow);
  }
  return table;
}

function render() {
  const week = DATA.weeks[sel.value];
  if (!week) return;
  const isLatest = sel.value === weekIds[0];
  const weekSeasons = Object.keys(week.raw && Object.keys(week.raw).length ? week.raw : week.progress).sort();
  const container = document.getElementById('seasons');
  container.innerHTML = '';
  const weekId = sel.value;
  const remarks = week.remarks || {};
  for (const season of weekSeasons) {
    const asOfDate = isLatest ? resolveAsOfDate(season) : week.as_of_date;
    const offsets = currentOffsets(season);

    const title = document.createElement('div');
    title.className = 'season-title';
    title.textContent = season;
    container.appendChild(title);

    const seasonRows = week.raw && week.raw[season];
    if (!seasonRows) {
      // raw 데이터가 없는 예전 스냅샷 등 — quarter별로 못 나누고 통짜 progress 하나만 있음.
      const progress = week.progress[season];
      STAGES.forEach(stage => {
        const owner = OWNER_BY_STAGE[stage];
        if (!(progress[owner] || {})[stage]) return;
        const stageTitle = document.createElement('div');
        stageTitle.className = 'quarter-title';
        stageTitle.textContent = `${stage} (${owner})`;
        container.appendChild(stageTitle);
        container.appendChild(renderStageTable(stage, owner, season, ['전체'], {'전체': progress}, progress, weekId, remarks));
      });
      continue;
    }

    const rowsByQuarter = {};
    seasonRows.forEach(row => {
      const q = normalizeQuarter(row.quarter);
      (rowsByQuarter[q] || (rowsByQuarter[q] = [])).push(row);
    });
    const quarters = QUARTER_ORDER.filter(q => rowsByQuarter[q]);
    const quarterProgress = {};
    quarters.forEach(q => { quarterProgress[q] = computeProgressFromRaw(rowsByQuarter[q], asOfDate, offsets); });
    const overallProgress = computeProgressFromRaw(seasonRows, asOfDate, offsets);

    STAGES.forEach(stage => {
      const owner = OWNER_BY_STAGE[stage];
      const stageTitle = document.createElement('div');
      stageTitle.className = 'quarter-title';
      stageTitle.textContent = `${stage} (${owner})`;
      container.appendChild(stageTitle);
      container.appendChild(renderStageTable(stage, owner, season, quarters, quarterProgress, overallProgress, weekId, remarks));
    });
  }
}

async function init() {
  await Promise.all([...seasons.map(loadSavedDueOffsets), loadSavedAsOfSettings()]);
  updateAsOfBadges();
  if (weekIds.length) { sel.value = weekIds[0]; await onWeekChange(); }
}
init();
</script>
</body>
</html>
"""


# [적용] 버튼이 브라우저에서 Supabase settings 테이블에 직접 쓰기 때문에 anon key를 여기 embed한다.
# 이 anon key는 이미 dcsai.fnf.co.kr/apps/mlb-qm-fitting 앱에도 공개되어 있어 새로운 노출은 아니다.
_STRIPPED_KEYS = {"legacy_xlsx_sources", "raw_apparel_sources"}  # 로컬 파일 경로라 브라우저에 보여줄 이유 없음


def build_report_html(snapshots: dict, settings: dict) -> str:
    snapshot_json = json.dumps(snapshots, ensure_ascii=False).replace("<", "\\u003c")
    public_settings = {k: v for k, v in settings.items() if k not in _STRIPPED_KEYS}
    settings_json = json.dumps(public_settings, ensure_ascii=False).replace("<", "\\u003c")
    due_offsets_list = [{"label": k, **v} for k, v in LABEL_OFFSETS.items()]
    due_offsets_json = json.dumps(due_offsets_list, ensure_ascii=False).replace("<", "\\u003c")
    return (_TEMPLATE
            .replace("__SNAPSHOT_JSON__", snapshot_json)
            .replace("__SETTINGS_JSON__", settings_json)
            .replace("__DUE_OFFSETS_JSON__", due_offsets_json))
