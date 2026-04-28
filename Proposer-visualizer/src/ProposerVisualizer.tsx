// src/ProposerVisualizer.tsx
// Grass timeline with fixed cell size + horizontal scrollbar + auto-follow latest.
// Virtualized drawing (only visible columns). Label modes & conditional markers (dash on cell).
// Export matched blocks to CSV & copy heights.
// Ignore nodes/transitions CSVs (no "Required columns not found").
// Controls area is arranged in TWO ROWS (grid) for better usability.
// + TopValidators scrollable up to 50
// + Block interval histograms (Δt): ALL & SAME-PROPOSER
// + Consecutive Stats card: adjacent same-proposer probability & streak metrics
// English only
// React 18 + PapaParse; Tailwind optional.

import React, { useCallback, useEffect, useMemo, useRef, useState } from "react";
import Papa from "papaparse";

/* ===========================
 * Types
 * =========================== */
type SeqRow = {
  height: number;
  time?: string; // ISO
  proposer_hex: string;
  proposer_moniker?: string;
};

type SummaryStats = {
  blocks: number | null;
  timeSpan: string | null;
  validators: number | null;
  proposals: number | null;
  edges: number | null;
};

type LabelMode = "totalT" | "inCell" | "none";
type BorderMode = "none" | "transition" | "validator" | "count" | "delay";

/* ===========================
 * Strings (English only)
 * =========================== */
const STRINGS = {
  title: "Proposer Timeline",
  subtitle:
    "GitHub-like grass. Fixed cell size with horizontal scroll. Cells show counts; matches marked by ー; streak≥2 marked by ×.",
  loadFromOut: "Load from out/",
  clear: "Clear",

  viewRange: "View range",
  minHeight: "Min height",
  maxHeight: "Max height",
  reset: "Reset",
  blocks: "Blocks",

  timeT: "Time t (blocks)",
  play: "Play",
  pause: "Pause",
  speed: "Speed",
  unitBlkSec: "blk/s",
  stepBack: "Step -1",
  stepFwd: "Step +1",

  proposals: "proposals",
  parseFailed: "Invalid CSV / parse failed",
  missingCols: "Required columns not found",
  fetchFailed: "Fetch failed",

  summary: "Summary",
  timeSpan: "Time Span (UTC)",
  validators: "Validators",
  totalProposes: "Total Proposes",
  edges: "Edges",

  topValidators: "Top Validators",
  byProposeCount: "By propose_count",

  cells: "Cells",
  stride: "Stride",

  labelMode: "Label",
  labelTotalT: "Total to t",
  labelInCell: "In cell",
  labelNone: "None",

  border: "Border",
  borderNone: "None",
  borderTransition: "Transitions",
  borderValidator: "Validator",
  borderCount: "Count ≥ N",
  borderDelay: "Delay ≥ S",
  validatorQuery: "HEX/moniker",
  countThreshold: "N",
  delayThreshold: "Threshold (sec)",
  borderColor: "Color",

  inCell: "in cell",
  totalUpToT: "total up to t",
  deltaFromPrev: "Δt from prev",

  followLatest: "Follow latest",

  exportBtn: "Export matched (CSV)",
  copyHeights: "Copy heights",
  matched: "Matched",
  noneToExport: "No matched blocks to export under current border rule.",
  noteCountMode:
    "Note: with current grid (1 block per cell), Count≥N matches only when N ≤ 1.",

  histTitleAll: "Block interval histogram (Δt in seconds) — ALL",
  histTitleSame: "Block interval histogram (Δt in seconds) — SAME PROPOSER",
  bins: "Bins",
  maxSec: "Max (sec, blank=auto)",
  overflow: "overflow",

  fixedStreakNote: "Streak≥2 highlight (×): ON (fixed)",

  consecTitle: "Consecutive Stats",
  pairProb: "Consecutive proposer probability (adjacent pairs)",
  samePairs: "Same pairs",
  pairsTotal: "Pairs total",
  runs: "Streak segments",
  runsGE2: "Segments ≥ 2",
  blocksInGE2: "Blocks in ≥ 2",
  fracBlocksInGE2: "Share of blocks in ≥ 2",
  avgRunLen: "Avg run length",
  medRunLen: "Median run length",

  algoTitle: "Selection Algorithm (Priority Queue)",
  algoDesc:
    "Simulate CometBFT's weighted round-robin using a priority queue. Edit s_i, step rounds, and watch priorities and selection counts. We display (p_i + s_i) centered to mean 0; the row with ✓ will be selected on Next Round.",
  idx: "i",
  votingPowerSi: "Voting Power s_i",
  priorityPi: "Priority p_i",
  proposerCol: "Proposer",
  frequencyCol: "Frequency",
  roundT: "Round",
  totalVotingPowerS: "Total Voting Power",
  nextRoundBtn: "Next Round",
};

type I18nStrings = typeof STRINGS;

/* ===========================
 * Constants (fixed grid)
 * =========================== */
const ROWS = 7;
const CELL = 56;
const GAP = 4;
const PAD_L = 8,
  PAD_R = 8,
  PAD_T = 8,
  PAD_B = 8;
const STRIDE = 1;

const STREAK_FIXED_LEN = 2;
const STREAK_X_COLOR = "#EF4444";

/* ===========================
 * Utils
 * =========================== */
function sanitizeHeaderName(h: string): string {
  if (!h) return "";
  return h.replace(/^\uFEFF/, "").trim().replace(/^"+|"+$/g, "");
}
function parseCountAny(x: any): number | null {
  if (x == null) return null;
  const s = String(x).trim().replace(/,/g, "").replace(/_/g, "");
  if (!s) return null;
  const n = Number(s);
  return Number.isFinite(n) ? n : null;
}
function normalizeHex(s?: string): string {
  if (!s) return "";
  return s.replace(/^\uFEFF/, "").trim().replace(/^0x/i, "").toUpperCase();
}
function shortHex(hex: string, left = 6, right = 4): string {
  const t = normalizeHex(hex);
  if (t.length <= left + right) return t;
  return `${t.slice(0, left)}…${t.slice(-right)}`;
}
function parseIso(s?: string): Date | null {
  if (!s) return null;
  const d = new Date(s);
  return Number.isNaN(+d) ? null : d;
}
function clamp(n: number, a: number, b: number) {
  return Math.max(a, Math.min(b, n));
}
function fmtUtc(d: Date): string {
  const p = (n: number) => String(n).padStart(2, "0");
  return `${d.getUTCFullYear()}-${p(d.getUTCMonth() + 1)}-${p(d.getUTCDate())} ${p(
    d.getUTCHours()
  )}:${p(d.getUTCMinutes())}Z`;
}
function fmtSec(s: number) {
  if (!Number.isFinite(s)) return "—";
  if (s < 1) return `${s.toFixed(3)}s`;
  if (s < 10) return `${s.toFixed(2)}s`;
  if (s < 100) return `${s.toFixed(1)}s`;
  return `${Math.round(s)}s`;
}
function fmtPct(x: number) {
  if (!Number.isFinite(x)) return "—";
  return `${(x * 100).toFixed(2)}%`;
}
function rollingHash32(s: string): number {
  let h = 2166136261 >>> 0;
  for (let i = 0; i < s.length; i++) {
    h ^= s.charCodeAt(i);
    h = Math.imul(h, 16777619);
  }
  return h >>> 0;
}
function hashColor(hex: string): string {
  const h = rollingHash32(normalizeHex(hex));
  const hue = h % 360;
  const sat = 60 + (h % 20);
  const light = 45 + (Math.floor(h / 7) % 15);
  return `hsl(${hue}, ${sat}%, ${light}%)`;
}

/* ===========================
 * CSV mapping / parsing
 * =========================== */
