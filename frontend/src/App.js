import { useState } from "react";
import Screener from "./pages/Screener";
import DataLoader from "./pages/DataLoader";

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
        {currentPage === "screener" && <Screener />}
        {currentPage === "dataloader" && <DataLoader />}
      </div>
    </div>
  );
}

export default App;