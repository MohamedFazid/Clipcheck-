"""WCAG 2.1 contrast audit of the FINAL interface (v4, frozen 2026-09-27 19:59), on the same ten screens as the v3 audit (findings.md):
(Copied into the repository on 2026-09-28 from Final Report/figures/src/, where the report build keeps the original.)
Check a video; results partly manipulated, unfamiliar, no verdict; the four Details tabs; History; Accuracy. The landing page is measured
separately.

    /opt/anaconda3/bin/python scripts/contrast_audit.py

Method: every visible element that directly holds text is measured. Text colour is the computed colour; a gradient label (background-clip:
text) is measured at its lower-contrast gradient stop. The background is found by compositing the computed background colours of the element
and its ancestors (alpha blending) over the page's base colour; background images, blur and the decorative pixel field are ignored, so
translucent panels are measured against the dark base they sit on. Ratio per WCAG 2.1: (L1 + 0.05) / (L2 + 0.05). Reported: elements below
4.5:1 (the strict criterion used for v1 to v3), and elements failing AA (large text, at least 24 px or 18.66 px bold, needs 3:1).
Creates its own analysis jobs and deletes only those. Output: results/ui_contrast_v4_final.json in the project.
"""
import json
import time
from datetime import datetime
from pathlib import Path

import requests
from playwright.sync_api import sync_playwright

BASE = 'http://localhost:8000'
MDD = Path(__file__).resolve().parent.parent   # the repository root
NOFACE = MDD / 'docs' / 'user_testing' / 'materials' / 'noface_silent.mp4'
OUT = MDD / 'results' / 'ui_contrast_v4_final.json'

MEASURE = r"""() => {
  const parse = s => { const m = s.match(/rgba?\(([^)]+)\)/); if (!m) return null;
    const p = m[1].split(',').map(x => parseFloat(x)); return [p[0], p[1], p[2], p.length > 3 ? p[3] : 1]; };
  const over = (top, bot) => { const a = top[3]; return [0,1,2].map(i => top[i] * a + bot[i] * (1 - a)).concat([1]); };
  const lum = c => { const f = v => { v /= 255; return v <= 0.03928 ? v / 12.92 : Math.pow((v + 0.055) / 1.055, 2.4); };
    return 0.2126 * f(c[0]) + 0.7152 * f(c[1]) + 0.0722 * f(c[2]); };
  const ratio = (a, b) => { const x = lum(a), y = lum(b); return (Math.max(x, y) + 0.05) / (Math.min(x, y) + 0.05); };
  const base = parse(getComputedStyle(document.body).backgroundColor) || [0, 0, 0, 1];
  const baseOpaque = base[3] < 1 ? over(base, [255, 255, 255, 1]) : base;
  const bgOf = el => { const chain = []; for (let e = el; e && e.nodeType === 1; e = e.parentElement) chain.push(e);
    let c = baseOpaque; for (const e of chain.reverse()) { const b = parse(getComputedStyle(e).backgroundColor); if (b && b[3] > 0) c = over(b, c); }
    return c; };
  const out = [];
  for (const el of document.querySelectorAll('body *')) {
    const own = [...el.childNodes].some(n => n.nodeType === 3 && n.textContent.trim());
    if (!own) continue;
    const cs = getComputedStyle(el), r = el.getBoundingClientRect();
    if (cs.visibility === 'hidden' || cs.display === 'none' || r.width < 1 || r.height < 1 || parseFloat(cs.opacity) === 0) continue;
    let hidden = false; for (let e = el; e; e = e.parentElement) { const s = getComputedStyle(e);
      if (s.display === 'none' || s.visibility === 'hidden' || parseFloat(s.opacity) === 0 || e.hasAttribute('hidden')) { hidden = true; break; } }
    if (hidden) continue;
    const bg = bgOf(el);
    let fgs = [];
    const col = parse(cs.color);
    if ((cs.backgroundClip === 'text' || cs.webkitBackgroundClip === 'text') && (!col || col[3] === 0)) {
      fgs = (cs.backgroundImage.match(/rgba?\([^)]+\)/g) || []).map(parse).filter(Boolean).map(c => over(c, bg));
    } else if (col) fgs = [over(col, bg)];
    if (!fgs.length) continue;
    const rs = fgs.map(f => ratio(f, bg)), worst = Math.min(...rs);
    const size = parseFloat(cs.fontSize), bold = parseInt(cs.fontWeight) >= 700;
    const large = size >= 24 || (bold && size >= 18.66);
    out.push({ text: el.textContent.trim().slice(0, 60), tag: el.tagName, cls: String(el.className).slice(0, 40), size, large,
               ratio: Math.round(worst * 100) / 100 });
  }
  return out;
}"""


