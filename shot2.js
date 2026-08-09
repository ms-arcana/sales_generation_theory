const { chromium } = require('playwright');
(async () => {
  const b = await chromium.launch();
  const p = await b.newPage({ viewport: { width: 1280, height: 1000 } });
  const errs = [];
  p.on('pageerror', e => errs.push(String(e)));
  p.on('console', m => { if (m.type()==='error' && !m.text().includes('ERR_TUNNEL')) errs.push('console: '+m.text()); });
  await p.goto('file:///home/claude/work/interim-report-v3.html');
  await p.waitForTimeout(900);
  const n = await p.$$eval('.slide', s => s.length);
  // check tab panels
  await p.evaluate(() => document.querySelectorAll('#dots button')[2].click());
  await p.waitForTimeout(200);
  await p.evaluate(() => document.querySelectorAll('#ttabs button')[4].click());
  await p.waitForTimeout(200);
  await p.screenshot({ path: 't_e.png', fullPage: true });
  const tlen = await p.$eval('#tpanel', e => e.textContent.length);
  await p.evaluate(() => document.querySelectorAll('#dots button')[4].click());
  await p.waitForTimeout(200);
  await p.evaluate(() => document.querySelectorAll('#dtabs button')[4].click());
  await p.waitForTimeout(200);
  await p.screenshot({ path: 'd_5.png', fullPage: true });
  const dlen = await p.$eval('#dpanel', e => e.textContent.length);
  const mrows = await p.$$eval('#matrix tr', r => r.length);
  console.log('slides',n,'tpanel',tlen,'dpanel',dlen,'matrixrows',mrows);
  console.log('errors', JSON.stringify(errs));
  await b.close();
})();
