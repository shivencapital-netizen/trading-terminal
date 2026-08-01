import React from "react";
import { Sparklines, SparklinesLine } from "react-sparklines";

export default function ScreenerResults({
  results,
  mode,
  pageTitle,
  selectedSymbol,
  onRowClick,
  sortField,
  sortDirection,
  onSort,
  alwaysShowQQQColumns = false,
}) {
  const formatNumber = (num) =>
    num?.toLocaleString("en-US", { maximumFractionDigits: 2 });

  const getSortIndicator = (field) =>
    sortField === field ? (sortDirection === "asc" ? " ▲" : " ▼") : "";

  const showQQQColumns =
    alwaysShowQQQColumns ||
    results.some((row) => row.qqq_rank != null || row.qqq_weight != null);

  const emptyColSpan = 9 + (mode === "history" ? 4 : 0) + (showQQQColumns ? 2 : 0);

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
          <div>
            <h2
              style={{
                margin: 0,
                fontWeight: 600,
                color: "#222",
                letterSpacing: "0.5px",
              }}
            >
              {pageTitle || (mode === "history" ? "History Screener Results" : "Live Screener Results")}
            </h2>
            <div style={{ color: "#666", fontSize: "14px", marginTop: "6px" }}>
              {mode === "history" ? "History mode" : "Live mode"}
            </div>
          </div>
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
              <th
                style={{ ...headerCell, textAlign: "left", cursor: "pointer" }}
                onClick={() => onSort("symbol")}
              >
                Symbol{getSortIndicator("symbol")}
              </th>
              {showQQQColumns && (
                <>
                  <th
                    style={{ ...headerCell, textAlign: "right", cursor: "pointer" }}
                    onClick={() => onSort("qqq_rank")}
                  >
                    QQQ Rank{getSortIndicator("qqq_rank")}
                  </th>
                  <th
                    style={{ ...headerCell, textAlign: "right", cursor: "pointer" }}
                    onClick={() => onSort("qqq_weight")}
                  >
                    QQQ Weight{getSortIndicator("qqq_weight")}
                  </th>
                </>
              )}
              <th
                style={{ ...headerCell, textAlign: "right", cursor: "pointer" }}
                onClick={() => onSort("high")}
              >
                High{getSortIndicator("high")}
              </th>
              <th
                style={{ ...headerCell, textAlign: "right", cursor: "pointer" }}
                onClick={() => onSort("last_price")}
              >
                Last Price{getSortIndicator("last_price")}
              </th>
              <th
                style={{ ...headerCell, textAlign: "right", cursor: "pointer" }}
                onClick={() => onSort("diff_percent")}
              >
                Diff%{getSortIndicator("diff_percent")}
              </th>
              <th
                style={{ ...headerCell, textAlign: "right", cursor: "pointer" }}
                onClick={() => onSort("low")}
              >
                Low{getSortIndicator("low")}
              </th>
              <th
                style={{ ...headerCell, textAlign: "right", cursor: "pointer" }}
                onClick={() => onSort("vwap")}
              >
                VWAP{getSortIndicator("vwap")}
              </th>
              <th
                style={{ ...headerCell, textAlign: "right", cursor: "pointer" }}
                onClick={() => onSort("percent_change")}
              >
                % Change{getSortIndicator("percent_change")}
              </th>
              <th
                style={{ ...headerCell, textAlign: "right", cursor: "pointer" }}
                onClick={() => onSort("volume")}
              >
                Volume{getSortIndicator("volume")}
              </th>
              {mode === "history" && (
                <>
                  <th
                    style={{ ...headerCell, textAlign: "right", cursor: "pointer" }}
                    onClick={() => onSort("score")}
                  >
                    Score{getSortIndicator("score")}
                  </th>
                  <th
                    style={{ ...headerCell, textAlign: "right", cursor: "pointer" }}
                    onClick={() => onSort("rsi")}
                  >
                    RSI{getSortIndicator("rsi")}
                  </th>
                  <th
                    style={{ ...headerCell, textAlign: "right", cursor: "pointer" }}
                    onClick={() => onSort("sma_bullish_crossover")}
                  >
                    SMA Cross{getSortIndicator("sma_bullish_crossover")}
                  </th>
                  <th
                    style={{ ...headerCell, textAlign: "right", cursor: "pointer" }}
                    onClick={() => onSort("rsi_bullish_divergence")}
                  >
                    RSI Div{getSortIndicator("rsi_bullish_divergence")}
                  </th>
                </>
              )}
              <th style={{ ...headerCell, textAlign: "center" }}>Chart</th>
            </tr>
          </thead>

          <tbody>
            {results.length === 0 && (
              <tr>
                <td
                  colSpan={emptyColSpan}
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
                  <td style={cellSymbol}>
                    <a
                      href={`https://www.tradingview.com/chart/?symbol=NASDAQ:${encodeURIComponent(
                        row.symbol
                      )}`}
                      target="_blank"
                      rel="noopener noreferrer"
                      onClick={(e) => e.stopPropagation()}
                      style={{ color: "#1a73e8", textDecoration: "none" }}
                      title={`Open ${row.symbol} TradingView chart`}
                    >
                      {row.symbol}
                    </a>
                  </td>

                  {showQQQColumns && (
                    <>
                      <td style={cellNumber}>{row.qqq_rank != null ? row.qqq_rank : "-"}</td>
                      <td style={cellNumber}>{row.qqq_weight != null ? `${row.qqq_weight.toFixed(1)}%` : "-"}</td>
                    </>
                  )}

                  <td style={cellNumber}>{formatNumber(row.high)}</td>

                  <td style={cellNumber}>{formatNumber(row.last_price)}</td>
                  <td style={cellNumber}>{row.diff_percent != null ? `${row.diff_percent.toFixed(2)}%` : "-"}</td>

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
