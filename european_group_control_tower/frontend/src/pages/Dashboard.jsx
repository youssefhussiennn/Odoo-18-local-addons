import { useMemo } from 'react';
import { useStore } from '../lib/store.jsx';
import { useNav } from '../lib/nav.jsx';
import { joinData, hasAcid } from '../lib/calc.js';
import { buildAlerts } from '../lib/alerts.js';
import { STAGES } from '../lib/constants.js';
import { fmtCompact, fmtNum } from '../lib/format.js';
import { Badge, Card, Kpi, PageHeader, toneFor, Empty } from '../components/ui.jsx';

const Bar = ({ pct, tone = 'green' }) => <div className="bar"><div className={`bar-fill ${tone}`} style={{ width: `${Math.min(100, pct)}%` }} /></div>;
const ago = (iso) => {
  const m = Math.round((Date.now() - new Date(iso).getTime()) / 60000);
  return m < 1 ? 'just now' : m < 60 ? `${m} min ago` : m < 1440 ? `${Math.round(m / 60)} h ago` : `${Math.round(m / 1440)} d ago`;
};

export default function Dashboard() {
  const { data } = useStore();
  const { go, openDetail } = useNav();

  const d = useMemo(() => {
    const rows = joinData(data);
    const alerts = buildAlerts(data);
    const withShip = rows.filter((r) => r.shipment);
    const total = rows.reduce((s, r) => s + (r.pm?.total || 0), 0);
    const outstanding = rows.reduce((s, r) => s + (r.pm?.remaining || 0), 0);
    const byCur = {};
    rows.forEach((r) => { byCur[r.po.currency] = (byCur[r.po.currency] || 0) + (r.pm?.total || 0); });
    const acid = withShip.filter((r) => hasAcid(data, r.shipment)).length;
    const stages = STAGES.map((s) => ({ s, n: withShip.filter((r) => r.shipment.stage === s).length }));
    const states = ['Delayed', 'Arriving Soon', 'On Schedule', 'Arrived', 'No ETA'].map((s) => ({ s, n: withShip.filter((r) => r.sm.state === s).length }));
    const delayed = withShip.filter((r) => r.sm.delayed).sort((a, b) => b.sm.daysDelayed - a.sm.daysDelayed);
    const soon = withShip.filter((r) => r.sm.arrivingSoon).sort((a, b) => a.sm.daysRemaining - b.sm.daysRemaining);
    const pay = ['Paid', 'Partial', 'Unpaid'].map((s) => ({ s, n: rows.filter((r) => r.pm?.status === s).length, amt: rows.filter((r) => r.pm?.status === s).reduce((a, r) => a + r.pm.remaining, 0) }));
    const overdue = rows.filter((r) => r.pm?.overdue);
    const missingDocs = {};
    alerts.filter((a) => a.type === 'missing_document').forEach((a) => { const t = a.title.replace('Missing document: ', ''); missingDocs[t] = (missingDocs[t] || 0) + 1; });
    return { rows, alerts, total, outstanding, byCur, acid, count: rows.length, stages, states, delayed, soon, pay, overdue, missingDocs };
  }, [data]);

  const pct = d.count ? Math.round((d.acid / d.count) * 100) : 0;
  const topAlerts = d.alerts.filter((a) => a.severity !== 'low').slice(0, 7);
  const missingTotal = Object.values(d.missingDocs).reduce((a, b) => a + b, 0);
  const maxStage = Math.max(1, ...d.stages.map((x) => x.n));

  const shipLine = (r) => (
    <tr key={r.po.id} className="click" onClick={() => openDetail(r.po.id)}>
      <td><b>{r.po.poNumber}</b></td>
      <td className="mono">{r.shipment.trackingNumber || '-'}</td>
      <td className="ell">{r.supplier?.company || '-'}</td>
      <td><Badge tone={toneFor.stage[r.shipment.stage]}>{r.shipment.stage}</Badge></td>
      <td className="right">{r.sm.delayed ? <b className="red-t">{r.sm.daysDelayed} days late</b> : <span>{r.sm.daysRemaining} d to ETA</span>}</td>
    </tr>
  );

  return (
    <>
      <PageHeader title="Control Tower" subtitle="Purchase Orders → Shipments → Tracking → Payments → Documents → Customs → Warehouse → Reports" />
      {!d.count && (
        <Card title="No data yet">
          <p className="muted">There are no purchase orders in Odoo yet. Create one, import an Excel file, or (managers) load the original Excel data from Settings.</p>
          <div className="row gap wrap top-gap">
            <button className="btn primary" onClick={() => go('pos')}>Go to Purchase Orders</button>
            <button className="btn" onClick={() => go('settings')}>Open Settings & Data</button>
          </div>
        </Card>
      )}
      <div className="kpis">
        <Kpi label="Purchase Orders" value={d.count} sub={`${data.shipments.length} shipments tracked`} onClick={() => go('pos')} />
        <Kpi label="Order Value" value={fmtCompact(d.total)} sub={Object.entries(d.byCur).map(([c, v]) => `${c} ${fmtCompact(v)}`).join(' · ')} />
        <Kpi label="Outstanding" value={fmtCompact(d.outstanding)} sub={`${d.total ? Math.round((d.outstanding / d.total) * 100) : 0}% of order value unpaid`} tone="warn" onClick={() => go('payments')} />
        <Kpi label="ACID Coverage" value={`${pct}%`} sub={`${d.acid} / ${d.count} ACID`} tone={pct < 50 ? 'warn' : ''} />
        <Kpi label="Delayed Shipments" value={d.delayed.length} sub="Past ETA, not arrived" tone={d.delayed.length ? 'bad' : ''} onClick={() => go('shipments')} />
        <Kpi label="Arriving Soon" value={d.soon.length} sub="ETA within 7 days" onClick={() => go('tracking')} />
        <Kpi label="Missing Documents" value={missingTotal} sub="On shipped POs" tone={missingTotal ? 'warn' : ''} onClick={() => go('documents')} />
        <Kpi label="Open Alerts" value={d.alerts.length} sub={`${d.alerts.filter((a) => a.severity === 'high').length} high priority`} tone="bad" onClick={() => go('alerts')} />
      </div>

      <div className="grid-2">
        <Card title="PO Pipeline">
          <div className="pipeline">
            {d.stages.map((x) => (
              <div className="pipe-col" key={x.s}>
                <div className="pipe-n">{x.n}</div>
                <div className="pipe-bar"><div style={{ height: `${(x.n / maxStage) * 100}%` }} /></div>
                <div className="pipe-l">{x.s}</div>
              </div>
            ))}
          </div>
        </Card>
        <Card title="Shipment Status">
          {d.states.map((x) => (
            <div className="stat-row" key={x.s}>
              <Badge tone={toneFor.state[x.s]}>{x.s}</Badge>
              <Bar pct={(x.n / Math.max(1, data.shipments.length)) * 100} tone={toneFor.state[x.s]} />
              <b>{x.n}</b>
            </div>
          ))}
        </Card>
      </div>

      <div className="grid-2">
        <Card title="Delayed Shipments" actions={<button className="btn sm" onClick={() => go('shipments')}>View all</button>}>
          <div className="scroll"><table className="grid compact"><tbody>{d.delayed.slice(0, 10).map(shipLine)}</tbody></table></div>
          {!d.delayed.length && <Empty>No delayed shipments.</Empty>}
        </Card>
        <Card title="Arriving Soon" actions={<button className="btn sm" onClick={() => go('tracking')}>Tracking</button>}>
          <div className="scroll"><table className="grid compact"><tbody>{d.soon.slice(0, 10).map(shipLine)}</tbody></table></div>
          {!d.soon.length && <Empty>Nothing arriving in the next 7 days.</Empty>}
        </Card>
      </div>

      <div className="grid-3">
        <Card title="Payment Status" actions={<button className="btn sm" onClick={() => go('payments')}>Payments</button>}>
          {d.pay.map((x) => (
            <div className="stat-row" key={x.s}>
              <Badge tone={toneFor.pay[x.s]}>{x.s}</Badge>
              <Bar pct={(x.n / Math.max(1, d.count)) * 100} tone={toneFor.pay[x.s]} />
              <b>{x.n}</b>
            </div>
          ))}
          <p className="muted small">Overdue: <b>{d.overdue.length}</b> · Remaining to pay: <b>{fmtNum(d.outstanding)}</b></p>
        </Card>
        <Card title="ACID Coverage">
          <div className="ring" style={{ '--p': pct }}><div><b>{pct}%</b><span>{d.acid} / {d.count} ACID</span></div></div>
          <p className="muted small center">{d.count - d.acid} POs still without an ACID number</p>
        </Card>
        <Card title="Missing Documents" actions={<button className="btn sm" onClick={() => go('documents')}>Documents</button>}>
          {Object.entries(d.missingDocs).map(([t, n]) => (<div className="stat-row" key={t}><span>{t}</span><div className="spacer" /><b>{n}</b></div>))}
          {!missingTotal && <Empty>No missing documents on shipped POs.</Empty>}
        </Card>
      </div>

      <div className="grid-2">
        <Card title="Alerts" actions={<button className="btn sm" onClick={() => go('alerts')}>All alerts</button>}>
          {topAlerts.map((a) => (
            <div className="alert-row" key={a.id} onClick={() => openDetail(a.poId)}>
              <Badge tone={toneFor.sev[a.severity]}>{a.severity}</Badge>
              <div><b>{a.poNumber}</b> · {a.title}<div className="muted small">{a.detail}</div></div>
            </div>
          ))}
          {!topAlerts.length && <Empty>No alerts.</Empty>}
        </Card>
        <Card title="Recent Activity">
          {(data.activity || []).slice(0, 8).map((a) => (
            <div className="alert-row" key={a.id}><span className={`dot ${a.kind}`} /><div>{a.text}<div className="muted small">{ago(a.ts)}</div></div></div>
          ))}
          {!(data.activity || []).length && <Empty>No activity yet.</Empty>}
        </Card>
      </div>
      <p className="muted small">Order value sums face amounts of USD and EUR orders as recorded in the source sheet.</p>
    </>
  );
}

