// Exporta cada <section class="slide"> de carrusel.html a slide-01.png … slide-10.png
// y corre un chequeo básico: tamaño mínimo de texto (28 px) y texto fuera de márgenes.
// Uso: node render.js
const path = require('path');
const { chromium } = require('playwright');

const SAFE = { x: 90, y: 110, w: 1080, h: 1350 };
const MIN_FONT = 28;

(async () => {
  const browser = await chromium.launch();
  const page = await browser.newPage({ viewport: { width: 1080, height: 1350 }, deviceScaleFactor: 1 });
  await page.goto('file://' + path.join(__dirname, 'carrusel.html'));
  await page.evaluate(() => document.fonts.ready);

  const report = await page.evaluate(({ SAFE, MIN_FONT }) => {
    const out = [];
    document.querySelectorAll('.slide').forEach((slide, i) => {
      const s = slide.getBoundingClientRect();
      const walker = document.createTreeWalker(slide, NodeFilter.SHOW_TEXT);
      let n;
      while ((n = walker.nextNode())) {
        if (!n.textContent.trim()) continue;
        const el = n.parentElement;
        const fs = parseFloat(getComputedStyle(el).fontSize);
        const range = document.createRange();
        range.selectNodeContents(n);
        for (const r of range.getClientRects()) {
          const box = { l: r.left - s.left, t: r.top - s.top, r: r.right - s.left, b: r.bottom - s.top };
          const issues = [];
          if (fs < MIN_FONT) issues.push(`font ${fs}px`);
          if (box.l < SAFE.x - 4 || box.r > SAFE.w - SAFE.x + 4) issues.push(`x ${Math.round(box.l)}–${Math.round(box.r)}`);
          if (box.t < SAFE.y - 12 || box.b > SAFE.h - SAFE.y + 12) issues.push(`y ${Math.round(box.t)}–${Math.round(box.b)}`);
          if (issues.length) out.push(`slide ${i + 1}: "${n.textContent.trim().slice(0, 40)}" → ${issues.join(', ')}`);
        }
      }
    });
    return out;
  }, { SAFE, MIN_FONT });

  const slides = await page.$$('.slide');
  for (let i = 0; i < slides.length; i++) {
    const file = path.join(__dirname, `slide-${String(i + 1).padStart(2, '0')}.png`);
    await slides[i].screenshot({ path: file });
  }
  await browser.close();

  console.log(`${slides.length} slides exportados.`);
  console.log(report.length ? 'Revisar:\n' + report.join('\n') : 'Chequeo OK: sin texto < 28 px ni fuera de márgenes.');
})();
