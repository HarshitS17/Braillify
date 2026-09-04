const { chromium } = require('playwright');
const path = require('path');

(async () => {
  const browser = await chromium.launch({ headless: true });
  const page = await browser.newPage();
  
  page.on('console', msg => {
      if (msg.type() === 'error') console.log(`[CONSOLE ERROR] ${msg.text()}`);
  });

  await page.goto('http://localhost:5173', { waitUntil: 'networkidle' });
  const fileInput = await page.$('input[type="file"]');
  await fileInput.setInputFiles(path.resolve(__dirname, '..', 'backend', 'test_diagram.pdf'));

  await page.click('text=Process Page');
  
  try {
      await page.waitForSelector('text=Region Editor', { timeout: 15000 });
      const acceptButton = await page.$('button:has-text("✓")');
      if (acceptButton) {
          await acceptButton.click();
          await page.click('text=Process & Edit ➔');
          await page.waitForTimeout(4000);
          const bodyText = await page.textContent('body');
          if (bodyText.includes('Workflow error')) {
              console.log(`❌ FAILED: PDF - ${bodyText.match(/Workflow error: [^\n]*/)[0]}`);
          } else {
              console.log(`✅ SUCCESS: PDF processed successfully.`);
          }
      } else {
          console.log(`⚠️ SKIPPED: PDF - No diagram candidates found.`);
      }
  } catch (e) {
      const bodyText = await page.textContent('body');
      if (bodyText.includes('Error:')) {
          console.log(`❌ FAILED: PDF - Error: ${bodyText.match(/Error: [^\n]*/)[0]}`);
      } else {
          console.log(`❌ FAILED: PDF - Timeout. ${e.message}`);
      }
  }
  
  await browser.close();
})();
