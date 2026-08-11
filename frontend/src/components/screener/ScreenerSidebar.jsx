export default function ScreenerSidebar({
  mode,
  setMode,
  breakoutEnabled,
  setBreakoutEnabled,
  breakoutLookbackDays,
  setBreakoutLookbackDays,
  criteria,
  setCriteria,
  runScreener,
}) {
  const inputStyle = {
    width: "100%",
    padding: "10px",
    marginTop: "6px",
    marginBottom: "18px",
    borderRadius: "6px",
    border: "1px solid #ccc",
    fontSize: "14px",
    outline: "none",
    transition: "border 0.2s",
  };

  const labelStyle = {
    fontSize: "13px",
    fontWeight: 600,
    color: "#444",
  };

  const tabStyle = (active) => ({
    flex: 1,
    padding: "10px 12px",
    border: "none",
    cursor: "pointer",
    fontWeight: 700,
    color: active ? "white" : "#444",
    background: active ? "#1a73e8" : "#f1f3f5",
    borderRadius: active ? "8px" : "8px",
  });

  return (
    <div
      style={{
        width: "280px",
        padding: "22px",
        background: "#ffffff",
        borderRight: "1px solid #e5e5e5",
        height: "100vh",
        boxShadow: "2px 0 8px rgba(0,0,0,0.05)",
      }}
    >
      <h2
        style={{
          marginBottom: "18px",
          fontWeight: 700,
          fontSize: "20px",
          color: "#222",
          letterSpacing: "0.5px",
        }}
      >
        Filters
      </h2>

      <div
        style={{
          padding: "12px",
          marginBottom: "14px",
          border: "1px solid #dbe7f3",
          borderRadius: "8px",
          background: "#f7fbff",
        }}
      >
        <label style={{ display: "flex", alignItems: "center", gap: "10px", fontSize: "13px", color: "#1f3b57", fontWeight: 700 }}>
          <input
            type="checkbox"
            checked={breakoutEnabled || false}
            onChange={(e) => setBreakoutEnabled(e.target.checked)}
          />
          Breakout scan mode
        </label>

        <div style={{ marginTop: "10px", display: "flex", alignItems: "center", gap: "10px" }}>
          <span style={{ fontSize: "12px", color: "#35516e", minWidth: "120px" }}>Lookback days</span>
          <input
            type="number"
            min="1"
            max="120"
            value={breakoutLookbackDays}
            onChange={(e) => setBreakoutLookbackDays(Math.max(1, Math.min(120, Number(e.target.value) || 1)))}
            style={{
              width: "90px",
              padding: "6px 8px",
              borderRadius: "6px",
              border: "1px solid #b9cfe3",
              fontSize: "13px",
            }}
          />
        </div>

        <div style={{ marginTop: "8px", fontSize: "11px", color: "#47617a", lineHeight: 1.35 }}>
          When enabled, this runs a separate breakout calculation every 5 minutes in Live mode.
        </div>

      </div>

      <div style={{ display: "flex", gap: "10px", marginBottom: "24px" }}>
        <button
          type="button"
          style={tabStyle(mode === "live")}
          onClick={() => setMode("live")}
        >
          Live
        </button>
        <button
          type="button"
          style={tabStyle(mode === "history")}
          onClick={() => setMode("history")}
        >
          History
        </button>
      </div>

      <label style={labelStyle}>Symbol</label>
      <input
        type="text"
        placeholder="AAPL"
        style={inputStyle}
        value={criteria.symbol || ""}
        onFocus={(e) => (e.target.style.border = "1px solid #1a73e8")}
        onBlur={(e) => (e.target.style.border = "1px solid #ccc")}
        onChange={(e) =>
          setCriteria({ ...criteria, symbol: e.target.value.toUpperCase() })
        }
      />

      <label style={labelStyle}>Min Price</label>
      <input
        type="number"
        placeholder="0"
        style={inputStyle}
        value={criteria.min_price || ""}
        onFocus={(e) => (e.target.style.border = "1px solid #1a73e8")}
        onBlur={(e) => (e.target.style.border = "1px solid #ccc")}
        onChange={(e) =>
          setCriteria({ ...criteria, min_price: e.target.value ? Number(e.target.value) : undefined })
        }
      />

      <label style={labelStyle}>Max Price</label>
      <input
        type="number"
        placeholder="1000"
        style={inputStyle}
        value={criteria.max_price || ""}
        onFocus={(e) => (e.target.style.border = "1px solid #1a73e8")}
        onBlur={(e) => (e.target.style.border = "1px solid #ccc")}
        onChange={(e) =>
          setCriteria({ ...criteria, max_price: e.target.value ? Number(e.target.value) : undefined })
        }
      />

      <label style={labelStyle}>Min Volume</label>
      <input
        type="number"
        placeholder="100000"
        style={inputStyle}
        value={criteria.min_volume || ""}
        onFocus={(e) => (e.target.style.border = "1px solid #1a73e8")}
        onBlur={(e) => (e.target.style.border = "1px solid #ccc")}
        onChange={(e) =>
          setCriteria({ ...criteria, min_volume: e.target.value ? Number(e.target.value) : undefined })
        }
      />

      {breakoutEnabled && (
        <div
          style={{
            marginTop: "6px",
            marginBottom: "18px",
            padding: "10px 12px",
            borderRadius: "8px",
            background: "#eef9f5",
            border: "1px solid #bfe9d9",
            color: "#215f4a",
            fontSize: "12px",
            lineHeight: 1.4,
          }}
        >
          Breakout mode is active. Technical filters are hidden to keep this view focused on day-trade breakout candidates.
        </div>
      )}

      {!breakoutEnabled && (
        <>
          <div
            style={{
              marginTop: "24px",
              marginBottom: "18px",
              fontSize: "14px",
              fontWeight: 700,
              color: "#222",
            }}
          >
            Technical Filters
          </div>

          <label style={{ display: "flex", alignItems: "center", gap: "10px", marginBottom: "14px", fontSize: "13px", color: "#444", fontWeight: 600 }}>
            <input
              type="checkbox"
              checked={criteria.price_above_sma20 || false}
              onChange={(e) =>
                setCriteria({ ...criteria, price_above_sma20: e.target.checked })
              }
            />
            Price above SMA 20
            <span title="Filters symbols trading above their 20-period simple moving average." style={{ fontSize: "12px", color: "#666", cursor: "help" }}>?</span>
          </label>

          <label style={{ display: "flex", alignItems: "center", gap: "10px", marginBottom: "14px", fontSize: "13px", color: "#444", fontWeight: 600 }}>
            <input
              type="checkbox"
              checked={criteria.price_above_sma50 || false}
              onChange={(e) =>
                setCriteria({ ...criteria, price_above_sma50: e.target.checked })
              }
            />
            Price above SMA 50
            <span title="Filters symbols trading above their 50-period simple moving average." style={{ fontSize: "12px", color: "#666", cursor: "help" }}>?</span>
          </label>

          <label style={{ display: "flex", alignItems: "center", gap: "10px", marginBottom: "14px", fontSize: "13px", color: "#444", fontWeight: 600 }}>
            <input
              type="checkbox"
              checked={criteria.price_above_5d_high || false}
              onChange={(e) =>
                setCriteria({ ...criteria, price_above_5d_high: e.target.checked })
              }
            />
            Price above 5-day high
            <span title="Filters symbols whose current price is above the highest intraday high from the previous 5 trading days." style={{ fontSize: "12px", color: "#666", cursor: "help" }}>?</span>
          </label>

          <label style={{ display: "flex", alignItems: "center", gap: "10px", marginBottom: "14px", fontSize: "13px", color: "#444", fontWeight: 600 }}>
            <input
              type="checkbox"
              checked={criteria.sma_bullish_crossover || false}
              onChange={(e) =>
                setCriteria({ ...criteria, sma_bullish_crossover: e.target.checked })
              }
            />
            SMA 20/50 Bullish Crossover
            <span title="Select symbols where the 20-period SMA has crossed above the 50-period SMA, indicating a bullish short-term trend shift." style={{ fontSize: "12px", color: "#666", cursor: "help" }}>?</span>
          </label>

          <label style={labelStyle}>RSI Min</label>
          <input
            type="number"
            placeholder="40"
            style={inputStyle}
            value={criteria.rsi_min || ""}
            onFocus={(e) => (e.target.style.border = "1px solid #1a73e8")}
            onBlur={(e) => (e.target.style.border = "1px solid #ccc")}
            onChange={(e) =>
              setCriteria({ ...criteria, rsi_min: e.target.value ? Number(e.target.value) : undefined })
            }
          />

          <label style={labelStyle}>RSI Max</label>
          <input
            type="number"
            placeholder="70"
            style={inputStyle}
            value={criteria.rsi_max || ""}
            onFocus={(e) => (e.target.style.border = "1px solid #1a73e8")}
            onBlur={(e) => (e.target.style.border = "1px solid #ccc")}
            onChange={(e) =>
              setCriteria({ ...criteria, rsi_max: e.target.value ? Number(e.target.value) : undefined })
            }
          />

          <label style={{ display: "flex", alignItems: "center", gap: "10px", marginBottom: "14px", fontSize: "13px", color: "#444", fontWeight: 600 }}>
            <input
              type="checkbox"
              checked={criteria.rsi_bullish_divergence || false}
              onChange={(e) =>
                setCriteria({ ...criteria, rsi_bullish_divergence: e.target.checked })
              }
            />
            RSI Bullish Divergence
            <span title="Select symbols where the RSI is rising while price is pulling back, suggesting a bullish divergence setup." style={{ fontSize: "12px", color: "#666", cursor: "help" }}>?</span>
          </label>

          <label style={labelStyle}>Min Volume Ratio</label>
          <input
            type="number"
            placeholder="1.5"
            step="0.1"
            style={inputStyle}
            value={criteria.avg_volume_ratio_min || ""}
            onFocus={(e) => (e.target.style.border = "1px solid #1a73e8")}
            onBlur={(e) => (e.target.style.border = "1px solid #ccc")}
            onChange={(e) =>
              setCriteria({ ...criteria, avg_volume_ratio_min: e.target.value ? Number(e.target.value) : undefined })
            }
          />

          <label style={labelStyle}>Min Score</label>
          <input
            type="number"
            placeholder="1"
            step="1"
            style={inputStyle}
            value={criteria.min_score || ""}
            onFocus={(e) => (e.target.style.border = "1px solid #1a73e8")}
            onBlur={(e) => (e.target.style.border = "1px solid #ccc")}
            onChange={(e) =>
              setCriteria({ ...criteria, min_score: e.target.value ? Number(e.target.value) : undefined })
            }
          />
        </>
      )}

      <button
        onClick={runScreener}
        style={{
          width: "100%",
          padding: "12px",
          background: "#1a73e8",
          color: "white",
          border: "none",
          borderRadius: "6px",
          cursor: "pointer",
          fontWeight: 600,
          fontSize: "15px",
          marginTop: "18px",
          transition: "background 0.2s, transform 0.1s",
        }}
        onMouseEnter={(e) => (e.target.style.background = "#1666c4")}
        onMouseLeave={(e) => (e.target.style.background = "#1a73e8")}
        onMouseDown={(e) => (e.target.style.transform = "scale(0.97)")}
        onMouseUp={(e) => (e.target.style.transform = "scale(1)")}
      >
        Run {mode === "history" ? "History" : "Live"} Screener
      </button>
    </div>
  );
}