function findHeader(headers: string[], candidates: string[]): string | null {
  const hs = headers.map((h) => sanitizeHeaderName(h).toLowerCase());
  for (const c of candidates) {
    const idx = hs.indexOf(c.toLowerCase());
    if (idx >= 0) return headers[idx];
  }
  for (const c of candidates) {
    const found = headers.find((h) =>
      sanitizeHeaderName(h).toLowerCase().includes(c.toLowerCase())
    );
    if (found) return found;
  }
  return null;
}
function detectSequenceMapping(headers: string[]) {
  const H = (name: string | null) => (name ? name : "__missing__");
  const hHeight = findHeader(headers, ["height", "block_height"]);
  const hTime = findHeader(headers, ["time", "timestamp", "block_time"]);
  const hHex = findHeader(headers, ["proposer_hex", "proposer", "proposer_address"]);
  const hMon = findHeader(headers, ["proposer_moniker", "moniker", "validator", "name"]);
  const ok = !!hHeight && !!hHex;
  return {
    ok,
    map: (row: any): SeqRow | null => {
      if (!ok) return null;
      const height = parseCountAny(row[H(hHeight)]);
      const rawHex = row[H(hHex)];
      if (height == null || rawHex == null) return null;
      const proposer_hex = normalizeHex(String(rawHex));
      return {
        height,
        time: hTime ? String(row[H(hTime)] ?? "") : undefined,
        proposer_hex,
        proposer_moniker: hMon ? String(row[H(hMon)] ?? "") : undefined,
      };
    },
  };
}
const isNodesOrTransitions = (name: string) => /(nodes|transitions)/i.test(name);
const isSequenceName = (name: string) => /sequence/i.test(name);

async function parseCsvText(
  name: string,
  text: string,
  s: I18nStrings = STRINGS
): Promise<{ sequence: SeqRow[]; errors: string[] }> {
  return new Promise((resolve) => {
    Papa.parse(text, {
      header: true,
      skipEmptyLines: true,
      dynamicTyping: false,
      transformHeader: sanitizeHeaderName,
      complete: (res) => {
        try {
          const raw = res.data as any[];
          const headers = (res.meta.fields ?? Object.keys(raw[0] ?? [])).map(sanitizeHeaderName);
          const seqMap = detectSequenceMapping(headers);
          if (!seqMap.ok) {
            if (isNodesOrTransitions(name)) return resolve({ sequence: [], errors: [] });
            if (isSequenceName(name))
              return resolve({ sequence: [], errors: [`${s.missingCols} (${name})`] });
            return resolve({ sequence: [], errors: [] });
          }
          const rows: SeqRow[] = [];
          for (const r of raw) {
            const m = seqMap.map(r);
            if (m) rows.push(m);
          }
          rows.sort((a, b) => a.height - b.height);
          resolve({ sequence: rows, errors: [] });
        } catch {
          resolve({ sequence: [], errors: [`${s.parseFailed} (${name})`] });
        }
      },
      error: (err) =>
        resolve({ sequence: [], errors: [`${s.parseFailed} (${name}): ${err.message}`] }),
    });
  });
}

/* ===========================
 * Component
 * =========================== */