def make_job(name):
    if name == 'upload:noface':
        with open(NOFACE, 'rb') as f:
            job = requests.post(f'{BASE}/api/upload', files={'file': ('noface_silent.mp4', f, 'video/mp4')}).json()
    else:
        demos = {d['name']: d['demo_id'] for d in requests.get(f'{BASE}/api/demo_clips').json()}
        job = requests.post(f'{BASE}/api/demo/{demos[name]}').json()
    requests.post(f'{BASE}/api/analyze/{job["id"]}')
    for _ in range(240):
        if requests.get(f'{BASE}/api/result/{job["id"]}').status_code == 200:
            return job['id']
        time.sleep(1)
    raise SystemExit('analysis did not finish')


def main():
    jobs = {}
    screens = {}
    try:
        for state, name in (('partial', 'FVRA_000.mp4'), ('unfamiliar', 'LAVDF_RVRA_000.mp4'), ('no_verdict', 'upload:noface')):
            jobs[state] = make_job(name)
        with sync_playwright() as p:
            br = p.chromium.launch(channel='chrome')
            pg = br.new_context(viewport={'width': 1440, 'height': 900}, reduced_motion='reduce').new_page()

            def measure(key, url, before=None, wait=2000):
                pg.goto(f'{BASE}/{url}'); pg.wait_for_load_state('networkidle'); pg.wait_for_timeout(wait)
                if before:
                    before()
                screens[key] = pg.evaluate(MEASURE)

            measure('check', '#/check')
            measure('result_partial', f'#/result/{jobs["partial"]}')
            measure('result_unfamiliar', f'#/result/{jobs["unfamiliar"]}')
            measure('result_no_verdict', f'#/result/{jobs["no_verdict"]}')
            for tab in ('findings', 'technical', 'limits', 'glossary'):
                def open_tab(tab=tab):
                    if pg.locator('#sheet').count() == 0:
                        pg.click('#btn-details'); pg.wait_for_timeout(700)
                    pg.click(f'#sheet [data-tab="{tab}"]'); pg.wait_for_timeout(700)
                measure(f'details_{tab}', f'#/result/{jobs["partial"]}', before=open_tab)
            measure('history', '#/history')
            measure('accuracy', '#/accuracy')

            def scroll_all():
                for _ in range(40):
                    pg.mouse.wheel(0, 900); pg.wait_for_timeout(80)
            measure('landing', '', before=scroll_all, wait=3000)
            br.close()
    finally:
        for j in jobs.values():
            requests.delete(f'{BASE}/api/queue/{j}')
    app = {k: v for k, v in screens.items() if k != 'landing'}
    summary = {}
    for group, data in (('app_ten_screens', app), ('landing', {'landing': screens['landing']})):
        els = [e for v in data.values() for e in v]
        below45 = [e for e in els if e['ratio'] < 4.5]
        fail_aa = [e for e in els if e['ratio'] < (3.0 if e['large'] else 4.5)]
        summary[group] = {'elements': len(els), 'per_screen': {k: len(v) for k, v in data.items()},
                          'below_4_5': len(below45), 'fail_wcag_aa': len(fail_aa),
                          'lowest_ratio': min((e['ratio'] for e in els), default=None),
                          'below_4_5_examples': sorted(below45, key=lambda e: e['ratio'])[:12]}
    OUT.write_text(json.dumps({'interface': 'v4 final (ui_v4_final_snapshot, frozen 2026-09-27 19:59)',
                               'measured_at': datetime.now().astimezone().isoformat(timespec='seconds'),
                               'method': __doc__.split('Method: ')[1].split('Creates its own')[0].strip(),
                               'summary': summary, 'screens': screens}, indent=1))
    print(json.dumps({k: {x: v[x] for x in ('elements', 'below_4_5', 'fail_wcag_aa', 'lowest_ratio', 'per_screen')} for k, v in summary.items()}, indent=1))
    for k, v in summary.items():
        for e in v['below_4_5_examples']:
            print(k, e['ratio'], e['size'], e['large'], e['tag'], e['cls'], '|', e['text'])


if __name__ == '__main__':
    main()
