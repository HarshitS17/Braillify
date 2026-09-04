const { chromium } = require('playwright');
const path = require('path');

(async () => {
  console.log("Launching browser...");
  const browser = await chromium.launch({ headless: true });
  const page = await browser.newPage();
  
  // Listen for console logs
  page.on('console', msg => console.log(`[BROWSER CONSOLE] ${msg.type()}: ${msg.text()}`));
  
  // Listen for network responses
  page.on('response', response => {
    if (response.url().includes('/api/')) {
      console.log(`[NETWORK] ${response.request().method()} ${response.url()} -> ${response.status()}`);
    }
  });

  console.log("Navigating to http://localhost:5173");
  await page.goto('http://localhost:5173', { waitUntil: 'networkidle' });

  // Wait for the app to be ready (Backend connected)
  console.log("Checking for Backend connected...");
  const text = await page.textContent('body');
  if (!text.includes('Backend connected')) {
    console.error("Backend not connected! Text:", text.substring(0, 200));
    await browser.close();
    return;
  }
  console.log("Backend is connected.");

  // Upload an image
  console.log("Uploading file...");
  const fileInput = await page.$('input[type="file"]');
  // Use the test image created earlier
  const imgPath = path.resolve(__dirname, '..', 'backend', 'test_biology_diagram.png');
  await fileInput.setInputFiles(imgPath);

  console.log("Clicking 'Process Page'...");
  await page.click('text=Process Page');
  
  // Wait for the region editor to appear
  console.log("Waiting for region editor...");
  await page.waitForSelector('text=Region Editor', { timeout: 30000 });
  
  // At this point, detection has completed. Let's find the "✓" accept button.
  console.log("Accepting candidate...");
  await page.click('button:has-text("✓")');

  // Click Process & Edit
  console.log("Clicking 'Process & Edit ➔'...");
  await page.click('text=Process & Edit ➔');

  // Wait for a few seconds to see what happens
  await page.waitForTimeout(5000);

  // Check the status text in PageViewer
  const bodyText = await page.textContent('body');
  if (bodyText.includes('Workflow error')) {
    console.log("❌ Workflow error found on page!");
    const statusMatch = bodyText.match(/Workflow error: .+/);
    console.log("Status text:", statusMatch ? statusMatch[0] : "Not found");
  } else {
    console.log("✅ No Workflow error found!");
  }

  await browser.close();
})();
