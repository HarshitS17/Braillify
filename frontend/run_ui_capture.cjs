const { chromium } = require('playwright');
const path = require('path');
const fs = require('fs');

const OUT_DIR = path.resolve(__dirname, '..', 'data', 'outputs');
fs.mkdirSync(OUT_DIR, { recursive: true });

(async () => {
  console.log("Launching browser...");
  const browser = await chromium.launch({ headless: true });
  const page = await browser.newPage({ viewport: { width: 1440, height: 900 } });

  page.on('console', msg => {
    if (msg.type() === 'error') console.log(`[BROWSER ERROR] ${msg.text()}`);
  });

  console.log("Navigating to http://localhost:5173 ...");
  await page.goto('http://localhost:5173', { waitUntil: 'networkidle' });

  const text = await page.textContent('body');
  if (!text.includes('Backend connected')) {
    console.error("Backend not connected! Screenshots aborted.");
    await browser.close();
    return;
  }
  console.log("✅ Backend connected — capturing home page.");
  await page.screenshot({ path: path.join(OUT_DIR, 'ui_1_home.png') });

  // Upload the test image
  console.log("Uploading test_biology_diagram.png ...");
  const fileInput = await page.$('input[type="file"]');
  const imgPath = path.resolve(__dirname, '..', 'backend', 'test_biology_diagram.png');
  await fileInput.setInputFiles(imgPath);
  await page.click('text=Process Page');

  // Wait for region editor with detected candidates
  await page.waitForSelector('text=Region Editor', { timeout: 30000 });
  await page.waitForTimeout(500);
  console.log("✅ Candidates detected — capturing detection view.");
  await page.screenshot({ path: path.join(OUT_DIR, 'ui_2_detection.png') });

  // Accept the candidate and run the workflow
  const acceptButton = await page.$('button:has-text("✓")');
  if (acceptButton) {
    await acceptButton.click();
    await page.click('text=Process & Edit ➔');
    await page.waitForTimeout(6000);
  }

  const bodyText = await page.textContent('body');
  if (bodyText.includes('Workflow error')) {
    console.error("❌ Workflow error:", bodyText.match(/Workflow error: [^\n]*/)[0]);
  } else {
    console.log("✅ Workflow complete — editor open. Capturing editor view.");
    await page.screenshot({ path: path.join(OUT_DIR, 'ui_3_editor.png') });
  }

  await browser.close();
  console.log(`Screenshots saved to ${OUT_DIR}`);
})();