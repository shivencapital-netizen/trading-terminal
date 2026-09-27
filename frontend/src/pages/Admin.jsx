import { useEffect, useState } from "react";

const API_BASE = process.env.REACT_APP_API_BASE || "http://127.0.0.1:8000";

const themes = [
  {
    id: "light",
    name: "Light",
    description: "Bright surfaces with clear contrast for daytime use.",
    swatches: ["#f4f7fb", "#ffffff", "#2563eb"],
  },
  {
    id: "dark",
    name: "Dark",
    description: "Low-glare dark surfaces for focused market monitoring.",
    swatches: ["#0b1220", "#151f30", "#60a5fa"],
  },
];

export default function Admin({ theme, onThemeChange }) {
  const [monitors, setMonitors] = useState([]);
  const [alerts, setAlerts] = useState([]);
  const [message, setMessage] = useState("");
  const [form, setForm] = useState({
    name: "Intraday RSI",
    symbols: "ALL",
    rsi_period: 14,
    rsi_level: 59,
    direction: "both",
    sms_enabled: false,
    sms_phone: "",
  });

  const loadMonitorData = async () => {
    const [monitorResponse, alertResponse] = await Promise.all([
      fetch(`${API_BASE}/api/v1/admin/intraday-rsi/monitors`),
      fetch(`${API_BASE}/api/v1/admin/intraday-rsi/alerts?limit=100`),
    ]);
    if (!monitorResponse.ok || !alertResponse.ok) throw new Error("Could not load intraday RSI monitors.");
    setMonitors(await monitorResponse.json());
    setAlerts(await alertResponse.json());
  };

  useEffect(() => {
    loadMonitorData().catch((error) => setMessage(error.message));
    const timer = window.setInterval(() => loadMonitorData().catch(() => {}), 60000);
    return () => window.clearInterval(timer);
  }, []);

  const updateForm = (event) => {
    const { name, value, type, checked } = event.target;
    setForm((current) => ({ ...current, [name]: type === "checkbox" ? checked : value }));
  };

  const createMonitor = async (event) => {
    event.preventDefault();
    setMessage("");
    try {
      const response = await fetch(`${API_BASE}/api/v1/admin/intraday-rsi/monitors`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          ...form,
          rsi_period: Number(form.rsi_period),
          rsi_level: Number(form.rsi_level),
          symbols: form.symbols.split(",").map((symbol) => symbol.trim()).filter(Boolean),
        }),
      });
      const body = await response.json();
      if (!response.ok) throw new Error(body.detail || "Could not create monitor.");
      setForm((current) => ({ ...current, name: "Intraday RSI", sms_enabled: false, sms_phone: "" }));
      setMessage("Monitor saved. Click Start to begin scanning live one-minute candles.");
      await loadMonitorData();
    } catch (error) {
      setMessage(error.message);
    }
  };

  const setMonitorState = async (monitor, action) => {
    const response = await fetch(`${API_BASE}/api/v1/admin/intraday-rsi/monitors/${monitor.id}/${action}`, { method: "POST" });
    if (!response.ok) throw new Error("Could not update monitor.");
    await loadMonitorData();
  };

  const deleteMonitor = async (monitor) => {
    if (!window.confirm(`Delete ${monitor.name}?`)) return;
    await fetch(`${API_BASE}/api/v1/admin/intraday-rsi/monitors/${monitor.id}`, { method: "DELETE" });
    await loadMonitorData();
  };

  return (
    <main className="admin-page">
      <header className="admin-page__header">
        <p className="admin-page__eyebrow">WORKSPACE SETTINGS</p>
        <h1>Admin</h1>
        <p>Manage app-wide preferences. More workspace settings can be added here.</p>
      </header>

      <section className="admin-card" aria-labelledby="appearance-heading">
        <div className="admin-card__heading">
          <div>
            <h2 id="appearance-heading">Appearance</h2>
            <p>Choose how the trading terminal looks on this device.</p>
          </div>
        </div>

        <div className="theme-options" role="radiogroup" aria-labelledby="appearance-heading">
          {themes.map((option) => (
            <button
              key={option.id}
              type="button"
              role="radio"
              aria-checked={theme === option.id}
              className={`theme-option${theme === option.id ? " theme-option--selected" : ""}`}
              onClick={() => onThemeChange(option.id)}
            >
              <span className={`theme-preview theme-preview--${option.id}`} aria-hidden="true">
                <span className="theme-preview__sidebar" />
                <span className="theme-preview__content">
                  <span />
                  <span />
                  <span />
                </span>
              </span>
              <span className="theme-option__details">
                <span className="theme-option__title">{option.name}</span>
                <span className="theme-option__description">{option.description}</span>
                <span className="theme-option__swatches" aria-hidden="true">
                  {option.swatches.map((color) => (
                    <span key={color} style={{ backgroundColor: color }} />
                  ))}
                </span>
              </span>
              <span className="theme-option__indicator" aria-hidden="true">
                {theme === option.id ? "Selected" : "Select"}
              </span>
            </button>
          ))}
        </div>
      </section>

      <section className="admin-card" aria-labelledby="intraday-rsi-heading">
        <div className="admin-card__heading">
          <div>
            <h2 id="intraday-rsi-heading">Intraday RSI monitors</h2>
            <p>Configure a background scan of live one-minute candles. A crossover is evaluated once per candle.</p>
          </div>
        </div>
        <form className="intraday-monitor-form" onSubmit={createMonitor}>
          <label>Name<input name="name" value={form.name} onChange={updateForm} required /></label>
          <label>Symbols<input name="symbols" value={form.symbols} onChange={updateForm} placeholder="ALL or AAPL, MSFT, NVDA" required /></label>
          <label>RSI period<input name="rsi_period" type="number" min="2" max="100" value={form.rsi_period} onChange={updateForm} /></label>
          <label>RSI level<input name="rsi_level" type="number" min="0" max="100" step="0.1" value={form.rsi_level} onChange={updateForm} /></label>
          <label>Direction<select name="direction" value={form.direction} onChange={updateForm}><option value="both">Above and below</option><option value="up">Crossing above</option><option value="down">Crossing below</option></select></label>
          <label className="intraday-monitor-checkbox"><input name="sms_enabled" type="checkbox" checked={form.sms_enabled} onChange={updateForm} /> Send SMS alerts</label>
          <label>SMS phone<input name="sms_phone" value={form.sms_phone} onChange={updateForm} placeholder="+15551234567" /></label>
          <button type="submit">Save monitor</button>
        </form>
        {message && <p className="admin-message" role="status">{message}</p>}
        <div className="intraday-monitor-list">
          {monitors.map((monitor) => (
            <article className="intraday-monitor-row" key={monitor.id}>
              <div><strong>{monitor.name}</strong><span>{monitor.symbols.join(", ")} · RSI({monitor.rsi_period}) at {monitor.rsi_level} · {monitor.direction}</span></div>
              <div className="intraday-monitor-actions">
                <span className={monitor.is_active ? "monitor-live" : "monitor-stopped"}>{monitor.is_active ? "RUNNING" : "STOPPED"}</span>
                <button type="button" onClick={() => setMonitorState(monitor, monitor.is_active ? "stop" : "start")}>{monitor.is_active ? "Stop" : "Start"}</button>
                <button type="button" onClick={() => deleteMonitor(monitor)}>Delete</button>
              </div>
              {monitor.last_error && <small className="admin-error">{monitor.last_error}</small>}
            </article>
          ))}
        </div>
        <div className="intraday-alerts">
          <h3>Recent crossovers</h3>
          {alerts.length === 0 ? <p>No RSI crossovers detected yet.</p> : (
            <table><thead><tr><th>Stock</th><th>Signal</th><th>RSI</th><th>Time</th><th>Close</th></tr></thead><tbody>
              {alerts.map((alert) => <tr key={alert.id}><td>{alert.symbol}</td><td>{alert.direction === "up" ? "Crossed above" : "Crossed below"} {alert.rsi_level}</td><td>{alert.rsi_previous.toFixed(2)} → {alert.rsi_current.toFixed(2)}</td><td>{new Date(alert.candle_timestamp).toLocaleTimeString([], { hour: "numeric", minute: "2-digit" })}</td><td>${alert.close.toFixed(2)}</td></tr>)}
            </tbody></table>
          )}
        </div>
      </section>
    </main>
  );
}
