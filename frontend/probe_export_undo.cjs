/**
 * Probe: why does Export SVG produce no download after an undo?
 */
const { chromium } = require('playwright');
const path = require('path');

(async () => {
  const browser = await chromium.launch({ headless: true });
  const page = await browser.newPage({ viewport: { width: 1440, height: 900 } });
  page.on('console', m => console.log('[console]', m.type(), m.text().slice(0, 200)));
  page.on('request', r => { if (r.url().includes('/export/')) console.log('>>> export request fired:', r.method(), r.url()); });
  page.on('response', r => { if (r.url().includes('/export/') || r.url().includes('/labels') && r.request().method() === 'PUT') console.log('<<<', r.status(), r.request().method(), r.url().split('/api/')[1]); });
  page.on('pageerror', e => console.log('[pageerror]', e.message));

  await page.goto('http://localhost:5173', { waitUntil: 'networkidle' });
  await page.setInputFiles('input[type="file"]', path.resolve(__dirname, '..', 'backend', 'qa_fixtures', '02_complex_biology.png'));
  await page.click('text=Process Page');
  await page.waitForSelector('text=Region Editor', { timeout: 20000 });
  await page.click('button:has-text("✓")');
  await page.click('text=Process & Edit ➔');
  await page.waitForSelector('text=Pipeline', { timeout: 30000 }).catch(() => {});
  await page.waitForTimeout(8000);

  const labelRect = page.locator('svg g[data-type="label"]').first().locator('rect');
  await labelRect.click({ force: true });
  await page.waitForSelector('#label-text-input', { timeout: 5000 });

  // Edit text
  await page.fill('#label-text-input', 'Heart Corrected');
  await page.click('button:has-text("Save Text")');
  await page.waitForTimeout(2500);

  // Export #1 (should work)
  console.log('--- EXPORT 1 ---');
  await page.click('button:has-text("Export SVG")');
  const d1 = await page.waitForEvent('download', { timeout: 10000 }).catch(() => null);
  console.log('download1:', !!d1, '| status:', await page.textContent('[role="status"]').catch(() => '?'));

  // Undo
  console.log('--- UNDO ---');
  await page.keyboard.press('Meta+z');
  await page.waitForTimeout(2000);
  console.log('status after undo:', await page.textContent('[role="status"]').catch(() => '?'));
  console.log('body has "All changes saved":', (await page.textContent('body')).includes('All changes saved'));

  // Export #2
  console.log('--- EXPORT 2 (after undo) ---');
  await page.click('button:has-text("Export SVG")');
  const d2 = await page.waitForEvent('download', { timeout: 10000 }).catch(() => null);
  console.log('download2:', !!d2, '| status:', await page.textContent('[role="status"]').catch(() => '?'));
  if (!d2) {
    await page.screenshot({ path: '/tmp/probe_export_fail.png' });
    console.log('body snapshot:', (await page.textContent('body')).slice(0, 300));
  }
  await browser.close();
})();
