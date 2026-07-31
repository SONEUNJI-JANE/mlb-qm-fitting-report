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
table{width:100%;border-collapse:collapse;background:#fff;border-radius:8px;overflow:hidden;margin-bottom:16px}
th,td{padding:8px 10px;border-bottom:1px solid #eee;text-align:left;font-size:12px}
th{background:#f8f9fa;color:#555}
.season-title{font-weight:700;font-size:15px;margin:20px 0 8px;padding-bottom:4px;border-bottom:2px solid #1a1a2e}
.season-title:first-child{margin-top:0}
</style>
</head>
<body>
<div class="hdr">
  <h1>MLB QM Fitting 주간 보고</h1>
  <select id="week-select" onchange="render()"></select>
</div>
<div class="content" id="seasons"></div>
<script id="snapshot-data" type="application/json">__SNAPSHOT_JSON__</script>
<script>
const DATA = JSON.parse(document.getElementById('snapshot-data').textContent);
const weekIds = Object.keys(DATA.weeks).sort().reverse();
const sel = document.getElementById('week-select');
weekIds.forEach(w => { const o = document.createElement('option'); o.value = w; o.textContent = w + ' (기준일 ' + DATA.weeks[w].as_of_date + ')'; sel.appendChild(o); });

function pct(done, all) { return all > 0 ? Math.round(done / all * 1000) / 10 : 0; }

function esc(s) {
  return String(s).replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
}

function render() {
  const week = DATA.weeks[sel.value];
  if (!week) return;
  const container = document.getElementById('seasons');
  container.innerHTML = '';
  for (const season of Object.keys(week.progress).sort()) {
    const title = document.createElement('div');
    title.className = 'season-title';
    title.textContent = season;
    container.appendChild(title);

    const table = document.createElement('table');
    table.innerHTML = '<thead><tr><th>담당</th><th>단계</th><th>총량대비</th><th>기준대비</th></tr></thead><tbody></tbody>';
    const tbody = table.querySelector('tbody');
    for (const owner of ['TD', 'QA']) {
      for (const stage of Object.keys(week.progress[season][owner] || {})) {
        const m = week.progress[season][owner][stage];
        const row = document.createElement('tr');
        row.innerHTML = `<td>${esc(owner)}</td><td>${esc(stage)}</td>` +
          `<td>${pct(m.total_done, m.total_all)}% (${m.total_done}/${m.total_all})</td>` +
          `<td>${pct(m.baseline_done, m.baseline_all)}% (${m.baseline_done}/${m.baseline_all})</td>`;
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


def build_report_html(snapshots: dict) -> str:
    snapshot_json = json.dumps(snapshots, ensure_ascii=False).replace("<", "\\u003c")
    return _TEMPLATE.replace("__SNAPSHOT_JSON__", snapshot_json)
