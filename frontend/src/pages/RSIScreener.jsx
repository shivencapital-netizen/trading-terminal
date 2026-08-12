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

export default function RSIScreener() {
  const [activeTab, setActiveTab] = useState("clear");
  const [rsiPeriod, setRsiPeriod] = useState(14);
  const [rsiLevel, setRsiLevel] = useState(59);
  const [direction, setDirection] = useState("above");
  const [symbolContains, setSymbolContains] = useState("");

  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [message, setMessage] = useState("");
  const [rows, setRows] = useState([]);

  const buildParams = () => {
    const params = new URLSearchParams({
      rsi_period: String(rsiPeriod),
      rsi_level: String(rsiLevel),
      direction,
    });
    if (symbolContains.trim()) {
      params.set("symbol_contains", symbolContains.trim().toUpperCase());
    }
    return params;
  };

  const refreshCache = async () => {
    setLoading(true);
    setError("");
    setMessage("Refreshing RSI cache...");

    try {
      const params = buildParams();
      const res = await fetch(`${API_BASE}/api/v1/screener/rsi-cross/cache/refresh?${params.toString()}`, {
        method: "POST",
      });
      const data = await parseJsonResponse(res);

      if (!res.ok) {
        setError(data.detail || "Failed to refresh RSI cache");
      } else {
        setMessage(`Cache refreshed. Saved ${data.count || 0} symbols for RSI ${rsiLevel}.`);
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
    setMessage("Clearing cached RSI rows...");

    try {
      const params = buildParams();
      const res = await fetch(`${API_BASE}/api/v1/screener/rsi-cross/cache/clear?${params.toString()}`, {
        method: "POST",
      });
      const data = await parseJsonResponse(res);

      if (!res.ok) {
        setError(data.detail || "Failed to clear RSI cache");
      } else {
        setMessage(`Cleared ${data.count || 0} cached rows for RSI ${rsiLevel}.`);
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
      const res = await fetch(`${API_BASE}/api/v1/screener/rsi-cross/cache?${params.toString()}`);
      const data = await parseJsonResponse(res);

      if (!res.ok) {
        setError(data.detail || "Failed to load RSI signals");
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
            background: "linear-gradient(120deg, #0b3d91 0%, #1c6dd0 100%)",
            color: "white",
            borderRadius: "14px",
            padding: "20px 24px",
            boxShadow: "0 8px 24px rgba(11, 61, 145, 0.25)",
            marginBottom: "18px",
          }}
        >
          <h1 style={{ margin: 0, fontSize: "30px", letterSpacing: "0.3px" }}>RSI Screener</h1>
          <div style={{ marginTop: "8px", fontSize: "15px", opacity: 0.95 }}>
            Daily RSI threshold crossover scan
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
              <Field label="RSI Period">
                <input
                  type="number"
                  min={2}
                  max={200}
                  value={rsiPeriod}
                  onChange={(e) => setRsiPeriod(Number(e.target.value || 14))}
                  style={inputStyle}
                />
              </Field>

              <Field label="RSI Value">
                <input
                  type="number"
                  min={0}
                  max={100}
                  step={0.1}
                  value={rsiLevel}
                  onChange={(e) => setRsiLevel(Number(e.target.value || 59))}
                  style={inputStyle}
                />
              </Field>

              <Field label="Cross Direction">
                <select value={direction} onChange={(e) => setDirection(e.target.value)} style={inputStyle}>
                  <option value="above">Crossed Above (from below)</option>
                  <option value="below">Crossed Below (from above)</option>
                </select>
              </Field>

              <Field label="Symbol Contains">
                <input
                  value={symbolContains}
                  onChange={(e) => setSymbolContains(e.target.value.toUpperCase())}
                  placeholder="e.g. AAPL or AA"
                  style={inputStyle}
                />
              </Field>

              {activeTab === "clear" && (
                <button type="button" onClick={clearCache} disabled={loading} style={getDangerActionStyle(loading)}>
                  Clear RSI Cache
                </button>
              )}

              {activeTab === "refresh" && (
                <button type="button" onClick={refreshCache} disabled={loading} style={getPrimaryActionStyle(loading)}>
                  Refresh RSI Cache
                </button>
              )}

              {activeTab === "screen" && (
                <button type="button" onClick={loadSavedSignals} disabled={loading} style={getPrimaryActionStyle(loading)}>
                  {loading ? "Loading..." : "Load Screening Results"}
                </button>
              )}
            </div>
          )}
        </div>

        {message && (
          <div style={{ background: "#dcfce7", color: "#166534", padding: "10px 12px", borderRadius: "8px", marginBottom: "12px" }}>
            {message}
          </div>
        )}

        {error && (
          <div style={{ background: "#fee2e2", color: "#991b1b", padding: "10px 12px", borderRadius: "8px", marginBottom: "12px" }}>
            {error}
          </div>
        )}

        {activeTab === "screen" && (
          <div
            style={{
              background: "white",
              borderRadius: "12px",
              border: "1px solid #e4e8f0",
              overflow: "hidden",
            }}
          >
            <div style={{ padding: "10px 14px", borderBottom: "1px solid #e9edf3", fontWeight: 700 }}>
              Matches: {rows.length}
            </div>
            <div style={{ overflowX: "auto" }}>
              <table style={{ width: "100%", borderCollapse: "collapse", minWidth: "1200px" }}>
                <thead>
                  <tr style={{ background: "#f8fafc" }}>
                    <th style={thStyle}>Symbol</th>
                    <th style={thStyle}>Signal Date</th>
                    <th style={thStyle}>Open</th>
                    <th style={thStyle}>Last</th>
                    <th style={thStyle}>% Change</th>
                    <th style={thStyle}>Prev Close</th>
                    <th style={thStyle}>RSI Prev</th>
                    <th style={thStyle}>RSI Curr</th>
                    <th style={thStyle}>RSI Level</th>
                    <th style={thStyle}>Direction</th>
                    <th style={thStyle}>Source Updated</th>
                    <th style={thStyle}>Cached At</th>
                  </tr>
                </thead>
                <tbody>
                  {rows.length === 0 && (
                    <tr>
                      <td colSpan={12} style={{ padding: "16px", color: "#6b7280", textAlign: "center" }}>
                        No screening results loaded yet. Click Load Screening Results.
                      </td>
                    </tr>
                  )}

                  {rows.map((row) => {
                    const up = (row.percent_change ?? 0) > 0;
                    const down = (row.percent_change ?? 0) < 0;
                    return (
                      <tr key={`${row.symbol}-${row.signal_date || ""}-${row.rsi_period}-${row.rsi_level}-${row.direction}`} style={{ borderTop: "1px solid #eef2f7" }}>
                        <td style={tdSymbol}>
                          <a
                            href={getYahooChartUrl(row.symbol)}
                            target="_blank"
                            rel="noopener noreferrer"
                            style={{ color: "#1d4ed8", textDecoration: "none" }}
                            title={`Open ${row.symbol} in Yahoo Finance`}
                          >
                            {row.symbol}
                          </a>
                        </td>
                        <td style={tdText}>{row.signal_date || "-"}</td>
                        <td style={tdNum}>{formatNum(row.open)}</td>
                        <td style={tdNum}>{formatNum(row.last_price)}</td>
                        <td style={{ ...tdNum, color: up ? "#0f9d58" : down ? "#d93025" : "#475467", fontWeight: 700 }}>
                          {row.percent_change != null ? `${row.percent_change.toFixed(2)}%` : "-"}
                        </td>
                        <td style={tdNum}>{formatNum(row.prev_day_close)}</td>
                        <td style={tdNum}>{formatNum(row.rsi_prev, 4)}</td>
                        <td style={tdNum}>{formatNum(row.rsi_curr, 4)}</td>
                        <td style={tdNum}>{formatNum(row.rsi_level, 2)}</td>
                        <td style={tdText}>{String(row.direction || "-").toUpperCase()}</td>
                        <td style={tdText}>{row.updated_at ? new Date(row.updated_at).toLocaleString() : "-"}</td>
                        <td style={tdText}>{row.cached_at ? new Date(row.cached_at).toLocaleString() : "-"}</td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

function Field({ label, children }) {
  return (
    <div style={{ display: "flex", flexDirection: "column", gap: "6px" }}>
      <label style={{ fontWeight: 700, fontSize: "13px", color: "#344054" }}>{label}</label>
      {children}
    </div>
  );
}

const inputStyle = {
  width: "100%",
  border: "1px solid #d0d5dd",
  borderRadius: "8px",
  padding: "9px 10px",
  fontSize: "14px",
  background: "white",
};

const thStyle = {
  textAlign: "left",
  fontSize: "12px",
  color: "#344054",
  fontWeight: 700,
  padding: "10px 12px",
};

const tdBase = {
  padding: "10px 12px",
  fontSize: "13px",
};

const tdSymbol = {
  ...tdBase,
  fontWeight: 700,
  color: "#1d4ed8",
};

const tdNum = {
  ...tdBase,
  textAlign: "right",
  fontVariantNumeric: "tabular-nums",
};

const tdText = {
  ...tdBase,
  color: "#475467",
};

function getTabStyle(active) {
  return {
    padding: "10px 16px",
    borderRadius: "12px",
    border: active ? "1px solid rgba(37, 99, 235, 0.18)" : "1px solid transparent",
    background: active ? "linear-gradient(180deg, #ffffff 0%, #f8fbff 100%)" : "transparent",
    color: active ? "#1d4ed8" : "#475467",
    fontWeight: 800,
    cursor: "pointer",
    boxShadow: active ? "0 6px 18px rgba(37, 99, 235, 0.10)" : "none",
    transition: "all 150ms ease",
  };
}

function getPrimaryActionStyle(loading) {
  return {
    padding: "10px 16px",
    borderRadius: "12px",
    border: "none",
    background: loading ? "#98a2b3" : "linear-gradient(135deg, #2563eb 0%, #1d4ed8 100%)",
    color: "white",
    fontWeight: 800,
    cursor: loading ? "not-allowed" : "pointer",
    boxShadow: loading ? "none" : "0 10px 20px rgba(37, 99, 235, 0.18)",
    transition: "transform 120ms ease, box-shadow 120ms ease, opacity 120ms ease",
  };
}

function getDangerActionStyle(loading) {
  return {
    padding: "10px 16px",
    borderRadius: "12px",
    border: "none",
    background: loading ? "#98a2b3" : "linear-gradient(135deg, #dc2626 0%, #b42318 100%)",
    color: "white",
    fontWeight: 800,
    cursor: loading ? "not-allowed" : "pointer",
    boxShadow: loading ? "none" : "0 10px 20px rgba(180, 35, 24, 0.16)",
    transition: "transform 120ms ease, box-shadow 120ms ease, opacity 120ms ease",
  };
}
