// not-burxt: gap — COULD be Burxt — see tests/languages.py
// **The blocker named for this is asserted, not measured, and that is recorded rather than fixed.** The
// ledger says Burxt has no way to read a rendered DOM; nobody has checked, and the Burxt session's
// sharpening of the sorting rule is why that matters — the honest question has two halves, *is the job
// allowed to depend on Burxt* AND *is the capability actually absent, or did I stop checking*. They found
// their own second-half error the same day: `scripts/editor-icons.py` written off as unportable when PNG
// decode and encode were both already reachable, and its `--check` compares pixels rather than file bytes,
// so a port never needed to match an encoder at all.
//
// Two capabilities are conflated in "drive a browser" and only one is the hard half: spawning a process is
// `lib/os.bx` and exists; reading back a rendered tree is the open question. A yes to the first reads as a
// yes to the wrong half, which is why the question was put to the language side split that way.
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
