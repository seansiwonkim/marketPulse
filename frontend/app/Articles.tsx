"use client";

import { useCallback, useEffect, useState } from "react";
import { API } from "./api";

// One model's verdict. `null` on an article means "not analyzed yet" (different from a score of 0).
type ModelResult = { model_name: string; label: string; score: number };

type Article = {
  id: number;
  ticker: string;
  title: string;
  source: string;
  url: string;
  published_at: string;
  finbert: ModelResult | null;
  vader: ModelResult | null;
};

const fmt = (n: number) => (n > 0 ? "+" : n < 0 ? "−" : "") + Math.abs(n).toFixed(2);

const when = (iso: string) =>
  new Date(iso).toLocaleString("en-US", {
    month: "short",
    day: "numeric",
    hour: "numeric",
    minute: "2-digit",
  });

// Color AND a word AND a symbol, so meaning never depends on color alone.
const LABELS: Record<string, { text: string; symbol: string; className: string }> = {
  positive: { text: "Positive", symbol: "▲", className: "pos" },
  negative: { text: "Negative", symbol: "▼", className: "neg" },
  neutral: { text: "Neutral", symbol: "●", className: "neu" },
};

function Verdict({ name, result }: { name: string; result: ModelResult | null }) {
  const label = result && (LABELS[result.label] ?? LABELS.neutral);
  return (
    <div className="verdict">
      <span className="model">{name}</span>
      {result && label ? (
        <span className={`badge ${label.className}`}>
          <span aria-hidden="true">{label.symbol}</span> {label.text}
          <b>{fmt(result.score)}</b>
        </span>
      ) : (
        <span className="pending">Awaiting analysis</span>
      )}
    </div>
  );
}

function Tile({ a }: { a: Article }) {
  return (
    <li className="tile">
      <a className="headline" href={a.url} target="_blank" rel="noopener noreferrer" title={a.title}>
        {a.title}
      </a>
      <p className="meta">
        {a.source}, {a.ticker}, {when(a.published_at)}
      </p>
      <Verdict name="FinBERT" result={a.finbert} />
      <Verdict name="VADER" result={a.vader} />
    </li>
  );
}

const POLL_MS = 60_000; // how often the page checks the API for news

type Page = { items: Article[]; next_cursor: string | null };

async function fetchPage(query: string, cursor?: string): Promise<Page> {
  // encodeURIComponent matters: a cursor contains "+" (the time zone), which a URL would read as a space.
  const url = `${API}/api/v1/articles?${query}${cursor ? `&cursor=${encodeURIComponent(cursor)}` : ""}`;
  const res = await fetch(url);
  if (!res.ok) throw new Error(String(res.status));
  return res.json();
}

// Fetches the first page, then more on request. Mounted with a key built from the filters,
// so changing a filter remounts it and starts fresh at "loading".
function ArticleList({
  query,
  ticker,
  onRefreshed,
}: {
  query: string;
  ticker: string;
  onRefreshed: () => void; // tells the parent the browser just asked the API for data
}) {
  const [articles, setArticles] = useState<Article[] | null>(null);
  const [latest, setLatest] = useState<Article[]>([]); // newest first page, re-fetched in the background
  const [cursor, setCursor] = useState<string | null>(null); // where the next page starts
  const [error, setError] = useState(false);
  const [loadingMore, setLoadingMore] = useState(false);
  const [attempt, setAttempt] = useState(0); // bump to reload the first page (retry, or "Show new articles")

  useEffect(() => {
    let stale = false;
    fetchPage(query)
      .then((page) => {
        if (stale) return;
        setArticles(page.items);
        setLatest(page.items);
        setCursor(page.next_cursor);
        setError(false);
        onRefreshed();
      })
      .catch(() => !stale && setError(true));
    return () => {
      stale = true;
    };
  }, [query, attempt, onRefreshed]);

  // Every minute, quietly peek at the newest page. We only store it; what shows on screen is decided below.
  useEffect(() => {
    const timer = setInterval(async () => {
      if (document.hidden) return; // don't poll from a background tab
      try {
        const page = await fetchPage(query);
        setLatest(page.items);
        onRefreshed();
      } catch {
        // stay quiet; the next tick tries again
      }
    }, POLL_MS);
    return () => clearInterval(timer);
  }, [query, onRefreshed]);

  async function loadMore() {
    if (!cursor) return;
    setLoadingMore(true);
    try {
      const page = await fetchPage(query, cursor);
      setArticles((prev) => [...(prev ?? []), ...page.items]);
      setCursor(page.next_cursor);
      setError(false);
      onRefreshed();
    } catch {
      setError(true);
    } finally {
      setLoadingMore(false);
    }
  }

  // Tiles already on screen get fresh scores in place (pending becomes a result) but never move.
  // Articles we haven't shown yet only produce a banner; the user decides when to pull them in.
  const fresh = new Map(latest.map((a) => [a.id, a]));
  const shown = articles?.map((a) => fresh.get(a.id) ?? a);
  const onScreen = new Set(articles?.map((a) => a.id));
  const hasNew = latest.some((a) => !onScreen.has(a.id));

  return (
    <>
      {error && (
        <p className="message" role="alert">
          Couldn&apos;t load headlines.{" "}
          <button className="link" onClick={() => (articles ? loadMore() : setAttempt((n) => n + 1))}>
            Try again
          </button>
        </p>
      )}
      {!error && articles === null && <p className="message">Loading headlines…</p>}
      {articles?.length === 0 && (
        <p className="message">No headlines match these filters{ticker ? ` for ${ticker}` : ""}.</p>
      )}

      {hasNew && articles && (
        <p className="banner" role="status">
          New articles available.{" "}
          <button className="link" onClick={() => setAttempt((n) => n + 1)}>
            Show new articles
          </button>
        </p>
      )}

      {shown && shown.length > 0 && (
        <>
          <ul className="grid">
            {shown.map((a) => (
              <Tile key={a.id} a={a} />
            ))}
          </ul>
          {cursor ? (
            <button className="more" onClick={loadMore} disabled={loadingMore}>
              {loadingMore ? "Loading…" : "Load more"}
            </button>
          ) : (
            <p className="note">That&apos;s every headline for these filters.</p>
          )}
        </>
      )}
    </>
  );
}

