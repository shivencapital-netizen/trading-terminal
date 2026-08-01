import { useEffect, useMemo, useState } from "react";
import ScreenerSidebar from "../components/screener/ScreenerSidebar";
import ScreenerResults from "../components/screener/ScreenerResults";
import { Sparklines, SparklinesLine } from "react-sparklines";

export default function Screener({ universeSymbols = null, universeMeta = {}, pageTitle = "Screener" }) {
  const [criteria, setCriteria] = useState({});
  const [results, setResults] = useState([]);
  const [mode, setMode] = useState("live");
  const [selectedSymbol, setSelectedSymbol] = useState(null);
  const [chartData, setChartData] = useState([]);
  const [chartLoading, setChartLoading] = useState(false);
  const [chartError, setChartError] = useState(null);
  const [sortField, setSortField] = useState("symbol");
  const [sortDirection, setSortDirection] = useState("asc");

  const buildQueryParams = (filters) => {
    const params = new URLSearchParams();
    if (filters.symbol) params.set("symbol", filters.symbol);
    if (filters.min_price !== undefined && filters.min_price !== null)
      params.set("min_price", filters.min_price);
    if (filters.max_price !== undefined && filters.max_price !== null)
      params.set("max_price", filters.max_price);
    if (filters.min_volume !== undefined && filters.min_volume !== null)
      params.set("min_volume", filters.min_volume);
    if (filters.price_above_sma20) params.set("price_above_sma20", "true");
    if (filters.price_above_sma50) params.set("price_above_sma50", "true");
    if (filters.sma_bullish_crossover) params.set("sma_bullish_crossover", "true");
    if (filters.rsi_min !== undefined && filters.rsi_min !== null)
      params.set("rsi_min", filters.rsi_min);
    if (filters.rsi_max !== undefined && filters.rsi_max !== null)
      params.set("rsi_max", filters.rsi_max);
    if (filters.rsi_bullish_divergence) params.set("rsi_bullish_divergence", "true");
    if (filters.avg_volume_ratio_min !== undefined && filters.avg_volume_ratio_min !== null)
      params.set("avg_volume_ratio_min", filters.avg_volume_ratio_min);
    if (filters.min_score !== undefined && filters.min_score !== null)
      params.set("min_score", filters.min_score);
    return params.toString();
  };

  const filterUniverse = (data) => {
    if (!universeSymbols || !Array.isArray(data)) return data;
    const universeSet = new Set(universeSymbols.map((s) => s.toUpperCase()));
    return data.filter((row) => universeSet.has(String(row.symbol || "").toUpperCase()));
  };

  const attachUniverseMeta = (data) => {
    if (!universeSymbols || !Array.isArray(data)) return data;
    const rankMap = new Map(universeSymbols.map((symbol, index) => [symbol.toUpperCase(), index + 1]));
    return data.map((row) => {
      const sym = String(row.symbol || "").toUpperCase();
      return {
        ...row,
        qqq_rank: rankMap.get(sym) || null,
        qqq_weight: universeMeta[sym] ?? null,
      };
    });
  };

  const runScreener = async () => {
    try {
      const url = "http://127.0.0.1:8000/api/v1/screener/run";
      const res = await fetch(url);
      const data = await res.json();
      const filtered = filterUniverse(Array.isArray(data) ? data : []);
      setResults(attachUniverseMeta(filtered));
      setSelectedSymbol(null);
      setChartData([]);
      setChartError(null);
    } catch (err) {
      console.error("Screener error:", err);
      setResults([]);
    }
  };

  const runHistoryScreener = async () => {
    try {
      const query = buildQueryParams(criteria);
      const url = `http://127.0.0.1:8000/api/v1/screener/history${
        query ? `?${query}` : ""
      }`;
      const res = await fetch(url);
      const data = await res.json();
      const filtered = filterUniverse(Array.isArray(data) ? data : []);
      setResults(attachUniverseMeta(filtered));
      setSelectedSymbol(null);
      setChartData([]);
      setChartError(null);
    } catch (err) {
      console.error("History screener error:", err);
      setResults([]);
    }
  };

  useEffect(() => {
    if (universeSymbols) {
      if (mode === "history") {
        runHistoryScreener();
      } else {
        runScreener();
      }
    }
  }, [universeSymbols, mode]);

  const handleSelectSymbol = async (symbol) => {
    setSelectedSymbol(symbol);
    setChartData([]);
    setChartError(null);
    setChartLoading(true);

    try {
      const endTime = new Date();
      const startTime = new Date(endTime.getTime() - 24 * 60 * 60 * 1000);
      const url = `http://127.0.0.1:8000/api/v1/charts/${symbol}?timeframe=1m&start_time=${encodeURIComponent(
        startTime.toISOString()
      )}&end_time=${encodeURIComponent(endTime.toISOString())}`;

      const res = await fetch(url);
      const data = await res.json();
      setChartData(Array.isArray(data) ? data : []);
    } catch (err) {
      console.error("Chart fetch error:", err);
      setChartError("Failed to load chart data.");
    } finally {
      setChartLoading(false);
    }
  };

  const handleRun = mode === "history" ? runHistoryScreener : runScreener;

  const sortedResults = useMemo(() => {
    const withDiff = results.map((row) => {
      const last = Number(row.last_price ?? row.lastPrice ?? 0);
      const high = Number(row.high ?? 0);
      return {
        ...row,
        diff_percent: last ? ((high - last) / last) * 100 : null,
      };
    });

    const getValue = (row, field) => {
      const value = row[field];
      if (value === null || value === undefined) return value;
      if (field === "symbol") return String(value).toUpperCase();
      if (typeof value === "boolean") return value ? 1 : 0;
      const num = Number(value);
      return Number.isNaN(num) ? String(value) : num;
    };

    const sorted = [...withDiff];
    sorted.sort((a, b) => {
      const aValue = getValue(a, sortField);
      const bValue = getValue(b, sortField);

      if (aValue === null || aValue === undefined) return 1;
      if (bValue === null || bValue === undefined) return -1;
      if (typeof aValue === "string" || typeof bValue === "string") {
        return String(aValue).localeCompare(String(bValue), undefined, {
          numeric: true,
          sensitivity: "base",
        });
      }
      return aValue - bValue;
    });

    if (sortDirection === "desc") {
      sorted.reverse();
    }

    return sorted;
  }, [results, sortField, sortDirection]);

  const handleSort = (field) => {
    if (sortField === field) {
      setSortDirection((prev) => (prev === "asc" ? "desc" : "asc"));
    } else {
      setSortField(field);
      setSortDirection("asc");
    }
  };

  const closePrices = chartData.map((c) => c.close);
  const latestCandle = chartData.length > 0 ? chartData[chartData.length - 1] : null;

  return (
    <div style={{ display: "flex", height: "100vh", width: "100%" }}>
      <ScreenerSidebar
        mode={mode}
        setMode={setMode}
        criteria={criteria}
        setCriteria={setCriteria}
        runScreener={handleRun}
      />

      <div style={{ flex: 1, display: "flex", flexDirection: "column", minHeight: 0, height: "100%", overflow: "hidden" }}>
        <div style={{ flex: 1, overflow: "hidden", minHeight: 0, height: "100%", maxHeight: "100%" }}>
          <ScreenerResults
            results={sortedResults}
            mode={mode}
            pageTitle={pageTitle}
            selectedSymbol={selectedSymbol}
            onRowClick={handleSelectSymbol}
            sortField={sortField}
            sortDirection={sortDirection}
            onSort={handleSort}
          />
        </div>
      </div>

      <div
        style={{
          width: "360px",
          padding: "20px",
          background: "#ffffff",
          borderLeft: "1px solid #e5e5e5",
          overflowY: "auto",
          display: "flex",
          flexDirection: "column",
        }}
      >
        <h2
          style={{
            marginBottom: "18px",
            fontWeight: 700,
            fontSize: "20px",
            color: "#222",
          }}
        >
          {selectedSymbol ? `${selectedSymbol} Chart` : "Chart Preview"}
        </h2>

        {!selectedSymbol && (
          <div style={{ color: "#666", lineHeight: 1.6 }}>
            Select a row in the results to load history candles and preview a chart.
          </div>
        )}

        {selectedSymbol && (
          <>
            {chartLoading && (
              <div style={{ color: "#444" }}>Loading chart data…</div>
            )}

            {chartError && (
              <div style={{ color: "#d93025" }}>{chartError}</div>
            )}

            {!chartLoading && !chartError && chartData.length === 0 && (
              <div style={{ color: "#666" }}>
                No history chart data available for the selected symbol.
              </div>
            )}

            {!chartLoading && chartData.length > 0 && (
              <>
                <div
                  style={{
                    marginBottom: "18px",
                    background: "#f5f7fa",
                    borderRadius: "12px",
                    padding: "16px",
                  }}
                >
                  <div
                    style={{
                      fontSize: "13px",
                      fontWeight: 600,
                      color: "#777",
                      marginBottom: "10px",
                    }}
                  >
                    Last 24h history / 1m candles
                  </div>
                  <div
                    style={{
                      display: "grid",
                      gridTemplateColumns: "1fr 1fr",
                      gap: "10px",
                    }}
                  >
                    <div>
                      <div style={summaryLabel}>Last</div>
                      <div style={summaryValue}>
                        {latestCandle.close.toFixed(2)}
                      </div>
                    </div>
                    <div>
                      <div style={summaryLabel}>Volume</div>
                      <div style={summaryValue}>
                        {latestCandle.volume.toLocaleString()}
                      </div>
                    </div>
                    <div>
                      <div style={summaryLabel}>High</div>
                      <div style={summaryValue}>
                        {latestCandle.high.toFixed(2)}
                      </div>
                    </div>
                    <div>
                      <div style={summaryLabel}>Low</div>
                      <div style={summaryValue}>
                        {latestCandle.low.toFixed(2)}
                      </div>
                    </div>
                  </div>
                </div>

                <div
                  style={{
                    background: "#f8f9fa",
                    borderRadius: "12px",
                    padding: "16px",
                  }}
                >
                  <Sparklines data={closePrices} width={300} height={180}>
                    <SparklinesLine color="#1a73e8" />
                  </Sparklines>
                </div>
              </>
            )}
          </>
        )}
      </div>
    </div>
  );
}

const summaryLabel = {
  fontSize: "12px",
  color: "#666",
  textTransform: "uppercase",
  letterSpacing: "0.03em",
  marginBottom: "6px",
};

const summaryValue = {
  fontSize: "18px",
  fontWeight: 700,
  color: "#222",
};
