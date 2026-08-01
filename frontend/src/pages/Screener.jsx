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

  const earningsCalendar = {
    AAPL: "Aug 1, 2026",
    MSFT: "Jul 22, 2026",
    GOOG: "Jul 25, 2026",
    GOOGL: "Jul 25, 2026",
    NVDA: "Aug 21, 2026",
    TSLA: "Aug 7, 2026",
    AMZN: "Jul 25, 2026",
    META: "Jul 24, 2026",
  };

  const importantDates = [
    { label: "Next Fed meeting", value: "Sep 17-18, 2026" },
    { label: "Next CPI release", value: "Aug 13, 2026" },
    { label: "Next economic data", value: "Aug 28, 2026 - FOMC minutes" },
    { label: "Next US market holiday", value: "Sep 1, 2026 - Labor Day" },
  ];

  const vixQuote = {
    label: "CBOE VIX",
    value: "18.42",
    change: "+0.12",
    trend: "+0.66%",
    source: "VIX Index",
  };

  const ivData = {
    AAPL: { iv: "23.8%", rank: "62", percentile: "78" },
    MSFT: { iv: "18.4%", rank: "54", percentile: "61" },
    GOOG: { iv: "21.2%", rank: "49", percentile: "58" },
    GOOGL: { iv: "21.0%", rank: "48", percentile: "57" },
    NVDA: { iv: "29.5%", rank: "87", percentile: "92" },
    TSLA: { iv: "62.3%", rank: "95", percentile: "99" },
    AMZN: { iv: "27.1%", rank: "72", percentile: "82" },
    META: { iv: "31.0%", rank: "81", percentile: "88" },
    AVGO: { iv: "—", rank: "—", percentile: "—" },
    PEP: { iv: "—", rank: "—", percentile: "—" },
    NFLX: { iv: "—", rank: "—", percentile: "—" },
    ADBE: { iv: "—", rank: "—", percentile: "—" },
    INTC: { iv: "—", rank: "—", percentile: "—" },
    CSCO: { iv: "—", rank: "—", percentile: "—" },
    QCOM: { iv: "—", rank: "—", percentile: "—" },
    AMD: { iv: "—", rank: "—", percentile: "—" },
    TXN: { iv: "—", rank: "—", percentile: "—" },
    AMAT: { iv: "—", rank: "—", percentile: "—" },
    COST: { iv: "—", rank: "—", percentile: "—" },
    CMCSA: { iv: "—", rank: "—", percentile: "—" },
  };

  // ivMap will hold dynamic IVs fetched from the backend when available
  const [ivMap, setIvMap] = useState({});

  // Try to fetch implied vol data for the top N results in background
  useEffect(() => {
    if (!results || results.length === 0) return;

    const symbolsToFetch = results.slice(0, 15).map((r) => String(r.symbol || "").toUpperCase());
    const controller = new AbortController();

    const fetchIvFor = async (sym) => {
      try {
        const res = await fetch(
          `http://127.0.0.1:8000/api/v1/greeks/latest?symbol=${encodeURIComponent(sym)}`,
          { signal: controller.signal }
        );
        if (!res.ok) return null;
        const data = await res.json();
        // Expecting { implied_vol: 0.271, iv_rank: 72, iv_percentile: 82 }
        if (data && (data.implied_vol || data.implied_vol === 0)) {
          return {
            iv: typeof data.implied_vol === "number" ? `${(data.implied_vol * 100).toFixed(1)}%` : String(data.implied_vol),
            rank: data.iv_rank != null ? String(data.iv_rank) : "—",
            percentile: data.iv_percentile != null ? String(data.iv_percentile) : "—",
          };
        }
      } catch (e) {
        // ignore fetch errors — backend may not expose this endpoint yet
      }
      return null;
    };

    let mounted = true;
    (async () => {
      const map = {};
      for (const s of symbolsToFetch) {
        const iv = await fetchIvFor(s);
        if (!mounted) break;
        if (iv) map[s] = iv;
      }
      if (mounted) setIvMap((prev) => ({ ...prev, ...map }));
    })();

    return () => {
      mounted = false;
      controller.abort();
    };
  }, [results]);

  // Show IV for selected symbol, or default to the top result symbol when none selected
  const displayedSymbol = selectedSymbol || (results && results.length > 0 ? String(results[0].symbol || "").toUpperCase() : null);
  // prefer dynamic ivMap values, then static ivData, then fallback placeholders
  const selectedStockIv = displayedSymbol
    ? ivMap[displayedSymbol] ?? ivData[displayedSymbol] ?? { iv: "TBD", rank: "—", percentile: "—" }
    : null;

  const topNews = [
    {
      title: "Global markets weigh Fed outlook amid rising rates",
      source: "Reuters",
      time: "2h ago",
      url: "https://www.reuters.com/markets/global-markets-weigh-fed-outlook-2026-08-01/",
    },
    {
      title: "Oil prices climb as OPEC+ holds production steady",
      source: "Bloomberg",
      time: "4h ago",
      url: "https://www.bloomberg.com/news/articles/2026-08-01/oil-prices-opec-plus-production",
    },
    {
      title: "Tech earnings season heats up with mega caps reporting",
      source: "CNBC",
      time: "1h ago",
      url: "https://www.cnbc.com/2026/08/01/tech-earnings-season-2026.html",
    },
  ];

  const stockNews = {
    AAPL: [
      {
        title: "Apple rumored to expand AI investments after strong iPhone sales",
        source: "The Wall Street Journal",
        time: "3h ago",
        url: "https://www.wsj.com/articles/apple-ai-investments-2026",
      },
    ],
    MSFT: [
      {
        title: "Microsoft cloud growth remains solid ahead of earnings",
        source: "Financial Times",
        time: "5h ago",
        url: "https://www.ft.com/content/microsoft-cloud-growth-2026",
      },
    ],
    NVDA: [
      {
        title: "NVIDIA stock edges higher as AI demand stays robust",
        source: "Reuters",
        time: "30m ago",
        url: "https://www.reuters.com/technology/nvidia-ai-demand-2026-08-01/",
      },
    ],
  };

  const relatedNews = displayedSymbol
    ? stockNews[displayedSymbol] ?? [
        {
          title: `No live related news available for ${displayedSymbol} yet.`,
          source: "Market Desk",
          time: "Just now",
          url: "#",
        },
      ]
    : topNews;

  const selectedStockEarnings = displayedSymbol
    ? earningsCalendar[displayedSymbol] ?? "TBD"
    : null;

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
            alwaysShowQQQColumns={Boolean(universeSymbols)}
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
          Market overview
        </h2>

        <div style={{ color: "#666", lineHeight: 1.6, marginBottom: "16px" }}>
          Live market context, volatility, and news for the selected stock.
        </div>

        {/* VIX moved into Important Info panel (compact) */}

        <div
          style={{
            marginTop: "18px",
            background: "#ffffff",
            borderRadius: "12px",
            padding: "14px",
            border: "1px solid #e5e5e5",
          }}
        >
          <div
            style={{
              display: "flex",
              justifyContent: "space-between",
              alignItems: "center",
              marginBottom: "12px",
            }}
          >
            <div
              style={{
                fontSize: "15px",
                fontWeight: 700,
                color: "#222",
              }}
            >
              Important Info
            </div>
            <div style={{ fontSize: "11px", color: "#666" }}>
              Macro + earnings
            </div>
          </div>

          {/* compact VIX tile aligned to the right inside the panel */}
          <div style={{ display: "flex", justifyContent: "flex-end", marginBottom: "10px" }}>
            <div
              style={{
                padding: "8px 10px",
                background: "#f8f9fa",
                borderRadius: "10px",
                border: "1px solid #e8eaed",
                textAlign: "right",
                minWidth: "92px",
              }}
            >
              <div style={{ fontSize: "10px", color: "#777", textTransform: "uppercase" }}>{vixQuote.label}</div>
              <div style={{ fontSize: "14px", fontWeight: 700, color: "#111" }}>{vixQuote.value}</div>
              <div style={{ fontSize: "11px", color: "#555" }}>{vixQuote.trend}</div>
            </div>
          </div>

          <div style={{ display: "grid", gap: "10px" }}>
            {selectedSymbol && selectedStockIv && (
              <div
                style={{
                  padding: "12px 14px",
                  background: "#f8f9fa",
                  borderRadius: "10px",
                  border: "1px solid #e8eaed",
                }}
              >
                <div style={{ fontSize: "11px", color: "#555" }}>
                  {selectedSymbol} IV snapshot
                </div>
                <div
                  style={{
                    marginTop: "8px",
                    display: "grid",
                    gridTemplateColumns: "1fr 1fr",
                    gap: "8px",
                  }}
                >
                  <div>
                    <div style={{ fontSize: "10px", color: "#777", textTransform: "uppercase" }}>
                      IV
                    </div>
                    <div style={{ fontSize: "14px", fontWeight: 700, color: "#111" }}>
                      {selectedStockIv.iv}
                    </div>
                  </div>
                  <div>
                    <div style={{ fontSize: "10px", color: "#777", textTransform: "uppercase" }}>
                      IV Rank
                    </div>
                    <div style={{ fontSize: "14px", fontWeight: 700, color: "#111" }}>
                      {selectedStockIv.rank}
                    </div>
                  </div>
                  <div style={{ gridColumn: "1 / -1" }}>
                    <div style={{ fontSize: "10px", color: "#777", textTransform: "uppercase" }}>
                      IV Percentile
                    </div>
                    <div style={{ fontSize: "14px", fontWeight: 700, color: "#111" }}>
                      {selectedStockIv.percentile}
                    </div>
                  </div>
                </div>
              </div>
            )}

            {importantDates.map((item) => (
              <div
                key={item.label}
                style={{
                  padding: "10px 12px",
                  background: "#f8f9fa",
                  borderRadius: "10px",
                  border: "1px solid #e8eaed",
                }}
              >
                <div style={{ fontSize: "11px", color: "#555" }}>
                  {item.label}
                </div>
                <div
                  style={{
                    marginTop: "3px",
                    fontSize: "13px",
                    fontWeight: 600,
                    color: "#111",
                  }}
                >
                  {item.value}
                </div>
              </div>
            ))}

            {selectedStockEarnings && (
              <div
                style={{
                  padding: "10px 12px",
                  background: "#f8f9fa",
                  borderRadius: "10px",
                  border: "1px solid #e8eaed",
                }}
              >
                <div style={{ fontSize: "11px", color: "#555" }}>
                  {selectedSymbol} earnings release
                </div>
                <div
                  style={{
                    marginTop: "3px",
                    fontSize: "13px",
                    fontWeight: 600,
                    color: "#111",
                  }}
                >
                  {selectedStockEarnings}
                </div>
              </div>
            )}
          </div>
        </div>

        <div
          style={{
            marginTop: "18px",
            background: "#ffffff",
            borderRadius: "12px",
            padding: "18px",
            border: "1px solid #e5e5e5",
          }}
        >
          <div
            style={{
              display: "flex",
              justifyContent: "space-between",
              alignItems: "center",
              marginBottom: "14px",
            }}
          >
            <div
              style={{
                fontSize: "15px",
                fontWeight: 700,
                color: "#222",
              }}
            >
              Top business news
            </div>
            <div style={{ fontSize: "12px", color: "#666" }}>
              Global + related
            </div>
          </div>
        </div>

        <div
          style={{
            marginTop: "18px",
            background: "#ffffff",
            borderRadius: "12px",
            padding: "18px",
            border: "1px solid #e5e5e5",
          }}
        >
          <div
            style={{
              display: "flex",
              justifyContent: "space-between",
              alignItems: "center",
              marginBottom: "14px",
            }}
          >
            <div
              style={{
                fontSize: "15px",
                fontWeight: 700,
                color: "#222",
              }}
            >
              Top business news
            </div>
            <div style={{ fontSize: "12px", color: "#666" }}>
              Global + related
            </div>
          </div>

          <div style={{ display: "grid", gap: "10px" }}>
            {relatedNews.map((item) => (
              <a
                key={item.title}
                href={item.url}
                target="_blank"
                rel="noopener noreferrer"
                style={{
                  padding: "10px 12px",
                  background: "#f8f9fa",
                  borderRadius: "8px",
                  border: "1px solid #e8eaed",
                  color: "inherit",
                  textDecoration: "none",
                  display: "block",
                }}
              >
                <div style={{ fontSize: "12px", fontWeight: 600, color: "#111" }}>
                  {item.title}
                </div>
                <div style={{ fontSize: "11px", color: "#555", marginTop: "4px" }}>
                  {item.source} · {item.time}
                </div>
              </a>
            ))}
          </div>
        </div>
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