export default function Articles({ ticker }: { ticker: string }) {
  const [scope, setScope] = useState<"ticker" | "all">("ticker");
  const [start, setStart] = useState("");
  const [end, setEnd] = useState("");

  // Two different clocks:
  //  - fetchedAt: when the server last got news from Finnhub (the pipeline's last success)
  //  - refreshedAt: when this browser last asked the server for data
  // fetchedAt: undefined = still loading, null = the pipeline has never succeeded.
  const [fetchedAt, setFetchedAt] = useState<string | null | undefined>(undefined);
  const [refreshedAt, setRefreshedAt] = useState<Date | null>(null);
  const markRefreshed = useCallback(() => setRefreshedAt(new Date()), []);

  useEffect(() => {
    const load = () =>
      fetch(`${API}/api/v1/status`)
        .then((res) => res.json())
        .then((s: { news_last_fetched: string | null }) => setFetchedAt(s.news_last_fetched))
        .catch(() => {}); // keep showing the last known value
    load();
    const timer = setInterval(() => !document.hidden && load(), POLL_MS);
    return () => clearInterval(timer);
  }, []);

  const badRange = start !== "" && end !== "" && start > end;

  const params = new URLSearchParams({ limit: "24" });
  if (scope === "ticker") params.set("ticker", ticker);
  if (start) params.set("start", start);
  if (end) params.set("end", end);
  const query = params.toString();

  return (
    <section className="articles" aria-labelledby="articles-heading">
      <h2 id="articles-heading">Latest headlines</h2>
      <p className="note">
        Newest first. FinBERT&apos;s score is its positive probability minus its negative probability.
        VADER&apos;s is its compound score. Both run from −1 to +1, but they are different measurements, so
        compare labels, not numbers.
      </p>

      <p className="status">
        <span>
          News last fetched:{" "}
          <b>{fetchedAt === undefined ? "…" : fetchedAt ? when(fetchedAt) : "not recorded yet"}</b>
        </span>
        <span>
          Dashboard refreshed:{" "}
          <b>
            {refreshedAt
              ? refreshedAt.toLocaleTimeString("en-US", { hour: "numeric", minute: "2-digit", second: "2-digit" })
              : "…"}
          </b>
        </span>
      </p>

      <div className="filters">
        <label>
          Show
          <select value={scope} onChange={(e) => setScope(e.target.value as "ticker" | "all")}>
            <option value="ticker">{ticker} only</option>
            <option value="all">All tickers</option>
          </select>
        </label>
        <label>
          From
          <input type="date" value={start} max={end || undefined} onChange={(e) => setStart(e.target.value)} />
        </label>
        <label>
          To
          <input type="date" value={end} min={start || undefined} onChange={(e) => setEnd(e.target.value)} />
        </label>
        {(start || end) && (
          <button
            className="link"
            onClick={() => {
              setStart("");
              setEnd("");
            }}
          >
            Clear dates
          </button>
        )}
      </div>

      {badRange ? (
        <p className="message" role="alert">
          The start date is after the end date. Pick a start on or before the end.
        </p>
      ) : (
        <ArticleList
          key={query}
          query={query}
          ticker={scope === "ticker" ? ticker : ""}
          onRefreshed={markRefreshed}
        />
      )}
    </section>
  );
}
