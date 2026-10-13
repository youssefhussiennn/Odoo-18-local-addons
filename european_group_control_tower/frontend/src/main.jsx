import { StrictMode } from 'react';
import { createRoot } from 'react-dom/client';
import css from './styles.css?inline';
import App from './App.jsx';
import ErrorBoundary from './components/ErrorBoundary.jsx';

// Entry point used by the Odoo client action:  const handle = window.EGControlTower.mount(el, { rpc });
//   rpc(route, params) -> Promise<result>   (Odoo's JSON-RPC helper; rejects with an RPCError on server errors)
// The app renders inside a Shadow DOM so its stylesheet never leaks into (or is changed by) Odoo's Bootstrap CSS.
export function mount(el, { rpc }) {
  const host = document.createElement('div');
  host.style.cssText = 'display:block;height:100%;';
  el.appendChild(host);
  const shadow = host.attachShadow({ mode: 'open' });
  const style = document.createElement('style');
  style.textContent = css;
  shadow.appendChild(style);
  const container = document.createElement('div');
  container.className = 'egct-app';
  shadow.appendChild(container);

  const root = createRoot(container);
  root.render(
    <StrictMode>
      <ErrorBoundary>
        <App rpc={rpc} />
      </ErrorBoundary>
    </StrictMode>,
  );
  return {
    unmount() {
      root.unmount();
      host.remove();
    },
  };
}
