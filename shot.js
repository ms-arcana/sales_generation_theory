const { chromium } = require('playwright');
(async () => {
  const b = await chromium.launch();
  const p = await b.newPage({ viewport: { width: 1280, height: 1000 } });
  const errs = [];
  p.on('pageerror', e => errs.push(String(e)));
  p.on('console', m => { if (m.type() === 'error') errs.push('console: ' + m.text()); });
  await p.goto('file:///home/claude/work/buyer-falsification-report.html');
  await p.waitForTimeout(1200);
  const n = await p.$$eval('.slide', s => s.length);
  for (let i = 0; i < n; i++) {
    await p.evaluate(i => { document.querySelectorAll('#dots button')[i].click(); }, i);
    await p.waitForTimeout(300);
    await p.screenshot({ path: `s${i}.png`, fullPage: true });
  }
  // interaction check on slide 2
  await p.evaluate(() => document.querySelectorAll('#dots button')[2].click());
  await p.waitForTimeout(200);
  await p.evaluate(() => document.querySelectorAll('.mcell')[6].click());
  await p.waitForTimeout(200);
  await p.screenshot({ path: 'interact.png', fullPage: true });
  const detailLen = await p.$eval('#detail', e => e.textContent.length);
  const rungs = await p.$$eval('.rung', e => e.map(x => x.className));
  console.log('slides', n, 'detailLen', detailLen);
  console.log('rungs', JSON.stringify(rungs));
  console.log('errors', JSON.stringify(errs));
  await b.close();
})();
