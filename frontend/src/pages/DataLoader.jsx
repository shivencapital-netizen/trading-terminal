import { useState, useEffect } from "react";

export default function DataLoader() {
  const [activeTab, setActiveTab] = useState("load");
  const [symbol, setSymbol] = useState("");
  const [years, setYears] = useState(1);
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState("");
  const [symbolStatus, setSymbolStatus] = useState([]);

  const loadData = async (e) => {
    e.preventDefault();
    if (!symbol.trim()) {
      setMessage("❌ Please enter a symbol");
      return;
    }

    setLoading(true);
    setMessage("⏳ Loading...");

    try {
      const res = await fetch(
        `http://127.0.0.1:8000/api/v1/admin/load-history-1m-delta?symbol=${symbol.toUpperCase()}&years=${years}`,
        { method: "POST" }
      );

      const data = await res.json();
      if (res.ok) {
        setMessage(
          `✅ Loaded ${data.inserted} candles for ${data.symbol}`
        );
        setSymbol("");
        fetchSymbolStatus();
      } else {
        setMessage(`❌ Error: ${data.detail || "Failed to load data"}`);
      }
    } catch (err) {
      console.error("Load error:", err);
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
          onClick={() => {
            setActiveTab("status");
            fetchSymbolStatus();
          }}
          style={{
            padding: "10px 20px",
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
      </div>

      {/* Load Data Tab */}
      {activeTab === "load" && (
        <div style={{ padding: "20px", background: "#f9f9f9", borderRadius: "4px" }}>
          <h2>Load 1-Minute Historical Data</h2>
          <form onSubmit={loadData} style={{ display: "flex", gap: "10px", flexWrap: "wrap" }}>
            <div>
              <label style={{ display: "block", marginBottom: "5px", fontWeight: "bold" }}>
                Symbol
              </label>
              <input
                type="text"
                value={symbol}
                onChange={(e) => setSymbol(e.target.value.toUpperCase())}
                placeholder="e.g., AAPL"
                style={{
                  padding: "8px",
                  border: "1px solid #ccc",
                  borderRadius: "4px",
                  width: "150px",
                }}
              />
            </div>

            <div>
              <label style={{ display: "block", marginBottom: "5px", fontWeight: "bold" }}>
                Years to Load
              </label>
              <input
                type="number"
                value={years}
                onChange={(e) => setYears(Math.max(1, parseInt(e.target.value) || 1))}
                min="1"
                style={{
                  padding: "8px",
                  border: "1px solid #ccc",
                  borderRadius: "4px",
                  width: "100px",
                }}
              />
            </div>

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
                {loading ? "Loading..." : "Load Data"}
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
