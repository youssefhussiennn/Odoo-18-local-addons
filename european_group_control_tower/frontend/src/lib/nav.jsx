import { createContext, useCallback, useContext, useEffect, useMemo, useState } from 'react';

const Ctx = createContext(null);
export const useNav = () => useContext(Ctx);

export const PAGES = ['dashboard', 'pos', 'shipments', 'tracking', 'payments', 'suppliers', 'documents', 'alerts', 'reports', 'settings'];
const fromHash = () => {
  const h = window.location.hash.replace(/^#\/?/, '');
  return PAGES.includes(h) ? h : 'dashboard';
};

// Page routing (hash based), shipment detail modal, editor modal and confirm dialog state.
export function NavProvider({ children }) {
  const [page, setPage] = useState(fromHash);
  const [detail, setDetail] = useState(null);
  const [editor, setEditor] = useState(null);
  const [confirmState, setConfirm] = useState(null);
  const [menu, setMenu] = useState(false);

  useEffect(() => {
    const onHash = () => setPage(fromHash());
    window.addEventListener('hashchange', onHash);
    return () => window.removeEventListener('hashchange', onHash);
  }, []);

  const go = useCallback((p) => { window.location.hash = `/${p}`; setPage(p); setMenu(false); setDetail(null); }, []);
  const value = useMemo(() => ({
    page, go, menu, setMenu,
    detail, openDetail: (poId) => setDetail(poId), closeDetail: () => setDetail(null),
    editor, edit: (kind, id = null, preset = {}) => setEditor({ kind, id, preset }), closeEdit: () => setEditor(null),
    confirmState, ask: (message, onYes, title = 'Please confirm') => setConfirm({ message, onYes, title }), closeConfirm: () => setConfirm(null),
  }), [page, go, menu, detail, editor, confirmState]);

  return <Ctx.Provider value={value}>{children}</Ctx.Provider>;
}
