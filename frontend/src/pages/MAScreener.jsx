import { useMemo, useState } from "react";

const API_BASE = process.env.REACT_APP_API_BASE || "http://127.0.0.1:8000";
const MA_OPTIONS = ["SMA", "EMA", "WMA"];
const PERIOD_OPTIONS = [5, 10, 20, 50, 100, 200];

const parseJsonResponse = async (res) => {
  const text = await res.text();
  if (!text) return {};
  try {
    return JSON.parse(text);
  } catch {
    return { detail: text };
  }
};

const getTradingViewUrl = (symbol) =>
  `https://www.tradingview.com/chart/?symbol=${encodeURIComponent(String(symbol || "").toUpperCase())}`;

export default function MAScreener() {
  const [activeTab, setActiveTab] = useState("clear");
  const [selectedFamily, setSelectedFamily] = useState("EMA");
  const [fastPeriod, setFastPeriod] = useState(10);
  const [slowPeriod, setSlowPeriod] = useState(50);
  const [direction, setDirection] = useState("above");
  const [symbolContains, setSymbolContains] = useState("");

  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [message, setMessage] = useState("");
  const [rows, setRows] = useState([]);

  const queryLabel = useMemo(() => {
    const dirText = direction === "above" ? "from below (crossed above)" : "from above (crossed below)";
    return `${selectedFamily} family across all fast/slow period pairs ${dirText}`;
  }, [selectedFamily, direction]);

  const selectFamily = (family) => {
    setSelectedFamily(family);
  };

  const buildParams = ({ familyBatch = false } = {}) => {
    const params = new URLSearchParams({
      fast_period: String(fastPeriod),
      slow_period: String(slowPeriod),
      fast_ma: selectedFamily,
      slow_ma: selectedFamily,
      direction,
    });
    if (familyBatch) {
      params.set("ma_family", selectedFamily);
    }
    if (symbolContains.trim()) {
      params.set("symbol_contains", symbolContains.trim().toUpperCase());
    }
    return params;
  };

  const refreshAllCache = async () => {
    setLoading(true);
    setError("");
    setMessage("⏳ Refreshing precomputed MA cache...");

    try {
      const params = buildParams({ familyBatch: true });
      const res = await fetch(`${API_BASE}/api/v1/screener/ma-cross/cache/refresh?${params.toString()}`, {
        method: "POST",
      });
      const data = await parseJsonResponse(res);

      if (!res.ok) {
        setError(data.detail || "Failed to refresh MA cache");
      } else {
        if (data.combinations) {
          setMessage(`✅ ${data.ma_family || selectedFamily} cache refreshed. Saved ${data.count || 0} signals across ${data.combinations} period pairs.`);
        } else {
          setMessage(`✅ Cache refreshed. Saved ${data.count || 0} signals.`);
        }
      }
    } catch (err) {
      setError(err.message || "Request failed");
    } finally {
      setLoading(false);
    }
  };

  const clearAllCache = async () => {
    setLoading(true);
    setError("");
    setMessage("⏳ Clearing cached MA rows...");

    try {
      const params = buildParams({ familyBatch: true });
      const res = await fetch(`${API_BASE}/api/v1/screener/ma-cross/cache/clear?${params.toString()}`, {
        method: "POST",
      });
      const data = await parseJsonResponse(res);

      if (!res.ok) {
        setError(data.detail || "Failed to clear MA cache");
      } else {
        const combosText = data.combinations ? ` across ${data.combinations} period pairs` : "";
        setMessage(`✅ Cleared ${data.count || 0} cached rows for ${data.ma_family || selectedFamily}${combosText}.`);
        setRows([]);
      }
    } catch (err) {
      setError(err.message || "Request failed");
    } finally {
      setLoading(false);
    }
  };

  const clearSelectedCache = async () => {
    setLoading(true);
    setError("");
    setMessage("⏳ Clearing selected cached MA pair...");

    try {
      const params = buildParams();
      const res = await fetch(`${API_BASE}/api/v1/screener/ma-cross/cache/clear?${params.toString()}`, {
        method: "POST",
      });
      const data = await parseJsonResponse(res);

      if (!res.ok) {
        setError(data.detail || "Failed to clear MA cache");
      } else {
        setMessage(`✅ Cleared ${data.count || 0} cached rows for ${selectedFamily} ${fastPeriod}/${slowPeriod}.`);
        setRows([]);
      }
    } catch (err) {
      setError(err.message || "Request failed");
    } finally {
      setLoading(false);
    }
  };

  const refreshSelectedCache = async () => {
    setLoading(true);
    setError("");
    setMessage("⏳ Refreshing selected MA pair...");

    try {
      const params = buildParams();
      const res = await fetch(`${API_BASE}/api/v1/screener/ma-cross/cache/refresh?${params.toString()}`, {
        method: "POST",
      });
      const data = await parseJsonResponse(res);

      if (!res.ok) {
        setError(data.detail || "Failed to refresh MA cache");
      } else {
        setMessage(`✅ Refreshed ${selectedFamily} ${fastPeriod}/${slowPeriod}. Saved ${data.count || 0} signals.`);
        await loadSelectedSignals();
      }
    } catch (err) {
      setError(err.message || "Request failed");
    } finally {
      setLoading(false);
    }
  };

  const loadSavedSignals = async (familyBatch = true) => {
    setLoading(true);
    setError("");
    setMessage("");

    try {
      const params = buildParams({ familyBatch });
      const res = await fetch(`${API_BASE}/api/v1/screener/ma-cross/cache?${params.toString()}`);
      const data = await parseJsonResponse(res);

      if (!res.ok) {
        setError(data.detail || "Failed to load saved MA signals");
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

  const loadSelectedSignals = async () => loadSavedSignals(false);

  const formatNum = (n, digits = 2) => (typeof n === "number" ? n.toLocaleString("en-US", { maximumFractionDigits: digits }) : "-");

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
          <h1 style={{ margin: 0, fontSize: "30px", letterSpacing: "0.3px" }}>Moving Average Screener</h1>
          <div style={{ marginTop: "8px", fontSize: "15px", opacity: 0.95 }}>{queryLabel}</div>
        </div>

        <div
          style={{
            background: "white",
            borderRadius: "12px",
            border: "1px solid #e4e8f0",
            padding: "12px 14px 0",
            marginBottom: "14px",
          }}
        >
          <div style={{ display: "flex", gap: "10px", flexWrap: "wrap", marginBottom: "10px" }}>
            <button
              type="button"
              onClick={() => setActiveTab("clear")}
              style={{
                padding: "10px 16px",
                borderRadius: "10px 10px 0 0",
                border: "1px solid #d0d5dd",
                borderBottom: activeTab === "clear" ? "1px solid white" : "1px solid #d0d5dd",
                background: activeTab === "clear" ? "white" : "#f8fafc",
                fontWeight: 700,
                cursor: "pointer",
              }}
            >
              Clear
            </button>
            <button
              type="button"
              onClick={() => setActiveTab("refresh")}
              style={{
                padding: "10px 16px",
                borderRadius: "10px 10px 0 0",
                border: "1px solid #d0d5dd",
                borderBottom: activeTab === "refresh" ? "1px solid white" : "1px solid #d0d5dd",
                background: activeTab === "refresh" ? "white" : "#f8fafc",
                fontWeight: 700,
                cursor: "pointer",
              }}
            >
              Refresh
            </button>
            <button
              type="button"
              onClick={() => setActiveTab("screen")}
              style={{
                padding: "10px 16px",
                borderRadius: "10px 10px 0 0",
                border: "1px solid #d0d5dd",
                borderBottom: activeTab === "screen" ? "1px solid white" : "1px solid #d0d5dd",
                background: activeTab === "screen" ? "white" : "#f8fafc",
                fontWeight: 700,
                cursor: "pointer",
              }}
            >
              Screening Results
            </button>
          </div>

          {activeTab === "refresh" && (
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
              <div style={{ gridColumn: "1 / -1", display: "flex", gap: "10px", flexWrap: "wrap" }}>
                {MA_OPTIONS.map((family) => (
                  <button
                    key={family}
                    type="button"
                    onClick={() => selectFamily(family)}
                    style={{
                      padding: "9px 14px",
                      borderRadius: "10px",
                      border: selectedFamily === family ? "1px solid #2563eb" : "1px solid #d0d5dd",
                      background: selectedFamily === family ? "#dbeafe" : "#fff",
                      color: selectedFamily === family ? "#1d4ed8" : "#344054",
                      fontWeight: 800,
                      cursor: "pointer",
                      height: "42px",
                    }}
                  >
                    {family}
                  </button>
                ))}
              </div>

              <div style={{ gridColumn: "1 / -1", display: "flex", gap: "10px", flexWrap: "wrap" }}>
                <button
                  type="button"
                  onClick={refreshAllCache}
                  disabled={loading}
                  style={{
                    padding: "10px 16px",
                    borderRadius: "10px",
                    border: "none",
                    background: loading ? "#98a2b3" : "#2563eb",
                    color: "white",
                    fontWeight: 800,
                    cursor: loading ? "not-allowed" : "pointer",
                  }}
                >
                  Refresh All {selectedFamily}
                </button>
                <button
                  type="button"
                  onClick={refreshSelectedCache}
                  disabled={loading}
                  style={{
                    padding: "10px 16px",
                    borderRadius: "10px",
                    border: "1px solid #d0d5dd",
                    background: loading ? "#98a2b3" : "#fff",
                    fontWeight: 700,
                    cursor: loading ? "not-allowed" : "pointer",
                  }}
                >
                  Refresh Selected Pair
                </button>
              </div>

              <Field label="Fast Period">
                <select value={fastPeriod} onChange={(e) => setFastPeriod(Number(e.target.value))} style={inputStyle}>
                  {PERIOD_OPTIONS.map((p) => (
                    <option key={p} value={p}>{p}</option>
                  ))}
                </select>
              </Field>

              <Field label="Slow Period">
                <select value={slowPeriod} onChange={(e) => setSlowPeriod(Number(e.target.value))} style={inputStyle}>
                  {PERIOD_OPTIONS.map((p) => (
                    <option key={p} value={p}>{p}</option>
                  ))}
                </select>
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

              <div style={{ gridColumn: "1 / -1", color: "#667085", fontSize: "13px" }}>
                Use Refresh All to rebuild every {selectedFamily} period pair, or Refresh Selected Pair for the dropdown values.
              </div>
            </div>
          )}

          {activeTab === "clear" && (
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
              <div style={{ gridColumn: "1 / -1", display: "flex", gap: "10px", flexWrap: "wrap" }}>
                {MA_OPTIONS.map((family) => (
                  <button
                    key={family}
                    type="button"
                    onClick={() => selectFamily(family)}
                    style={{
                      padding: "9px 14px",
                      borderRadius: "10px",
                      border: selectedFamily === family ? "1px solid #2563eb" : "1px solid #d0d5dd",
                      background: selectedFamily === family ? "#dbeafe" : "#fff",
                      color: selectedFamily === family ? "#1d4ed8" : "#344054",
                      fontWeight: 800,
                      cursor: "pointer",
                      height: "42px",
                    }}
                  >
                    {family}
                  </button>
                ))}
              </div>

              <div style={{ gridColumn: "1 / -1", display: "flex", gap: "10px", flexWrap: "wrap" }}>
                <button
                  type="button"
                  onClick={clearAllCache}
                  disabled={loading}
                  style={{
                    padding: "10px 16px",
                    borderRadius: "10px",
                    border: "none",
                    background: loading ? "#98a2b3" : "#b42318",
                    color: "white",
                    fontWeight: 800,
                    cursor: loading ? "not-allowed" : "pointer",
                  }}
                >
                  Clear All {selectedFamily}
                </button>
                <button
                  type="button"
                  onClick={clearSelectedCache}
                  disabled={loading}
                  style={{
                    padding: "10px 16px",
                    borderRadius: "10px",
                    border: "1px solid #d0d5dd",
                    background: loading ? "#98a2b3" : "#fff",
                    fontWeight: 700,
                    cursor: loading ? "not-allowed" : "pointer",
                  }}
                >
                  Clear Selected Pair
                </button>
              </div>

              <Field label="Fast Period">
                <select value={fastPeriod} onChange={(e) => setFastPeriod(Number(e.target.value))} style={inputStyle}>
                  {PERIOD_OPTIONS.map((p) => (
                    <option key={p} value={p}>{p}</option>
                  ))}
                </select>
              </Field>

              <Field label="Slow Period">
                <select value={slowPeriod} onChange={(e) => setSlowPeriod(Number(e.target.value))} style={inputStyle}>
                  {PERIOD_OPTIONS.map((p) => (
                    <option key={p} value={p}>{p}</option>
                  ))}
                </select>
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

              <div style={{ gridColumn: "1 / -1", color: "#667085", fontSize: "13px" }}>
                Clear removes cached rows first. Then use Refresh to rebuild the same family or pair.
              </div>
            </div>
          )}

          {activeTab === "screen" && (
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
              {MA_OPTIONS.map((family) => (
                <button
                  key={family}
                  type="button"
                  onClick={() => selectFamily(family)}
                  style={{
                    padding: "9px 14px",
                    borderRadius: "10px",
                    border: selectedFamily === family ? "1px solid #2563eb" : "1px solid #d0d5dd",
                    background: selectedFamily === family ? "#dbeafe" : "#fff",
                    color: selectedFamily === family ? "#1d4ed8" : "#344054",
                    fontWeight: 800,
                    cursor: "pointer",
                    height: "42px",
                  }}
                >
                  {family}
                </button>
              ))}

              <Field label="Fast Period">
                <select value={fastPeriod} onChange={(e) => setFastPeriod(Number(e.target.value))} style={inputStyle}>
                  {PERIOD_OPTIONS.map((p) => (
                    <option key={p} value={p}>{p}</option>
                  ))}
                </select>
              </Field>

              <Field label="Slow Period">
                <select value={slowPeriod} onChange={(e) => setSlowPeriod(Number(e.target.value))} style={inputStyle}>
                  {PERIOD_OPTIONS.map((p) => (
                    <option key={p} value={p}>{p}</option>
                  ))}
                </select>
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

              <button
                type="button"
                onClick={() => loadSavedSignals(true)}
                disabled={loading}
                style={{
                  ...inputStyle,
                  border: "none",
                  background: loading ? "#98a2b3" : "#2563eb",
                  color: "white",
                  fontWeight: 700,
                  cursor: loading ? "not-allowed" : "pointer",
                  height: "42px",
                }}
              >
                {loading ? "Loading..." : "Load Screening Results"}
              </button>

              <div style={{ gridColumn: "1 / -1", color: "#667085", fontSize: "13px" }}>
                Load the cached screening results for the selected family and filters.
              </div>
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
                    {[
                      "Symbol",
                      "Signal Date",
                      "Fast Period",
                      "Slow Period",
                      "Open",
                      "Last",
                      "% Change",
                      "Prev Close",
                      "Fast Prev",
                      "Fast Curr",
                      "Slow Prev",
                      "Slow Curr",
                      "Source Updated",
                      "Cached At",
                    ].map((h) => (
                      <th key={h} style={thStyle}>{h}</th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {rows.length === 0 && (
                    <tr>
                      <td colSpan={14} style={{ padding: "16px", color: "#6b7280", textAlign: "center" }}>
                        No screening results loaded yet. Click Load Screening Results.
                      </td>
                    </tr>
                  )}

                  {rows.map((row) => {
                    const up = (row.percent_change ?? 0) > 0;
                    const down = (row.percent_change ?? 0) < 0;
                    return (
                      <tr key={`${row.symbol}-${row.fast_period}-${row.slow_period}-${row.signal_date || ""}`} style={{ borderTop: "1px solid #eef2f7" }}>
                        <td style={tdSymbol}>
                          <a
                            href={getTradingViewUrl(row.symbol)}
                            target="_blank"
                            rel="noopener noreferrer"
                            style={{ color: "#1d4ed8", textDecoration: "none" }}
                            title={`Open ${row.symbol} in TradingView`}
                          >
                            {row.symbol}
                          </a>
                        </td>
                        <td style={tdText}>{row.signal_date || "-"}</td>
                        <td style={tdNum}>{row.fast_period ?? "-"}</td>
                        <td style={tdNum}>{row.slow_period ?? "-"}</td>
                        <td style={tdNum}>{formatNum(row.open)}</td>
                        <td style={tdNum}>{formatNum(row.last_price)}</td>
                        <td style={{ ...tdNum, color: up ? "#0f9d58" : down ? "#d93025" : "#475467", fontWeight: 700 }}>
                          {row.percent_change != null ? `${row.percent_change.toFixed(2)}%` : "-"}
                        </td>
                        <td style={tdNum}>{formatNum(row.prev_day_close)}</td>
                        <td style={tdNum}>{formatNum(row.fast_prev, 4)}</td>
                        <td style={tdNum}>{formatNum(row.fast_curr, 4)}</td>
                        <td style={tdNum}>{formatNum(row.slow_prev, 4)}</td>
                        <td style={tdNum}>{formatNum(row.slow_curr, 4)}</td>
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
