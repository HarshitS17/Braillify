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
    if (!body.includes('Backend connected')) throw new Error('Backend not connected on load');
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

    await page.setInputFiles('input[type="file"]', path.join(FIXTURES_DIR, fixture));
    entry.steps.push('upload: file selected');
    await page.click('text=Process Page');
    try {
      await page.waitForSelector('text=Region Editor', { timeout: 20000 });
      entry.steps.push('process: region editor appeared');
    } catch (e) {
      const t = await page.textContent('body');
      entry.steps.push(`process: FAILED - ${t.match(/Status: [^\n]*/)?.[0] || 'no region editor'}`);
      entry.failure = t.slice(0, 500);
      return entry;
    }
    await page.screenshot({ path: path.join(OUT_DIR, `${fixture}.02_detection.png`) });

    const acceptBtn = await page.$('button:has-text("✓")');
    if (acceptBtn) {
      await acceptBtn.click();
      entry.steps.push('detection: candidate accepted');
      await page.click('text=Process & Edit ➔');
    } else {
      entry.steps.push('detection: NO candidates to accept — cannot proceed');
      entry.failure = 'no candidates';
      return entry;
    }

    await page.waitForSelector('text=Pipeline', { timeout: 30000 }).catch(() => {});
    await page.waitForTimeout(8000);
    const editorBody = await page.textContent('body');
    entry.editor = {
      elements: editorBody.match(/(\d+) elements/)?.[1],
      labels: editorBody.match(/(\d+) labels/)?.[1],
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