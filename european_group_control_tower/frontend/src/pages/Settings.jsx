import { useState } from 'react';
import { useStore } from '../lib/store.jsx';
import { useNav } from '../lib/nav.jsx';
import { exportAll, exportWorkbook, flatRows } from '../lib/exporter.js';
import { seedData } from '../data/seed.js';
import { EMPTY_DATA } from '../lib/importer.js';
import { Card, PageHeader } from '../components/ui.jsx';
import ImportModal from '../components/ImportModal.jsx';

export default function Settings() {
  const { data, user, replaceAll, notify } = useStore();
  const { ask } = useNav();
  const [imp, setImp] = useState(null);

  return (
    <>
      <PageHeader title="Settings & Data" subtitle="Import, export, backup and access" />
      <div className="grid-2">
        <Card title="Import">
          <p className="muted">Import POs and shipments from Excel with flexible column mapping, or load an ACID list (Order Reference + ACID#).</p>
          <div className="row gap wrap">
            <button className="btn primary" onClick={() => setImp('shipments')}>Import shipments (Excel / CSV)</button>
            <button className="btn" onClick={() => setImp('acid')}>Import ACID list</button>
          </div>
        </Card>
        <Card title="Export & backup">
          <p className="muted">Full workbook with one sheet per module, plus a sheet in the original import format so it can be re-imported.</p>
          <div className="row gap wrap">
            <button className="btn primary" onClick={() => exportAll(data)}>Export everything (XLSX)</button>
            <button className="btn" onClick={() => exportWorkbook({ Shipments: flatRows(data) }, `european-group-shipments-${new Date().toISOString().slice(0, 10)}.xlsx`)}>Export shipments sheet only</button>
          </div>
        </Card>
        <Card title="Storage">
          <p>Records: <b>{data.pos.length}</b> POs · <b>{data.shipments.length}</b> shipments · <b>{data.payments.length}</b> payments · <b>{data.suppliers.length}</b> suppliers · <b>{data.documents.length}</b> documents</p>
          <p className="muted small">All data is stored in the Odoo database (models <code>egct.po</code>, <code>egct.shipment</code>, <code>egct.payment</code>, <code>egct.document</code>, <code>egct.supplier</code>) and is shared by every user with access to the Control Tower.</p>
          {user.isManager ? (
            <div className="row gap wrap">
              <button className="btn" onClick={() => ask('Replace ALL data with the original Excel data (european-group-shipments.xlsx + acid.xlsx)? All current records will be lost.', async () => { if (await replaceAll(seedData(), 'Initial load from european-group-shipments.xlsx + acid.xlsx')) notify('Original data loaded'); }, 'Load original Excel data')}>Load original Excel data</button>
              <button className="btn danger" onClick={() => ask('Delete ALL Control Tower data from Odoo? Export a backup first.', async () => { if (await replaceAll({ ...EMPTY_DATA }, 'All data cleared')) notify('All data cleared'); }, 'Clear all data')}>Clear all data</button>
            </div>
          ) : (
            <p className="muted small">Replacing or clearing all data is limited to Control Tower managers.</p>
          )}
        </Card>
        <Card title="Access">
          <p>Signed in as <b>{user.name}</b> ({user.isManager ? 'Manager' : 'User'}). Access is controlled by Odoo: users of the <i>Control Tower / User</i> group can work with all records; the <i>Manager</i> group can additionally replace or clear all data.</p>
          <p className="muted small">Assign the groups under Settings → Users &amp; Companies → Users. The Odoo login and session replace the previous one-time-code gate.</p>
        </Card>
      </div>
      {imp && <ImportModal kind={imp} onClose={() => setImp(null)} />}
    </>
  );
}
