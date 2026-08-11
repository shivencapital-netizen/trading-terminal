import React from "react";
import { Sparklines, SparklinesLine } from "react-sparklines";

export default function ScreenerResults({
  results,
  mode,
  pageTitle,
  liveStatusText,
  liveStatusActive = false,
  breakoutEnabled = false,
  newBreakoutSymbols,
  selectedSymbol,
  onRowClick,
  sortField,
  sortDirection,
  onSort,
  alwaysShowQQQColumns = false,
}) {
  const showQQQColumns = alwaysShowQQQColumns;
  const showBreakoutTimeColumn = breakoutEnabled && mode === "live";
  const emptyColSpan =
    (showQQQColumns ? (mode === "history" ? 15 : 11) : mode === "history" ? 13 : 9)
    + (showBreakoutTimeColumn ? 1 : 0);

  const formatBreakoutTime = (value) => {
    if (!value) return "-";
    const parts = String(value).split("T");
    const time = parts[1];
    if (!time) return "-";
    return `${time.slice(0, 5)} ET`;
  };

  const getSortIndicator = (field) => {
    if (sortField !== field) return "";
    return sortDirection === "asc" ? " ▲" : " ▼";
  };

  const formatNumber = (value) => {
    if (value === null || value === undefined || Number.isNaN(Number(value))) return "-";
    return Number(value).toLocaleString("en-US", {
      maximumFractionDigits: 2,
    });
  };

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

        {liveStatusText && (
          <div
            style={{
              padding: "10px 14px",
              borderRadius: "999px",
              background: liveStatusActive ? "#e6f4ea" : "#fff4e5",
              color: liveStatusActive ? "#137333" : "#8a4b00",
              fontSize: "13px",
              fontWeight: 600,
              maxWidth: "50%",
              textAlign: "right",
            }}
          >
            {liveStatusText}
          </div>
        )}
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
                <th style={{ ...headerCell, textAlign: "left", cursor: "pointer" }} onClick={() => onSort("symbol")}>
                  Symbol{getSortIndicator("symbol")}
                </th>
                <th style={{ ...headerCell, textAlign: "right", cursor: "pointer" }} onClick={() => onSort("open")}>
                  Open{getSortIndicator("open")}
                </th>
                {showQQQColumns && (
                  <>
                    <th style={{ ...headerCell, textAlign: "right", cursor: "pointer" }} onClick={() => onSort("qqq_rank")}>
                      QQQ Rank{getSortIndicator("qqq_rank")}
                    </th>
                    <th style={{ ...headerCell, textAlign: "right", cursor: "pointer" }} onClick={() => onSort("qqq_weight")}>
                      QQQ Weight{getSortIndicator("qqq_weight")}
                    </th>
                  </>
                )}
                <th style={{ ...headerCell, textAlign: "right", cursor: "pointer" }} onClick={() => onSort("high")}>
                  High{getSortIndicator("high")}
                </th>
                <th style={{ ...headerCell, textAlign: "right", cursor: "pointer" }} onClick={() => onSort("last_price")}>
                  Last Price{getSortIndicator("last_price")}
                </th>
                <th style={{ ...headerCell, textAlign: "right", cursor: "pointer" }} onClick={() => onSort("diff_percent")}>
                  Diff%{getSortIndicator("diff_percent")}
                </th>
                <th style={{ ...headerCell, textAlign: "right", cursor: "pointer" }} onClick={() => onSort("low")}>
                  Low{getSortIndicator("low")}
                </th>
                <th style={{ ...headerCell, textAlign: "right", cursor: "pointer" }} onClick={() => onSort("vwap")}>
                  VWAP{getSortIndicator("vwap")}
                </th>
                <th style={{ ...headerCell, textAlign: "right", cursor: "pointer" }} onClick={() => onSort("percent_change")}>
                  % Change{getSortIndicator("percent_change")}
                </th>
                <th style={{ ...headerCell, textAlign: "right", cursor: "pointer" }} onClick={() => onSort("volume")}>
                  Volume{getSortIndicator("volume")}
                </th>
                {showBreakoutTimeColumn && (
                  <th style={{ ...headerCell, textAlign: "right", cursor: "pointer" }} onClick={() => onSort("breakout_happened_at")}>
                    Breakout At{getSortIndicator("breakout_happened_at")}
                  </th>
                )}
                {mode === "history" && (
                  <>
                    <th style={{ ...headerCell, textAlign: "right", cursor: "pointer" }} onClick={() => onSort("score")}>
                      Score{getSortIndicator("score")}
                    </th>
                    <th style={{ ...headerCell, textAlign: "right", cursor: "pointer" }} onClick={() => onSort("rsi")}>
                      RSI{getSortIndicator("rsi")}
                    </th>
                    <th style={{ ...headerCell, textAlign: "right", cursor: "pointer" }} onClick={() => onSort("sma_bullish_crossover")}>
                      SMA Cross{getSortIndicator("sma_bullish_crossover")}
                    </th>
                    <th style={{ ...headerCell, textAlign: "right", cursor: "pointer" }} onClick={() => onSort("rsi_bullish_divergence")}>
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
                    No results yet - run the screener.
                  </td>
                </tr>
              )}

              {results.map((row) => {
                const isUp = row.percent_change > 0;
                const isDown = row.percent_change < 0;
                const active = selectedSymbol === row.symbol;
                const isNewBreakout =
                  breakoutEnabled &&
                  mode === "live" &&
                  newBreakoutSymbols &&
                  typeof newBreakoutSymbols.has === "function" &&
                  newBreakoutSymbols.has(String(row.symbol || "").toUpperCase());

                const rowBackground = active
                  ? "#eaf4ff"
                  : isNewBreakout
                    ? "#fff4cc"
                    : "white";

                const rowHoverBackground = active
                  ? "#e7f0ff"
                  : isNewBreakout
                    ? "#ffefbd"
                    : "#f8f9fa";

                return (
                  <tr
                    key={row.symbol}
                    style={{
                      borderBottom: "1px solid #eee",
                      transition: "background 0.2s, transform 0.15s",
                      background: rowBackground,
                      cursor: "pointer",
                    }}
                    onClick={() => onRowClick(row.symbol)}
                    onMouseEnter={(e) => (e.currentTarget.style.background = rowHoverBackground)}
                    onMouseLeave={(e) => (e.currentTarget.style.background = rowBackground)}
                  >
                    <td style={cellSymbol}>
                      <a
                        href={`https://finance.yahoo.com/chart/${encodeURIComponent(String(row.symbol || "").toUpperCase())}`}
                        target="_blank"
                        rel="noopener noreferrer"
                        onClick={(e) => e.stopPropagation()}
                        style={{ color: "#1a73e8", textDecoration: "none" }}
                        title={`Open ${row.symbol} Yahoo Finance chart`}
                      >
                        {row.symbol}
                      </a>
                      {isNewBreakout && (
                        <span
                          style={{
                            marginLeft: "8px",
                            padding: "2px 6px",
                            borderRadius: "999px",
                            background: "#fbbc04",
                            color: "#3c2f00",
                            fontSize: "10px",
                            fontWeight: 700,
                            verticalAlign: "middle",
                          }}
                        >
                          NEW
                        </span>
                      )}
                    </td>
                    <td style={cellNumber}>{formatNumber(row.open)}</td>

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
                    {showBreakoutTimeColumn && (
                      <td style={cellNumber}>{formatBreakoutTime(row.breakout_happened_at)}</td>
                    )}
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
                        />
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