export default function ProposerVisualizer() {
  const S = STRINGS;

  const [sequence, setSequence] = useState<SeqRow[]>([]);
  const [errors, setErrors] = useState<string[]>([]);
  const [viewMin, setViewMin] = useState<number | null>(null);
  const [viewMax, setViewMax] = useState<number | null>(null);

  const [tBlocks, setTBlocks] = useState<number>(0);
  const [isPlaying, setIsPlaying] = useState<boolean>(false);
  const [speed, setSpeed] = useState<number>(100);
  const [labelMode, setLabelMode] = useState<LabelMode>("totalT");

  const [borderMode, setBorderMode] = useState<BorderMode>("none");
  const [borderQuery, setBorderQuery] = useState<string>("");
  const [countThreshold, setCountThreshold] = useState<number>(2);
  const [delayThresholdSec, setDelayThresholdSec] = useState<number>(2);
  const [borderColor, setBorderColor] = useState<string>("#111111");

  const [histBins, setHistBins] = useState<number>(100);
  const [histMaxSec, setHistMaxSec] = useState<number | null>(10);

  const [followLatest, setFollowLatest] = useState<boolean>(true);
  const autoScrollFlag = useRef<boolean>(false);

  const [initialTried, setInitialTried] = useState(false);

  const loadInitialFromOut = useCallback(async () => {
    try {
      const res = await fetch("/out/index.json", { cache: "no-store" });
      if (!res.ok) return false;
      const mani = (await res.json()) as { files?: string[] };
      const files = (mani.files ?? []).filter((f) => /\.csv$/i.test(f) && isSequenceName(f));
      if (files.length === 0) return false;

      const results = await Promise.all(
        files.map(async (fname) => {
          const r = await fetch(`/out/${fname}`, { cache: "no-store" });
          if (!r.ok) return { sequence: [], errors: [`${S.fetchFailed}: /out/${fname}`] };
          const text = await r.text();
          return parseCsvText(fname, text, S);
        })
      );

      const seqs = results.flatMap((r) => r.sequence);
      const errs = results.flatMap((r) => r.errors);
      if (seqs.length > 0) {
        seqs.sort((a, b) => a.height - b.height);
        setSequence(seqs);
        setErrors(errs);
        setViewMin(seqs[0].height);
        setViewMax(seqs[seqs.length - 1].height);
        setTBlocks(0); // start from 0
      } else {
        setErrors(errs.length ? errs : ["No sequence rows found in /out CSVs."]);
      }
      return true;
    } catch {
      return false;
    }
  }, [S]);

  useEffect(() => {
    if (initialTried) return;
    (async () => {
      await loadInitialFromOut();
      setInitialTried(true);
    })();
  }, [initialTried, loadInitialFromOut]);

  const clearAll = () => {
    setSequence([]);
    setErrors([]);
    setViewMin(null);
    setViewMax(null);
    setTBlocks(0);
    setIsPlaying(false);
    setBorderMode("none");
  };

  const globalMinH = useMemo(() => (sequence.length ? sequence[0].height : null), [sequence]);
  const globalMaxH = useMemo(
    () => (sequence.length ? sequence[sequence.length - 1].height : null),
    [sequence]
  );
  const effMin = viewMin ?? globalMinH ?? 0;
  const effMax = viewMax ?? globalMaxH ?? 0;

  const filtered = useMemo(
    () => sequence.filter((r) => r.height >= effMin && r.height <= effMax),
    [sequence, effMin, effMax]
  );

  const filteredT = useMemo(() => {
    const T = clamp(Math.floor(tBlocks), 0, filtered.length);
    return filtered.slice(0, T);
  }, [filtered, tBlocks]);

  useEffect(() => {
    setTBlocks((prev) => clamp(Math.floor(prev), 0, filtered.length));
  }, [filtered.length]);

  const monikerMap = useMemo(() => {
    const m = new Map<string, string>();
    for (const r of sequence) {
      if (r.proposer_moniker) m.set(normalizeHex(r.proposer_hex), r.proposer_moniker);
    }
    return m;
  }, [sequence]);

  const countByHexT = useMemo(() => {
    const m = new Map<string, number>();
    for (const r of filteredT) {
      const k = normalizeHex(r.proposer_hex);
      m.set(k, (m.get(k) ?? 0) + 1);
    }
    return m;
  }, [filteredT]);

  const deltaSecByHeight = useMemo(() => {
    const map = new Map<number, number | null>();
    let prevTime: Date | null = null;
    for (let i = 0; i < sequence.length; i++) {
      const curTime = parseIso(sequence[i].time);
      if (curTime && prevTime) {
        map.set(sequence[i].height, (curTime.getTime() - prevTime.getTime()) / 1000);
      } else {
        map.set(sequence[i].height, null);
      }
      prevTime = curTime;
    }
    return map;
  }, [sequence]);

  const deltasAllT = useMemo(() => {
    const arr: number[] = [];
    for (let i = 1; i < filteredT.length; i++) {
      const d = deltaSecByHeight.get(filteredT[i].height);
      if (d != null && Number.isFinite(d) && d >= 0) arr.push(d);
    }
    return arr;
  }, [filteredT, deltaSecByHeight]);

  const deltasSameT = useMemo(() => {
    const arr: number[] = [];
    for (let i = 1; i < filteredT.length; i++) {
      const prev = filteredT[i - 1];
      const cur = filteredT[i];
      if (normalizeHex(prev.proposer_hex) === normalizeHex(cur.proposer_hex)) {
        const d = deltaSecByHeight.get(cur.height);
        if (d != null && Number.isFinite(d) && d >= 0) arr.push(d);
      }
    }
    return arr;
  }, [filteredT, deltaSecByHeight]);

  const streakLenAtIndex = useMemo(() => {
    const n = filteredT.length;
    const out = new Array<number>(n).fill(1);
    let i = 0;
    while (i < n) {
      const hex = normalizeHex(filteredT[i].proposer_hex);
      let j = i + 1;
      while (j < n && normalizeHex(filteredT[j].proposer_hex) === hex) j++;
      const len = j - i;
      for (let k = i; k < j; k++) out[k] = len;
      i = j;
    }
    return out;
  }, [filteredT]);

  const consecutive = useMemo(() => {
    const N = filteredT.length;
    if (N <= 1) {
      return {
        pairs: 0,
        samePairs: 0,
        pSame: 0,
        runs: N ? 1 : 0,
        runsGE2: 0,
        blocksInRunsGE2: 0,
        fracBlocksInGE2: 0,
        avgRunLen: N,
        medianRunLen: N,
      };
    }
    const runLens: number[] = [];
    let i = 0;
    while (i < N) {
      const hex = normalizeHex(filteredT[i].proposer_hex);
      let j = i + 1;
      while (j < N && normalizeHex(filteredT[j].proposer_hex) === hex) j++;
      runLens.push(j - i);
      i = j;
    }
    const runs = runLens.length;
    const pairs = N - 1;
    const samePairs = N - runs;
    const pSame = pairs > 0 ? samePairs / pairs : 0;
    const lensGE2 = runLens.filter((x) => x >= 2);
    const blocksInRunsGE2 = lensGE2.reduce((s, v) => s + v, 0);
    const fracBlocksInGE2 = N > 0 ? blocksInRunsGE2 / N : 0;
    const avgRunLen = runs > 0 ? N / runs : N;
    const medRunLen = (() => {
      const a = [...runLens].sort((x, y) => x - y);
      const m = Math.floor(a.length / 2);
      return a.length % 2 ? a[m] : (a[m - 1] + a[m]) / 2;
    })();
    return {
      pairs,
      samePairs,
      pSame,
      runs,
      runsGE2: lensGE2.length,
      blocksInRunsGE2,
      fracBlocksInGE2,
      avgRunLen,
      medianRunLen: medRunLen,
    };
  }, [filteredT]);

  const summary: SummaryStats = useMemo(() => {
    if (!filteredT.length) {
      return { blocks: 0, timeSpan: null, validators: 0, proposals: 0, edges: 0 };
    }
    const minH = filteredT[0].height;
    const maxH = filteredT[filteredT.length - 1].height;
    const blocks = maxH - minH + 1;

    const times = filteredT.map((r) => parseIso(r.time)).filter((d): d is Date => !!d);
    const minD = times.length ? times.reduce((a, b) => (a < b ? a : b)) : null;
    const maxD = times.length ? times.reduce((a, b) => (a > b ? a : b)) : null;
    const timeSpan = minD && maxD ? `${fmtUtc(minD)} – ${fmtUtc(maxD)}` : null;

    const validators = new Set(filteredT.map((r) => normalizeHex(r.proposer_hex))).size;
    const proposals = filteredT.length;
    const edgesSet = new Set<string>();
    for (let i = 1; i < filteredT.length; i++) {
      const a = normalizeHex(filteredT[i - 1].proposer_hex);
      const b = normalizeHex(filteredT[i].proposer_hex);
      if (a && b && a !== b) edgesSet.add(`${a}->${b}`);
    }
    return { blocks, timeSpan, validators, proposals, edges: edgesSet.size };
  }, [filteredT]);

  const topList = useMemo(() => {
    const arr = Array.from(countByHexT.entries()).map(([hex, count]) => ({
      hex,
      count,
      label: monikerMap.get(hex) ?? shortHex(hex),
    }));
    arr.sort((a, b) => b.count - a.count);
    return arr.slice(0, 50);
  }, [countByHexT, monikerMap]);

  const wrapperRef = useRef<HTMLDivElement>(null);
  const scrollRef = useRef<HTMLDivElement>(null);
  const spacerRef = useRef<HTMLDivElement>(null);
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const tooltipRef = useRef<HTMLDivElement>(null);

  const [viewportW, setViewportW] = useState<number>(960);
  const [areaH, setAreaH] = useState<number>(80);
  const [drawInfo, setDrawInfo] = useState<{
    columns: number;
    rows: number;
    stride: number;
    cells: number;
  } | null>(null);

  useEffect(() => {
    if (!wrapperRef.current) return;
    const obs = new ResizeObserver((ents) => {
      for (const e of ents) setViewportW(Math.max(360, e.contentRect.width));
    });
    obs.observe(wrapperRef.current);
    return () => obs.disconnect();
  }, []);

  const drawGrass = useCallback(() => {
    const canvas = canvasRef.current;
    const sc = scrollRef.current;
    if (!canvas || !sc) return;

    const N = filteredT.length;
    const numCells = Math.ceil(N / STRIDE);
    const columns = Math.max(1, Math.ceil(numCells / ROWS));
    const totalW = PAD_L + PAD_R + columns * CELL + (columns - 1) * GAP;
    const totalH = PAD_T + PAD_B + ROWS * CELL + (ROWS - 1) * GAP;

    const sb = Math.max(0, sc.offsetHeight - sc.clientHeight);

    if (spacerRef.current) {
      spacerRef.current.style.width = `${totalW}px`;
      spacerRef.current.style.height = `${totalH}px`;
    }
    setAreaH(totalH + sb);

    const dpr = Math.min(2, (window as any).devicePixelRatio || 1);
    const vw = sc.clientWidth || viewportW;
    const ch = totalH;
    canvas.width = Math.floor(vw * dpr);
    canvas.height = Math.floor(ch * dpr);
    canvas.style.width = `${vw}px`;
    canvas.style.height = `${ch}px`;
    const ctx = canvas.getContext("2d")!;
    (ctx as any).resetTransform?.();
    ctx.scale(dpr, dpr);

    ctx.clearRect(0, 0, vw, ch);
    ctx.fillStyle = "#fff";
    ctx.fillRect(0, 0, vw, ch);

    const scrollLeft = sc.scrollLeft;

    const cellSpan = CELL + GAP;
    const firstCol = Math.max(0, Math.floor((scrollLeft - PAD_L) / cellSpan));
    const colsInView = Math.ceil((vw + 2) / cellSpan) + 2;
    const lastCol = Math.min(columns - 1, firstCol + colsInView);

    const q = borderQuery.trim();
    const qLower = q.toLowerCase();
    const qUpper = q.toUpperCase();

    for (let col = firstCol; col <= lastCol; col++) {
      for (let row = 0; row < ROWS; row++) {
        const c = col * ROWS + row;
        if (c >= numCells) break;

        const xGlobal = PAD_L + col * cellSpan;
        const x = xGlobal - scrollLeft;
        const y = PAD_T + row * cellSpan;

        const startIdx = c * STRIDE;
        const endIdx = Math.min(N - 1, (c + 1) * STRIDE - 1);
        const last = filteredT[endIdx];
        const lastHexNorm = normalizeHex(last.proposer_hex);

        const fill = hashColor(last.proposer_hex);
        ctx.fillStyle = fill;
        ctx.fillRect(x, y, CELL, CELL);

        const streakLen = streakLenAtIndex[endIdx];
        if (streakLen >= STREAK_FIXED_LEN) {
          ctx.save();
          ctx.strokeStyle = STREAK_X_COLOR;
          ctx.globalAlpha = 0.9;
          ctx.lineCap = "round";
          ctx.lineWidth = Math.max(2, Math.floor(CELL / 6));
          const p = Math.max(2, Math.floor(CELL * 0.12));
          ctx.beginPath();
          ctx.moveTo(x + p, y + p);
          ctx.lineTo(x + CELL - p, y + CELL - p);
          ctx.moveTo(x + CELL - p, y + p);
          ctx.lineTo(x + p, y + CELL - p);
          ctx.stroke();
          ctx.restore();
        }

        let shouldMark = false;
        if (borderMode === "transition") {
          let prev = startIdx > 0 ? normalizeHex(filteredT[startIdx - 1].proposer_hex) : null;
          let cur = normalizeHex(filteredT[startIdx].proposer_hex);
          if (prev === null || prev !== cur) {
            shouldMark = true;
          } else {
            for (let i = startIdx + 1; i <= endIdx; i++) {
              const h = normalizeHex(filteredT[i].proposer_hex);
              if (h !== prev) {
                shouldMark = true;
                break;
              }
            }
          }
        } else if (borderMode === "validator") {
          if (q) {
            const moniker = (last.proposer_moniker ?? "").toLowerCase();
            shouldMark = lastHexNorm.includes(qUpper) || moniker.includes(qLower);
          }
        } else if (borderMode === "count") {
          let cntInCell = 0;
          for (let i = startIdx; i <= endIdx; i++) {
            if (normalizeHex(filteredT[i].proposer_hex) === lastHexNorm) cntInCell++;
          }
          shouldMark = cntInCell >= countThreshold;
        } else if (borderMode === "delay") {
          for (let i = startIdx; i <= endIdx; i++) {
            const d = deltaSecByHeight.get(filteredT[i].height);
            if (d != null && Number.isFinite(d) && d >= delayThresholdSec) {
              shouldMark = true;
              break;
            }
          }
        }

        let labelText: string | null = null;
        if (labelMode === "inCell") {
          labelText = "1";
        } else if (labelMode === "totalT") {
          labelText = String(countByHexT.get(lastHexNorm) ?? 0);
        }
        if (labelText && CELL >= 9) {
          const minPx = 7;
          let fontPx = Math.max(minPx, Math.floor(CELL * 0.7));
          ctx.textAlign = "center";
          ctx.textBaseline = "middle";
          while (fontPx >= minPx) {
            ctx.font = `700 ${fontPx}px ui-sans-serif, system-ui, -apple-system, Segoe UI, Roboto, Helvetica Neue, Arial`;
            const w = ctx.measureText(labelText).width;
            if (w <= CELL - 2) break;
            fontPx -= 1;
          }
          ctx.lineWidth = Math.max(1, Math.floor(fontPx / 5));
          ctx.strokeStyle = "rgba(0,0,0,0.38)";
          ctx.fillStyle = "rgba(255,255,255,0.95)";
          const cx = x + CELL / 2;
          const cy = y + CELL / 2;
          ctx.strokeText(labelText, cx, cy);
          ctx.fillText(labelText, cx, cy);
        }

        if (shouldMark) {
          ctx.save();
          ctx.strokeStyle = borderColor;
          ctx.globalAlpha = 0.9;
          ctx.lineCap = "round";
          ctx.lineWidth = Math.max(2, Math.floor(CELL / 6));
          const p = Math.max(2, Math.floor(CELL * 0.12));
          const yBar = y + CELL / 2;
          ctx.beginPath();
          ctx.moveTo(x + p, yBar);
          ctx.lineTo(x + CELL - p, yBar);
          ctx.stroke();
          ctx.restore();
        }
      }
    }

    setDrawInfo({ columns, rows: ROWS, stride: STRIDE, cells: numCells });

    if (followLatest) {
      const rightWanted = Math.max(0, totalW - vw);
      if (Math.abs(sc.scrollLeft - rightWanted) > 1) {
        autoScrollFlag.current = true;
        sc.scrollLeft = rightWanted;
      }
    }
  }, [
    filteredT,
    countByHexT,
    deltaSecByHeight,
    labelMode,
    borderMode,
    borderQuery,
    countThreshold,
    delayThresholdSec,
    borderColor,
    viewportW,
    followLatest,
    streakLenAtIndex,
  ]);

  useEffect(() => {
    drawGrass();
  }, [drawGrass]);

  useEffect(() => {
    const el = scrollRef.current;
    if (!el) return;
    const onScroll = () => {
      drawGrass();
      if (autoScrollFlag.current) {
        autoScrollFlag.current = false;
      } else if (followLatest) {
        setFollowLatest(false);
      }
    };
    el.addEventListener("scroll", onScroll, { passive: true });
    return () => el.removeEventListener("scroll", onScroll);
  }, [drawGrass, followLatest]);

  const lastTsRef = useRef<number | null>(null);
  useEffect(() => {
    if (!isPlaying) {
      lastTsRef.current = null;
      return;
    }
    let raf = 0;
    const tick = (ts: number) => {
      if (lastTsRef.current == null) lastTsRef.current = ts;
      const dt = (ts - lastTsRef.current) / 1000;
      lastTsRef.current = ts;
      setTBlocks((prev) => {
        const nxt = prev + dt * speed;
        if (nxt >= filtered.length) {
          setIsPlaying(false);
          return filtered.length;
        }
        return nxt;
      });
      raf = requestAnimationFrame(tick);
    };
    raf = requestAnimationFrame(tick);
    return () => cancelAnimationFrame(raf);
  }, [isPlaying, speed, filtered.length]);

  const onMouseMove = useCallback(
    (ev: React.MouseEvent) => {
      const sc = scrollRef.current;
      const tip = tooltipRef.current;
      if (!sc || !tip) return;

      const rect = sc.getBoundingClientRect();
      const xView = ev.clientX - rect.left;
      const yView = ev.clientY - rect.top;
      const xContent = xView + sc.scrollLeft;

      const col = Math.floor((xContent - PAD_L) / (CELL + GAP));
      const row = Math.floor((yView - PAD_T) / (CELL + GAP));
      if (col < 0 || row < 0 || row >= ROWS) {
        tip.style.display = "none";
        return;
      }
      const N = filteredT.length;
      const idxCell = col * ROWS + row;
      const startIdx = idxCell * STRIDE;
      if (idxCell < 0 || startIdx >= N) {
        tip.style.display = "none";
        return;
      }
      const endIdx = Math.min(N - 1, (idxCell + 1) * STRIDE - 1);
      const startRow = filteredT[startIdx];
      const endRow = filteredT[endIdx];
      const lastHexNorm = normalizeHex(endRow.proposer_hex);
      const moniker =
        endRow.proposer_moniker ?? monikerMap.get(lastHexNorm) ?? shortHex(endRow.proposer_hex);
      const totalCnt = countByHexT.get(lastHexNorm) ?? 0;
      const lastDelta = deltaSecByHeight.get(endRow.height);
      const streakLen = streakLenAtIndex[endIdx];

      const wrapRect = wrapperRef.current?.getBoundingClientRect();
      const wx = wrapRect ? ev.clientX - wrapRect.left : xView;
      const wy = wrapRect ? ev.clientY - wrapRect.top : yView;

      tip.style.display = "block";
      tip.style.left = `${wx + 12}px`;
      tip.style.top = `${wy + 12}px`;
      tip.innerHTML = `<div class="text-xs">
        <div><b>H ${startRow.height}${
        startRow.height === endRow.height ? "" : `–${endRow.height}`
      }</b>${endRow.time ? ` · ${fmtUtc(new Date(endRow.time))}` : ""}</div>
        <div>proposer: <b>${moniker}</b> <code>${shortHex(endRow.proposer_hex)}</code></div>
        <div>${S.totalUpToT}: <b>${totalCnt.toLocaleString("en-US")}</b>${
        lastDelta != null ? ` ・ ${S.deltaFromPrev}: <b>${fmtSec(lastDelta)}</b>` : ""
      }${streakLen >= STREAK_FIXED_LEN ? ` ・ streak: <b>${streakLen}</b> ×` : ""}</div>
      </div>`;
    },
    [filteredT, monikerMap, countByHexT, deltaSecByHeight, streakLenAtIndex, S]
  );

  const onMouseLeave = () => {
    if (tooltipRef.current) tooltipRef.current.style.display = "none";
  };

  const onResetRange = () => {
    if (!sequence.length) return;
    setViewMin(sequence[0].height);
    setViewMax(sequence[sequence.length - 1].height);
    setTBlocks(0);
  };
  const tInt = Math.floor(clamp(tBlocks, 0, filtered.length));

  type MatchRow = {
    height: number;
    time?: string;
    proposer_hex: string;
    proposer_moniker?: string;
    delta_sec?: number | null;
    reason: string;
    prev_hex?: string | null;
    prev_moniker?: string | null;
  };

  const matchedRows = useMemo<MatchRow[]>(() => {
    const out: MatchRow[] = [];
    if (borderMode === "none") return out;

    const q = borderQuery.trim();
    const qLower = q.toLowerCase();
    const qUpper = q.toUpperCase();

    for (let i = 0; i < filteredT.length; i++) {
      const r = filteredT[i];
      const curHex = normalizeHex(r.proposer_hex);
      const curMon = r.proposer_moniker ?? monikerMap.get(curHex) ?? undefined;
      const dsec = deltaSecByHeight.get(r.height) ?? null;

      let match = false;
      let reason = "";
      let prev_hex: string | null = null;
      let prev_moniker: string | null = null;

      if (borderMode === "transition") {
        const prev = i > 0 ? filteredT[i - 1] : null;
        if (!prev) {
          match = true;
          reason = "first block in range";
        } else {
          const pHex = normalizeHex(prev.proposer_hex);
          if (pHex !== curHex) {
            match = true;
            reason = `transition ${shortHex(pHex)}→${shortHex(curHex)}`;
            prev_hex = pHex;
            prev_moniker = prev.proposer_moniker ?? monikerMap.get(pHex) ?? null;
          }
        }
      } else if (borderMode === "validator") {
        if (q) {
          const mon = (curMon ?? "").toLowerCase();
          if (curHex.includes(qUpper) || mon.includes(qLower)) {
            match = true;
            reason = `validator match "${q}"`;
          }
        }
      } else if (borderMode === "count") {
        const cntInCell = 1;
        if (cntInCell >= countThreshold) {
          match = true;
          reason = `count>=${countThreshold} (cell=${cntInCell})`;
        }
      } else if (borderMode === "delay") {
        if (dsec != null && Number.isFinite(dsec) && dsec >= delayThresholdSec) {
          match = true;
          reason = `delay>=${delayThresholdSec}s (Δt=${fmtSec(dsec)})`;
        }
      }

      if (match) {
        out.push({
          height: r.height,
          time: r.time,
          proposer_hex: curHex,
          proposer_moniker: curMon,
          delta_sec: dsec,
          reason,
          prev_hex,
          prev_moniker,
        });
      }
    }
    return out;
  }, [
    filteredT,
    borderMode,
    borderQuery,
    countThreshold,
    delayThresholdSec,
    monikerMap,
    deltaSecByHeight,
  ]);

  const matchedHeights = useMemo(() => matchedRows.map((m) => m.height), [matchedRows]);

  const downloadCsv = () => {
    if (matchedRows.length === 0) {
      window.alert(S.noneToExport + (borderMode === "count" ? `\n\n${S.noteCountMode}` : ""));
      return;
    }
    const header = [
      "height",
      "time",
      "proposer_hex",
      "proposer_moniker",
      "delta_sec",
      "reason",
      "prev_hex",
      "prev_moniker",
    ];
    const esc = (v: any) => {
      if (v == null) return "";
      const s = String(v);
      return /[",\n]/.test(s) ? `"${s.replace(/"/g, '""')}"` : s;
    };
    const lines = [header.join(",")];
    for (const r of matchedRows) {
      lines.push(
        [
          esc(r.height),
          esc(r.time ?? ""),
          esc(r.proposer_hex),
          esc(r.proposer_moniker ?? ""),
          esc(r.delta_sec ?? ""),
          esc(r.reason),
          esc(r.prev_hex ?? ""),
          esc(r.prev_moniker ?? ""),
        ].join(",")
      );
    }
    const csv = lines.join("\n");
    const blob = new Blob([csv], { type: "text/csv;charset=utf-8;" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `matched_blocks_${borderMode}_${Date.now()}.csv`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    setTimeout(() => URL.revokeObjectURL(url), 0);
  };

  const copyHeights = async () => {
    if (matchedHeights.length === 0) {
      window.alert(S.noneToExport + (borderMode === "count" ? `\n\n${S.noteCountMode}` : ""));
      return;
    }
    const text = matchedHeights.join("\n");
    try {
      await navigator.clipboard.writeText(text);
    } catch {
      const ta = document.createElement("textarea");
      ta.value = text;
      document.body.appendChild(ta);
      ta.select();
      document.execCommand("copy");
      document.body.removeChild(ta);
    }
  };

  return (
    <div className="p-4 max-w-[1400px] mx-auto">
      <header className="mb-4 flex flex-col gap-2 md:flex-row md:items-end md:justify-between">
        <div>
          <h1 className="text-2xl font-bold">{S.title}</h1>
          <p className="text-sm text-gray-500">{S.subtitle}</p>
        </div>
        <div className="flex gap-2 items-center">
          <button
            className="px-3 py-2 rounded-lg bg-gray-100 hover:bg-gray-200 text-sm"
            onClick={() => loadInitialFromOut()}
            type="button"
          >
            {S.loadFromOut}
          </button>
          <button
            className="px-3 py-2 rounded-lg bg-gray-100 hover:bg-gray-200 text-sm"
            onClick={clearAll}
            type="button"
          >
            {S.clear}
          </button>
        </div>
      </header>

      {errors.length > 0 && (
        <div className="mb-4 space-y-1">
          {errors.map((m, i) => (
            <div key={i} className="text-sm px-3 py-2 rounded-md bg-amber-50 text-amber-700">
              {m}
            </div>
          ))}
        </div>
      )}

      <div className="rounded-2xl border border-gray-200 p-4 shadow-sm bg-white mb-4 space-y-3">
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-3 items-end">
          <div className="lg:col-span-5">
            <div className="text-gray-700 font-semibold mb-2">{S.viewRange}</div>
            <div className="flex flex-wrap items-end gap-3">
              <label className="text-sm flex items-center gap-2">
                <span className="text-gray-600">{S.minHeight}</span>
                <input
                  type="number"
                  value={viewMin ?? ""}
                  placeholder={String(globalMinH ?? "")}
                  onChange={(e) =>
                    setViewMin(e.currentTarget.value === "" ? null : Number(e.currentTarget.value))
                  }
                  className="w-28 rounded border px-2 py-1 text-sm"
                />
              </label>
              <span className="text-gray-500">–</span>
              <label className="text-sm flex items-center gap-2">
                <span className="text-gray-600">{S.maxHeight}</span>
                <input
                  type="number"
                  value={viewMax ?? ""}
                  placeholder={String(globalMaxH ?? "")}
                  onChange={(e) =>
                    setViewMax(e.currentTarget.value === "" ? null : Number(e.currentTarget.value))
                  }
                  className="w-28 rounded border px-2 py-1 text-sm"
                />
              </label>
              <button
                className="px-3 py-1.5 rounded-lg bg-gray-100 hover:bg-gray-200 text-sm"
                onClick={onResetRange}
                type="button"
              >
                {S.reset}
              </button>
            </div>
          </div>

          <div className="lg:col-span-7">
            <div className="text-gray-700 font-semibold mb-2">{S.timeT}</div>
            <div className="flex items-center gap-3">
              <input
                type="range"
                min={0}
                max={Math.max(0, filtered.length)}
                step={1}
                value={tInt}
                onChange={(e) => setTBlocks(Number(e.currentTarget.value))}
                className="flex-1"
              />
              <input
                type="number"
                min={0}
                max={Math.max(0, filtered.length)}
                step={1}
                value={tInt}
                onChange={(e) => setTBlocks(Number(e.currentTarget.value))}
                className="w-28 rounded border px-2 py-1 text-sm"
              />
              <span className="text-sm text-gray-500">
                {tInt.toLocaleString("en-US")} / {filtered.length.toLocaleString("en-US")}
              </span>
              <button
                type="button"
                className="px-2 py-1 rounded bg-gray-100 hover:bg-gray-200 text-sm"
                onClick={() => setTBlocks((v) => clamp(Math.floor(v - 1), 0, filtered.length))}
                title={S.stepBack}
              >
                −1
              </button>
              <button
                type="button"
                className="px-2 py-1 rounded bg-gray-100 hover:bg-gray-200 text-sm"
                onClick={() => setTBlocks((v) => clamp(Math.floor(v + 1), 0, filtered.length))}
                title={S.stepFwd}
              >
                +1
              </button>
              <button
                type="button"
                className="px-3 py-1 rounded bg-gray-900 text-white hover:opacity-90 text-sm"
                onClick={() => setIsPlaying((p) => !p)}
              >
                {isPlaying ? S.pause : S.play}
              </button>
              <label className="text-sm flex items-center gap-2">
                <span className="text-gray-600">{S.speed}</span>
                <select
                  value={speed}
                  onChange={(e) => setSpeed(Number(e.currentTarget.value))}
                  className="rounded border px-2 py-1 text-sm"
                >
                  <option value={1}>1 {S.unitBlkSec}</option>
                  <option value={2}>2 {S.unitBlkSec}</option>
                  <option value={5}>5 {S.unitBlkSec}</option>
                  <option value={7}>7 {S.unitBlkSec}</option>
                  <option value={10}>10 {S.unitBlkSec}</option>
                  <option value={15}>15 {S.unitBlkSec}</option>
                  <option value={20}>20 {S.unitBlkSec}</option>
                  <option value={30}>30 {S.unitBlkSec}</option>
                  <option value={50}>50 {S.unitBlkSec}</option>
                  <option value={100}>100 {S.unitBlkSec}</option>
                </select>
              </label>
            </div>
          </div>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-12 gap-3 items-center">
          <div className="lg:col-span-7">
            <div className="flex flex-wrap items-center gap-3">
              <label className="text-sm flex items-center gap-2">
                <span className="text-gray-600">{S.labelMode}</span>
                <select
                  value={labelMode}
                  onChange={(e) => setLabelMode(e.currentTarget.value as LabelMode)}
                  className="rounded border px-2 py-1 text-sm"
                >
                  <option value="totalT">{S.labelTotalT}</option>
                  <option value="inCell">{S.labelInCell}</option>
                  <option value="none">{S.labelNone}</option>
                </select>
              </label>

              <label className="text-sm flex items-center gap-2">
                <span className="text-gray-600">{S.border}</span>
                <select
                  value={borderMode}
                  onChange={(e) => setBorderMode(e.currentTarget.value as BorderMode)}
                  className="rounded border px-2 py-1 text-sm"
                >
                  <option value="none">{S.borderNone}</option>
                  <option value="transition">{S.borderTransition}</option>
                  <option value="validator">{S.borderValidator}</option>
                  <option value="count">{S.borderCount}</option>
                  <option value="delay">{S.borderDelay}</option>
                </select>
              </label>

              {borderMode === "validator" && (
                <label className="text-sm flex items-center gap-2">
                  <span className="text-gray-600">{S.validatorQuery}</span>
                  <input
                    type="text"
                    value={borderQuery}
                    onChange={(e) => setBorderQuery(e.currentTarget.value)}
                    placeholder="e.g. CB5A63 / moniker"
                    className="w-48 rounded border px-2 py-1 text-sm"
                  />
                </label>
              )}

              {borderMode === "count" && (
                <label className="text-sm flex items-center gap-2">
                  <span className="text-gray-600">{S.countThreshold}</span>
                  <input
                    type="number"
                    min={1}
                    value={countThreshold}
                    onChange={(e) =>
                      setCountThreshold(Math.max(1, Number(e.currentTarget.value || 1)))
                    }
                    className="w-20 rounded border px-2 py-1 text-sm"
                  />
                </label>
              )}

              {borderMode === "delay" && (
                <label className="text-sm flex items-center gap-2">
                  <span className="text-gray-600">{S.delayThreshold}</span>
                  <input
                    type="number"
                    min={0}
                    step={0.1}
                    value={delayThresholdSec}
                    onChange={(e) =>
                      setDelayThresholdSec(Math.max(0, Number(e.currentTarget.value || 0)))
                    }
                    className="w-24 rounded border px-2 py-1 text-sm"
                  />
                </label>
              )}

              <label className="text-sm flex items-center gap-2">
                <span className="text-gray-600">{S.borderColor}</span>
                <input
                  type="color"
                  value={borderColor}
                  onChange={(e) => setBorderColor(e.currentTarget.value)}
                  className="w-10 h-8 p-0 border rounded"
                />
              </label>

              <label className="text-sm flex items-center gap-2">
                <input
                  type="checkbox"
                  checked={followLatest}
                  onChange={(e) => setFollowLatest(e.currentTarget.checked)}
                  className="rounded border"
                />
                <span className="text-gray-600">{S.followLatest}</span>
              </label>

              <span className="text-xs px-2 py-1 rounded bg-emerald-50 text-emerald-700 border border-emerald-200">
                {S.fixedStreakNote}
              </span>
            </div>
          </div>

          <div className="lg:col-span-3">
            <div className="flex items-center gap-2">
              <button
                type="button"
                className="px-3 py-1.5 rounded bg-indigo-600 text-white hover:opacity-90 text-sm"
                onClick={downloadCsv}
              >
                {S.exportBtn}
              </button>
              <button
                type="button"
                className="px-3 py-1.5 rounded bg-gray-100 hover:bg-gray-200 text-sm"
                onClick={copyHeights}
              >
                {S.copyHeights}
              </button>
              <span className="text-sm text-gray-500">
                {S.matched}: {matchedHeights.length.toLocaleString("en-US")}
              </span>
            </div>
            {borderMode === "count" && (
              <div className="text-xs text-gray-500 mt-1">{S.noteCountMode}</div>
            )}
          </div>

          <div className="lg:col-span-2">
            {drawInfo && (
              <div className="flex items-center gap-4 justify-end w-full text-sm text-gray-500">
                <span>
                  {S.cells}: {drawInfo.columns.toLocaleString("en-US")}×
                  {drawInfo.rows.toLocaleString("en-US")}
                </span>
                <span>{S.stride}: {drawInfo.stride.toLocaleString("en-US")}</span>
                <span>{S.blocks}: {filteredT.length.toLocaleString("en-US")}</span>
              </div>
            )}
          </div>
        </div>
      </div>

      <div ref={wrapperRef} className="relative w-full">
        <div
          ref={scrollRef}
          className="relative w-full overflow-x-auto overflow-y-hidden rounded border border-gray-200 bg-white"
          style={{ height: `${areaH}px` }}
          onMouseMove={onMouseMove}
          onMouseLeave={onMouseLeave}
        >
          <div ref={spacerRef} />
        </div>

        <canvas ref={canvasRef} className="absolute top-0 left-0 right-0 pointer-events-none" />
        <div
          ref={tooltipRef}
          style={{ display: "none" }}
          className="absolute top-0 left-0 z-10 px-2 py-1 rounded bg-white/95 border border-gray-200 shadow text-gray-800 pointer-events-none"
        />
      </div>

      <HistogramCard
        S={S}
        title={S.histTitleAll}
        deltas={deltasAllT}
        bins={histBins}
        setBins={(n) => setHistBins(clamp(Math.floor(n), 5, 400))}
        maxSec={histMaxSec}
        setMaxSec={(v) => setHistMaxSec(v)}
      />
      <HistogramCard
        S={S}
        title={S.histTitleSame}
        deltas={deltasSameT}
        bins={histBins}
        setBins={(n) => setHistBins(clamp(Math.floor(n), 5, 400))}
        maxSec={histMaxSec}
        setMaxSec={(v) => setHistMaxSec(v)}
      />

      <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mt-4">
        <SummaryCard S={S} stats={summary} />
        <ConsecutiveCard S={S} s={consecutive} />
        <TopValidatorsCard S={S} items={topList} />
      </div>

      <AlgoSimulatorCard S={S} />
    </div>
  );
}

/* ============ Histogram Card ============ */
function HistogramCard({
  S,
  title,
  deltas,
  bins,
  setBins,
  maxSec,
  setMaxSec,
}: {
  S: I18nStrings;
  title: string;
  deltas: number[];
  bins: number;
  setBins: (n: number) => void;
  maxSec: number | null;
  setMaxSec: (n: number | null) => void;
}) {
  const containerRef = useRef<HTMLDivElement>(null);
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const [w, setW] = useState(600);
  const [h, setH] = useState(200);

  useEffect(() => {
    if (!containerRef.current) return;
    const obs = new ResizeObserver((ents) => {
      for (const e of ents) setW(Math.max(360, Math.floor(e.contentRect.width)));
    });
    obs.observe(containerRef.current);
    return () => obs.disconnect();
  }, []);

  const stats = useMemo(() => {
    if (deltas.length === 0) return { mean: 0, p50: 0, p95: 0, max: 0 };
    const a = [...deltas].sort((x, y) => x - y);
    const quant = (p: number) =>
      a[Math.min(a.length - 1, Math.max(0, Math.floor(p * (a.length - 1))))];
    const sum = a.reduce((s, v) => s + v, 0);
    return { mean: sum / a.length, p50: quant(0.5), p95: quant(0.95), max: a[a.length - 1] };
  }, [deltas]);

  const usedMax = useMemo(() => {
    if (maxSec != null && maxSec > 0) return maxSec;
    return Math.max(1, stats.p95 || stats.max || 1);
  }, [maxSec, stats]);

  const hist = useMemo(() => {
    const B = Math.max(5, Math.min(400, Math.floor(bins)));
    const counts = new Array<number>(B).fill(0);
    let overflow = 0;
    for (const v of deltas) {
      if (!Number.isFinite(v) || v < 0) continue;
      if (v >= usedMax) {
        overflow++;
      } else {
        const idx = Math.min(B - 1, Math.floor((v / usedMax) * B));
        counts[idx]++;
      }
    }
    const maxCount = counts.length ? Math.max(...counts) : 1;
    return { B, counts, maxCount, overflow };
  }, [deltas, bins, usedMax]);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const padL = 32;
    const padR = 16;
    const padT = 28;
    const padB = 34;
    const dpr = Math.min(2, (window as any).devicePixelRatio || 1);
    const cw = w;
    const ch = h;
    canvas.width = Math.floor(cw * dpr);
    canvas.height = Math.floor(ch * dpr);
    canvas.style.width = `${cw}px`;
    canvas.style.height = `${ch}px`;

    const ctx = canvas.getContext("2d")!;
    (ctx as any).resetTransform?.();
    ctx.scale(dpr, dpr);

    ctx.clearRect(0, 0, cw, ch);
    ctx.fillStyle = "#fff";
    ctx.fillRect(0, 0, cw, ch);

    const plotW = cw - padL - padR;
    const plotH = ch - padT - padB;
    const x0 = padL;
    const y0 = ch - padB;

    ctx.strokeStyle = "rgba(0,0,0,0.15)";
    ctx.beginPath();
    ctx.moveTo(x0, y0 + 0.5);
    ctx.lineTo(x0 + plotW, y0 + 0.5);
    ctx.stroke();

    const barW = plotW / hist.B;
    for (let i = 0; i < hist.B; i++) {
      const c = hist.counts[i];
      const hpx = hist.maxCount > 0 ? (c / hist.maxCount) * plotH : 0;
      const x = x0 + i * barW + 1;
      const y = y0 - hpx;
      ctx.fillStyle = "hsl(220, 60%, 65%)";
      ctx.fillRect(x, y, Math.max(1, barW - 2), hpx);
    }

    if (stats.mean > 0) {
      const xm = x0 + Math.min(1, stats.mean / usedMax) * plotW;
      ctx.strokeStyle = "rgba(220,0,0,0.7)";
      ctx.setLineDash([4, 4]);
      ctx.beginPath();
      ctx.moveTo(xm + 0.5, y0);
      ctx.lineTo(xm + 0.5, y0 - plotH);
      ctx.stroke();
      ctx.setLineDash([]);
    }

    ctx.fillStyle = "#444";
    ctx.font = "20px ui-sans-serif, system-ui";
    ctx.textAlign = "center";
    ctx.textBaseline = "top";
    const maxTick = Math.min(200, Math.floor(usedMax));
    for (let s = 0; s <= maxTick; s++) {
      const x = x0 + (s / usedMax) * plotW;
      ctx.strokeStyle = "rgba(0,0,0,0.2)";
      ctx.beginPath();
      ctx.moveTo(x + 0.5, y0 + 0.5);
      ctx.lineTo(x + 0.5, y0 + 5.5);
      ctx.stroke();
      ctx.fillText(String(s), x, y0 + 8);
    }
    if (usedMax > maxTick) {
      const x = x0 + plotW;
      ctx.beginPath();
      ctx.moveTo(x + 0.5, y0 + 0.5);
      ctx.lineTo(x + 0.5, y0 + 5.5);
      ctx.stroke();
      ctx.fillText(String(Math.round(usedMax)), x, y0 + 8);
    }

    if (hist.overflow > 0) {
      ctx.fillStyle = "#666";
      ctx.textAlign = "right";
      ctx.fillText(`${S.overflow}: ${hist.overflow}`, x0 + plotW, padT - 12);
    }

    ctx.fillStyle = "#111";
    ctx.textAlign = "left";
    ctx.font = "13px ui-sans-serif, system-ui";
    ctx.fillText(title, x0, padT - 12);
  }, [w, h, hist, usedMax, stats, title, S.overflow]);

  return (
    <div className="rounded-2xl border border-gray-200 p-4 shadow-sm bg-white mt-4">
      <div className="flex items-end justify-between gap-3 mb-2">
        <h2 className="font-semibold">{title}</h2>
        <div className="flex items-center gap-3 text-sm">
          <label className="flex items-center gap-2">
            <span className="text-gray-600">{S.bins}</span>
            <input
              type="number"
              min={5}
              max={400}
              value={bins}
              onChange={(e) => setBins(Number(e.currentTarget.value || 100))}
              className="w-24 rounded border px-2 py-1 text-sm"
            />
          </label>
          <label className="flex items-center gap-2">
            <span className="text-gray-600">{S.maxSec}</span>
            <input
              type="number"
              min={0}
              step={0.1}
              value={maxSec ?? ""}
              onChange={(e) => {
                const v = e.currentTarget.value;
                setMaxSec(v === "" ? null : Math.max(0, Number(v)));
              }}
              className="w-32 rounded border px-2 py-1 text-sm"
            />
          </label>
        </div>
      </div>

      <div ref={containerRef} className="w-full">
        <canvas ref={canvasRef} className="w-full h-[200px] block" />
      </div>

      <div className="text-xs text-gray-500 mt-2">
        mean: {fmtSec(stats.mean)} ・ p50: {fmtSec(stats.p50)} ・ p95: {fmtSec(stats.p95)} ・ max:{" "}
        {fmtSec(stats.max)}
      </div>
    </div>
  );
}

/* ============ Summary Card ============ */
function SummaryCard({ S, stats }: { S: I18nStrings; stats: SummaryStats }) {
  const fmtOrDash = (v: number | null) => (v == null ? "—" : v.toLocaleString("en-US"));
  return (
    <div className="rounded-2xl border border-gray-200 p-4 shadow-sm bg-white">
      <h2 className="font-semibold mb-3">{S.summary}</h2>
      <ul className="text-sm space-y-1">
        <li>
          <span className="text-gray-500">{S.blocks}:</span> {fmtOrDash(stats.blocks)}
        </li>
        <li>
          <span className="text-gray-500">{S.timeSpan}:</span> {stats.timeSpan ?? "—"}
        </li>
        <li>
          <span className="text-gray-500">{S.validators}:</span> {fmtOrDash(stats.validators)}
        </li>
        <li>
          <span className="text-gray-500">{S.totalProposes}:</span> {fmtOrDash(stats.proposals)}
        </li>
        <li>
          <span className="text-gray-500">{S.edges}:</span> {fmtOrDash(stats.edges)}
        </li>
      </ul>
    </div>
  );
}

/* ============ Consecutive Stats Card ============ */
function ConsecutiveCard({
  S,
  s,
}: {
  S: I18nStrings;
  s: {
    pairs: number;
    samePairs: number;
    pSame: number;
    runs: number;
    runsGE2: number;
    blocksInRunsGE2: number;
    fracBlocksInGE2: number;
    avgRunLen: number;
    medianRunLen: number;
  };
}) {
  const dash = "—";
  const fmtN = (n: number) => (Number.isFinite(n) ? n.toLocaleString("en-US") : dash);
  const fmtF = (x: number) => (Number.isFinite(x) ? x.toFixed(3) : dash);
  return (
    <div className="rounded-2xl border border-gray-200 p-4 shadow-sm bg-white">
      <h2 className="font-semibold mb-3">{S.consecTitle}</h2>
      <ul className="text-sm space-y-1">
        <li>
          <span className="text-gray-500">{S.pairProb}:</span> <b>{fmtPct(s.pSame)}</b>{" "}
          <span className="text-gray-400">
            ({S.samePairs}: {fmtN(s.samePairs)} / {S.pairsTotal}: {fmtN(s.pairs)})
          </span>
        </li>
        <li>
          <span className="text-gray-500">{S.runs}:</span> {fmtN(s.runs)} ・{" "}
          <span className="text-gray-500">{S.runsGE2}:</span> {fmtN(s.runsGE2)}
        </li>
        <li>
          <span className="text-gray-500">{S.blocksInGE2}:</span> {fmtN(s.blocksInRunsGE2)} ・{" "}
          <span className="text-gray-500">{S.fracBlocksInGE2}:</span>{" "}
          <b>{fmtPct(s.fracBlocksInGE2)}</b>
        </li>
        <li>
          <span className="text-gray-500">{S.avgRunLen}:</span> {fmtF(s.avgRunLen)} ・{" "}
          <span className="text-gray-500">{S.medRunLen}:</span> {fmtF(s.medianRunLen)}
        </li>
      </ul>
      <p className="text-xs text-gray-500 mt-2">
        Definition: probability that adjacent blocks share the same proposer = (#same pairs) /
        (N-1).
      </p>
    </div>
  );
}

/* ============ Top Validators Card (scrollable, up to 50) ============ */
function TopValidatorsCard({
  S,
  items,
}: {
  S: I18nStrings;
  items: { hex: string; label: string; count: number }[];
}) {
  const rows = items.slice(0, 50);
  const max = rows.length ? Math.max(...rows.map((d) => d.count)) : 1;
  return (
    <div className="rounded-2xl border border-gray-200 p-4 shadow-sm bg-white">
      <h2 className="font-semibold">{S.topValidators}</h2>
      <p className="text-xs text-gray-500 mb-3">{S.byProposeCount}</p>
      {rows.length === 0 ? (
        <div className="text-sm text-gray-500">—</div>
      ) : (
        <ul className="space-y-2 max-h-96 overflow-y-auto pr-1">
          {rows.map((it) => (
            <li key={it.hex}>
              <div className="flex items-center justify-between text-sm">
                <div className="flex items-center gap-2">
                  <span
                    className="inline-block w-3 h-3 rounded-full"
                    style={{ background: hashColor(it.hex) }}
                    aria-hidden
                  />
                  <span className="font-medium">{it.label}</span>
                </div>
                <div className="text-gray-600">{it.count.toLocaleString("en-US")}</div>
              </div>
              <div className="h-2 w-full bg-gray-100 rounded mt-1 overflow-hidden">
                <div
                  className="h-2 rounded"
                  style={{
                    width: `${(100 * it.count) / max}%`,
                    background: hashColor(it.hex),
                    opacity: 0.85,
                  }}
                />
              </div>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}

/* ============ Algorithm Transition Simulator (Priority Queue / Smooth WRR) ============ */
function AlgoSimulatorCard({ S }: { S: I18nStrings }) {
  const [weights, setWeights] = React.useState<number[]>([2, 11, 31, 22, 33]);
  const [prio, setPrio] = React.useState<number[]>(() => weights.map(() => 0));
  const [freq, setFreq] = React.useState<number[]>(() => weights.map(() => 0));
  const [t, setT] = React.useState<number>(0);

  React.useEffect(() => {
    setPrio((p) => (p.length === weights.length ? p : Array(weights.length).fill(0)));
    setFreq((f) => (f.length === weights.length ? f : Array(weights.length).fill(0)));
  }, [weights.length]);

  const Ssum = React.useMemo(
    () => weights.reduce((s, v) => s + Math.max(0, Number(v) || 0), 0),
    [weights]
  );

  const view = React.useMemo(() => {
    const pPlus = prio.map((p, i) => p + (Number(weights[i]) || 0));
    const mean = pPlus.length ? pPlus.reduce((a, b) => a + b, 0) / pPlus.length : 0;
    const centered = pPlus.map((v) => v - mean);
    let best = 0;
    for (let i = 1; i < centered.length; i++) if (centered[i] > centered[best]) best = i;
    return { centered, best };
  }, [prio, weights]);

  const step = () => {
    if (Ssum <= 0 || weights.length === 0) return;
    const pPlus = prio.map((p, i) => p + (Number(weights[i]) || 0));
    const j = view.best;
    pPlus[j] -= Ssum;
    setPrio(pPlus);
    setFreq((f) => {
      const g = f.slice();
      g[j] = (g[j] ?? 0) + 1;
      return g;
    });
    setT((x) => x + 1);
  };

  const reset = () => {
    setPrio(Array(weights.length).fill(0));
    setFreq(Array(weights.length).fill(0));
    setT(0);
  };

  const updateWeight = (i: number, v: number) => {
    setWeights((w) => {
      const a = w.slice();
      a[i] = Math.max(0, Number.isFinite(v) ? v : 0);
      return a;
    });
  };

  const addRow = () => setWeights((w) => [...w, 1]);
  const removeRow = (i: number) =>
    setWeights((w) => (w.length <= 1 ? w : w.filter((_, k) => k !== i)));

  return (
    <div className="rounded-2xl border border-gray-200 p-4 shadow-sm bg-white mt-4">
      <div className="flex items-start justify-between gap-3 mb-3">
        <div>
          <h2 className="font-semibold text-xl md:text-2xl">{S.algoTitle}</h2>
          <p className="text-sm md:text-base text-gray-500 mt-1">{S.algoDesc}</p>
        </div>
        <div className="text-base md:text-lg text-gray-600 whitespace-nowrap">
          {S.roundT} <span className="font-semibold">t = {t.toLocaleString("en-US")}</span>
          <span className="mx-2">,</span>
          {S.totalVotingPowerS}{" "}
          <span className="font-semibold">S = {Ssum.toLocaleString("en-US")}</span>
        </div>
      </div>

      <div className="overflow-x-auto">
        <table className="min-w-[560px] w-full text-base md:text-lg">
          <thead>
            <tr className="text-left text-gray-600 border-b">
              <th className="py-1 pr-2 w-12">{S.idx}</th>
              <th className="py-1 pr-2">{S.votingPowerSi}</th>
              <th className="py-1 pr-2">{S.priorityPi}</th>
              <th className="py-1 pr-2">{S.proposerCol}</th>
              <th className="py-1 pr-2">{S.frequencyCol}</th>
              <th className="py-1 pr-2"></th>
            </tr>
          </thead>
          <tbody>
            {weights.map((w, i) => (
              <tr key={i} className="border-b last:border-b-0">
                <td className="py-1 pr-2">{i + 1}</td>
                <td className="py-1 pr-2">
                  <input
                    type="number"
                    value={w}
                    onChange={(e) => updateWeight(i, Number(e.currentTarget.value))}
                    className="w-24 rounded border px-2 py-1"
                  />
                </td>
                <td className="py-1 pr-2 tabular-nums">{view.centered[i].toFixed(1)}</td>
                <td className="py-1 pr-2">{view.best === i ? "✓" : ""}</td>
                <td className="py-1 pr-2">{(freq[i] ?? 0).toLocaleString("en-US")}</td>
                <td className="py-1 pr-2">
                  <button
                    type="button"
                    className="text-sm md:text-base text-red-600 hover:underline"
                    onClick={() => removeRow(i)}
                    title="remove row"
                  >
                    {weights.length > 1 ? "−" : ""}
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      <div className="flex items-center gap-2 mt-3">
        <button
          className="px-3 py-1.5 rounded bg-gray-900 text-white hover:opacity-90 text-base md:text-lg"
          type="button"
          onClick={step}
        >
          {S.nextRoundBtn}
        </button>
        <button
          className="px-3 py-1.5 rounded bg-gray-100 hover:bg-gray-200 text-base md:text-lg"
          type="button"
          onClick={reset}
        >
          {S.reset}
        </button>
        <button
          className="ml-2 px-2 py-1 rounded bg-gray-100 hover:bg-gray-200 text-sm md:text-base"
          type="button"
          onClick={addRow}
        >
          + row
        </button>
      </div>
    </div>
  );
}