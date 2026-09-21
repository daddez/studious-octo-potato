import { webkit } from 'playwright';
import fs from 'fs';
import path from 'path';
import https from 'https';
import { fileURLToPath } from 'url';

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const SAFARI_UA = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Safari/605.1.15';

const CAPTCHA_TYPES = {
  recaptcha_v2: ['g-recaptcha', 'grecaptcha'],
  hcaptcha: ['h-captcha', 'hcaptcha'],
  recaptcha_v3: ['recaptcha/enterprise']
};

function detectCaptcha(html) {
  for (const [type, markers] of Object.entries(CAPTCHA_TYPES)) {
    if (markers.some(m => html.includes(m))) return type;
  }
  return null;
}

async function solveCaptchaWith2Captcha(page, captchaType) {
  const apiKey = process.env.CAPTCHA_API_KEY;
  if (!apiKey) {
    console.log('[CAPTCHA] API key non configurato, skip');
    return false;
  }

  console.log(`[CAPTCHA] Rilevato: ${captchaType}`);

  try {
    const element = await page.$('[class*="captcha"], [data-captcha], .g-recaptcha, .h-captcha');
    if (!element) {
      console.log('[CAPTCHA] Elemento non trovato nel DOM');
      return false;
    }

    const screenshot = await element.screenshot();
    const base64 = screenshot.toString('base64');
    console.log(`[CAPTCHA] Screenshot: ${screenshot.length} bytes`);

    return new Promise((resolve) => {
      const postData = JSON.stringify({
        clientKey: apiKey,
        task: {
          type: captchaType === 'recaptcha_v2' ? 'RecaptchaV2TaskProxyless' : 'HCaptchaTaskProxyless',
          websiteURL: process.env.URL,
          websiteKey: 'placeholder',
          body: base64
        }
      });

      const options = {
        hostname: 'api.2captcha.com',
        port: 443,
        path: '/createTask',
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Content-Length': Buffer.byteLength(postData)
        }
      };

      const req = https.request(options, (res) => {
        let data = '';
        res.on('data', (chunk) => { data += chunk; });
        res.on('end', () => {
          try {
            const result = JSON.parse(data);
            if (result.taskId) {
              console.log(`[CAPTCHA] Task creato: ${result.taskId}`);
              resolve(true);
            } else {
              console.log(`[CAPTCHA] Errore: ${result.errorCode}`);
              resolve(false);
            }
          } catch (e) {
            resolve(false);
          }
        });
      });

      req.on('error', () => resolve(false));
      req.write(postData);
      req.end();
    });
  } catch (e) {
    console.log(`[CAPTCHA] Errore: ${e.message}`);
    return false;
  }
}

async function main() {
  const url = process.env.URL;
  const jobId = process.env.JOB_ID;

  console.log(`[RENDER] URL: ${url}`);
  console.log(`[RENDER] Job ID: ${jobId}`);
  console.log(`[RENDER] Browser: Safari (webkit) su macOS`);

  const browser = await webkit.launch({ headless: true });
  const context = await browser.createContext({
    userAgent: SAFARI_UA,
    locale: 'it-IT'
  });
  const page = await context.newPage();

  await page.setExtraHTTPHeaders({
    'Accept-Language': 'it-IT,it;q=0.9,en;q=0.8',
    'DNT': '1',
    'Connection': 'keep-alive',
    'Upgrade-Insecure-Requests': '1'
  });

  try {
    console.log(`[RENDER] Navigazione...`);
    await page.goto(url, { waitUntil: 'networkidle', timeout: 60000 });

    await page.waitForTimeout(Math.random() * 2000 + 1000);

    let html = await page.content();
    const captchaType = detectCaptcha(html);

    if (captchaType) {
      await solveCaptchaWith2Captcha(page, captchaType);
      await page.waitForTimeout(3000);
      html = await page.content();
    } else {
      console.log('[CAPTCHA] Nessun CAPTCHA rilevato');
    }

    const outputDir = 'render-results';
    if (!fs.existsSync(outputDir)) {
      fs.mkdirSync(outputDir, { recursive: true });
    }

    const outputFile = path.join(outputDir, `rendered-${jobId}.html`);
    fs.writeFileSync(outputFile, html, 'utf-8');
    console.log(`[RENDER] HTML salvato: ${outputFile} (${html.length} bytes)`);

    const metaFile = path.join(outputDir, `meta-${jobId}.json`);
    const meta = {
      url,
      jobId,
      browser: 'Safari (webkit)',
      os: 'macOS',
      timestamp: new Date().toISOString(),
      htmlSize: html.length,
      captchaDetected: !!captchaType
    };
    fs.writeFileSync(metaFile, JSON.stringify(meta, null, 2), 'utf-8');
    console.log('[RENDER] Completato con successo');

    process.exit(0);
  } catch (e) {
    console.error(`[RENDER] Errore: ${e.message}`);
    process.exit(1);
  } finally {
    await browser.close();
  }
}

main();
