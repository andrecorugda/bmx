// not-burxt: gap — COULD be Burxt — see tests/languages.py
import puppeteer from '/home/andre/.npm/_npx/7d92d9a2d2ccc630/node_modules/puppeteer/lib/esm/puppeteer/puppeteer.js';
const jobs = process.argv.slice(2);
const browser = await puppeteer.launch({ headless: true, args: ['--no-sandbox'] });
const page = await browser.newPage();
await page.setViewport({ width: 1000, height: 700, deviceScaleFactor: 2 });
for (const j of jobs) {
  await page.goto('file://' + process.cwd() + '/' + j + '.html', { waitUntil: 'networkidle0' });
  const el = await page.$('.wrap');
  await el.screenshot({ path: j + '.png' });
  console.log('shot', j + '.png');
}
await browser.close();
