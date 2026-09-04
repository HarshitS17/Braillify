/** Probe: PDF fixture detection candidates + accept button actionability. */
const { chromium } = require('playwright');
const path = require('path');

(async () => {
  const browser = await chromium.launch({ headless: true });
  const page = await browser.newPage({ viewport: { width: 1440, height: 900 } });
  page.on('console', m => { if (m.type() === 'error') console.log('[console.error]', m.text().slice(0, 200)); });
  page.on('response', r => { if (r.status() >= 400) console.log('[http]', r.status(), r.request().method(), r.url().split('/api/')[1]); });

  await page.goto('http://localhost:5173', { waitUntil: 'networkidle' });
  await page.setInputFiles('input[type="file"]', path.resolve(__dirname, '..', 'backend', 'qa_fixtures', '09_textbook_page.pdf'));
  await page.click('text=Process Page');
  await page.waitForSelector('text=Region Editor', { timeout: 20000 });
  await page.waitForTimeout(1500);

  const btns = await page.$$eval('button', els => els.map(e => ({
    text: e.textContent.trim().slice(0, 30), visible: !!(e.offsetParent || e.getClientRects().length),
    box: (() => { const b = e.getBoundingClientRect(); return [b.x, b.y, b.width, b.height].map(v => Math.round(v)); })(),
  })));
  console.log('buttons:', JSON.stringify(btns.filter(b => b.text.includes('✓') || b.text.includes('Accept') || b.text.includes('Reject')), null, 1));

  const bodyText = await page.textContent('body');
  const candMatch = bodyText.match(/\d+ candidate\(s\)/);
  console.log('candidate summary:', candMatch ? candMatch[0] : 'no candidate text found');
  console.log('has Region Editor heading:', bodyText.includes('Region Editor'));
  console.log('body excerpt:', bodyText.replace(/\s+/g, ' ').slice(0, 400));

  await page.screenshot({ path: '/tmp/pdf_region_editor.png', fullPage: false });

  // Try clicking via locator (auto-retry, avoids stale elementHandle)
  const accept = page.locator('button:has-text("✓")').first();
  const cnt = await accept.count();
  console.log('accept button count:', cnt);
  if (cnt) {
    try {
      await accept.click({ timeout: 8000 });
      console.log('locator click OK');
      await page.click('text=Process & Edit ➔');
      await page.waitForSelector('text=Pipeline', { timeout: 30000 }).catch(() => {});
      await page.waitForTimeout(8000);
      const t = await page.textContent('body');
      console.log('after accept:', t.match(/\d+ elements/)?.[0], 'elements,', t.match(/\d+ labels/)?.[0], 'labels, workflow error:', t.includes('Workflow error'));
      await page.screenshot({ path: '/tmp/pdf_editor.png' });
    } catch (e) {
      console.log('locator click FAILED:', e.message.split('\n')[0]);
      const bb = await accept.boundingBox().catch(() => null);
      console.log('accept bbox:', bb);
    }
  }
  await browser.close();
})();
