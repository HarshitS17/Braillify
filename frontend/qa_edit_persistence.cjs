/**
 * QA E2E: Human-in-the-loop persistence test (THE critical acceptance test).
 * Real UI: edit label text -> drag label -> delete element -> undo/redo ->
 * validate -> export SVG/PDF -> verify edits survive export & reload.
 * Usage: node qa_edit_persistence.cjs [fixture-name-substring]
 */
const { chromium } = require('playwright');
const path = require('path');
const fs = require('fs');

const FRONTEND = process.env.QE2E_URL || 'http://localhost:5173';
const FIXTURES_DIR = path.resolve(__dirname, '..', 'backend', 'qa_fixtures');
const OUT_DIR = path.resolve(__dirname, '..', 'data', 'outputs', 'qa');
fs.mkdirSync(OUT_DIR, { recursive: true });

const fixture = fs.readdirSync(FIXTURES_DIR)
  .filter(f => /\.(png|jpe?g)$/i.test(f) && !f.startsWith('_'))
  .find(f => f.includes(process.argv[2] || '02_complex'));
if (!fixture) throw new Error('fixture not found');
console.log('fixture:', fixture);

const report = { fixture, steps: [], consoleErrors: [], httpFailures: [], failures: [], pass: true };
const step = (s) => { report.steps.push(s); console.log('STEP:', s); };
const fail = (s) => { report.failures.push(s); report.pass = false; console.log('FAIL:', s); };
const ok = (cond, s) => cond ? step('OK: ' + s) : fail(s);
const shot = (page, name) => page.screenshot({ path: path.join(OUT_DIR, `edit.${name}.png`) });

async function waitSaved(page, timeout = 8000) {
  try {
    await page.waitForFunction(() => {
      const t = document.body.innerText;
      return t.includes('All changes saved') || t.includes('Save failed');
    }, { timeout });
    const saved = await page.evaluate(() => document.body.innerText.includes('All changes saved'));
    if (!saved) {
      const snap = await page.evaluate(() => document.body.innerText.slice(0, 700));
      fail('save indicator: Save failed after action. body: ' + snap.replace(/\n/g, ' | '));
    }
    return saved;
  } catch { fail('save indicator never reached terminal state'); return false; }
}
const getPanelLabelText = (page) => page.$eval('#label-text-input', el => el.value).catch(() => null);
async function getPanelBraille(page) {
  return page.evaluate(() => {
    // Braille text renders in the panel as U+2800..U+28FF glyphs.
    const el = [...document.querySelectorAll('.text-lg')]
      .find(n => /[\u2800-\u28FF]/.test(n.textContent || ''));
    return el ? el.textContent.trim() : null;
  });
}
async function getPanelPos(page) {
  return page.evaluate(() => {
    const m = document.body.innerText.match(/x: ([\d.]+), y: ([\d.]+)/);
    return m ? { x: parseFloat(m[1]), y: parseFloat(m[2]) } : null;
  });
}
async function getCounts(page) {
  return page.evaluate(() => {
    const m = document.body.innerText.match(/(\d+) elements[\s\S]*?(\d+) labels/);
    return m ? { elements: +m[1], labels: +m[2] } : null;
  });
}

