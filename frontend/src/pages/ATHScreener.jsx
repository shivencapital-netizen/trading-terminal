import { useState } from "react";

const API_BASE = process.env.REACT_APP_API_BASE || "http://127.0.0.1:8000";

const parseJsonResponse = async (res) => {
  const text = await res.text();
  if (!text) return {};
  try {
    return JSON.parse(text);
  } catch {
    return { detail: text };
  }
};

const getYahooChartUrl = (symbol) =>
  `https://finance.yahoo.com/chart/${encodeURIComponent(String(symbol || "").toUpperCase())}`;

const inputStyle = {
  width: "100%",
  padding: "10px 12px",
  borderRadius: "10px",
  border: "1px solid #d1d5db",
  background: "#fff",
  fontSize: "14px",
};

const getTabStyle = (active) => ({
  padding: "10px 16px",
  borderRadius: "10px",
  border: "1px solid #dbe4f0",
  background: active ? "#0f6fff" : "#f8fafc",
  color: active ? "white" : "#1f2937",
  fontWeight: 600,
  cursor: "pointer",
});

export default function ATHScreener() {
  const [activeTab, setActiveTab] = useState("clear");
  const [direction, setDirection] = useState("above");
  const [symbolContains, setSymbolContains] = useState("");
  const [minHistoryDays, setMinHistoryDays] = useState(30);

  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [message, setMessage] = useState("");
  const [rows, setRows] = useState([]);

  const buildParams = () => {
    const params = new URLSearchParams({
      direction,
      min_history_days: String(minHistoryDays),
    });
    if (symbolContains.trim()) {
      params.set("symbol_contains", symbolContains.trim().toUpperCase());
    }
    return params;
  };

  const refreshCache = async () => {
    setLoading(true);
    setError("");
    setMessage("Refreshing ATH cache...");

    try {
      const params = buildParams();
      const res = await fetch(`${API_BASE}/api/v1/screener/ath-cross/cache/refresh?${params.toString()}`, {
        method: "POST",
      });
      const data = await parseJsonResponse(res);

      if (!res.ok) {
        setError(data.detail || "Failed to refresh ATH cache");
      } else {
        setMessage(`Cache refreshed. Saved ${data.count || 0} symbols for ${direction} ATH crossings.`);
      }
    } catch (err) {
      setError(err.message || "Request failed");
    } finally {
      setLoading(false);
    }
  };

  const clearCache = async () => {
    setLoading(true);
    setError("");
    setMessage("Clearing cached ATH rows...");

    try {
      const params = buildParams();
      const res = await fetch(`${API_BASE}/api/v1/screener/ath-cross/cache/clear?${params.toString()}`, {
        method: "POST",
      });
      const data = await parseJsonResponse(res);

      if (!res.ok) {
        setError(data.detail || "Failed to clear ATH cache");
      } else {
        setMessage(`Cleared ${data.count || 0} cached rows for ATH ${direction}.`);
        setRows([]);
      }
    } catch (err) {
      setError(err.message || "Request failed");
    } finally {
      setLoading(false);
    }
  };

  const loadSavedSignals = async () => {
    setLoading(true);
    setError("");
    setMessage("");

    try {
      const params = buildParams();
      const res = await fetch(`${API_BASE}/api/v1/screener/ath-cross/cache?${params.toString()}`);
      const data = await parseJsonResponse(res);

      if (!res.ok) {
        setError(data.detail || "Failed to load ATH signals");
        setRows([]);
      } else {
        setRows(Array.isArray(data) ? data : []);
      }
    } catch (err) {
      setError(err.message || "Request failed");
      setRows([]);
    } finally {
      setLoading(false);
    }
  };

  const formatNum = (n, digits = 2) =>
    typeof n === "number" ? n.toLocaleString("en-US", { maximumFractionDigits: digits }) : "-";

  return (
    <div style={{ padding: "24px", background: "#f3f5f9", minHeight: "100%" }}>
      <div style={{ maxWidth: "1400px", margin: "0 auto" }}>
        <div
          style={{
            background: "linear-gradient(120deg, #0f172a 0%, #1d4ed8 100%)",
            color: "white",
            borderRadius: "14px",
            padding: "20px 24px",
            boxShadow: "0 8px 24px rgba(15, 23, 42, 0.25)",
            marginBottom: "18px",
          }}
        >
          <h1 style={{ margin: 0, fontSize: "30px", letterSpacing: "0.3px" }}>All-Time High Screener</h1>
          <div style={{ marginTop: "8px", fontSize: "15px", opacity: 0.95 }}>
            Finds symbols that crossed a new all-time high on the latest trading day
          </div>
        </div>

        <div
          style={{
            background: "rgba(255,255,255,0.92)",
            borderRadius: "18px",
            border: "1px solid rgba(229, 231, 235, 0.9)",
            padding: "12px 12px 0",
            boxShadow: "0 10px 30px rgba(15, 23, 42, 0.06)",
            marginBottom: "14px",
          }}
        >
          <div
            style={{
              display: "flex",
              gap: "8px",
              flexWrap: "wrap",
              marginBottom: "12px",
              padding: "6px",
              borderRadius: "14px",
              background: "#f8fafc",
              border: "1px solid #e5e7eb",
            }}
          >
            <button type="button" onClick={() => setActiveTab("clear")} style={getTabStyle(activeTab === "clear")}>
              Clear
            </button>
            <button type="button" onClick={() => setActiveTab("refresh")} style={getTabStyle(activeTab === "refresh")}>
              Refresh
            </button>
            <button type="button" onClick={() => setActiveTab("screen")} style={getTabStyle(activeTab === "screen")}>
              Screening Results
            </button>
          </div>

          {(activeTab === "clear" || activeTab === "refresh" || activeTab === "screen") && (
            <div
              style={{
                borderTop: "1px solid #e4e8f0",
                padding: "18px 4px 18px",
                display: "grid",
                gridTemplateColumns: "repeat(auto-fit, minmax(180px, 1fr))",
                gap: "12px",
                alignItems: "end",
              }}
            >
              <div>
                <label style={{ display: "block", marginBottom: "6px", fontWeight: 600 }}>Direction</label>
                <select value={direction} onChange={(e) => setDirection(e.target.value)} style={inputStyle}>
                  <option value="above">Crossed Above ATH</option>
                  <option value="below">Crossed Below ATH</option>
                </select>
              </div>

              <div>
                <label style={{ display: "block", marginBottom: "6px", fontWeight: 600 }}>Min History Days</label>
                <input
                  type="number"
                  min={2}
                  max={3650}
                  value={minHistoryDays}
                  onChange={(e) => setMinHistoryDays(Number(e.target.value || 30))}
                  style={inputStyle}
                />
              </div>

              <div>
                <label style={{ display: "block", marginBottom: "6px", fontWeight: 600 }}>Symbol Contains</label>
                <input
                  value={symbolContains}
                  onChange={(e) => setSymbolContains(e.target.value.toUpperCase())}
                  placeholder="e.g. AAPL or MSFT"
                  style={inputStyle}
                />
              </div>

              {activeTab === "clear" && (
                <button
                  type="button"
                  onClick={clearCache}
                  disabled={loading}
                  style={{ ...inputStyle, background: "#ef4444", color: "white", border: "none", height: "42px" }}
                >
                  {loading ? "Working..." : "Clear Cache"}
                </button>
              )}

              {activeTab === "refresh" && (
                <button
                  type="button"
                  onClick={refreshCache}
                  disabled={loading}
                  style={{ ...inputStyle, background: "#2563eb", color: "white", border: "none", height: "42px" }}
                >
                  {loading ? "Working..." : "Refresh Cache"}
                </button>
              )}

              {activeTab === "screen" && (
                <button
                  type="button"
                  onClick={loadSavedSignals}
                  disabled={loading}
                  style={{ ...inputStyle, background: "#059669", color: "white", border: "none", height: "42px" }}
                >
                  {loading ? "Loading..." : "Load Signals"}
                </button>
              )}
            </div>
          )}

          {error && (
            <div style={{ color: "#b91c1c", background: "#fef2f2", border: "1px solid #fecaca", padding: "12px 14px", borderRadius: "10px", margin: "0 4px 14px" }}>
              {error}
            </div>
          )}

          {message && (
            <div style={{ color: "#166534", background: "#ecfdf5", border: "1px solid #a7f3d0", padding: "10px 14px", borderRadius: "10px", margin: "0 4px 14px" }}>
              {message}
            </div>
          )}
        </div>

        <div style={{ background: "white", borderRadius: "14px", border: "1px solid #e5e7eb", overflow: "hidden" }}>
          <table style={{ width: "100%", borderCollapse: "collapse" }}>
            <thead>
              <tr style={{ background: "#f8fafc" }}>
                <th style={cellStyle}>Symbol</th>
                <th style={cellStyle}>Last</th>
                <th style={cellStyle}>Prev Close</th>
                <th style={cellStyle}>Prev ATH</th>
                <th style={cellStyle}>% Change</th>
                <th style={cellStyle}>Updated</th>
                <th style={cellStyle}>Chart</th>
              </tr>
            </thead>
            <tbody>
              {rows.map((row) => (
                <tr key={`${row.symbol}-${row.updated_at || row.signal_date}`} style={{ borderTop: "1px solid #eef2f7" }}>
                  <td style={cellStyle}><strong>{row.symbol}</strong></td>
                  <td style={cellStyle}>{formatNum(row.last_price, 2)}</td>
                  <td style={cellStyle}>{formatNum(row.prev_day_close, 2)}</td>
                  <td style={cellStyle}>{formatNum(row.previous_high, 2)}</td>
                  <td style={{ ...cellStyle, color: Number(row.percent_change) >= 0 ? "#15803d" : "#b91c1c", fontWeight: 700 }}>
                    {formatNum(row.percent_change, 2)}%
                  </td>
                  <td style={cellStyle}>{row.updated_at ? new Date(row.updated_at).toLocaleString() : "-"}</td>
                  <td style={cellStyle}>
                    <a href={getYahooChartUrl(row.symbol)} target="_blank" rel="noreferrer" style={{ color: "#2563eb" }}>
                      Yahoo
                    </a>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}

const cellStyle = {
  padding: "12px 14px",
  textAlign: "left",
  fontSize: "14px",
  whiteSpace: "nowrap",
};
