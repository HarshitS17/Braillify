/** QA: unsupported file via UI + responsive layouts + keyboard focus checks. */
const { chromium } = require('playwright');
const path = require('path');
const fs = require('fs');
const OUT = path.resolve(__dirname, '..', 'data', 'outputs', 'qa');
const FX = path.resolve(__dirname, '..', 'backend', 'qa_fixtures');
const results = [];
const ok = (c, s) => { results.push((c ? 'PASS ' : 'FAIL ') + s); console.log((c ? 'PASS:' : 'FAIL:') + ' ' + s); };

(async () => {
  const browser = await chromium.launch({ headless: true });
  const page = await browser.newPage({ viewport: { width: 1440, height: 900 } });
  const consoleErrors = [];
  page.on('console', m => { if (m.type() === 'error') consoleErrors.push(m.text()); });

  // ---- 1. Unsupported file (.txt) through the UI ----
  await page.goto('http://localhost:5173', { waitUntil: 'networkidle' });
  await page.setInputFiles('input[type="file"]', path.join(FX, '10_not_an_image.txt'));
  await page.click('button:has-text("Process Page")');
  await page.waitForFunction(() => /Error/i.test(document.body.innerText), { timeout: 8000 }).catch(() => {});
  const body = await page.textContent('body');
  ok(/Error/i.test(body), 'unsupported .txt shows visible error in UI');
  ok(!/Infinity|undefined|NaN/.test(body), 'error message contains no raw undefined/NaN');
  const loadingGone = await page.evaluate(() => !document.body.innerText.match(/Processing\.\.\./));
  ok(loadingGone, 'loading state cleared after error (recovery possible)');
  await page.screenshot({ path: path.join(OUT, 'unsupported_error.png') });

  // ---- 2. Responsive layouts (landing + editor) ----
  for (const [w, h] of [[1280, 800], [1024, 768]]) {
    await page.setViewportSize({ width: w, height: h });
    await page.goto('http://localhost:5173', { waitUntil: 'networkidle' });
    const overflow = await page.evaluate(() => document.documentElement.scrollWidth - document.documentElement.clientWidth);
    ok(overflow <= 0, `landing ${w}x${h}: no horizontal overflow (${overflow}px)`);
    await page.screenshot({ path: path.join(OUT, `responsive_landing_${w}.png`) });

    // editor at small viewport
    await page.setInputFiles('input[type="file"]', path.join(FX, '01_simple_biology.png'));
    await page.click('text=Process Page');
    await page.waitForSelector('text=Region Editor', { timeout: 20000 });
    await page.click('button:has-text("✓")');
    await page.click('text=Process & Edit ➔');
    await page.waitForSelector('text=Pipeline', { timeout: 30000 }).catch(() => {});
    await page.waitForTimeout(6000);
    const edOverflow = await page.evaluate(() => document.documentElement.scrollWidth - document.documentElement.clientWidth);
    ok(edOverflow <= 0, `editor ${w}x${h}: no horizontal overflow (${edOverflow}px)`);
    // export buttons still visible/clickable
    const expVisible = await page.isVisible('button:has-text("Export SVG")');
    ok(expVisible, `editor ${w}x${h}: Export SVG button visible`);
    await page.screenshot({ path: path.join(OUT, `responsive_editor_${w}.png`) });
  }

  // ---- 3. Keyboard accessibility: focus visible, tab reaches controls ----
  await page.setViewportSize({ width: 1440, height: 900 });
  await page.reload({ waitUntil: 'networkidle' });
  let focusedTags = [];
  for (let i = 0; i < 12; i++) {
    await page.keyboard.press('Tab');
    focusedTags.push(await page.evaluate(() => document.activeElement ? document.activeElement.tagName + (document.activeElement.className ? '.' + String(document.activeElement.className).split(' ')[0] : '') : 'none'));
  }
  const reachedInteractive = focusedTags.some(t => /^(BUTTON|INPUT|A|SELECT|TEXTAREA)/.test(t));
  ok(reachedInteractive, 'keyboard Tab reaches interactive controls: ' + focusedTags.slice(0, 6).join(', '));
  const focusStyle = await page.evaluate(() => {
    const el = document.activeElement;
    if (!el) return 'none';
    const s = getComputedStyle(el);
    return `outline=${s.outlineWidth}/${s.outlineColor} shadow=${s.boxShadow !== 'none'}`;
  });
  console.log('focus indicator on active element:', focusStyle);

  await browser.close();
  console.log('\n==== RESPONSIVE/A11Y RESULTS ====');
  console.log(results.join('\n'));
  console.log('console errors:', consoleErrors.length, consoleErrors.slice(0, 3));
  fs.writeFileSync(path.join(OUT, 'responsive_a11y_results.json'), JSON.stringify({ results, consoleErrors }, null, 2));
  process.exit(results.some(r => r.startsWith('FAIL')) ? 1 : 0);
})();
