import { useEffect, useState } from "react";
import Screener from "./pages/Screener";
import DataLoader from "./pages/DataLoader";
import Admin from "./pages/Admin";
import MAScreener from "./pages/MAScreener";
import RSIScreener from "./pages/RSIScreener";
import ATHScreener from "./pages/ATHScreener";

const QQQ_SYMBOLS = [
  "AAPL",
  "MSFT",
  "NVDA",
  "GOOGL",
  "GOOG",
  "AMZN",
  "META",
  "TSLA",
  "AVGO",
  "PEP",
  "NFLX",
  "ADBE",
  "INTC",
  "CSCO",
  "QCOM",
  "AMD",
  "TXN",
  "AMAT",
  "COST",
  "CMCSA",
];

const QQQ_WEIGHTS = {
  NVDA: 10.5,
  MSFT: 8.2,
  AAPL: 7.0,
  AMZN: 3.5,
  GOOG: 3.3,
  GOOGL: 3.3,
  META: 2.8,
  TSLA: 2.3,
  AVGO: 2.0,
  PEP: 1.8,
  NFLX: 1.7,
  ADBE: 1.6,
  INTC: 1.4,
  CSCO: 1.4,
  QCOM: 1.2,
  AMD: 1.2,
  TXN: 1.0,
  AMAT: 0.9,
  COST: 0.9,
  CMCSA: 0.8,
};

function App() {
  const [currentPage, setCurrentPage] = useState("screener");
  const [theme, setTheme] = useState(() => {
    const savedTheme = window.localStorage.getItem("trading-terminal-theme");
    return savedTheme === "dark" ? "dark" : "light";
  });

  useEffect(() => {
    window.localStorage.setItem("trading-terminal-theme", theme);
  }, [theme]);

  return (
    <div className="app-shell" data-theme={theme}>
      {/* Navigation Bar */}
      <div
        className="app-nav"
        style={{
          display: "flex",
          background: "#333",
          color: "white",
          padding: "0",
          borderBottom: "2px solid #007bff",
        }}
      >
        <button
          className={`app-nav__button${currentPage === "market" ? " app-nav__button--active" : ""}`}
          onClick={() => setCurrentPage("market")}
          type="button"
        >
          📈 Market
        </button>
        <button
          onClick={() => setCurrentPage("screener")}
          style={{
            padding: "15px 20px",
            background: currentPage === "screener" ? "#007bff" : "#333",
            color: "white",
            border: "none",
            cursor: "pointer",
            fontSize: "16px",
            fontWeight: "bold",
            transition: "background 0.3s",
          }}
          onMouseOver={(e) =>
            currentPage !== "screener" && (e.target.style.background = "#555")
          }
          onMouseOut={(e) =>
            currentPage !== "screener" && (e.target.style.background = "#333")
          }
        >
          📊 Screener
        </button>
        <button
          onClick={() => setCurrentPage("qqq")}
          style={{
            padding: "15px 20px",
            background: currentPage === "qqq" ? "#007bff" : "#333",
            color: "white",
            border: "none",
            cursor: "pointer",
            fontSize: "16px",
            fontWeight: "bold",
            transition: "background 0.3s",
          }}
          onMouseOver={(e) =>
            currentPage !== "qqq" && (e.target.style.background = "#555")
          }
          onMouseOut={(e) =>
            currentPage !== "qqq" && (e.target.style.background = "#333")
          }
        >
          🟣 QQQ Screener
        </button>
        <button
          onClick={() => setCurrentPage("dataloader")}
          style={{
            padding: "15px 20px",
            background: currentPage === "dataloader" ? "#007bff" : "#333",
            color: "white",
            border: "none",
            cursor: "pointer",
            fontSize: "16px",
            fontWeight: "bold",
            transition: "background 0.3s",
          }}
          onMouseOver={(e) =>
            currentPage !== "dataloader" && (e.target.style.background = "#555")
          }
          onMouseOut={(e) =>
            currentPage !== "dataloader" && (e.target.style.background = "#333")
          }
        >
          ⬇️ Data Loader
        </button>
        <button
          onClick={() => setCurrentPage("ma")}
          style={{
            padding: "15px 20px",
            background: currentPage === "ma" ? "#007bff" : "#333",
            color: "white",
            border: "none",
            cursor: "pointer",
            fontSize: "16px",
            fontWeight: "bold",
            transition: "background 0.3s",
          }}
          onMouseOver={(e) =>
            currentPage !== "ma" && (e.target.style.background = "#555")
          }
          onMouseOut={(e) =>
            currentPage !== "ma" && (e.target.style.background = "#333")
          }
        >
          📈 MA Screener
        </button>
        <button
          onClick={() => setCurrentPage("rsi")}
          style={{
            padding: "15px 20px",
            background: currentPage === "rsi" ? "#007bff" : "#333",
            color: "white",
            border: "none",
            cursor: "pointer",
            fontSize: "16px",
            fontWeight: "bold",
            transition: "background 0.3s",
          }}
          onMouseOver={(e) =>
            currentPage !== "rsi" && (e.target.style.background = "#555")
          }
          onMouseOut={(e) =>
            currentPage !== "rsi" && (e.target.style.background = "#333")
          }
        >
          📉 RSI Screener
        </button>
        <button
          onClick={() => setCurrentPage("ath")}
          style={{
            padding: "15px 20px",
            background: currentPage === "ath" ? "#007bff" : "#333",
            color: "white",
            border: "none",
            cursor: "pointer",
            fontSize: "16px",
            fontWeight: "bold",
            transition: "background 0.3s",
          }}
          onMouseOver={(e) =>
            currentPage !== "ath" && (e.target.style.background = "#555")
          }
          onMouseOut={(e) =>
            currentPage !== "ath" && (e.target.style.background = "#333")
          }
        >
          🏆 ATH Screener
        </button>
        <button
          className={`app-nav__button${currentPage === "admin" ? " app-nav__button--active" : ""}`}
          onClick={() => setCurrentPage("admin")}
          type="button"
        >
          ⚙️ Admin
        </button>
      </div>

      {/* Page Content */}
      <div className="app-content">
        {currentPage === "market" && (
          <Screener fixedMode="live" pageTitle="Market" />
        )}
        {currentPage === "screener" && (
          <Screener fixedMode="history" pageTitle="All Stocks Screener" />
        )}
        {currentPage === "qqq" && (
          <Screener
            fixedMode="history"
            universeSymbols={QQQ_SYMBOLS}
            universeMeta={QQQ_WEIGHTS}
            pageTitle="QQQ Screener"
          />
        )}
        {currentPage === "dataloader" && <DataLoader />}
        {currentPage === "ma" && <MAScreener />}
        {currentPage === "rsi" && <RSIScreener />}
        {currentPage === "ath" && <ATHScreener />}
        {currentPage === "admin" && <Admin theme={theme} onThemeChange={setTheme} />}
      </div>
    </div>
  );
}

export default App;