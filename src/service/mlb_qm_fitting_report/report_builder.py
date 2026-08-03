import json

from src.service.mlb_qm_fitting_report.xlsx_source import LABEL_OFFSETS

_TEMPLATE = """<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>MLB QM Fitting 주간 보고</title>
<style>
body{font-family:'Malgun Gothic','Apple SD Gothic Neo',sans-serif;font-size:13px;background:#f0f1f4;color:#1a1a2e;margin:0}
.hdr{background:#1a1a2e;color:#fff;padding:14px 24px;display:flex;align-items:center;gap:12px}
.hdr h1{font-size:17px;margin:0}
select{padding:6px 10px;border-radius:6px;border:1px solid #ccc;font-size:12px}
.content{padding:20px;max-width:1100px;margin:0 auto}
table{width:100%;table-layout:fixed;border-collapse:collapse;background:#fff;border-radius:8px;overflow:hidden;margin-bottom:16px}
th,td{padding:6px 10px;border-bottom:1px solid #eee;text-align:left;font-size:12px}
th{background:#f8f9fa;color:#555;font-weight:700}
.grp-th{text-align:center;border-left:1px solid #eee}
.num-th,.num-td{text-align:center;font-variant-numeric:tabular-nums;width:90px}
.num-td.pct{font-weight:700}
.owner-col{width:64px;text-align:center}
.stage-col{width:64px;text-align:center}
.act-col{width:60px;text-align:center}
.grp-a{background:#eef3fc}
.grp-b{background:#f4f1fb}
th.grp-a,th.grp-th:first-of-type{border-left:1px solid #e5e7eb}
.season-title{font-weight:700;font-size:15px;margin:20px 0 8px;padding-bottom:4px;border-bottom:2px solid #1a1a2e}
.season-title:first-child{margin-top:0}
.btn{padding:3px 8px;border-radius:4px;border:1px solid #ccc;background:#fff;font-size:11px;cursor:pointer}
.btn:hover{background:#f0f1f4}
.edit-cell{display:inline-flex;align-items:center;gap:3px;white-space:nowrap}
.edit-cell input{width:40px;padding:2px 3px;font-size:11px}
.num-td.pct.grp-a:has(.edit-cell){overflow:visible;position:relative}
.override-bar{position:sticky;bottom:0;background:#1a1a2e;color:#fff;padding:10px 20px;display:none;align-items:center;gap:12px;font-size:12px}
.override-bar.show{display:flex}
.override-bar .btn{background:#4a65a9;color:#fff;border:none}
.settings-bar{background:#fff;border:1px solid #e5e7eb;border-radius:8px;margin:0 auto 12px;max-width:1100px;padding:12px 16px;font-size:12px}
.settings-bar summary{cursor:pointer;font-weight:700;color:#1a1a2e}
.settings-bar .row{display:flex;flex-wrap:wrap;align-items:center;gap:8px;margin-top:10px}
.settings-bar label{color:#555;white-space:nowrap}
.settings-bar input,.settings-bar select{padding:4px 6px;font-size:11px;border:1px solid #ccc;border-radius:4px}
.settings-bar .desc{color:#888;font-size:11px;margin:4px 0 0}
.th-table{width:100%;border-collapse:collapse;margin-top:10px}
.th-table th,.th-table td{padding:5px 8px;border-bottom:1px solid #f0f1f4;font-size:11px;text-align:left}
.th-table th{color:#888;font-weight:700}
.th-table td:first-child{color:#555}
.th-table input{width:36px;text-align:right}
.tabs{display:flex;gap:4px;margin-left:auto}
.tab-btn{padding:6px 16px;border-radius:6px 6px 0 0;border:none;background:rgba(255,255,255,0.12);color:#fff;font-size:12px;font-weight:700;cursor:pointer}
.tab-btn.active{background:#f0f1f4;color:#1a1a2e}
.analysis-section{background:#fff;border-radius:8px;padding:16px 20px;margin-bottom:16px}
.analysis-section h3{font-size:14px;margin:0 0 4px}
.analysis-section .sub{color:#888;font-size:11px;margin:0 0 12px}
.donut-grid{display:flex;flex-wrap:wrap;gap:16px}
.donut-cell{display:flex;flex-direction:column;align-items:center;width:88px}
.donut-cell .name{font-size:10px;color:#555;text-align:center;margin-top:4px;line-height:1.3}
.big-stat{display:flex;align-items:center;gap:20px}
.big-stat .num{font-size:36px;font-weight:700}
.big-stat .detail{color:#888;font-size:12px}
</style>
</head>
<body>
<div class="hdr">
  <h1>MLB QM Weekly Analysis</h1>
  <select id="week-select" onchange="onWeekChange()"></select>
  <div class="tabs">
    <button class="tab-btn active" id="tab-btn-main" onclick="switchTab('main')">메인</button>
    <button class="tab-btn" id="tab-btn-analysis" onclick="switchTab('analysis')">분석</button>
  </div>
</div>
<div id="main-tab">
<div style="max-width:1100px;margin:16px auto 0">
  <details class="settings-bar">
    <summary>기준일 설정 (시즌별)</summary>
    <p class="desc">전체 스타일 수 기준 = 완료 / 전체. Due Date 기준 = as_of_date까지 due date 지난 것 중 완료 / 지난 것 전체(계획 대비 실적).<br>기준 요일 = 매주 자동 적용(예: 금요일 지정 시 실행일 기준 직전 금요일을 그 주 기준일로 씀). 특정 주만 다른 날짜 쓰려면 날짜 지정. 시즌마다 따로 설정 가능.</p>
    <div id="as-of-rows"></div>
    <div class="row"><button class="btn" onclick="applySettings()">적용</button><span id="settings-status"></span></div>
  </details>
  <div id="due-offset-panels"></div>
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
<script id="snapshot-data" type="application/json">__SNAPSHOT_JSON__</script>
<script id="settings-data" type="application/json">__SETTINGS_JSON__</script>
<script id="due-offsets-data" type="application/json">__DUE_OFFSETS_JSON__</script>
<script>
const DATA = JSON.parse(document.getElementById('snapshot-data').textContent);
const SETTINGS = JSON.parse(document.getElementById('settings-data').textContent);
const DUE_OFFSETS = JSON.parse(document.getElementById('due-offsets-data').textContent);
const weekIds = Object.keys(DATA.weeks).sort().reverse();
const sel = document.getElementById('week-select');
weekIds.forEach(w => { const o = document.createElement('option'); o.value = w; o.textContent = w + ' (기준일 ' + DATA.weeks[w].as_of_date + ')'; sel.appendChild(o); });

const seasons = weekIds.length ? Object.keys(DATA.weeks[weekIds[0]].raw || {}).sort() : [];
const asOfBySeason = SETTINGS.as_of_by_season || {};

const asOfRowsEl = document.getElementById('as-of-rows');
seasons.forEach(season => {
  const s = asOfBySeason[season] || {};
  const row = document.createElement('div');
  row.className = 'row';
  row.dataset.season = season;
  row.innerHTML = `<label style="min-width:48px;font-weight:700">${esc(season)}</label>` +
    `<label>기준 요일</label><select data-field="weekday">
      <option value="MON">월</option><option value="TUE">화</option><option value="WED">수</option>
      <option value="THU">목</option><option value="FRI">금</option>
    </select>
    <label>특정 날짜로 고정(선택)</label><input type="date" data-field="override">` +
    `<span class="as-of-badge" style="margin-left:8px;color:#4a65a9;font-weight:700"></span>`;
  row.querySelector('[data-field="weekday"]').value = s.as_of_weekday || SETTINGS.as_of_weekday || 'FRI';
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

// 최신 주차 화면은 이 값들로 라이브 재계산한다(과거 주차는 스냅샷 당시 as_of_date 그대로 씀).
const JS_WEEKDAY = {MON: 1, TUE: 2, WED: 3, THU: 4, FRI: 5, SAT: 6, SUN: 0};

function resolveAsOfDate(season) {
  const row = asOfRowsEl.querySelector(`[data-season="${season}"]`);
  const override = row ? row.querySelector('[data-field="override"]').value : '';
  if (override) return override;
  const weekday = row ? row.querySelector('[data-field="weekday"]').value : 'FRI';
  const target = JS_WEEKDAY[weekday] ?? 5;
  const today = new Date();
  let daysBack = (today.getDay() - target + 7) % 7;
  if (daysBack === 0) daysBack = 7;
  const d = new Date(today);
  d.setDate(d.getDate() - daysBack);
  return d.toISOString().slice(0, 10);
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
        if (s.as_of_weekday) row.querySelector('[data-field="weekday"]').value = s.as_of_weekday;
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
      as_of_weekday: row.querySelector('[data-field="weekday"]').value,
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

async function onWeekChange() {
  await loadOverridesForWeek(sel.value);
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
          let confirmRawDate = d.confirm_date || null;
          let confirmStage = d.confirm_date ? `${ordinalRound(d.round)} ${stage}`.trim() : null;
          let confirmReason = d.confirm_date ? (d.reason || null) : null;
          if (!confirmRawDate) {
            const recent = recentActivityBefore(row, stage);
            if (recent) { confirmRawDate = recent.date; confirmStage = recent.label; confirmReason = recent.reason; }
          }
          bucket.overdue.push({
            style_code: row.style_code, vendor: row.vendor || null, due, status: d.status || '접수 전',
            confirm_stage: confirmStage, confirm_date: confirmRawDate ? shortDate(confirmRawDate) : null,
            elapsed_days: businessDaysSince(confirmRawDate, asOfDate), overdue_days: businessDaysSince(due, asOfDate),
            reason: confirmReason,
          });
        }
      }
    }
  }
  return result;
}

function toggleOverdue(id) {
  const el = document.getElementById(id);
  if (el) el.style.display = el.style.display === 'none' ? 'block' : 'none';
}

let activeTab = 'main';

function switchTab(tab) {
  activeTab = tab;
  document.getElementById('main-tab').style.display = tab === 'main' ? '' : 'none';
  document.getElementById('analysis-tab').style.display = tab === 'analysis' ? '' : 'none';
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

function donutSVG(pct, size, color, subLabel) {
  size = size || 80;
  const stroke = Math.round(size * 0.13);
  const r = (size - stroke) / 2;
  const c = size / 2;
  const circumference = 2 * Math.PI * r;
  const p = Math.max(0, Math.min(100, pct));
  const offset = circumference * (1 - p / 100);
  const col = color || colorForPct(p);
  return `<svg width="${size}" height="${size}" viewBox="0 0 ${size} ${size}">
    <circle cx="${c}" cy="${c}" r="${r}" fill="none" stroke="#eef0f4" stroke-width="${stroke}"/>
    <circle cx="${c}" cy="${c}" r="${r}" fill="none" stroke="${col}" stroke-width="${stroke}"
      stroke-dasharray="${circumference.toFixed(1)}" stroke-dashoffset="${offset.toFixed(1)}"
      stroke-linecap="round" transform="rotate(-90 ${c} ${c})"/>
    <text x="${c}" y="${subLabel ? c - 4 : c}" text-anchor="middle" dominant-baseline="central" font-size="${size * 0.22}" font-weight="700" fill="#1a1a2e">${Math.round(p)}%</text>
    ${subLabel ? `<text x="${c}" y="${c + size * 0.18}" text-anchor="middle" dominant-baseline="central" font-size="${size * 0.11}" fill="#999">${escSvg(subLabel)}</text>` : ''}
  </svg>`;
}

function escSvg(s) { return esc(String(s == null ? '' : s)); }

function hBarChart(items, opts) {
  opts = opts || {};
  const width = opts.width || 460;
  const barHeight = opts.barHeight || 20;
  const gap = 8;
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
    bars += `<text x="${labelWidth - 8}" y="${y + barHeight / 2}" text-anchor="end" dominant-baseline="central" font-size="11" fill="#555">${escSvg(it.label)}</text>` +
      `<rect x="${labelWidth}" y="${y + 2}" width="${w.toFixed(1)}" height="${barHeight - 4}" rx="4" fill="${it.color || color}"/>` +
      `<text x="${labelWidth + w + 6}" y="${y + barHeight / 2}" dominant-baseline="central" font-size="11" fill="#1a1a2e">${escSvg(it.value)}${unit}</text>`;
  });
  return `<svg width="${width}" height="${Math.max(height, 1)}">${bars}</svg>`;
}

function lineChart(seriesList, opts) {
  opts = opts || {};
  const width = opts.width || 520, height = opts.height || 180;
  const yMin = opts.yMin != null ? opts.yMin : 0;
  const yMax = opts.yMax != null ? opts.yMax : 100;
  const pad = {left: 34, right: 16, top: 14, bottom: 22};
  const w = width - pad.left - pad.right, h = height - pad.top - pad.bottom;
  const xLabels = seriesList[0] ? seriesList[0].points.map(p => p.x) : [];
  const n = xLabels.length;
  const xAt = i => pad.left + (n <= 1 ? w / 2 : (i / (n - 1)) * w);
  const yAt = v => pad.top + h - (Math.max(yMin, Math.min(yMax, v)) - yMin) / (yMax - yMin) * h;
  const gridVals = [0, 0.25, 0.5, 0.75, 1].map(t => Math.round((yMin + (yMax - yMin) * t) * 10) / 10);
  const grid = gridVals.map(v =>
    `<line x1="${pad.left}" y1="${yAt(v).toFixed(1)}" x2="${width - pad.right}" y2="${yAt(v).toFixed(1)}" stroke="#eee"/>` +
    `<text x="${pad.left - 6}" y="${(yAt(v) + 3).toFixed(1)}" text-anchor="end" font-size="9" fill="#aaa">${v}</text>`
  ).join('');
  const labels = xLabels.map((x, i) => `<text x="${xAt(i).toFixed(1)}" y="${height - 6}" text-anchor="middle" font-size="9" fill="#888">${escSvg(x)}</text>`).join('');
  const lines = seriesList.map(s => {
    const path = s.points.map((p, i) => `${i === 0 ? 'M' : 'L'}${xAt(i).toFixed(1)},${yAt(p.y).toFixed(1)}`).join(' ');
    const dots = s.points.map((p, i) => `<circle cx="${xAt(i).toFixed(1)}" cy="${yAt(p.y).toFixed(1)}" r="3" fill="${s.color}"/>`).join('');
    return `<path d="${path}" fill="none" stroke="${s.color}" stroke-width="2"/>${dots}`;
  }).join('');
  const legend = seriesList.map((s, i) => `<span style="display:inline-flex;align-items:center;gap:4px;margin-right:12px;font-size:11px;color:#555">` +
    `<span style="width:10px;height:10px;border-radius:50%;background:${s.color};display:inline-block"></span>${esc(s.name)}</span>`).join('');
  return `<div>${legend}</div><svg width="${width}" height="${height}">${grid}${lines}${labels}</svg>`;
}

const CATEGORIES = ['KNIT', 'SWEATER', 'WOVEN', 'DENIM'];

const GROUP_LABELS = {vendor: '협력사', item: '아이템', td: 'TD', qa: 'QA'};

function groupKeyForRow(row, groupBy) {
  if (groupBy === 'item') return row.item || '미상';
  if (groupBy === 'td') return row.td || '미배정';
  if (groupBy === 'qa') return row.qa || '미배정';
  return vendorAlias(row.vendor) || '미상';
}

function analysisStats(rawRows, asOfDate, offsets, groupBy) {
  const byGroup = {}, byCategory = {}, byStage = {FIT: {done: 0, total: 0}, PP: {done: 0, total: 0}, TOP: {done: 0, total: 0}};
  let overallDone = 0, overallTotal = 0;
  const groupOverdueDays = {};
  const groupOverdueDaysByStage = {FIT: {}, PP: {}, TOP: {}};
  for (const row of rawRows) {
    const group = groupKeyForRow(row, groupBy);
    const category = CATEGORIES.find(c => row.label && row.label.startsWith(c)) || '미분류';
    for (const stage of STAGES) {
      const isDone = row[`${stage.toLowerCase()}_done`];
      const due = resolveDue(row, stage, offsets);
      // due date를 못 구했어도 이미 완료된 건은 완료로 잡는다(안 그러면 통계에서 조용히 빠짐).
      const isDue = !!(due && due <= asOfDate) || (!due && isDone);
      if (!isDue) continue;
      overallTotal++;
      byStage[stage].total++;
      if (!byGroup[group]) byGroup[group] = {done: 0, total: 0};
      if (!byCategory[category]) byCategory[category] = {done: 0, total: 0};
      byGroup[group].total++;
      byCategory[category].total++;
      if (isDone) {
        overallDone++;
        byStage[stage].done++;
        byGroup[group].done++;
        byCategory[category].done++;
      } else {
        const days = businessDaysSince(due, asOfDate) || 0;
        (groupOverdueDays[group] || (groupOverdueDays[group] = [])).push(days);
        const byStageMap = groupOverdueDaysByStage[stage];
        (byStageMap[group] || (byStageMap[group] = [])).push(days);
      }
    }
  }
  return {byGroup, byCategory, byStage, overallDone, overallTotal, groupOverdueDays, groupOverdueDaysByStage};
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

// "2026-W35" -> 그 ISO 주의 금요일 날짜(Date). 기준일 설정이 금요일 기준인 것과 맞춤.
function isoWeekLabelToFriday(weekStr) {
  const [y, w] = weekStr.split('-W').map(Number);
  const jan4 = new Date(y, 0, 4);
  const jan4Day = (jan4.getDay() + 6) % 7;
  const monday = new Date(jan4);
  monday.setDate(jan4.getDate() - jan4Day + (w - 1) * 7);
  const friday = new Date(monday);
  friday.setDate(monday.getDate() + 4);
  return friday;
}

function periodDisplayLabel(key, period) {
  if (period === 'month') return key;
  const f = isoWeekLabelToFriday(key);
  return `${key} (${f.getMonth() + 1}/${f.getDate()})`;
}

function periodShortLabel(key, period) {
  if (period === 'month') return key.slice(5);
  const f = isoWeekLabelToFriday(key);
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

// stage별 원자료: 실제 due date가 있는 건은 {duePeriod, confirmPeriod, onTime, hasRealDue:true}로,
// due date를 못 구했지만 이미 완료된 건(라벨/ETD 누락 등)은 hasRealDue:false로 따로 표시한다.
// 후자는 "주차별" 표를 오염시키면 안 되니(그 주에 실제 일어난 일이 아님) 주차별 집계에선 빼고
// 누적 집계에만 기준일 시점에 반영한다.
function dueDateRecordsByStage(rawRows, offsets, todayIso, period) {
  const records = {FIT: [], PP: [], TOP: []};
  for (const row of rawRows) {
    for (const stage of STAGES) {
      const due = resolveDue(row, stage, offsets);
      const isDone = row[`${stage.toLowerCase()}_done`];
      if (due) {
        if (due > todayIso) continue;
        // 승인 완료(isDone) 상태가 아니면 confirm_date가 있어도(예: 최신 회차가 Rejected인데
        // 전달일만 채워진 경우) 정시 승인으로 치면 안 된다 — 완료 건수보다 정시 건수가 많아지는
        // 모순이 생김.
        const confirmDate = isDone ? effectiveConfirmDate(row, stage) : null;
        records[stage].push({
          duePeriod: periodLabel(due, period),
          confirmPeriod: confirmDate ? periodLabel(confirmDate, period) : null,
          onTime: !!(confirmDate && confirmDate <= due),
          hasRealDue: true,
        });
      } else if (isDone) {
        records[stage].push({duePeriod: null, confirmPeriod: periodLabel(todayIso, period), onTime: true, hasRealDue: false});
      }
    }
  }
  return records;
}

// "주차별" = 그 주에 due였던 것 중 실제 승인일이 due date 이내였던 비율(due date 있는 것만, 영구 고정).
function dueDateOnTimeComplianceByStage(records) {
  const byStagePeriod = {FIT: {}, PP: {}, TOP: {}};
  STAGES.forEach(st => {
    records[st].forEach(rec => {
      if (!rec.hasRealDue) return;
      const byPeriod = byStagePeriod[st];
      if (!byPeriod[rec.duePeriod]) byPeriod[rec.duePeriod] = {onTime: 0, total: 0};
      byPeriod[rec.duePeriod].total++;
      if (rec.onTime) byPeriod[rec.duePeriod].onTime++;
    });
  });
  return byStagePeriod;
}

// 누적용 원자료: due 기간별로 묶되, "정시냐"가 아니라 "지금 됐냐"만 본다(메인탭 Due Date 기준과
// 동일한 isDue/isDone 판정). due 없이 이미 완료된 건(라벨/ETD 누락)은 주차별 표를 오염시키면
// 안 되니 기준일 기간에만 합류.
function cumulativeDoneRecordsByStage(rawRows, offsets, todayIso, period) {
  const records = {FIT: [], PP: [], TOP: []};
  for (const row of rawRows) {
    for (const stage of STAGES) {
      const due = resolveDue(row, stage, offsets);
      const isDone = row[`${stage.toLowerCase()}_done`];
      if (due) {
        if (due > todayIso) continue;
        records[stage].push({period: periodLabel(due, period), done: isDone});
      } else if (isDone) {
        records[stage].push({period: periodLabel(todayIso, period), done: true});
      }
    }
  }
  return records;
}

// 기간 순서대로 단순 런닝 합계(누적). confirm_date 비교(정시 여부) 없이 그냥 "됐냐"만 쌓는다.
function withCumulativeDone(records, sortedPeriods) {
  const result = {};
  STAGES.forEach(st => {
    result[st] = {};
    let cumDone = 0, cumTotal = 0;
    sortedPeriods.forEach(p => {
      const inPeriod = records[st].filter(r => r.period === p);
      cumDone += inPeriod.filter(r => r.done).length;
      cumTotal += inPeriod.length;
      result[st][p] = {cumDone, cumTotal};
    });
  });
  return result;
}

let analysisPeriod = 'week';
let analysisGroupBy = 'vendor';
let analysisOverdueStage = 'ALL';
const STAGE_COLORS = {FIT: '#4a65a9', PP: '#e0a72e', TOP: '#2e9e5b'};

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

function filterCheckboxesHtml(rows, dim) {
  const values = [...new Set(rows.map(r => filterFieldValue(r, dim)))].sort();
  const cur = analysisFilters[dim];
  const cb = v => `<label style="display:block;font-weight:400;white-space:nowrap">` +
    `<input type="checkbox" value="${escSvg(v)}"${cur.includes(v) ? ' checked' : ''} onchange="toggleFilterValue('${dim}', this.value, this.checked)"> ${esc(v)}</label>`;
  if (dim !== 'vendor') return values.map(cb).join('');
  const byCat = {};
  values.forEach(v => { const cat = VENDOR_CATEGORY[v] || '기타'; (byCat[cat] || (byCat[cat] = [])).push(v); });
  return ['KNIT', 'WOVEN', 'SWEATER', 'DENIM', '기타'].filter(c => byCat[c])
    .map(cat => `<div style="font-weight:700;color:#555;margin-top:4px">${esc(cat)}</div>${byCat[cat].map(cb).join('')}`).join('');
}

// 필터 체크박스 한 줄(표 위에 바로 붙임 — 따로 떨어진 패널 아님). 아무것도 체크 안 하면 전체.
function filterRowHtml(rows) {
  return `<div style="display:flex;gap:14px;flex-wrap:wrap;align-items:flex-start;margin-bottom:10px">` +
    Object.keys(FILTER_DIM_LABELS).map(dim =>
      `<span style="font-size:11px">` +
      `<label style="font-weight:700;color:#888;display:block;margin-bottom:2px">${esc(FILTER_DIM_LABELS[dim])}</label>` +
      `<div style="min-width:110px;max-height:110px;overflow-y:auto;border:1px solid #e5e7eb;border-radius:4px;padding:4px 6px;background:#fff">${filterCheckboxesHtml(rows, dim)}</div></span>`
    ).join('') + `</div>`;
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
  const groupLabel = GROUP_LABELS[groupBy];
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
  const stats = analysisStats(rows, asOfDate, offsets, groupBy);
  const periodLabelKr = period === 'month' ? '월' : '주';

  // 주차별(정시) 표는 dueDateRecordsByStage/dueDateOnTimeComplianceByStage 그대로 씀(고정값, 안 바뀜).
  const dueRecords = season === '26FW' ? dueDateRecordsByStage(rows, offsets, asOfDate, period) : null;
  const onTimeByStage = dueRecords ? dueDateOnTimeComplianceByStage(dueRecords) : null;
  // 누적은 "정시" 개념을 빼고, 메인탭 Due Date 기준과 동일한 isDue/isDone 로직을 기간별로 누적 합산.
  const doneRecords = season === '26FW' ? cumulativeDoneRecordsByStage(rows, offsets, asOfDate, period) : null;
  const allPeriods = onTimeByStage
    ? [...new Set([
        ...STAGES.flatMap(st => Object.keys(onTimeByStage[st])),
        ...(doneRecords ? STAGES.flatMap(st => doneRecords[st].map(r => r.period)) : []),
        periodLabel(asOfDate, period),
      ])].sort()
    : [];
  const doneCum = doneRecords ? withCumulativeDone(doneRecords, allPeriods) : null;
  // 아래 "주별 승인율" 표의 맨 마지막(최신) 누적 행이랑 완전히 같은 숫자를 쓴다 — 위 요약 도넛과
  // 아래 상세표 숫자가 서로 다르게 보이면 안 되니까, 별도 계산 없이 그 표의 최종 누적을 그대로 씀.
  // 이 값은 메인탭 "Due Date 기준" 값과도 100% 같아야 정상(같은 isDue/isDone 로직을 기간별로 쪼갠 것뿐).
  const lastPeriod = allPeriods.length ? allPeriods[allPeriods.length - 1] : null;
  const finalDonePct = {};
  STAGES.forEach(st => {
    if (!doneCum || !lastPeriod) { finalDonePct[st] = null; return; }
    const b = doneCum[st][lastPeriod];
    finalDonePct[st] = b && b.cumTotal ? {pct: Math.round(b.cumDone / b.cumTotal * 1000) / 10, done: b.cumDone, total: b.cumTotal} : null;
  });

  // 주차별 정시율 단순평균(왼쪽) — 데이터 있는 주만 평균낸다.
  const avgOnTimePct = {};
  STAGES.forEach(st => {
    if (!onTimeByStage) { avgOnTimePct[st] = null; return; }
    const pcts = Object.values(onTimeByStage[st]).filter(b => b.total > 0).map(b => b.onTime / b.total * 100);
    avgOnTimePct[st] = pcts.length ? Math.round(pcts.reduce((a, b) => a + b, 0) / pcts.length * 10) / 10 : null;
  });

  // 단계별 Due Date 달성률: 왼쪽 = 전체 기간 주차별 정시율 평균, 오른쪽 = 누적 승인율(아래 표 최종 누적과 동일). 서로 다른 개념, 다른 숫자가 정상.
  const sec1 = document.createElement('div');
  sec1.className = 'analysis-section';
  const cumHalf = `<div><div style="font-weight:700;font-size:12px;color:#555;margin-bottom:8px">주차별 Due Date 준수율</div><div style="display:flex;gap:16px">` +
    STAGES.map(st => {
      const p = avgOnTimePct[st];
      return `<div>${donutSVG(p ?? 0, 76)}<div style="text-align:center;font-size:11px;color:#888;margin-top:4px">${st} ${p != null ? `(${p}%)` : '-'}</div></div>`;
    }).join('') + `</div></div>`;
  const avgHalf = `<div><div style="font-weight:700;font-size:12px;color:#555;margin-bottom:8px">누적 Due Date 준수율</div><div style="display:flex;gap:16px">` +
    STAGES.map(st => {
      const v = finalDonePct[st];
      return `<div>${donutSVG(v ? v.pct : 0, 76)}<div style="text-align:center;font-size:11px;color:#888;margin-top:4px">${st} ${v ? `(${v.done}/${v.total})` : '-'}</div></div>`;
    }).join('') + `</div></div>`;
  sec1.innerHTML = `<h3>단계별 Due Date 달성률</h3>` +
    `<div style="display:flex;gap:40px;flex-wrap:wrap">${cumHalf}${avgHalf}</div>`;
  container.appendChild(sec1);

  const controlsHtml = `<div style="margin-bottom:10px">` +
    `<label style="font-weight:700;margin-right:8px">기간 단위</label>` +
    `<select onchange="analysisPeriod=this.value;renderAnalysis()"><option value="week"${period === 'week' ? ' selected' : ''}>주</option><option value="month"${period === 'month' ? ' selected' : ''}>월</option></select></div>`;
  const groupByHtml = `<label style="font-weight:700;margin-right:8px;font-size:12px">그룹 기준</label>` +
    `<select onchange="analysisGroupBy=this.value;renderAnalysis()" style="margin-right:16px">` +
    Object.entries(GROUP_LABELS).map(([k, v]) => `<option value="${k}"${groupBy === k ? ' selected' : ''}>${v}</option>`).join('') +
    `</select>`;

  // 핵심 지표: 스타일 due date가 속한 기간별 "정시 승인율"(FIT/PP/TOP 각각, 주차별 + 누적). 필터도 이 표 위에 바로 붙임.
  if (season === '26FW') {
    const onTimeSeries = STAGES.map(st => ({
      name: st,
      color: STAGE_COLORS[st],
      points: allPeriods.map(p => {
        const b = onTimeByStage[st][p];
        return {x: periodShortLabel(p, period), y: b && b.total ? Math.round(b.onTime / b.total * 1000) / 10 : null};
      }).filter(pt => pt.y != null),
    })).filter(s => s.points.length > 1);
    const secOnTime = document.createElement('div');
    secOnTime.className = 'analysis-section';
    secOnTime.innerHTML = `<h3>주차별 Due Date 준수율</h3>` +
      filterRowHtml(allRows) +
      controlsHtml +
      (onTimeSeries.length ? lineChart(onTimeSeries, {width: 900, height: 240}) : `<p class="sub">데이터가 부족함</p>`) +
      `<table style="width:100%;font-size:11px;border-collapse:collapse;margin-top:10px">` +
      `<thead><tr><th style="text-align:left;padding:4px" rowspan="2">${periodLabelKr}</th>` +
      STAGES.map(st => `<th style="text-align:center;padding:4px" colspan="2">${st}</th>`).join('') + `</tr>` +
      `<tr>` + STAGES.map(() => `<th style="text-align:right;padding:4px;font-weight:400;color:#888">주차별(정시)</th><th style="text-align:right;padding:4px;font-weight:400;color:#888">누적(완료)</th>`).join('') + `</tr></thead><tbody>` +
      allPeriods.map(p => `<tr><td style="padding:4px">${esc(periodDisplayLabel(p, period))}</td>` +
        STAGES.map(st => {
          const wk = onTimeByStage[st][p];
          const cm = doneCum[st][p];
          const curPct = wk && wk.total ? Math.round(wk.onTime / wk.total * 1000) / 10 : null;
          const cumPct = cm && cm.cumTotal ? Math.round(cm.cumDone / cm.cumTotal * 1000) / 10 : null;
          const cur = curPct != null ? `${curPct}% (${wk.onTime}/${wk.total})` : '-';
          const cum = cumPct != null ? `${cumPct}% (${cm.cumDone}/${cm.cumTotal})` : '-';
          const curColor = curPct != null ? colorForPct(curPct) : '#ccc';
          const cumColor = cumPct != null ? colorForPct(cumPct) : '#ccc';
          return `<td style="text-align:right;padding:4px;color:${curColor}">${cur}</td><td style="text-align:right;padding:4px;color:${cumColor};font-weight:700">${cum}</td>`;
        }).join('') + `</tr>`).join('') + `</tbody></table>`;
    container.appendChild(secOnTime);
  } else {
    const stub = document.createElement('div');
    stub.className = 'analysis-section';
    stub.innerHTML = `<h3>주차별 Due Date 준수율</h3>` + filterRowHtml(allRows) + controlsHtml +
      `<p class="sub">${esc(season)} 상세 분석은 추후 추가 예정(레이아웃만 26FW와 동일하게 자리 잡아둠).</p>`;
    container.appendChild(stub);
  }

  // 그룹별 평균 초과일수 — 초과 없는 그룹도 0으로 다 보여준다. 전체 스타일(전체 기간) 기준이고, 단계 드롭다운으로 FIT/PP/TOP만 볼 수도 있음.
  const overdueSource = analysisOverdueStage === 'ALL' ? stats.groupOverdueDays : stats.groupOverdueDaysByStage[analysisOverdueStage];
  const overdueEntries = Object.keys(stats.byGroup)
    .map(g => {
      const days = overdueSource[g];
      return {label: g, value: days && days.length ? Math.round(days.reduce((a, b) => a + b, 0) / days.length) : 0};
    })
    .sort((a, b) => b.value - a.value);
  if (overdueEntries.length) {
    const sec4 = document.createElement('div');
    sec4.className = 'analysis-section';
    const stageSelectHtml = `<label style="font-weight:700;margin-right:8px;font-size:12px">단계</label>` +
      `<select onchange="analysisOverdueStage=this.value;renderAnalysis()" style="margin-bottom:10px">` +
      `<option value="ALL"${analysisOverdueStage === 'ALL' ? ' selected' : ''}>전체</option>` +
      STAGES.map(st => `<option value="${st}"${analysisOverdueStage === st ? ' selected' : ''}>${st}</option>`).join('') +
      `</select>`;
    sec4.innerHTML = `<h3>${esc(groupLabel)}별 평균 초과 영업일</h3><p class="sub">현재(${esc(asOfDate)}) 기준, 전체 스타일 중 기준일 넘겼는데 아직 미완료인 건들의 평균 초과일수(0이면 그런 건 없음)</p>` +
      groupByHtml + stageSelectHtml +
      hBarChart(overdueEntries, {unit: '일', color: '#d9534f'});
    container.appendChild(sec4);
  }
}

function render() {
  const week = DATA.weeks[sel.value];
  if (!week) return;
  const isLatest = sel.value === weekIds[0];
  const weekSeasons = Object.keys(week.raw && Object.keys(week.raw).length ? week.raw : week.progress).sort();
  const container = document.getElementById('seasons');
  container.innerHTML = '';
  for (const season of weekSeasons) {
    const asOfDate = isLatest ? resolveAsOfDate(season) : week.as_of_date;
    const offsets = currentOffsets(season);
    const progress = (week.raw && week.raw[season])
      ? computeProgressFromRaw(week.raw[season], asOfDate, offsets)
      : week.progress[season];

    const title = document.createElement('div');
    title.className = 'season-title';
    title.textContent = season;
    container.appendChild(title);

    const table = document.createElement('table');
    table.innerHTML = `<thead>
      <tr><th class="owner-col" rowspan="2">담당</th><th class="stage-col" rowspan="2">단계</th>
        <th class="grp-th grp-a" colspan="3">전체 스타일 수 기준</th><th class="grp-th grp-b" colspan="3">Due Date 기준</th>
        ${isLatest ? '<th class="act-col" rowspan="2"></th>' : ''}</tr>
      <tr><th class="num-th grp-a">비율</th><th class="num-th grp-a">승인</th><th class="num-th grp-a">전체</th>
        <th class="num-th grp-b">비율</th><th class="num-th grp-b">승인</th><th class="num-th grp-b">전체</th></tr>
      </thead><tbody></tbody>`;
    const tbody = table.querySelector('tbody');
    for (const owner of ['TD', 'QA']) {
      for (const stage of Object.keys(progress[owner] || {})) {
        let m = progress[owner][stage];
        const key = editKey(season, owner, stage);
        if (edits[key]) m = {...m, total_done: edits[key].override_numerator, total_all: edits[key].override_denominator};
        const overdue = m.overdue || [];
        const overdueId = `overdue-${key}`.replace(/[^\\w-]/g, '_');
        const row = document.createElement('tr');
        row.innerHTML = `<td class="owner-col">${esc(owner)}</td><td class="stage-col">${esc(stage)}</td>` +
          `<td class="num-td pct grp-a" id="cell-${key}">${pct(m.total_done, m.total_all)}%</td><td class="num-td grp-a">${m.total_done}</td><td class="num-td grp-a">${m.total_all}</td>` +
          `<td class="num-td pct grp-b">${pct(m.baseline_done, m.baseline_all)}%</td><td class="num-td grp-b">${m.baseline_done}</td><td class="num-td grp-b">${m.baseline_all}</td>` +
          (isLatest ? `<td class="act-col"><button class="btn" onclick="startEdit('${season}','${owner}','${stage}',${m.total_done},${m.total_all})">수정</button></td>` : '');
        tbody.appendChild(row);

        if (overdue.length) {
          const detailRow = document.createElement('tr');
          const colspan = isLatest ? 9 : 8;
          detailRow.innerHTML = `<td colspan="${colspan}" style="background:#fafbfe;padding:0">` +
            `<div style="padding:4px 10px"><a href="#" onclick="toggleOverdue('${overdueId}');return false" style="font-size:11px;color:#4a65a9">미완료 ${overdue.length}건 상세 ▾</a></div>` +
            `<div id="${overdueId}" style="display:none;padding:0 10px 8px">` +
            `<table style="width:100%;font-size:10px;border-collapse:collapse">` +
            `<thead><tr style="color:#888"><th style="text-align:left;padding:3px 6px">스타일</th><th style="text-align:left;padding:3px 6px">협력사</th><th style="text-align:left;padding:3px 6px">DUE DATE</th><th style="text-align:left;padding:3px 6px">초과일수</th><th style="text-align:left;padding:3px 6px">현재 status</th>` +
              `<th style="text-align:left;padding:3px 6px">이전 Stage</th><th style="text-align:left;padding:3px 6px">전달일</th>` +
              `<th style="text-align:left;padding:3px 6px">사유</th><th style="text-align:left;padding:3px 6px">소요일</th></tr></thead>` +
            `<tbody>` + overdue.map(o => `<tr style="border-top:1px solid #eee">` +
              `<td style="padding:3px 6px">${esc(o.style_code)}</td><td style="padding:3px 6px">${esc(vendorAlias(o.vendor) || '-')}</td><td style="padding:3px 6px">${esc(shortDate(o.due))}</td>` +
              `<td style="padding:3px 6px">${o.overdue_days != null ? esc('+' + o.overdue_days) : '-'}</td>` +
              `<td style="padding:3px 6px">${esc(o.status)}</td>` +
              `<td style="padding:3px 6px">${esc(o.confirm_stage || '-')}</td><td style="padding:3px 6px">${esc(o.confirm_date || '-')}</td>` +
              `<td style="padding:3px 6px">${esc(o.reason || '-')}</td>` +
              `<td style="padding:3px 6px">${o.elapsed_days != null ? esc(String(o.elapsed_days)) : '-'}</td></tr>`).join('') +
            `</tbody></table></div></td>`;
          tbody.appendChild(detailRow);
        }
      }
    }
    container.appendChild(table);
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
