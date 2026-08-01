import { useState } from "react";
import Screener from "./pages/Screener";
import DataLoader from "./pages/DataLoader";

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

  return (
    <div style={{ display: "flex", flexDirection: "column", height: "100vh" }}>
      {/* Navigation Bar */}
      <div
        style={{
          display: "flex",
          background: "#333",
          color: "white",
          padding: "0",
          borderBottom: "2px solid #007bff",
        }}
      >
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
      </div>

      {/* Page Content */}
      <div style={{ flex: 1, overflow: "auto" }}>
        {currentPage === "screener" && <Screener pageTitle="All Stocks Screener" />}
        {currentPage === "qqq" && (
          <Screener
            universeSymbols={QQQ_SYMBOLS}
            universeMeta={QQQ_WEIGHTS}
            pageTitle="QQQ Screener"
          />
        )}
        {currentPage === "dataloader" && <DataLoader />}
      </div>
    </div>
  );
}

export default App;