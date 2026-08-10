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

const getYahooChartUrl = (symbol) =>
  `https://finance.yahoo.com/chart/${encodeURIComponent(String(symbol || "").toUpperCase())}`;

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
  const [periodSort, setPeriodSort] = useState({ key: "fast_period", direction: "asc" });

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

  const togglePeriodSort = (key) => {
    setPeriodSort((prev) => {
      if (prev.key === key) {
        return {
          key,
          direction: prev.direction === "asc" ? "desc" : "asc",
        };
      }
      return {
        key,
        direction: "asc",
      };
    });
  };

  const getSortIndicator = (key) => {
    if (periodSort.key !== key) {
      return "";
    }
    return periodSort.direction === "asc" ? " ▲" : " ▼";
  };

  const sortedRows = useMemo(() => {
    const copy = [...rows];
    const factor = periodSort.direction === "asc" ? 1 : -1;

    copy.sort((a, b) => {
      const left = Number(a?.[periodSort.key] ?? 0);
      const right = Number(b?.[periodSort.key] ?? 0);

      if (left !== right) {
        return (left - right) * factor;
      }

      const symbolA = String(a?.symbol ?? "");
      const symbolB = String(b?.symbol ?? "");
      return symbolA.localeCompare(symbolB);
    });

    return copy;
  }, [rows, periodSort]);

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
            <button
              type="button"
              onClick={() => setActiveTab("clear")}
              style={getTabStyle(activeTab === "clear")}
            >
              Clear
            </button>
            <button
              type="button"
              onClick={() => setActiveTab("refresh")}
              style={getTabStyle(activeTab === "refresh")}
            >
              Refresh
            </button>
            <button
              type="button"
              onClick={() => setActiveTab("screen")}
              style={getTabStyle(activeTab === "screen")}
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
                    style={getFamilyPillStyle(selectedFamily === family)}
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
                  style={getPrimaryActionStyle(loading, false)}
                >
                  Refresh All {selectedFamily}
                </button>
                <button
                  type="button"
                  onClick={refreshSelectedCache}
                  disabled={loading}
                  style={getSecondaryActionStyle(loading)}
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
                    style={getFamilyPillStyle(selectedFamily === family)}
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
                  style={getDangerActionStyle(loading, false)}
                >
                  Clear All {selectedFamily}
                </button>
                <button
                  type="button"
                  onClick={clearSelectedCache}
                  disabled={loading}
                  style={getSecondaryActionStyle(loading)}
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
                    style={getFamilyPillStyle(selectedFamily === family)}
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
                {loading ? "Loading..." : "Load All Results"}
              </button>

              <button
                type="button"
                onClick={() => loadSavedSignals(false)}
                disabled={loading}
                style={getSecondaryActionStyle(loading)}
              >
                Load Selected Pair
              </button>

              <div style={{ gridColumn: "1 / -1", color: "#667085", fontSize: "13px" }}>
                Load All Results uses the full selected family. Load Selected Pair applies the fast/slow period filters.
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
                    <th style={thStyle}>Symbol</th>
                    <th style={thStyle}>Signal Date</th>
                    <th
                      style={{ ...thStyle, cursor: "pointer", userSelect: "none" }}
                      onClick={() => togglePeriodSort("fast_period")}
                      title="Sort by Fast Period"
                    >
                      Fast Period{getSortIndicator("fast_period")}
                    </th>
                    <th
                      style={{ ...thStyle, cursor: "pointer", userSelect: "none" }}
                      onClick={() => togglePeriodSort("slow_period")}
                      title="Sort by Slow Period"
                    >
                      Slow Period{getSortIndicator("slow_period")}
                    </th>
                    <th style={thStyle}>Open</th>
                    <th style={thStyle}>Last</th>
                    <th style={thStyle}>% Change</th>
                    <th style={thStyle}>Prev Close</th>
                    <th style={thStyle}>Fast Prev</th>
                    <th style={thStyle}>Fast Curr</th>
                    <th style={thStyle}>Slow Prev</th>
                    <th style={thStyle}>Slow Curr</th>
                    <th style={thStyle}>Source Updated</th>
                    <th style={thStyle}>Cached At</th>
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

                  {sortedRows.map((row) => {
                    const up = (row.percent_change ?? 0) > 0;
                    const down = (row.percent_change ?? 0) < 0;
                    return (
                      <tr key={`${row.symbol}-${row.fast_period}-${row.slow_period}-${row.signal_date || ""}`} style={{ borderTop: "1px solid #eef2f7" }}>
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

function getFamilyPillStyle(active) {
  return {
    padding: "10px 16px",
    borderRadius: "999px",
    border: active ? "1px solid #2563eb" : "1px solid #d0d5dd",
    background: active ? "linear-gradient(180deg, #eff6ff 0%, #dbeafe 100%)" : "#fff",
    color: active ? "#1d4ed8" : "#344054",
    fontWeight: 800,
    cursor: "pointer",
    height: "42px",
    minWidth: "84px",
    boxShadow: active ? "0 8px 18px rgba(37, 99, 235, 0.12)" : "0 1px 2px rgba(16, 24, 40, 0.04)",
    transition: "all 150ms ease",
  };
}

function getPrimaryActionStyle(loading, compact) {
  return {
    padding: compact ? "9px 14px" : "10px 16px",
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

function getSecondaryActionStyle(loading) {
  return {
    padding: "10px 16px",
    borderRadius: "12px",
    border: "1px solid #d0d5dd",
    background: loading ? "#98a2b3" : "#fff",
    color: loading ? "white" : "#344054",
    fontWeight: 700,
    cursor: loading ? "not-allowed" : "pointer",
    boxShadow: loading ? "none" : "0 4px 12px rgba(16, 24, 40, 0.06)",
    transition: "transform 120ms ease, box-shadow 120ms ease, background 120ms ease",
  };
}

function getDangerActionStyle(loading, compact) {
  return {
    padding: compact ? "9px 14px" : "10px 16px",
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
