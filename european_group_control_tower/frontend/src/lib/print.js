import css from '../styles.css?inline';
import logo from '../assets/european-group-logo.jpeg';

// Prints an HTML fragment through a hidden iframe that carries the app stylesheet. This keeps printing
// independent of the surrounding Odoo page (navbar, scroll containers) and of the Shadow DOM boundary.
export function printHtml(html, title = 'Control Tower') {
  const frame = document.createElement('iframe');
  frame.setAttribute('aria-hidden', 'true');
  frame.style.cssText = 'position:fixed;right:0;bottom:0;width:0;height:0;border:0;visibility:hidden;';
  document.body.appendChild(frame);
  const doc = frame.contentDocument;
  doc.open();
  doc.write(`<!doctype html><html><head><meta charset="utf-8"><title>${title}</title><style>${css}</style></head>`
    + `<body class="egct-app egct-print"><div class="print-brand"><img src="${logo}" alt="European Group"/>`
    + `<div>EUROPEAN GROUP | CONTROL TOWER</div></div>${html}</body></html>`);
  doc.close();
  const run = () => {
    try { frame.contentWindow.focus(); frame.contentWindow.print(); } finally { setTimeout(() => frame.remove(), 1500); }
  };
  const img = doc.querySelector('img');
  if (img && !img.complete) { img.onload = run; img.onerror = run; } else { setTimeout(run, 50); }
}
