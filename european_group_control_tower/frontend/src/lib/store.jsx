import { createContext, useCallback, useContext, useEffect, useMemo, useRef, useState } from 'react';
import { EMPTY_DATA } from './importer.js';

const Ctx = createContext(null);
export const useStore = () => useContext(Ctx);

// Odoo's RPCError keeps the server message in error.data.message; fall back to whatever we got.
const errorText = (e) => e?.data?.message || e?.message || (typeof e === 'string' ? e : 'Request failed');

// Server-backed store. The whole dataset lives in Odoo (egct.* models); every write goes through a controller
// route which returns the fresh dataset, so the UI is always rendering what is actually saved.
// Every mutation returns a Promise<boolean> (false = failed, an error toast has already been shown).
export function StoreProvider({ rpc, children }) {
  const [data, setData] = useState(null);
  const [user, setUser] = useState({ name: '', isManager: false });
  const [loadError, setLoadError] = useState('');
  const [toast, setToast] = useState(null);
  const [saving, setSaving] = useState(0);
  const alive = useRef(true);

  const notify = useCallback((msg, type = 'ok') => {
    const id = Date.now() + Math.random();
    setToast({ id, msg, type });
    setTimeout(() => setToast((t) => (t && t.id === id ? null : t)), 3500);
  }, []);

  const load = useCallback(async () => {
    setLoadError('');
    try {
      const r = await rpc('/egct/bootstrap', {});
      if (!alive.current) return;
      setData({ ...EMPTY_DATA, ...r.data });
      setUser(r.user);
    } catch (e) {
      if (alive.current) setLoadError(errorText(e));
    }
  }, [rpc]);

  useEffect(() => {
    alive.current = true;
    load();
    return () => { alive.current = false; };
  }, [load]);

  const api = useMemo(() => {
    // Runs one RPC, swaps in the returned dataset, reports failures as a toast.
    const call = async (route, params) => {
      setSaving((n) => n + 1);
      try {
        const r = await rpc(route, params);
        if (alive.current && r?.data) setData({ ...EMPTY_DATA, ...r.data });
        return r || {};
      } catch (e) {
        notify(errorText(e), 'err');
        return null;
      } finally {
        if (alive.current) setSaving((n) => n - 1);
      }
    };

    // Generic create/update for suppliers / shipments / payments / documents.
    const upsert = async (coll, rec, label) => !!(await call('/egct/save', { coll, rec, label }));
    const remove = async (coll, id, label) => !!(await call('/egct/remove', { coll, id, label }));
    // Creating a PO also creates its shipment and payment record on the server.
    const savePO = async (po) => !!(await call('/egct/po/save', { po }));
    const deletePO = async (id) => !!(await call('/egct/po/delete', { id }));
    const importDataset = async (dataset, mode, label) => !!(await call('/egct/import', { dataset, mode, label }));
    const importAcid = async (map) => !!(await call('/egct/import_acid', { items: [...map.entries()] }));
    const replaceAll = async (dataset, label) => importDataset(dataset, 'replace', label);

    return { upsert, remove, savePO, deletePO, importDataset, importAcid, replaceAll, notify, reload: load };
  }, [rpc, notify, load]);

  const value = useMemo(() => ({ data, user, toast, saving: saving > 0, ...api }), [data, user, toast, saving, api]);

  if (!data) {
    return (
      <div className="boot">
        {loadError ? (
          <div className="boot-card">
            <h3>Control Tower could not load</h3>
            <div className="err-box">{loadError}</div>
            <button className="btn primary block" onClick={load}>Try again</button>
          </div>
        ) : (
          <p className="muted">Loading Control Tower…</p>
        )}
      </div>
    );
  }
  return <Ctx.Provider value={value}>{children}</Ctx.Provider>;
}
