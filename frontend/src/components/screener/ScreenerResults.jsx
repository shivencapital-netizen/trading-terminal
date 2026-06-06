import React from "react";
import { Sparklines, SparklinesLine } from "react-sparklines";

export default function ScreenerResults({ results }) {
  const formatNumber = (num) =>
    num?.toLocaleString("en-US", { maximumFractionDigits: 2 });

  return (
    <div
      style={{
        flex: 1,
        padding: "20px",
        background: "#f8f9fa",
        overflowY: "auto",
      }}
    >
      <h2
        style={{
          marginBottom: "20px",
          fontWeight: 600,
          color: "#222",
          letterSpacing: "0.5px",
        }}
      >
        Screener Results
      </h2>

      <div
        style={{
          background: "white",
          borderRadius: "10px",
          boxShadow: "0 2px 8px rgba(0,0,0,0.08)",
          overflow: "hidden",
        }}
      >
        <table style={{ width: "100%", borderCollapse: "collapse" }}>
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

              return (
                <tr
                  key={row.symbol}
                  style={{
                    borderBottom: "1px solid #eee",
                    transition: "background 0.2s",
                  }}
                  onMouseEnter={(e) =>
                    (e.currentTarget.style.background = "#f8f9fa")
                  }
                  onMouseLeave={(e) =>
                    (e.currentTarget.style.background = "white")
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
