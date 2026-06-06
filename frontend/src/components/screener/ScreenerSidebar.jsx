export default function ScreenerSidebar({ criteria, setCriteria, runScreener }) {
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

  return (
    <div
      style={{
        width: "260px",
        padding: "22px",
        background: "#ffffff",
        borderRight: "1px solid #e5e5e5",
        height: "100vh",
        boxShadow: "2px 0 8px rgba(0,0,0,0.05)",
      }}
    >
      <h2
        style={{
          marginBottom: "25px",
          fontWeight: 700,
          fontSize: "20px",
          color: "#222",
          letterSpacing: "0.5px",
        }}
      >
        Filters
      </h2>

      {/* Symbol Filter */}
      <label style={labelStyle}>Symbol</label>
      <input
        type="text"
        placeholder="AAPL"
        style={inputStyle}
        onFocus={(e) => (e.target.style.border = "1px solid #1a73e8")}
        onBlur={(e) => (e.target.style.border = "1px solid #ccc")}
        onChange={(e) =>
          setCriteria({ ...criteria, symbol: e.target.value.toUpperCase() })
        }
      />

      {/* Min Price */}
      <label style={labelStyle}>Min Price</label>
      <input
        type="number"
        placeholder="0"
        style={inputStyle}
        onFocus={(e) => (e.target.style.border = "1px solid #1a73e8")}
        onBlur={(e) => (e.target.style.border = "1px solid #ccc")}
        onChange={(e) =>
          setCriteria({ ...criteria, min_price: Number(e.target.value) })
        }
      />

      {/* Max Price */}
      <label style={labelStyle}>Max Price</label>
      <input
        type="number"
        placeholder="1000"
        style={inputStyle}
        onFocus={(e) => (e.target.style.border = "1px solid #1a73e8")}
        onBlur={(e) => (e.target.style.border = "1px solid #ccc")}
        onChange={(e) =>
          setCriteria({ ...criteria, max_price: Number(e.target.value) })
        }
      />

      {/* Min Volume */}
      <label style={labelStyle}>Min Volume</label>
      <input
        type="number"
        placeholder="100000"
        style={inputStyle}
        onFocus={(e) => (e.target.style.border = "1px solid #1a73e8")}
        onBlur={(e) => (e.target.style.border = "1px solid #ccc")}
        onChange={(e) =>
          setCriteria({ ...criteria, min_volume: Number(e.target.value) })
        }
      />

      {/* Run Button */}
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
          marginTop: "10px",
          transition: "background 0.2s, transform 0.1s",
        }}
        onMouseEnter={(e) => (e.target.style.background = "#1666c4")}
        onMouseLeave={(e) => (e.target.style.background = "#1a73e8")}
        onMouseDown={(e) => (e.target.style.transform = "scale(0.97)")}
        onMouseUp={(e) => (e.target.style.transform = "scale(1)")}
      >
        Run Screener
      </button>
    </div>
  );
}
