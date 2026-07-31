import { useState } from "react";
import ScreenerSidebar from "../components/screener/ScreenerSidebar";
import ScreenerResults from "../components/screener/ScreenerResults";
import { Sparklines, SparklinesLine } from "react-sparklines";

export default function Screener() {
  const [criteria, setCriteria] = useState({});
  const [results, setResults] = useState([]);
  const [mode, setMode] = useState("live");
  const [selectedSymbol, setSelectedSymbol] = useState(null);
  const [chartData, setChartData] = useState([]);
  const [chartLoading, setChartLoading] = useState(false);
  const [chartError, setChartError] = useState(null);

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

  const runScreener = async () => {
    try {
      const res = await fetch("http://127.0.0.1:8000/api/v1/screener/run");
      const data = await res.json();
      setResults(Array.isArray(data) ? data : []);
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
      setResults(Array.isArray(data) ? data : []);
      setSelectedSymbol(null);
      setChartData([]);
      setChartError(null);
    } catch (err) {
      console.error("History screener error:", err);
      setResults([]);
    }
  };

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
            results={results}
            mode={mode}
            selectedSymbol={selectedSymbol}
            onRowClick={handleSelectSymbol}
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
