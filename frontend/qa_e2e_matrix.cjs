/**
 * QA E2E driver — exercises the REAL TactileEd UI end-to-end per fixture.
 * Usage: node qa_e2e_matrix.cjs [fixture|all]
 */
const { chromium } = require('playwright');
const path = require('path');
const fs = require('fs');

const FRONTEND = process.env.QE2E_URL || 'http://localhost:5173';
const FIXTURES_DIR = path.resolve(__dirname, '..', 'backend', 'qa_fixtures');
const OUT_DIR = path.resolve(__dirname, '..', 'data', 'outputs', 'qa');
fs.mkdirSync(OUT_DIR, { recursive: true });

const fixtures = fs.readdirSync(FIXTURES_DIR).filter(f => /\.(png|jpe?g|pdf)$/i.test(f) && !f.startsWith('_')).sort();
const target = process.argv[2] || 'all';
const selected = target === 'all' ? fixtures : fixtures.filter(f => f.includes(target));
const report = { environment: { url: FRONTEND }, fixtures: {} };

async function runFixture(browser, fixture) {
  const entry = { fixture, steps: [], consoleErrors: [], httpFailures: [], downloads: [] };
  const page = await browser.newPage({ viewport: { width: 1440, height: 900 }, acceptDownloads: true });
  page.on('console', msg => { if (msg.type() === 'error') entry.consoleErrors.push(msg.text()); });
  page.on('response', res => {
    if (res.status() >= 400) entry.httpFailures.push(`${res.request().method()} ${res.url()} -> ${res.status()}`);
  });
  const ctxIds = {};

  try {
    await page.goto(FRONTEND, { waitUntil: 'networkidle' });
    const body = await page.textContent('body');
    if (!body.includes('Connected') || body.includes('Offline')) throw new Error('Backend not connected on load');
    entry.steps.push('landing: backend connected');
    await page.screenshot({ path: path.join(OUT_DIR, `${fixture}.01_home.png`) });

    page.once('response', async res => {
      if (res.url().endsWith('/api/projects') && res.request().method() === 'POST') {
        try { const j = await res.json(); ctxIds.projectId = j.id; } catch {}
      }
    });
    page.once('response', async res => {
      if (res.request().method() === 'POST' && /\/pages$/.test(res.url())) {
        try { const j = await res.json(); ctxIds.pageId = j.page_id; } catch {}
      }
    });
    page.on('response', async res => {
      if (res.request().method() === 'POST' && /\/diagrams$/.test(res.url())) {
        try { const j = await res.json(); ctxIds.diagramIds = (j || []).map(d => d.id); } catch {}
      }
    });
    page.on('response', async res => {
      if (res.request().method() === 'POST' && /\/workflow$/.test(res.url())) {
        try { const j = await res.json(); ctxIds.diagramId = j.id; } catch {}
      }
    });

    // New tabbed landing: enter the workspace before uploading.
    // Wait for the hero button (the landing re-renders once /health resolves),
    // click it, then verify the file input actually mounts; fall back to the
    // header "Workspace" tab if not.
    let fileInput = await page.$('input[type="file"]');
    if (!fileInput) {
      const openWs = await page.waitForSelector('button:has-text("Open Workspace")', { timeout: 20000 }).catch(() => null);
      if (openWs) {
        await page.waitForTimeout(1500); // let post-health re-render settle
        await openWs.click().catch(() => {});
        entry.steps.push('navigation: clicked Open Workspace');
      }
      await page.waitForSelector('input[type="file"]', { state: 'attached', timeout: 15000 }).catch(() => {});
      if (!(await page.$('input[type="file"]'))) {
        await page.click('text=Workspace').catch(() => {});
        entry.steps.push('navigation: clicked Workspace tab (fallback)');
        await page.waitForSelector('input[type="file"]', { state: 'attached', timeout: 30000 });
      }
      entry.steps.push('navigation: workspace opened');
    }

    await page.setInputFiles('input[type="file"]', path.join(FIXTURES_DIR, fixture));
    entry.steps.push('upload: file selected');
    await page.click('text=Start Extraction Pipeline');
    try {
      await page.waitForSelector('text=Detected Regions', { timeout: 60000 });
      entry.steps.push('process: region editor appeared');
    } catch (e) {
      const t = await page.textContent('body');
      entry.steps.push(`process: FAILED - ${t.match(/Status: [^\n]*/)?.[0] || 'no region editor'}`);
      entry.failure = t.slice(0, 500);
      return entry;
    }
    await page.screenshot({ path: path.join(OUT_DIR, `${fixture}.02_detection.png`) });

    const acceptBtn = await page.$('button:has-text("Accept")');
    if (acceptBtn) {
      await acceptBtn.click();
      await page.waitForTimeout(500);
      entry.steps.push('detection: candidate accepted');
      const editBtn = await page.waitForSelector('button:has-text("Process & Edit")', { timeout: 15000 });
      await editBtn.click();
    } else {
      entry.steps.push('detection: NO candidates to accept — cannot proceed');
      entry.failure = 'no candidates';
      return entry;
    }

    await page.waitForSelector('text=Pipeline', { timeout: 60000 }).catch(() => {});
    // wait for the editor to render element/label stats (network + cold start)
    // wait for the editor to load actual content (nonzero elements); blank
    // fixtures legitimately stay at 0, so swallow the timeout for those.
    await page.waitForFunction(() => /([1-9]\d*) elm/.test(document.body.innerText), { timeout: 90000 }).catch(() => {});
    const editorBody = await page.textContent('body');
    entry.editor = {
      elements: editorBody.match(/(\d+) elm/)?.[1],
      labels: editorBody.match(/(\d+) lbl/)?.[1],
    };
    entry.steps.push(`editor: rendered with ${entry.editor.elements} elements, ${entry.editor.labels} labels`);
    await page.screenshot({ path: path.join(OUT_DIR, `${fixture}.03_editor.png`) });

    if (editorBody.includes('Workflow error')) {
      entry.steps.push('editor: WORKFLOW ERROR PRESENT');
      entry.failure = editorBody.match(/Workflow error: [^\n]*/)?.[0];
      return entry;
    }
    return entry;
  } catch (err) {
    entry.exception = err.message;
    const t = await page.textContent('body').catch(() => '');
    entry.failure = (entry.failure || '') + ' | ' + err.message + ' | body: ' + t.slice(0, 400);
    return entry;
  } finally {
    await page.close();
  }
}

(async () => {
  const browser = await chromium.launch({ headless: true });
  for (const fixture of selected) {
    console.log(`\n=============== ${fixture} ===============`);
    report.fixtures[fixture] = await runFixture(browser, fixture);
    const e = report.fixtures[fixture];
    console.log('steps:', e.steps?.join(' | '));
    if (e.failure) console.log('FAILURE:', e.failure);
    if (e.editor) console.log('editor elements/labels:', e.editor.elements, '/', e.editor.labels);
    if (e.consoleErrors?.length) console.log('console errors:', e.consoleErrors.length, e.consoleErrors.slice(0, 3));
    if (e.httpFailures?.length) console.log('http failures:', e.httpFailures.slice(0, 3));
  }
  await browser.close();
  fs.writeFileSync(path.join(OUT_DIR, 'report.json'), JSON.stringify(report, null, 2));
  console.log('\nReport saved to', path.join(OUT_DIR, 'report.json'));
})();