import json

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
th,td{padding:8px 10px;border-bottom:1px solid #eee;text-align:left;font-size:12px}
th{background:#f8f9fa;color:#555}
th:nth-child(1),td:nth-child(1){width:70px}
th:nth-child(2),td:nth-child(2){width:70px}
th:nth-child(3),td:nth-child(3),th:nth-child(4),td:nth-child(4){width:220px;text-align:right;font-variant-numeric:tabular-nums}
th:nth-child(5),td:nth-child(5){width:70px;text-align:center}
.season-title{font-weight:700;font-size:15px;margin:20px 0 8px;padding-bottom:4px;border-bottom:2px solid #1a1a2e}
.season-title:first-child{margin-top:0}
.btn{padding:3px 8px;border-radius:4px;border:1px solid #ccc;background:#fff;font-size:11px;cursor:pointer}
.btn:hover{background:#f0f1f4}
.edit-cell input{width:52px;padding:2px 4px;font-size:11px}
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
.th-table td{padding:5px 8px;border-bottom:1px solid #f0f1f4;font-size:11px}
.th-table td:first-child{color:#555}
.th-table td:last-child{width:90px;text-align:right}
.th-table input{width:48px;text-align:right}
</style>
</head>
<body>
<div class="hdr">
  <h1>MLB QM Fitting 주간 보고</h1>
  <select id="week-select" onchange="render()"></select>
</div>
<div style="max-width:1100px;margin:16px auto 0">
  <details class="settings-bar">
    <summary>기준일 설정</summary>
    <p class="desc">총량대비 = 완료 / 전체. 기준대비 = as_of_date까지 due date 지난 것 중 완료 / 지난 것 전체(계획 대비 실적).<br>기준 요일 = 매주 자동 적용(예: 금요일 지정 시 실행일 기준 직전 금요일을 그 주 기준일로 씀). 특정 주만 다른 날짜 쓰려면 아래 날짜 지정.</p>
    <div class="row">
      <label>기준 요일</label>
      <select id="set-weekday">
        <option value="MON">월</option><option value="TUE">화</option><option value="WED">수</option>
        <option value="THU">목</option><option value="FRI">금</option><option value="SAT">토</option><option value="SUN">일</option>
      </select>
      <label>특정 날짜로 고정(선택)</label>
      <input type="date" id="set-date-override">
      <button class="btn" onclick="downloadSettings()">설정 파일 다운로드</button>
    </div>
  </details>
  <details class="settings-bar">
    <summary>체이스(마감) 경고 기준일수</summary>
    <p class="desc">단계별 상태에서 다음 샘플 접수까지 며칠 전부터 경고 대상으로 볼지. 대시보드엔 표시 안 되고 계산 로직에서만 씀.</p>
    <table class="th-table" id="th-table"><tbody></tbody></table>
    <div class="row"><button class="btn" onclick="downloadSettings()">설정 파일 다운로드</button></div>
  </details>
</div>
<div class="content" id="seasons"></div>
<div class="override-bar" id="override-bar">
  <span id="override-count"></span>
  <span>수정한 값을 파일로 받아 overrides/ 폴더에 넣고 다시 실행하면 반영됩니다.</span>
  <button class="btn" onclick="downloadOverrides()">오버라이드 파일 다운로드</button>
</div>
<script id="snapshot-data" type="application/json">__SNAPSHOT_JSON__</script>
<script id="settings-data" type="application/json">__SETTINGS_JSON__</script>
<script>
const DATA = JSON.parse(document.getElementById('snapshot-data').textContent);
const SETTINGS = JSON.parse(document.getElementById('settings-data').textContent);
const weekIds = Object.keys(DATA.weeks).sort().reverse();
const sel = document.getElementById('week-select');
weekIds.forEach(w => { const o = document.createElement('option'); o.value = w; o.textContent = w + ' (기준일 ' + DATA.weeks[w].as_of_date + ')'; sel.appendChild(o); });

document.getElementById('set-weekday').value = SETTINGS.as_of_weekday || 'FRI';
document.getElementById('set-date-override').value = SETTINGS.as_of_date_override || '';

const thBody = document.querySelector('#th-table tbody');
Object.entries(SETTINGS.chase_thresholds || {}).forEach(([desc, days]) => {
  const row = document.createElement('tr');
  row.innerHTML = `<td>${esc(desc)}</td><td><input type="number" data-th="${esc(desc)}" value="${days}"> 일</td>`;
  thBody.appendChild(row);
});

function downloadSettings() {
  const chase_thresholds = {};
  thBody.querySelectorAll('input[data-th]').forEach(inp => { chase_thresholds[inp.dataset.th] = parseInt(inp.value, 10); });
  const updated = {
    ...SETTINGS,
    as_of_weekday: document.getElementById('set-weekday').value,
    as_of_date_override: document.getElementById('set-date-override').value || null,
    chase_thresholds,
  };
  const blob = new Blob([JSON.stringify(updated, null, 2)], {type: 'application/json'});
  const a = document.createElement('a');
  a.href = URL.createObjectURL(blob);
  a.download = 'report_settings.json';
  a.click();
}

function pct(done, all) { return all > 0 ? Math.round(done / all * 1000) / 10 : 0; }

function esc(s) {
  return String(s).replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
}

let edits = {}; // key `${season}|${owner}|${stage}` -> {season, stage, owner_type, override_numerator, override_denominator}

function editKey(season, owner, stage) { return `${season}|${owner}|${stage}`; }

function startEdit(season, owner, stage, done, all) {
  const cell = document.getElementById(`cell-${editKey(season, owner, stage)}`);
  cell.innerHTML = `<span class="edit-cell"><input type="number" id="in-done-${editKey(season, owner, stage)}" value="${done}"> / ` +
    `<input type="number" id="in-all-${editKey(season, owner, stage)}" value="${all}"> ` +
    `<button class="btn" onclick="applyEdit('${season}','${owner}','${stage}')">적용</button></span>`;
}

function applyEdit(season, owner, stage) {
  const key = editKey(season, owner, stage);
  const done = parseInt(document.getElementById(`in-done-${key}`).value, 10);
  const all = parseInt(document.getElementById(`in-all-${key}`).value, 10);
  edits[key] = {season, stage, owner_type: owner, override_numerator: done, override_denominator: all};
  render();
  const bar = document.getElementById('override-bar');
  bar.classList.add('show');
  document.getElementById('override-count').textContent = `수정 ${Object.keys(edits).length}건`;
}

function downloadOverrides() {
  const payload = Object.values(edits);
  const blob = new Blob([JSON.stringify(payload, null, 2)], {type: 'application/json'});
  const a = document.createElement('a');
  a.href = URL.createObjectURL(blob);
  a.download = `${sel.value}.json`;
  a.click();
}

function render() {
  const week = DATA.weeks[sel.value];
  if (!week) return;
  const isLatest = sel.value === weekIds[0];
  const container = document.getElementById('seasons');
  container.innerHTML = '';
  for (const season of Object.keys(week.progress).sort()) {
    const title = document.createElement('div');
    title.className = 'season-title';
    title.textContent = season;
    container.appendChild(title);

    const table = document.createElement('table');
    table.innerHTML = `<thead><tr><th>담당</th><th>단계</th><th>총량대비</th><th>기준대비</th>${isLatest ? '<th></th>' : ''}</tr></thead><tbody></tbody>`;
    const tbody = table.querySelector('tbody');
    for (const owner of ['TD', 'QA']) {
      for (const stage of Object.keys(week.progress[season][owner] || {})) {
        let m = week.progress[season][owner][stage];
        const key = editKey(season, owner, stage);
        if (edits[key]) m = {...m, total_done: edits[key].override_numerator, total_all: edits[key].override_denominator};
        const row = document.createElement('tr');
        row.innerHTML = `<td>${esc(owner)}</td><td>${esc(stage)}</td>` +
          `<td id="cell-${key}">${pct(m.total_done, m.total_all)}% (${m.total_done}/${m.total_all})</td>` +
          `<td>${pct(m.baseline_done, m.baseline_all)}% (${m.baseline_done}/${m.baseline_all})</td>` +
          (isLatest ? `<td><button class="btn" onclick="startEdit('${season}','${owner}','${stage}',${m.total_done},${m.total_all})">수정</button></td>` : '');
        tbody.appendChild(row);
      }
    }
    container.appendChild(table);
  }
}

if (weekIds.length) { sel.value = weekIds[0]; render(); }
</script>
</body>
</html>
"""


_SECRET_KEYS = {"supabase_url", "supabase_anon_key"}


def build_report_html(snapshots: dict, settings: dict) -> str:
    snapshot_json = json.dumps(snapshots, ensure_ascii=False).replace("<", "\\u003c")
    public_settings = {k: v for k, v in settings.items() if k not in _SECRET_KEYS}
    settings_json = json.dumps(public_settings, ensure_ascii=False).replace("<", "\\u003c")
    return (_TEMPLATE
            .replace("__SNAPSHOT_JSON__", snapshot_json)
            .replace("__SETTINGS_JSON__", settings_json))
