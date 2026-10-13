export const str = (v) => (v === null || v === undefined ? '' : String(v).trim());

export const num = (v) => {
  if (v === null || v === undefined || v === '') return 0;
  if (typeof v === 'number') return Number.isFinite(v) ? v : 0;
  const n = parseFloat(String(v).replace(/[^0-9.\-]/g, ''));
  return Number.isFinite(n) ? n : 0;
};

const pad = (n) => String(n).padStart(2, '0');

// Accepts Date, Excel serial number, YYYY-MM-DD, DD/MM/YYYY, DD-MM-YYYY. Returns 'YYYY-MM-DD' or ''.
export function toISODate(v) {
  if (v === null || v === undefined || v === '') return '';
  if (v instanceof Date) return Number.isNaN(v.getTime()) ? '' : `${v.getFullYear()}-${pad(v.getMonth() + 1)}-${pad(v.getDate())}`;
  if (typeof v === 'number') {
    if (v > 20000 && v < 80000) {
      const d = new Date(Math.round((v - 25569) * 86400000));
      return `${d.getUTCFullYear()}-${pad(d.getUTCMonth() + 1)}-${pad(d.getUTCDate())}`;
    }
    return '';
  }
  const s = String(v).trim();
  let m = s.match(/^(\d{4})-(\d{1,2})-(\d{1,2})/);
  if (m) return `${m[1]}-${pad(m[2])}-${pad(m[3])}`;
  m = s.match(/^(\d{1,2})[/.-](\d{1,2})[/.-](\d{4})$/);
  if (m) return `${m[3]}-${pad(m[2])}-${pad(m[1])}`;
  const d = new Date(s);
  return Number.isNaN(d.getTime()) ? '' : toISODate(d);
}

export const parseISO = (iso) => {
  if (!iso) return null;
  const [y, m, d] = iso.split('-').map(Number);
  return new Date(y, m - 1, d);
};

export const fmtDate = (iso) => {
  if (!iso) return '-';
  const d = parseISO(iso);
  return d ? d.toLocaleDateString('en-GB', { day: '2-digit', month: 'short', year: 'numeric' }) : '-';
};

export const fmtNum = (n, digits = 0) =>
  Number(n || 0).toLocaleString('en-US', { minimumFractionDigits: digits, maximumFractionDigits: digits });

export const fmtMoney = (n, cur = '') => `${cur ? cur + ' ' : ''}${fmtNum(n, 2)}`;

export const fmtCompact = (n) => {
  const v = Number(n || 0);
  if (Math.abs(v) >= 1e6) return `${(v / 1e6).toFixed(1)}M`;
  if (Math.abs(v) >= 1e3) return `${(v / 1e3).toFixed(0)}K`;
  return fmtNum(v);
};

export const slug = (s) => str(s).toLowerCase().replace(/[^a-z0-9\u0600-\u06ff]+/g, '-').replace(/^-|-$/g, '');
export const uid = (p) => `${p}-${Date.now().toString(36)}${Math.random().toString(36).slice(2, 6)}`;
export const normName = (s) => str(s).toLowerCase().replace(/\s+/g, ' ');
export const normHeader = (s) => str(s).toLowerCase().replace(/[^a-z0-9\u0600-\u06ff]/g, '');
