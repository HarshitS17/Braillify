/** Probe: what happens when a .txt is uploaded through the UI? */
const { chromium } = require('playwright');
const path = require('path');
(async () => {
  const browser = await chromium.launch({ headless: true });
  const page = await browser.newPage();
  page.on('console', m => console.log('[console]', m.type(), m.text().slice(0, 150)));
  page.on('response', r => { if (r.url().includes('/api/')) console.log('<<', r.status(), r.request().method(), r.url().split('/api/')[1]); });
  page.on('requestfailed', r => console.log('XX FAILED', r.url(), r.failure()?.errorText));
  await page.goto('http://localhost:5173', { waitUntil: 'networkidle' });
  await page.setInputFiles('input[type="file"]', path.resolve(__dirname, '..', 'backend', 'qa_fixtures', '10_not_an_image.txt'));
  await page.waitForTimeout(800);
  console.log('status after select:', await page.textContent('[data-testid="status"]',).catch(() => '(no status testid)'));
  const btn = await page.$('button:has-text("Process Page")');
  console.log('Process button present:', !!btn, '| disabled:', btn ? await btn.isDisabled() : '-');
  if (btn && !(await btn.isDisabled())) {
    await btn.click();
    await page.waitForTimeout(2500);
  }
  console.log('body status line:', (await page.textContent('body')).match(/Status:[^\n]*/)?.[0]);
  await page.screenshot({ path: '/tmp/txt_upload.png' });
  await browser.close();
})();
