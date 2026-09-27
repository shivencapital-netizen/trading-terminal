import { useCallback, useEffect, useState } from "react";

const API_BASE = process.env.REACT_APP_API_BASE || "http://127.0.0.1:8000";
const EXAMPLES = [
  "How many times did QQQ close more than 3% up or more than 3% down in the last 2 years?",
  "How many weeks in the last 3 years did QQQ close above or below 2% from the previous week's last trading day close?",
  "Count days when NVDA moved over 5% in the last 1 year",
  "Show SPY moves greater than 2% over the last 5 years",
];

function formatDate(value) {
  return new Date(`${value}T12:00:00`).toLocaleDateString(undefined, {
    year: "numeric",
    month: "short",
    day: "numeric",
  });
}

function formatTimestamp(value) {
  return new Date(value).toLocaleString(undefined, {
    month: "short",
    day: "numeric",
    hour: "numeric",
    minute: "2-digit",
  });
}

function BacktestResult({ result }) {
  const [eventsFilter, setEventsFilter] = useState("all");
  const hasThreshold = result.threshold_percent > 0;
  const periodName = result.timeframe === "week" ? "weeks" : "sessions";
  const expectedPeriods = result.expected_periods ?? (result.years || 2) * 240;
  const events = [
    ...result.positive_events.map((event) => ({ ...event, direction: "up" })),
    ...result.negative_events.map((event) => ({ ...event, direction: "down" })),
  ]
    .filter((event) => eventsFilter === "all" || event.direction === eventsFilter)
    .sort((left, right) => right.date.localeCompare(left.date));

  return (
    <>
      <div className="backtest-answer">
        <div className="backtest-answer-icon" aria-hidden="true">✓</div>
        <div>
          <p className="backtest-answer-label">ANALYSIS COMPLETE</p>
          <h2>
            {result.symbol} had <strong>{result.positive_count}</strong> {periodName} with gains
            {hasThreshold ? ` above +${result.threshold_percent}%` : ""}, and <strong>{result.negative_count}</strong>
            {" "}{periodName} with losses{hasThreshold ? ` below −${result.threshold_percent}%` : ""}.
          </h2>
          <p>
            {result.analyzed_sessions.toLocaleString()} {periodName} analyzed ·{" "}
            {result.data_start_date && result.data_end_date
              ? `${formatDate(result.data_start_date)} – ${formatDate(result.data_end_date)} data coverage (requested ${formatDate(result.start_date)} – ${formatDate(result.end_date)})`
              : `No ${periodName} available in this range`}
          </p>
          <p>
            Interpreted as {result.interpretation.symbol} ·{" "}
            {result.interpretation.lookback_trading_days
              ? `${result.interpretation.lookback_trading_days} trading days`
              : `${result.interpretation.years || result.years} ${(result.interpretation.years || result.years) === 1 ? "year" : "years"}`} ·{" "}
            {result.interpretation.timeframe === "week" || result.timeframe === "week" ? "weekly" : "daily"}
            {hasThreshold ? ` · ±${result.interpretation.threshold_percent}%` : " · all gains/losses"}
          </p>
        </div>
      </div>

      {result.analyzed_sessions < expectedPeriods * 0.8 && (
        <div className="backtest-coverage-warning" role="status">
      Limited history: only {result.analyzed_sessions.toLocaleString()} {periodName} are available
          {" "}for this query, so the result may not cover the full requested period.
        </div>
      )}

      <div className="backtest-metrics">
        <article className="backtest-metric">
          <div className="backtest-metric-label">
            <span className="backtest-dot backtest-dot--up" /> LARGE UP {result.timeframe === "week" ? "WEEKS" : "DAYS"}
          </div>
          <strong className="backtest-metric-value backtest-text--up">{result.positive_count}</strong>
          <span className="backtest-metric-caption">
            {result.timeframe === "week" ? "Weekly" : "Daily"} close-to-close gains{hasThreshold ? ` > +${result.threshold_percent}%` : ""}
          </span>
        </article>
        <article className="backtest-metric">
          <div className="backtest-metric-label">
            <span className="backtest-dot backtest-dot--down" /> LARGE DOWN {result.timeframe === "week" ? "WEEKS" : "DAYS"}
          </div>
          <strong className="backtest-metric-value backtest-text--down">{result.negative_count}</strong>
          <span className="backtest-metric-caption">
            {result.timeframe === "week" ? "Weekly" : "Daily"} close-to-close losses{hasThreshold ? ` < −${result.threshold_percent}%` : ""}
          </span>
        </article>
        <article className="backtest-metric">
          <div className="backtest-metric-label">{result.timeframe === "week" ? "WEEKS TESTED" : "SESSIONS TESTED"}</div>
          <strong className="backtest-metric-value">{result.analyzed_sessions.toLocaleString()}</strong>
          <span className="backtest-metric-caption">With a prior {result.timeframe || "day"} close</span>
        </article>
      </div>

      <article className="backtest-events-card">
        <div className="backtest-events-header">
          <div>
            <h2>Move history</h2>
            <p>{hasThreshold ? "Review every period that crossed the threshold." : "Review every gain and loss."}</p>
          </div>
          <div className="backtest-event-filters" role="group" aria-label="Filter move history">
            {[
              ["all", "All moves"],
              ["up", "Up days"],
              ["down", "Down days"],
            ].map(([value, label]) => (
              <button
                key={value}
                type="button"
                className={eventsFilter === value ? "is-active" : ""}
                onClick={() => setEventsFilter(value)}
              >
                {label}
              </button>
            ))}
          </div>
        </div>
        {events.length ? (
          <div className="backtest-table-wrap">
            <table>
              <thead>
                <tr><th>SESSION</th><th>DIRECTION</th><th>PREVIOUS CLOSE</th><th>CLOSE</th><th>CHANGE</th></tr>
              </thead>
              <tbody>
                {events.map((event) => (
                  <tr key={`${event.date}-${event.direction}`}>
                    <td>{formatDate(event.date)}</td>
                    <td>
                      <span className={`backtest-event-tag backtest-event-tag--${event.direction}`}>
                        {event.direction === "up" ? "▲ Up" : "▼ Down"}
                      </span>
                    </td>
                    <td>${event.previous_close.toFixed(2)}</td>
                    <td>${event.close.toFixed(2)}</td>
                    <td className={event.direction === "up" ? "backtest-text--up" : "backtest-text--down"}>
                      {event.change_percent > 0 ? "+" : ""}{event.change_percent.toFixed(2)}%
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : (
          <div className="backtest-empty">No gains or losses found in the selected period.</div>
        )}
      </article>

      <details className="backtest-methodology">
        <summary>How this result is calculated</summary>
        <p>{result.methodology}</p>
      </details>
    </>
  );
}

function BacktestLab() {
  const [question, setQuestion] = useState("");
  const [result, setResult] = useState(null);
  const [history, setHistory] = useState([]);
  const [activeConversationId, setActiveConversationId] = useState(null);
  const [loading, setLoading] = useState(false);
  const [historyLoading, setHistoryLoading] = useState(true);
  const [historyError, setHistoryError] = useState("");
  const [error, setError] = useState("");
  const [assistantStatus, setAssistantStatus] = useState("checking");
  const [assistantMessage, setAssistantMessage] = useState("");

  const checkAssistantStatus = useCallback(async () => {
    setAssistantStatus("checking");
    try {
      const response = await fetch(`${API_BASE}/api/v1/backtest/assistant-status`);
      if (!response.ok) {
        throw new Error("Could not check local Ollama configuration.");
      }
      const status = await response.json();
      setAssistantStatus(status.status);
      setAssistantMessage(status.message || "");
    } catch {
      setAssistantStatus("unavailable");
      setAssistantMessage("Could not check the local AI service. Make sure the backend is running.");
    }
  }, []);

  const refreshHistory = useCallback(async () => {
    setHistoryLoading(true);
    setHistoryError("");
    try {
      const response = await fetch(`${API_BASE}/api/v1/backtest/history`);
      const body = await response.json();
      if (!response.ok) {
        throw new Error(body.detail || "Could not load saved backtests.");
      }
      setHistory(body);
    } catch (historyLoadError) {
      setHistoryError(historyLoadError.message || "Could not load saved backtests.");
    } finally {
      setHistoryLoading(false);
    }
  }, []);

  useEffect(() => {
    checkAssistantStatus();
    refreshHistory();
  }, [checkAssistantStatus, refreshHistory]);

  async function runQuestion(value = question) {
    const trimmedQuestion = value.trim();
    if (!trimmedQuestion) {
      setError("Enter a question to run an analysis.");
      return;
    }
    setQuestion(trimmedQuestion);
    setError("");
    setResult(null);
    setActiveConversationId(null);
    setLoading(true);
    try {
      const response = await fetch(`${API_BASE}/api/v1/backtest/ask`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ question: trimmedQuestion }),
      });
      const body = await response.json();
      if (!response.ok) {
        throw new Error(body.detail || "The backtest query could not be completed.");
      }
      setResult(body);
      setActiveConversationId(body.conversation_id);
      await refreshHistory();
    } catch (requestError) {
      setError(requestError.message || "Unable to reach the backtest service.");
    } finally {
      setLoading(false);
    }
  }

  async function openConversation(conversationId) {
    setError("");
    setActiveConversationId(conversationId);
    setResult(null);
    setLoading(true);
    try {
      const response = await fetch(`${API_BASE}/api/v1/backtest/history/${conversationId}`);
      const body = await response.json();
      if (!response.ok) {
        throw new Error(body.detail || "Could not load this saved backtest.");
      }
      setQuestion(body.question);
      setResult(body);
    } catch (requestError) {
      setError(requestError.message || "Could not load this saved backtest.");
    } finally {
      setLoading(false);
    }
  }

  function startNewQuestion() {
    setQuestion("");
    setResult(null);
    setActiveConversationId(null);
    setError("");
  }

  const assistantDescription = assistantStatus === "offline"
    ? `${assistantMessage} Install Ollama, then run: ollama pull qwen3:4b`
    : assistantStatus === "model-missing" || assistantStatus === "not-configured"
      ? assistantMessage
      : assistantStatus === "ready"
        ? "Your question is interpreted by Ollama running on this computer. Candle data and all calculations stay in your local database."
        : assistantStatus === "unavailable"
          ? assistantMessage
          : "Checking that Ollama is running locally and the qwen3:4b model is downloaded.";

  return (
    <main className="backtest-page">
      <header className="backtest-header">
        <div>
          <p className="backtest-eyebrow">RESEARCH WORKSPACE · HISTORICAL DATA</p>
          <h1>Backtest Lab</h1>
          <p className="backtest-subtitle">Ask a market question. Your saved analyses stay here.</p>
        </div>
        <div className="backtest-status-group">
          <span className={`backtest-status backtest-status--${assistantStatus}`}>
            <span />
            {assistantStatus === "ready" && "OLLAMA READY"}
            {assistantStatus === "checking" && "CHECKING OLLAMA"}
            {assistantStatus === "offline" && "OLLAMA OFFLINE"}
            {assistantStatus === "model-missing" && "MODEL NOT DOWNLOADED"}
            {assistantStatus === "not-configured" && "OLLAMA NEEDS SETUP"}
            {assistantStatus === "unavailable" && "BACKEND UNAVAILABLE"}
          </span>
          {assistantStatus !== "ready" && (
            <button
              className="backtest-status-check"
              type="button"
              onClick={checkAssistantStatus}
              disabled={assistantStatus === "checking"}
            >
              Check again
            </button>
          )}
        </div>
      </header>

      <div className="backtest-workspace">
        <aside className="backtest-sidebar">
          <section className="backtest-query-card" aria-labelledby="backtest-query-title">
            <div className="backtest-card-heading">
              <div className="backtest-assistant-mark" aria-hidden="true">✳</div>
              <div>
                <h2 id="backtest-query-title">Ask a question</h2>
                <p>Describe the daily or weekly move you want to test.</p>
              </div>
            </div>
            <form
              onSubmit={(event) => {
                event.preventDefault();
                runQuestion();
              }}
            >
              <label className="backtest-sr-only" htmlFor="backtest-question">Your backtest question</label>
              <textarea
                id="backtest-question"
                value={question}
                onChange={(event) => setQuestion(event.target.value)}
                placeholder="e.g. How often did QQQ move over 3% in the last 2 years?"
                rows={5}
              />
              <div className="backtest-query-footer">
                <span>Ollama AI · Local candle data</span>
                <button type="submit" disabled={loading}>
                  {loading ? "Analyzing…" : "Run analysis"} <span aria-hidden="true">→</span>
                </button>
              </div>
            </form>
            <div className="backtest-examples">
              <span>EXAMPLES</span>
              {EXAMPLES.map((example) => (
                <button type="button" key={example} onClick={() => setQuestion(example)}>
                  {example}
                </button>
              ))}
            </div>
            <p className="backtest-beta-note">{assistantDescription}</p>
          </section>

          <section className="backtest-history" aria-labelledby="backtest-history-title">
            <div className="backtest-history-heading">
              <div>
                <h2 id="backtest-history-title">History</h2>
                <p>Your saved analyses</p>
              </div>
              <button type="button" onClick={startNewQuestion}>＋ New</button>
            </div>
            {historyError && <p className="backtest-history-error" role="alert">{historyError}</p>}
            {historyLoading ? (
              <p className="backtest-history-empty">Loading saved analyses…</p>
            ) : history.length ? (
              <div className="backtest-history-list">
                {history.map((item) => (
                  <button
                    key={item.id}
                    type="button"
                    className={`backtest-history-item${activeConversationId === item.id ? " is-active" : ""}`}
                    onClick={() => openConversation(item.id)}
                  >
                    <span className="backtest-history-question">{item.question}</span>
                    <span className="backtest-history-meta">
                      {item.symbol} · {item.timeframe === "week" ? "Weekly" : "Daily"}
                      {" · "}{item.period_label || `${item.years} years`}
                      {" · "}+{item.positive_count} / −{item.negative_count} · {formatTimestamp(item.created_at)}
                    </span>
                  </button>
                ))}
              </div>
            ) : (
              <p className="backtest-history-empty">Completed analyses will be saved here.</p>
            )}
          </section>
        </aside>

        <section className="backtest-conversation" aria-label="Backtest conversation">
          <div className="backtest-conversation-header">
            <div>
              <p className="backtest-eyebrow">ANALYSIS</p>
              <h2>
                {result
                  ? `${result.symbol} ${result.timeframe === "week" ? "weekly" : "daily"} move analysis`
                  : "Your results appear here"}
              </h2>
            </div>
            {result?.created_at && (
              <span className="backtest-conversation-date">{formatTimestamp(result.created_at)}</span>
            )}
          </div>

          {error && <div className="backtest-error" role="alert">{error}</div>}

          {loading && (
            <div className="backtest-loading" role="status">
              <span className="backtest-loading-spinner" />
              <div>
                <strong>{activeConversationId ? "Opening saved analysis…" : "Analyzing your question…"}</strong>
                <p>Ollama interprets the request, then your database provides the numbers.</p>
              </div>
            </div>
          )}

          {!loading && result ? (
            <div className="backtest-thread">
              <div className="backtest-question-bubble">
                <span>YOU ASKED</span>
                <p>{result.question}</p>
              </div>
              <BacktestResult result={result} />
            </div>
          ) : !loading ? (
            <div className="backtest-welcome">
              <div className="backtest-assistant-mark" aria-hidden="true">✳</div>
              <h2>Run an analysis to get started</h2>
              <p>Your question and its results will be saved to History so you can revisit them anytime.</p>
            </div>
          ) : null}
        </section>
      </div>
    </main>
  );
}

export default BacktestLab;
