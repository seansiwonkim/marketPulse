"use client";

import { useEffect, useState } from "react";
import {
  CartesianGrid,
  Line,
  LineChart,
  ReferenceLine,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

import Articles from "./Articles";
import { API } from "./api";

const TICKERS = ["NVDA", "AAPL", "TSLA"];

// Names the backend stores in sentiment_scores.model_name.
const FINBERT = "ProsusAI/finbert";
const VADER = "vader";

// Shape of one item from GET /api/v1/stocks/{ticker}/sentiment/daily
type Day = { date: string; avg_score: number; article_count: number };

// One chart row: a date plus one value per model.
type Row = { date: string; finbert?: number; vader?: number };

async function fetchDaily(ticker: string, model: string): Promise<Day[]> {
  const url = `${API}/api/v1/stocks/${ticker}/sentiment/daily?model=${encodeURIComponent(model)}`;
  const res = await fetch(url);
  if (!res.ok) throw new Error(`API returned ${res.status}`);
  return res.json();
}

// Recharts wants one object per x value, so merge the two lists by date.
function mergeByDate(finbert: Day[], vader: Day[]): Row[] {
  const byDate = new Map<string, Row>();
  for (const d of finbert) byDate.set(d.date, { date: d.date, finbert: d.avg_score });
  for (const d of vader) {
    byDate.set(d.date, { ...byDate.get(d.date), date: d.date, vader: d.avg_score });
  }
  return [...byDate.values()].sort((a, b) => a.date.localeCompare(b.date));
}

function mood(score: number) {
  if (score > 0.05) return "positive";
  if (score < -0.05) return "negative";
  return "mixed";
}

const fmt = (n: number) => (n > 0 ? "+" : n < 0 ? "−" : "") + Math.abs(n).toFixed(2);

// "2026-11-22" -> "Nov 22". The "T00:00" keeps it in local time, so the day never shifts.
const shortDate = (d: string) =>
  new Date(`${d}T00:00`).toLocaleDateString("en-US", { month: "short", day: "numeric" });

export default function Home() {
  const [ticker, setTicker] = useState(TICKERS[0]);
  const [rows, setRows] = useState<Row[] | null>(null); // null = loading
  const [error, setError] = useState("");

  // Runs on first render and again whenever `ticker` changes.
  useEffect(() => {
    let stale = false; // ignore a slow response if the user already picked another ticker

    Promise.all([fetchDaily(ticker, FINBERT), fetchDaily(ticker, VADER)])
      .then(([finbert, vader]) => {
        if (!stale) setRows(mergeByDate(finbert, vader));
      })
      .catch(() => {
        if (!stale) setError(`Can't reach the API at ${API}. Check that docker compose is running.`);
      });

    return () => {
      stale = true;
    };
  }, [ticker]);

  const latest = rows?.[rows.length - 1];
  const reduceMotion =
    typeof window !== "undefined" && window.matchMedia("(prefers-reduced-motion: reduce)").matches;

  return (
    <main className="page">
      <label className="picker">
        Ticker
        <select
          className="ticker"
          value={ticker}
          onChange={(e) => {
            setTicker(e.target.value);
            setRows(null); // back to "loading" until the new data arrives
            setError("");
          }}
        >
          {TICKERS.map((t) => (
            <option key={t}>{t}</option>
          ))}
        </select>
      </label>

      <h1>
        {latest?.finbert !== undefined
          ? `${ticker} news is leaning ${mood(latest.finbert)}.`
          : rows?.length === 0
            ? `${ticker} has no news yet.`
            : `Loading ${ticker}…`}
      </h1>

      {latest && (
        <p className="readings">
          <span className="reading">
            <span className="swatch" />
            FinBERT <b>{latest.finbert !== undefined ? fmt(latest.finbert) : "n/a"}</b>
          </span>
          <span className="reading">
            <span className="swatch dashed" />
            VADER <b>{latest.vader !== undefined ? fmt(latest.vader) : "n/a"}</b>
          </span>
          <span>on {shortDate(latest.date)}</span>
        </p>
      )}

      {error && <p className="message" role="alert">{error}</p>}

      {rows?.length === 0 && (
        <p className="message">
          No articles for {ticker} yet. Run the ingest worker, then the sentiment worker, and reload.
        </p>
      )}

      {rows && rows.length > 0 && (
        <div className="chart">
          <ResponsiveContainer width="100%" height="100%">
            <LineChart data={rows} margin={{ top: 8, right: 16, bottom: 0, left: -8 }}>
              <CartesianGrid vertical={false} stroke="var(--rule)" />
              <XAxis
                dataKey="date"
                tickFormatter={shortDate}
                stroke="var(--muted)"
                tick={{ fontSize: 14 }}
                tickLine={false}
              />
              <YAxis
                domain={[-1, 1]}
                ticks={[-1, -0.5, 0, 0.5, 1]}
                stroke="var(--muted)"
                tick={{ fontSize: 14 }}
                tickLine={false}
                axisLine={false}
              />
              <ReferenceLine y={0} stroke="var(--zero)" strokeWidth={1.5} />
              <Tooltip
                labelFormatter={(d) => shortDate(String(d))}
                formatter={(v) => fmt(Number(v))}
                contentStyle={{
                  background: "var(--paper)",
                  border: "1px solid var(--zero)",
                  borderRadius: 0,
                  color: "var(--ink)",
                }}
              />
              <Line
                name="FinBERT"
                dataKey="finbert"
                stroke="var(--finbert)"
                strokeWidth={3}
                dot={{ r: 4 }}
                isAnimationActive={!reduceMotion}
              />
              <Line
                name="VADER"
                dataKey="vader"
                stroke="var(--vader)"
                strokeWidth={3}
                strokeDasharray="8 5"
                dot={{ r: 4 }}
                isAnimationActive={!reduceMotion}
              />
            </LineChart>
          </ResponsiveContainer>
        </div>
      )}

      <p className="note">
        Scores run from −1 (negative) to +1 (positive). Each point is the average score of one day&apos;s
        headlines. FinBERT is trained on financial text; VADER is a general word-list scorer and tends
        to read more positive.
      </p>

      <Articles ticker={ticker} />
    </main>
  );
}
