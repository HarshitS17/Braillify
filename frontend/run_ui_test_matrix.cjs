const { chromium } = require('playwright');
const path = require('path');

const images = [
    'test_biology_diagram.png',
    'test_math.png',
    'test_circuit.png',
    'test_noisy.png',
    'test_empty.png'
];

(async () => {
  const browser = await chromium.launch({ headless: true });
  
  for (const imgName of images) {
    console.log(`\n================================`);
    console.log(`Testing image: ${imgName}`);
    console.log(`================================`);
    
    const page = await browser.newPage();
    let hasError = false;
    
    page.on('console', msg => {
        if (msg.type() === 'error') {
            console.log(`[CONSOLE ERROR] ${msg.text()}`);
        }
    });

    await page.goto('http://localhost:5173', { waitUntil: 'networkidle' });
    
    const fileInput = await page.$('input[type="file"]');
    const imgPath = path.resolve(__dirname, '..', 'backend', imgName);
    await fileInput.setInputFiles(imgPath);

    await page.click('text=Process Page');
    
    try {
        await page.waitForSelector('text=Region Editor', { timeout: 15000 });
        
        // Wait for candidates
        const acceptButton = await page.$('button:has-text("✓")');
        if (acceptButton) {
            await acceptButton.click();
            await page.click('text=Process & Edit ➔');
            await page.waitForTimeout(4000);
            
            const bodyText = await page.textContent('body');
            if (bodyText.includes('Workflow error')) {
                console.log(`❌ FAILED: ${imgName} - ${bodyText.match(/Workflow error: [^\n]*/)[0]}`);
            } else if (bodyText.includes('Please upload and extract a diagram first.')) {
                console.log(`❌ FAILED: ${imgName} - Diagram extraction failed silently or didn't switch tab.`);
            } else {
                console.log(`✅ SUCCESS: ${imgName} processed successfully.`);
            }
        } else {
            console.log(`⚠️ SKIPPED: ${imgName} - No diagram candidates found to accept.`);
        }
    } catch (e) {
        const bodyText = await page.textContent('body');
        if (bodyText.includes('Error:')) {
            console.log(`❌ FAILED: ${imgName} - Pre-processing error: ${bodyText.match(/Error: [^\n]*/)[0]}`);
        } else {
            console.log(`❌ FAILED: ${imgName} - Timeout waiting for Region Editor. ${e.message}`);
        }
    }
    await page.close();
  }
  
  await browser.close();
})();