(async () => {
  const browser = await chromium.launch({ headless: true });
  const page = await browser.newPage({ viewport: { width: 1440, height: 900 }, acceptDownloads: true });
  page.on('console', msg => { if (msg.type() === 'error') report.consoleErrors.push(msg.text()); });
  page.on('pageerror', err => report.consoleErrors.push('PAGEERROR: ' + err.message));
  page.on('requestfailed', req => report.httpFailures.push(`FAILED ${req.method()} ${req.url()} :: ${req.failure()?.errorText}`));
  page.on('response', res => {
    if (res.status() >= 400) report.httpFailures.push(`${res.request().method()} ${res.url()} -> ${res.status()}`);
  });
  const ids = {};
  page.on('response', async res => {
    try {
      if (res.request().method() === 'POST' && /\/api\/projects$/.test(res.url())) ids.projectId = (await res.json()).id;
      if (res.request().method() === 'POST' && /\/pages$/.test(res.url())) ids.pageId = (await res.json()).page_id;
      if (res.request().method() === 'POST' && /\/workflow$/.test(res.url())) ids.diagramId = (await res.json()).id;
    } catch {}
  });

  const saveSvg = async (name) => {
    // Register the download listener BEFORE clicking: the download event can
    // fire before a post-click waitForEvent() attaches (race → missed event).
    const dlPromise = page.waitForEvent('download', { timeout: 15000 }).catch(() => null);
    await page.click('button:has-text("Export SVG")');
    const dl = await dlPromise;
    if (dl) await dl.saveAs(path.join(OUT_DIR, name));
    return dl ? fs.readFileSync(path.join(OUT_DIR, name), 'utf8') : null;
  };

  try {
    await page.goto(FRONTEND, { waitUntil: 'networkidle' });
    ok((await page.textContent('body')).includes('Backend connected'), 'landing: backend connected');

    await page.setInputFiles('input[type="file"]', path.join(FIXTURES_DIR, fixture));
    await page.click('text=Process Page');
    await page.waitForSelector('text=Region Editor', { timeout: 20000 });
    step('process: region editor appeared');

    const acceptBtn = await page.$('button:has-text("✓")');
    ok(!!acceptBtn, 'detection: candidate found');
    await acceptBtn.click();
    await page.click('text=Process & Edit ➔');
    await page.waitForSelector('text=Pipeline', { timeout: 30000 }).catch(() => {});
    await page.waitForTimeout(8000);
    const counts0 = await getCounts(page);
    ok(!!counts0 && counts0.labels >= 1, `editor rendered: ${JSON.stringify(counts0)}`);
    await shot(page, '01_editor_initial');

    const labelRect = page.locator('svg g[data-type="label"]').first().locator('rect');
    await labelRect.click({ force: true });
    await page.waitForSelector('#label-text-input', { timeout: 5000 });
    const T0 = await getPanelLabelText(page);
    const B0 = await getPanelBraille(page);
    const P0 = await getPanelPos(page);
    ok(!!T0 && !!B0 && !!P0, `label selected: text=${JSON.stringify(T0)} braille=${B0} pos=(${P0.x},${P0.y})`);

    const svg0 = await saveSvg('edit.svg_baseline.svg');
    ok(!!svg0 && svg0.includes(B0), 'baseline SVG export contains original braille');
    await waitSaved(page);

    // ---- EDIT 1: correct label text via PropertiesPanel ----
    await page.fill('#label-text-input', 'Heart Corrected');
    await page.click('button:has-text("Save Text")');
    await page.waitForFunction(() => document.body.innerText.includes('Label updated'), { timeout: 8000 }).catch(() => {});
    const saved1 = await waitSaved(page);
    const T1 = await getPanelLabelText(page);
    const B1 = await getPanelBraille(page);
    ok(saved1 && T1 === 'Heart Corrected', `text edit applied+saved: ${JSON.stringify(T1)}`);
    ok(!!B1 && B1 !== B0, `braille re-translated in UI: ${B0} -> ${B1}`);
    await shot(page, '02_text_edited');

    // ---- EDIT 2: drag label on canvas ----
    const bb = await labelRect.boundingBox();
    await page.mouse.move(bb.x + bb.width / 2, bb.y + bb.height / 2);
    await page.mouse.down();
    await page.mouse.move(bb.x + bb.width / 2 + 60, bb.y + bb.height / 2 + 45, { steps: 8 });
    await page.mouse.up();
    await page.waitForTimeout(300);
    const saved2 = await waitSaved(page);
    const P1 = await getPanelPos(page);
    ok(saved2 && P1 && (Math.abs(P1.x - P0.x) > 20 || Math.abs(P1.y - P0.y) > 20),
       `drag moved label: (${P0.x},${P0.y}) -> (${P1 && P1.x},${P1 && P1.y})`);
    await shot(page, '03_dragged');

    // ---- Export after edits: edits MUST be in the SVG ----
    const svg1 = await saveSvg('edit.svg_after_edits.svg');
    ok(!!svg1 && svg1.includes(B1), 'EDIT SURVIVED EXPORT: corrected braille in SVG');
    ok(!!svg1 && svg1 !== svg0, 'SVG changed after edits');
    await shot(page, '04_after_export');

    // ---- UNDO #1 (Cmd+Z): undoes the most recent mutation = the DRAG ----
    await page.keyboard.press('Meta+z');
    await page.waitForTimeout(400);
    const saved3 = await waitSaved(page);
    const P2 = await getPanelPos(page);
    const T2a = await getPanelLabelText(page);
    ok(saved3 && T2a === 'Heart Corrected' && P2 && Math.abs(P2.x - P0.x) < 1 && Math.abs(P2.y - P0.y) < 1,
       `undo #1 reverts drag (position back to ${P2 && P2.x},${P2 && P2.y}), text kept: ${JSON.stringify(T2a)}`);
    const svg2a = await saveSvg('edit.svg_after_undo1.svg');
    ok(!!svg2a && svg2a.includes(B1), 'undo #1 export keeps corrected braille');

    // ---- UNDO #2: undoes the TEXT edit ----
    await page.keyboard.press('Meta+z');
    await page.waitForTimeout(400);
    await waitSaved(page);
    const T2 = await getPanelLabelText(page);
    const B2 = await getPanelBraille(page);
    ok(T2 === T0, `undo #2 restored text: ${JSON.stringify(T2)}`);
    ok(B2 === B0, `undo #2 restored braille: ${B2}`);
    const svg2 = await saveSvg('edit.svg_after_undo2.svg');
    ok(!!svg2 && svg2.includes(B0) && !svg2.includes(B1), 'UNDO SURVIVED EXPORT: original braille back, corrected gone');
    await shot(page, '05_after_undo');

    // ---- REDO (Cmd+Shift+Z): re-applies the TEXT edit ----
    await page.keyboard.press('Meta+Shift+z');
    await page.waitForTimeout(400);
    await waitSaved(page);
    const T3 = await getPanelLabelText(page);
    ok(T3 === 'Heart Corrected', `redo re-applied text: ${JSON.stringify(T3)}`);

    // ---- ELEMENT delete + undo + redo ----
    const countsA = await getCounts(page);
    await page.locator('svg > line, svg > circle, svg > polygon, svg > polyline').first().click({ force: true });
    await page.click('button:has-text("Delete Element")');
    const saved4 = await waitSaved(page);
    const countsB = await getCounts(page);
    ok(saved4 && countsB.elements === countsA.elements - 1, `element deleted & persisted: ${countsA.elements} -> ${countsB.elements}`);
    await page.keyboard.press('Meta+z');
    await page.waitForTimeout(300);
    await waitSaved(page);
    const countsC = await getCounts(page);
    ok(countsC.elements === countsA.elements, `undo restored element: ${countsC.elements}`);
    await page.keyboard.press('Meta+Shift+z');
    await page.waitForTimeout(300);
    await waitSaved(page);
    const countsD = await getCounts(page);
    ok(countsD.elements === countsA.elements - 1, `redo re-deleted element: ${countsD.elements}`);
    await page.keyboard.press('Meta+z'); // final state keeps the element
    await page.waitForTimeout(300);
    await waitSaved(page);
    await shot(page, '06_element_edits');

    // ---- Validation through UI ----
    await page.click('button:has-text("Validat")');
    await page.waitForFunction(() =>
      document.body.innerText.includes('Validation passed') ||
      /issue\(s\) found/.test(document.body.innerText) ||
      document.body.innerText.includes('Validation failed'), { timeout: 15000 });
    const vText = await page.evaluate(() => {
      const t = document.body.innerText;
      return (t.match(/\d+ issue\(s\) found/) || [t.includes('Validation passed') ? 'Validation passed' : 'Validation failed'])[0];
    });
    step(`validation result: ${vText}`);
    await shot(page, '07_validation');

    // ---- PDF export through UI ----
    const dlPdfPromise = page.waitForEvent('download', { timeout: 20000 }).catch(() => null);
    await page.click('button:has-text("Export PDF")');
    const dlPdf = await dlPdfPromise;
    ok(!!dlPdf, 'PDF export via UI');
    const pdfPath = path.join(OUT_DIR, 'edit.final.pdf');
    if (dlPdf) await dlPdf.saveAs(pdfPath);
    const pdfHead = fs.readFileSync(pdfPath).slice(0, 5).toString();
    ok(pdfHead === '%PDF-', `PDF valid header: ${pdfHead}, ${fs.statSync(pdfPath).size} bytes`);

    // ---- RELOAD persistence ----
    await page.reload({ waitUntil: 'networkidle' });
    step('page reloaded (app resets to landing — no project-reopen UI: documented gap)');
    const persisted = await page.evaluate(async ({ pid, pgid, did }) => {
      const r = await fetch(`/api/projects/${pid}/pages/${pgid}/diagrams/${did}/labels`);
      if (!r.ok) return { error: r.status };
      return r.json();
    }, { pid: ids.projectId, pgid: ids.pageId, did: ids.diagramId });
    if (persisted.error) {
      fail('reload persistence fetch failed: ' + persisted.error);
    } else {
      const pl = (persisted || []).find(l => l.text === 'Heart Corrected');
      ok(!!pl, 'RELOAD PERSISTENCE: corrected text in backend after refresh');
      if (pl && pl.placement && P2) {
        ok(Math.abs(pl.placement.position.x - P2.x) < 1 && Math.abs(pl.placement.position.y - P2.y) < 1,
           `RELOAD PERSISTENCE: final position persisted (${pl.placement.position.x.toFixed(1)},${pl.placement.position.y.toFixed(1)})`);
      }
      if (pl) ok(pl.braille && pl.braille.braille_unicode === B1, 'RELOAD PERSISTENCE: re-translated braille persisted');
    }
  } catch (err) {
    fail('exception: ' + err.message);
    await shot(page, '99_exception').catch(() => {});
  } finally {
    await shot(page, '08_final').catch(() => {});
    await page.close();
    await browser.close();
  }

  console.log('\n===== SUMMARY =====');
  console.log('PASS:', report.pass);
  console.log('steps:', report.steps.length, '| failures:', report.failures.length);
  if (report.failures.length) console.log('failures:', report.failures);
  console.log('console errors:', report.consoleErrors.length, report.consoleErrors.slice(0, 5));
  console.log('http failures:', report.httpFailures.length, report.httpFailures.slice(0, 5));
  fs.writeFileSync(path.join(OUT_DIR, 'edit_persistence_report.json'), JSON.stringify(report, null, 2));
  process.exit(report.pass && report.consoleErrors.length === 0 ? 0 : 1);
})();



