import { Component } from 'react';

// Shows the real error instead of a blank white screen if any component throws while rendering.
export default class ErrorBoundary extends Component {
  constructor(props) { super(props); this.state = { error: null }; }
  static getDerivedStateFromError(error) { return { error }; }
  componentDidCatch(error, info) { console.error('Control Tower crashed:', error, info); }
  render() {
    if (!this.state.error) return this.props.children;
    return (
      <div style={{ padding: 32, fontFamily: 'system-ui, sans-serif', maxWidth: 720, margin: '40px auto' }}>
        <h2 style={{ color: '#b42318' }}>Something went wrong</h2>
        <p>The application hit an error. Your data is stored in Odoo and has not been affected.</p>
        <pre style={{ background: '#f4f4f4', padding: 12, borderRadius: 8, whiteSpace: 'pre-wrap' }}>{String(this.state.error?.stack || this.state.error)}</pre>
        <button onClick={() => window.location.reload()} style={{ padding: '8px 16px', cursor: 'pointer' }}>Reload</button>
      </div>
    );
  }
}
