import Shell from './components/Shell.jsx';
import EditorHost from './components/EditorHost.jsx';
import ShipmentDetail from './components/ShipmentDetail.jsx';
import { StoreProvider } from './lib/store.jsx';
import { NavProvider, useNav } from './lib/nav.jsx';
import Dashboard from './pages/Dashboard.jsx';
import POs from './pages/POs.jsx';
import Shipments from './pages/Shipments.jsx';
import Tracking from './pages/Tracking.jsx';
import Payments from './pages/Payments.jsx';
import Suppliers from './pages/Suppliers.jsx';
import Documents from './pages/Documents.jsx';
import Alerts from './pages/Alerts.jsx';
import Reports from './pages/Reports.jsx';
import Settings from './pages/Settings.jsx';

const PAGE = { dashboard: Dashboard, pos: POs, shipments: Shipments, tracking: Tracking, payments: Payments, suppliers: Suppliers, documents: Documents, alerts: Alerts, reports: Reports, settings: Settings };

function Routes() {
  const { page } = useNav();
  const Page = PAGE[page] || Dashboard;
  return (
    <Shell>
      <Page />
      <ShipmentDetail />
      <EditorHost />
    </Shell>
  );
}

// Authentication is handled by Odoo (login + access groups); the app only needs the JSON-RPC function.
export default function App({ rpc }) {
  return (
    <StoreProvider rpc={rpc}>
      <NavProvider>
        <Routes />
      </NavProvider>
    </StoreProvider>
  );
}
