/** Probe 2: is the accept button continuously moving? What covers it? */
const { chromium } = require('playwright');
const path = require('path');

(async () => {
  const browser = await chromium.launch({ headless: true });
  const page = await browser.newPage({ viewport: { width: 1440, height: 900 } });
  await page.goto('http://localhost:5173', { waitUntil: 'networkidle' });
  await page.setInputFiles('input[type="file"]', path.resolve(__dirname, '..', 'backend', 'qa_fixtures', '09_textbook_page.pdf'));
  await page.click('text=Process Page');
  await page.waitForSelector('text=Region Editor', { timeout: 20000 });

  for (let i = 0; i < 6; i++) {
    const b = await page.evaluate(() => {
      const btn = [...document.querySelectorAll('button')].find(e => e.textContent.trim() === '✓');
      if (!btn) return null;
      const r = btn.getBoundingClientRect();
      // what would receive the click at the button's center?
      const cx = r.x + r.width / 2, cy = r.y + r.height / 2;
      const top = document.elementFromPoint(cx, cy);
      return {
        x: Math.round(r.x), y: Math.round(r.y), w: Math.round(r.width), h: Math.round(r.height),
        coveredBy: top ? top.tagName + '.' + (top.className || '').toString().slice(0, 40) : 'none',
        isSelf: top === btn || btn.contains(top),
        scrollY: Math.round(window.scrollY),
        docH: document.documentElement.scrollHeight,
        winH: window.innerHeight,
      };
    });
    console.log(i, JSON.stringify(b));
    await page.waitForTimeout(700);
  }

  // check img elements state (naturalWidth 0 = broken)
  const imgs = await page.$$eval('img', els => els.map(e => ({
    src: e.src.split('/').slice(-2).join('/'), ok: e.complete && e.naturalWidth > 0,
    w: e.clientWidth, h: e.clientHeight,
  })));
  console.log('images:', JSON.stringify(imgs, null, 1));
  await browser.close();
})();
