import React from "react";
import { Sparklines, SparklinesLine } from "react-sparklines";

export default function ScreenerResults({
  results,
  mode,
  selectedSymbol,
  onRowClick,
}) {
  const formatNumber = (num) =>
    num?.toLocaleString("en-US", { maximumFractionDigits: 2 });

  return (
    <div
      style={{
        flex: 1,
        display: "flex",
        flexDirection: "column",
        minHeight: 0,
        height: "100%",
        maxHeight: "100%",
        padding: "20px",
        background: "#f8f9fa",
        overflow: "hidden",
      }}
    >
      <div
        style={{
          display: "flex",
          alignItems: "center",
          justifyContent: "space-between",
          marginBottom: "20px",
          flex: "0 0 auto",
        }}
      >
        <h2
          style={{
            margin: 0,
            fontWeight: 600,
            color: "#222",
            letterSpacing: "0.5px",
          }}
        >
          {mode === "history" ? "History Screener Results" : "Live Screener Results"}
        </h2>
        <span style={{ color: "#666", fontSize: "14px" }}>
          {results.length} rows
        </span>
      </div>

      <div
        style={{
          flex: 1,
          minHeight: 0,
          background: "white",
          borderRadius: "10px",
          boxShadow: "0 2px 8px rgba(0,0,0,0.08)",
          display: "flex",
          flexDirection: "column",
          overflow: "hidden",
        }}
      >
        <div style={{ flex: 1, minHeight: 0, maxHeight: "100%", overflowY: "auto" }}>
          <table style={{ width: "100%", minWidth: "100%", borderCollapse: "collapse" }}>
          <thead>
            <tr
              style={{
                background: "#f1f3f5",
                borderBottom: "2px solid #dee2e6",
              }}
            >
              <th style={{ ...headerCell, textAlign: "left" }}>Symbol</th>
              <th style={{ ...headerCell, textAlign: "right" }}>High</th>
              <th style={{ ...headerCell, textAlign: "right" }}>Last Price</th>
              <th style={{ ...headerCell, textAlign: "right" }}>Low</th>
              <th style={{ ...headerCell, textAlign: "right" }}>VWAP</th>
              <th style={{ ...headerCell, textAlign: "right" }}>% Change</th>
              <th style={{ ...headerCell, textAlign: "right" }}>Volume</th>
              {mode === "history" && (
                <>
                  <th style={{ ...headerCell, textAlign: "right" }}>Score</th>
                  <th style={{ ...headerCell, textAlign: "right" }}>RSI</th>
                  <th style={{ ...headerCell, textAlign: "right" }}>SMA Cross</th>
                  <th style={{ ...headerCell, textAlign: "right" }}>RSI Div</th>
                </>
              )}
              <th style={{ ...headerCell, textAlign: "center" }}>Chart</th>
            </tr>
          </thead>

          <tbody>
            {results.length === 0 && (
              <tr>
                <td
                  colSpan="8"
                  style={{
                    padding: "20px",
                    textAlign: "center",
                    color: "#777",
                    fontStyle: "italic",
                  }}
                >
                  No results yet — run the screener.
                </td>
              </tr>
            )}

            {results.map((row) => {
              const isUp = row.percent_change > 0;
              const isDown = row.percent_change < 0;
              const active = selectedSymbol === row.symbol;

              return (
                <tr
                  key={row.symbol}
                  style={{
                    borderBottom: "1px solid #eee",
                    transition: "background 0.2s, transform 0.15s",
                    background: active ? "#eaf4ff" : "white",
                    cursor: "pointer",
                  }}
                  onClick={() => onRowClick(row.symbol)}
                  onMouseEnter={(e) =>
                    (e.currentTarget.style.background = active ? "#e7f0ff" : "#f8f9fa")
                  }
                  onMouseLeave={(e) =>
                    (e.currentTarget.style.background = active ? "#eaf4ff" : "white")
                  }
                >
                  <td style={cellSymbol}>{row.symbol}</td>

                  <td style={cellNumber}>{formatNumber(row.high)}</td>

                  <td style={cellNumber}>{formatNumber(row.last_price)}</td>

                  <td style={cellNumber}>{formatNumber(row.low)}</td>

                  <td style={cellNumber}>{formatNumber(row.vwap)}</td>

                  <td
                    style={{
                      ...cellNumber,
                      fontWeight: 600,
                      color: isUp ? "#0f9d58" : isDown ? "#d93025" : "#444",
                    }}
                  >
                    {row.percent_change?.toFixed(2)}%
                  </td>

                  <td style={cellNumber}>{formatNumber(row.volume)}</td>
                  {mode === "history" && (
                    <>
                      <td style={cellNumber}>{row.score != null ? row.score.toFixed(1) : "-"}</td>
                      <td style={cellNumber}>{row.rsi != null ? row.rsi.toFixed(1) : "-"}</td>
                      <td style={cellNumber}>{row.sma_bullish_crossover ? "Yes" : "No"}</td>
                      <td style={cellNumber}>{row.rsi_bullish_divergence ? "Yes" : "No"}</td>
                    </>
                  )}

                  <td style={{ ...cellNumber, textAlign: "center" }}>
                    {row.sparkline && row.sparkline.length > 0 ? (
                      <Sparklines data={row.sparkline} width={80} height={30}>
                        <SparklinesLine color="#1a73e8" />
                      </Sparklines>
                    ) : (
                      <div
                        style={{
                          width: "80px",
                          height: "30px",
                          background: "#eee",
                          borderRadius: "4px",
                          display: "inline-block",
                        }}
                      ></div>
                    )}
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </div>
  </div>
  );
}

const headerCell = {
  padding: "12px 14px",
  fontSize: "14px",
  fontWeight: 600,
  color: "#333",
  borderBottom: "1px solid #dee2e6",
};

const cellSymbol = {
  padding: "12px 14px",
  fontWeight: 600,
  color: "#1a73e8",
  textAlign: "left",
};

const cellNumber = {
  padding: "12px 14px",
  textAlign: "right",
  fontVariantNumeric: "tabular-nums",
  color: "#333",
};
