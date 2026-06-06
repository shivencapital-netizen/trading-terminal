import { useState } from "react";
import ScreenerSidebar from "../components/screener/ScreenerSidebar";
import ScreenerResults from "../components/screener/ScreenerResults";

export default function Screener() {
  const [criteria, setCriteria] = useState({});
  const [results, setResults] = useState([]);

  const runScreener = async () => {
    try {
      const res = await fetch("http://127.0.0.1:8000/api/v1/screener/run");

      const data = await res.json();

      // Prevent crashes if backend returns non-array
      setResults(Array.isArray(data) ? data : []);
    } catch (err) {
      console.error("Screener error:", err);
      setResults([]);
    }
  };

  return (
    <div style={{ display: "flex", height: "100vh" }}>
      <ScreenerSidebar
        criteria={criteria}
        setCriteria={setCriteria}
        runScreener={runScreener}
      />
      <ScreenerResults results={results} />
    </div>
  );
}
