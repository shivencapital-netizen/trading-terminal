import { useState, useEffect } from "react";

export default function DataLoader() {
  const [activeTab, setActiveTab] = useState("load");
  const [incrementalScope, setIncrementalScope] = useState("one");
  const [incrementalSymbol, setIncrementalSymbol] = useState("");
  const [fullScope, setFullScope] = useState("single");
  const [fullSymbol, setFullSymbol] = useState("");
  const [fullYears, setFullYears] = useState(1);
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState("");
  const [symbolStatus, setSymbolStatus] = useState([]);
  const [deleteMode, setDeleteMode] = useState("symbol-year");
  const [deleteSymbol, setDeleteSymbol] = useState("");
  const [deleteYear, setDeleteYear] = useState(new Date().getFullYear());

  const runIncremental = async (e) => {
    e.preventDefault();

    if (incrementalScope === "one" && !incrementalSymbol.trim()) {
      setMessage("❌ Please enter a symbol for incremental update");
      return;
    }

    setLoading(true);
    setMessage("⏳ Running incremental update...");

    try {
      let url = "http://127.0.0.1:8000/api/v1/admin/load-history-1m-delta";
      if (incrementalScope === "one") {
        url += `?symbol=${incrementalSymbol.toUpperCase()}`;
      }

      const res = await fetch(url, { method: "POST" });
      const data = await res.json();

      if (res.ok) {
        setMessage(`✅ Incremental loaded ${data.inserted} candles for ${data.symbol}`);
        setIncrementalSymbol("");
        fetchSymbolStatus();
      } else {
        setMessage(`❌ Error: ${data.detail || "Failed to load data"}`);
      }
    } catch (err) {
      console.error("Incremental load error:", err);
      setMessage(`❌ Error: ${err.message}`);
    } finally {
      setLoading(false);
    }
  };

  const runFullLoad = async (e) => {
    e.preventDefault();

    if (fullScope === "single" && !fullSymbol.trim()) {
      setMessage("❌ Please enter a symbol for full load");
      return;
    }

    setLoading(true);
    setMessage("⏳ Running full load...");

    try {
      let url = "http://127.0.0.1:8000/api/v1/admin/load-history-1m";
      if (fullScope === "single") {
        url += `?symbol=${fullSymbol.toUpperCase()}&years=${fullYears}`;
      } else if (fullScope === "all-one-year") {
        url += `?years=1`;
      } else {
        url += `?years=${fullYears}`;
      }

      const res = await fetch(url, { method: "POST" });
      const data = await res.json();

      if (res.ok) {
        const displayTarget = data.symbol === "ALL" ? "all symbols" : data.symbol;
        setMessage(`✅ Full load inserted ${data.inserted} candles for ${displayTarget}`);
        setFullSymbol("");
        fetchSymbolStatus();
      } else {
        setMessage(`❌ Error: ${data.detail || "Failed to load data"}`);
      }
    } catch (err) {
      console.error("Full load error:", err);
      setMessage(`❌ Error: ${err.message}`);
    } finally {
      setLoading(false);
    }
  };

  const fetchSymbolStatus = async () => {
    
    try {
      const res = await fetch("http://127.0.0.1:8000/api/v1/admin/symbol-status");
      if (res.ok) {
        const data = await res.json();
        setSymbolStatus(Array.isArray(data) ? data : []);
      }
    } catch (err) {
      console.error("Status fetch error:", err);
    }
  };

  const deleteData = async (e) => {
    e.preventDefault();

    if (deleteMode === "symbol-year" && !deleteSymbol.trim()) {
      setMessage("❌ Please enter a symbol");
      return;
    }

    const confirmed = window.confirm(
      `⚠️ Are you sure you want to delete? This cannot be undone!\n\nMode: ${
        deleteMode === "all" ? "All symbols" :
        deleteMode === "all-years" ? "All years for one symbol" :
        deleteMode === "current-year" ? "Current year data" :
        "One symbol, one year"
      }`
    );

    if (!confirmed) return;

    setLoading(true);
    setMessage("⏳ Deleting...");

    try {
      let url = "http://127.0.0.1:8000/api/v1/admin/delete-history-1m";

      if (deleteMode === "all") {
        url += "?mode=all";
      } else if (deleteMode === "all-years") {
        url += `?mode=all-years&symbol=${deleteSymbol.toUpperCase()}`;
      } else if (deleteMode === "current-year") {
        url += `?mode=current-year`;
      } else if (deleteMode === "symbol-year") {
        url += `?mode=symbol-year&symbol=${deleteSymbol.toUpperCase()}&year=${deleteYear}`;
      }

      const res = await fetch(url, { method: "POST" });
      const data = await res.json();

      if (res.ok) {
        setMessage(`✅ Deleted ${data.deleted || 0} candles successfully`);
        setDeleteSymbol("");
        fetchSymbolStatus();
      } else {
        setMessage(`❌ Error: ${data.detail || "Failed to delete data"}`);
      }
    } catch (err) {
      console.error("Delete error:", err);
      setMessage(`❌ Error: ${err.message}`);
    } finally {
      setLoading(false);
    }
  };

  // Fetch status on mount
  useEffect(() => {
    fetchSymbolStatus();
  }, []);

  return (
    <div style={{ padding: "20px", maxWidth: "1200px" }}>
      <h1>📊 Historical Data Loader</h1>

      {/* Tabs */}
      <div style={{ marginBottom: "20px", borderBottom: "2px solid #ddd" }}>
        <button
          onClick={() => setActiveTab("load")}
          style={{
            padding: "10px 20px",
            marginRight: "10px",
            background: activeTab === "load" ? "#007bff" : "#f0f0f0",
            color: activeTab === "load" ? "white" : "black",
            border: "none",
            borderRadius: "4px 4px 0 0",
            cursor: "pointer",
            fontWeight: "bold",
          }}
        >
          Load Data
        </button>
        <button
          onClick={() => setActiveTab("status")}
          style={{
            padding: "10px 20px",
            marginRight: "10px",
            background: activeTab === "status" ? "#007bff" : "#f0f0f0",
            color: activeTab === "status" ? "white" : "black",
            border: "none",
            borderRadius: "4px 4px 0 0",
            cursor: "pointer",
            fontWeight: "bold",
          }}
        >
          Load Status
        </button>
        <button
          onClick={() => setActiveTab("delete")}
          style={{
            padding: "10px 20px",
            background: activeTab === "delete" ? "#dc3545" : "#f0f0f0",
            color: activeTab === "delete" ? "white" : "black",
            border: "none",
            borderRadius: "4px 4px 0 0",
            cursor: "pointer",
            fontWeight: "bold",
          }}
        >
          Delete Data
        </button>
      </div>

      {/* Load Data Tab */}
      {activeTab === "load" && (
        <div style={{ padding: "20px", background: "#f9f9f9", borderRadius: "4px" }}>
          <h2>Load 1-Minute Historical Data</h2>
          <form onSubmit={runIncremental} style={{ display: "flex", flexDirection: "column", gap: "15px" }}>
            <div>
              <label style={{ display: "block", marginBottom: "10px", fontWeight: "bold" }}>
                Incremental Mode
              </label>
              <div style={{ display: "flex", gap: "15px", flexWrap: "wrap" }}>
                <label style={{ display: "flex", alignItems: "center", cursor: "pointer" }}>
                  <input
                    type="radio"
                    value="one"
                    checked={incrementalScope === "one"}
                    onChange={(e) => setIncrementalScope(e.target.value)}
                    style={{ marginRight: "5px" }}
                  />
                  One symbol incremental
                </label>
                <label style={{ display: "flex", alignItems: "center", cursor: "pointer" }}>
                  <input
                    type="radio"
                    value="all"
                    checked={incrementalScope === "all"}
                    onChange={(e) => setIncrementalScope(e.target.value)}
                    style={{ marginRight: "5px" }}
                  />
                  All symbols incremental
                </label>
              </div>
            </div>

            {incrementalScope === "one" && (
              <div>
                <label style={{ display: "block", marginBottom: "5px", fontWeight: "bold" }}>
                  Symbol
                </label>
                <input
                  type="text"
                  value={incrementalSymbol}
                  onChange={(e) => setIncrementalSymbol(e.target.value.toUpperCase())}
                  placeholder="e.g., AAPL"
                  style={{
                    padding: "8px",
                    border: "1px solid #ccc",
                    borderRadius: "4px",
                    width: "150px",
                  }}
                />
              </div>
            )}

            <div style={{ display: "flex", alignItems: "flex-end" }}>
              <button
                type="submit"
                disabled={loading}
                style={{
                  padding: "8px 20px",
                  background: loading ? "#ccc" : "#28a745",
                  color: "white",
                  border: "none",
                  borderRadius: "4px",
                  cursor: loading ? "not-allowed" : "pointer",
                  fontWeight: "bold",
                }}
              >
                {loading ? "Running..." : "Run Incremental Update"}
              </button>
            </div>
          </form>

          <div style={{ height: "1px", background: "#ddd", margin: "30px 0" }} />

          <div>
            <h3>Full Load</h3>
            <form onSubmit={runFullLoad} style={{ display: "flex", flexDirection: "column", gap: "15px" }}>
              <div>
                <label style={{ display: "block", marginBottom: "10px", fontWeight: "bold" }}>
                  Full Load Mode
                </label>
                <div style={{ display: "flex", gap: "15px", flexWrap: "wrap" }}>
                  <label style={{ display: "flex", alignItems: "center", cursor: "pointer" }}>
                    <input
                      type="radio"
                      value="single"
                      checked={fullScope === "single"}
                      onChange={(e) => setFullScope(e.target.value)}
                      style={{ marginRight: "5px" }}
                    />
                    Single symbol full load
                  </label>
                  <label style={{ display: "flex", alignItems: "center", cursor: "pointer" }}>
                    <input
                      type="radio"
                      value="all-one-year"
                      checked={fullScope === "all-one-year"}
                      onChange={(e) => setFullScope(e.target.value)}
                      style={{ marginRight: "5px" }}
                    />
                    All symbols, 1 year
                  </label>
                  <label style={{ display: "flex", alignItems: "center", cursor: "pointer" }}>
                    <input
                      type="radio"
                      value="all-all-years"
                      checked={fullScope === "all-all-years"}
                      onChange={(e) => setFullScope(e.target.value)}
                      style={{ marginRight: "5px" }}
                    />
                    All symbols, N years
                  </label>
                </div>
              </div>

              {fullScope === "single" && (
                <div>
                  <label style={{ display: "block", marginBottom: "5px", fontWeight: "bold" }}>
                    Symbol
                  </label>
                  <input
                    type="text"
                    value={fullSymbol}
                    onChange={(e) => setFullSymbol(e.target.value.toUpperCase())}
                    placeholder="e.g., AAPL"
                    style={{
                      padding: "8px",
                      border: "1px solid #ccc",
                      borderRadius: "4px",
                      width: "150px",
                    }}
                  />
                </div>
              )}

              {(fullScope === "single" || fullScope === "all-all-years") && (
                <div>
                  <label style={{ display: "block", marginBottom: "5px", fontWeight: "bold" }}>
                    Years to Load
                  </label>
                  <input
                    type="number"
                    value={fullYears}
                    onChange={(e) => setFullYears(Math.max(1, parseInt(e.target.value) || 1))}
                    min="1"
                    style={{
                      padding: "8px",
                      border: "1px solid #ccc",
                      borderRadius: "4px",
                      width: "100px",
                    }}
                  />
                </div>
              )}

              <div style={{ display: "flex", alignItems: "flex-end" }}>
                <button
                  type="submit"
                  disabled={loading}
                  style={{
                    padding: "8px 20px",
                    background: loading ? "#ccc" : "#007bff",
                    color: "white",
                    border: "none",
                    borderRadius: "4px",
                    cursor: loading ? "not-allowed" : "pointer",
                    fontWeight: "bold",
                  }}
                >
                  {loading ? "Running..." : "Run Full Load"}
                </button>
              </div>
            </form>
          </div>

          {message && (
            <div
              style={{
                marginTop: "15px",
                padding: "10px",
                background: message.includes("✅") ? "#d4edda" : "#f8d7da",
                color: message.includes("✅") ? "#155724" : "#721c24",
                border: "1px solid",
                borderRadius: "4px",
              }}
            >
              {message}
            </div>
          )}
        </div>
      )}

      {/* Delete Tab (sibling of Load and Status) */}
      {activeTab === "delete" && (
        <div style={{ padding: "20px", background: "#f9f9f9", borderRadius: "4px" }}>
          <h2 style={{ color: "#dc3545" }}>⚠️ Delete Historical Data</h2>
          <form onSubmit={deleteData} style={{ display: "flex", flexDirection: "column", gap: "15px" }}>
            <div>
              <label style={{ display: "block", marginBottom: "10px", fontWeight: "bold" }}>
                Delete Mode
              </label>
              <div style={{ display: "flex", gap: "15px", flexWrap: "wrap" }}>
                <label style={{ display: "flex", alignItems: "center", cursor: "pointer" }}>
                  <input
                    type="radio"
                    value="symbol-year"
                    checked={deleteMode === "symbol-year"}
                    onChange={(e) => setDeleteMode(e.target.value)}
                    style={{ marginRight: "5px" }}
                  />
                  One Symbol, One Year
                </label>
                <label style={{ display: "flex", alignItems: "center", cursor: "pointer" }}>
                  <input
                    type="radio"
                    value="all-years"
                    checked={deleteMode === "all-years"}
                    onChange={(e) => setDeleteMode(e.target.value)}
                    style={{ marginRight: "5px" }}
                  />
                  All Years for One Symbol
                </label>
                <label style={{ display: "flex", alignItems: "center", cursor: "pointer" }}>
                  <input
                    type="radio"
                    value="current-year"
                    checked={deleteMode === "current-year"}
                    onChange={(e) => setDeleteMode(e.target.value)}
                    style={{ marginRight: "5px" }}
                  />
                  All Symbols - Current Year
                </label>
                <label style={{ display: "flex", alignItems: "center", cursor: "pointer" }}>
                  <input
                    type="radio"
                    value="all"
                    checked={deleteMode === "all"}
                    onChange={(e) => setDeleteMode(e.target.value)}
                    style={{ marginRight: "5px" }}
                  />
                  All Symbols, All Years
                </label>
              </div>
            </div>

            {(deleteMode === "symbol-year" || deleteMode === "all-years") && (
              <div>
                <label style={{ display: "block", marginBottom: "5px", fontWeight: "bold" }}>
                  Symbol
                </label>
                <input
                  type="text"
                  value={deleteSymbol}
                  onChange={(e) => setDeleteSymbol(e.target.value.toUpperCase())}
                  placeholder="e.g., AAPL"
                  style={{
                    padding: "8px",
                    border: "1px solid #ccc",
                    borderRadius: "4px",
                    width: "150px",
                  }}
                />
              </div>
            )}

            {deleteMode === "symbol-year" && (
              <div>
                <label style={{ display: "block", marginBottom: "5px", fontWeight: "bold" }}>
                  Year
                </label>
                <input
                  type="number"
                  value={deleteYear}
                  onChange={(e) => setDeleteYear(parseInt(e.target.value))}
                  min="2000"
                  max={new Date().getFullYear()}
                  style={{
                    padding: "8px",
                    border: "1px solid #ccc",
                    borderRadius: "4px",
                    width: "100px",
                  }}
                />
              </div>
            )}

            <div>
              <button
                type="submit"
                disabled={loading}
                style={{
                  padding: "10px 20px",
                  background: loading ? "#999" : "#dc3545",
                  color: "white",
                  border: "none",
                  borderRadius: "4px",
                  cursor: loading ? "not-allowed" : "pointer",
                  fontWeight: "bold",
                  width: "fit-content",
                }}
              >
                {loading ? "Deleting..." : "🗑️ Delete Data"}
              </button>
            </div>
          </form>

          {message && (
            <div
              style={{
                marginTop: "15px",
                padding: "10px",
                background: message.includes("✅") ? "#d4edda" : "#f8d7da",
                color: message.includes("✅") ? "#155724" : "#721c24",
                border: "1px solid",
                borderRadius: "4px",
              }}
            >
              {message}
            </div>
          )}
        </div>
      )}

      {/* Status Tab */}
      {activeTab === "status" && (
        <div style={{ padding: "20px", background: "#f9f9f9", borderRadius: "4px" }}>
          <h2>Symbol Load Status</h2>
          <button
            onClick={fetchSymbolStatus}
            style={{
              marginBottom: "15px",
              padding: "8px 16px",
              background: "#17a2b8",
              color: "white",
              border: "none",
              borderRadius: "4px",
              cursor: "pointer",
              fontWeight: "bold",
            }}
          >
            🔄 Refresh Status
          </button>

          {symbolStatus.length === 0 ? (
            <p style={{ color: "#666" }}>No symbols loaded yet.</p>
          ) : (
            <table
              style={{
                width: "100%",
                borderCollapse: "collapse",
                background: "white",
                borderRadius: "4px",
              }}
            >
              <thead>
                <tr style={{ background: "#f5f5f5", borderBottom: "2px solid #ddd" }}>
                  <th style={{ padding: "12px", textAlign: "left", fontWeight: "bold" }}>
                    Symbol
                  </th>
                  <th style={{ padding: "12px", textAlign: "left", fontWeight: "bold" }}>
                    Candle Count
                  </th>
                  <th style={{ padding: "12px", textAlign: "left", fontWeight: "bold" }}>
                    Last Loaded Time
                  </th>
                  <th style={{ padding: "12px", textAlign: "left", fontWeight: "bold" }}>
                    Status
                  </th>
                </tr>
              </thead>
              <tbody>
                {symbolStatus.map((item, idx) => (
                  <tr key={idx} style={{ borderBottom: "1px solid #eee" }}>
                    <td style={{ padding: "12px", fontWeight: "bold" }}>{item.symbol}</td>
                    <td style={{ padding: "12px" }}>{item.candle_count}</td>
                    <td style={{ padding: "12px", fontSize: "0.9em", color: "#666" }}>
                      {item.last_loaded_time
                        ? new Date(item.last_loaded_time).toLocaleString()
                        : "Never"}
                    </td>
                    <td style={{ padding: "12px" }}>
                      <span
                        style={{
                          padding: "4px 8px",
                          borderRadius: "4px",
                          background: item.candle_count > 0 ? "#d4edda" : "#f8d7da",
                          color: item.candle_count > 0 ? "#155724" : "#721c24",
                          fontSize: "0.85em",
                          fontWeight: "bold",
                        }}
                      >
                        {item.candle_count > 0 ? "✅ Loaded" : "⏳ Pending"}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </div>
      )}
    </div>
  );
}
