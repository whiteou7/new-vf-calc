import initSqlJs from "sql.js"
import {
  calculateVFWithMode,
  clearCoeff,
  clearCoeffExceed,
  getLamp,
  gradeFromScore,
  normalizeLampForScoring,
  roundLevelForMode,
} from "@/scoring.js"
import { findFuzzyMatch, normalizeTitleArtist } from "./fuzzy.js"
import { getLevelFromMdb } from "./musicDb.js"

const PATH_FILTER = "LOWER(path) LIKE '%sdvx%' OR LOWER(path) LIKE '%sound voltex%'"

export async function openDb(buffer) {
  const SQL = await initSqlJs({ locateFile: (f) => import.meta.env.BASE_URL + f })
  return new SQL.Database(new Uint8Array(buffer))
}

// Returns { error } or { players, scoresTable, chartsTable }. A null player means "no user".
export function inspectDb(db) {
  const tableCheck = db.exec("SELECT name FROM sqlite_master WHERE type='table' AND (name='scores' OR name='Scores' OR name='charts' OR name='Charts')")
  const tables = (tableCheck[0]?.values ?? []).map((r) => r[0])
  const scoresTable = tables.find((t) => t.toLowerCase() === "scores")
  const chartsTable = tables.find((t) => t.toLowerCase() === "charts")
  if (!scoresTable || !chartsTable) {
    return { error: "Invalid maps.db: missing Scores or Charts table." }
  }

  const usersResult = db.exec(`SELECT DISTINCT user_name FROM ${scoresTable}`)
  const rawPlayers = (usersResult[0]?.values ?? []).map((r) => r[0])
  // empty strings are the same "no user" player as null
  const players = Array.from(
    new Set(
      rawPlayers.map((u) => {
        const v = u == null ? null : String(u).trim()
        return v === "" ? null : v
      })
    )
  )
  if (players.length === 0) {
    return { error: "No players found in maps.db." }
  }
  return { players, scoresTable, chartsTable }
}

function loadCharts(db, chartsTable) {
  let rows
  try {
    rows = db.exec(`SELECT hash, title, artist, path, diff_index, diff_shortname FROM ${chartsTable} WHERE (${PATH_FILTER})`)[0]?.values ?? []
  } catch (e) {
    throw new Error("Charts query failed. Check table/column names: " + (e?.message || String(e)))
  }

  const byHash = new Map()
  for (const [hash, title, artist, path, diff_index, diff_shortname] of rows) {
    const h = String(hash ?? "").trim()
    byHash.set(h, {
      hash: h,
      title: String(title ?? "").trim(),
      artist: String(artist ?? "").trim(),
      path: String(path ?? ""),
      diff_index: Number(diff_index) ?? 0,
      diff_shortname: String(diff_shortname ?? "").trim()
    })
  }
  return byHash
}

function loadPlaysByChart(db, userName, scoresTable, chartsTable) {
  const userCondition =
    userName == null
      ? "(s.user_name IS NULL OR s.user_name = '')"
      : "s.user_name = ?"

  const stmt = db.prepare(`
    SELECT s.chart_hash, s.score, s.miss, s.gauge_type, s.gauge, s.timestamp
    FROM ${scoresTable} s
    INNER JOIN ${chartsTable} c ON c.hash = s.chart_hash AND (${PATH_FILTER})
    WHERE ${userCondition}
  `)
  if (userName != null) stmt.bind([userName])

  const playsByChart = new Map()
  while (stmt.step()) {
    const row = stmt.getAsObject()
    const h = String(row.chart_hash ?? "").trim()
    if (!playsByChart.has(h)) playsByChart.set(h, [])
    playsByChart.get(h).push({
      score: Number(row.score) || 0,
      miss: row.miss,
      gauge_type: row.gauge_type,
      gauge: row.gauge,
      timestamp: row.timestamp ?? null,
    })
  }
  stmt.free()
  return playsByChart
}

function bestLamp(plays, { exceed, disableMaxxive }) {
  const coeffTable = exceed ? clearCoeffExceed : clearCoeff
  let best = "FAILED"
  let bestCoeff = clearCoeff["FAILED"]

  for (const p of plays) {
    const lamp = getLamp(p.score, p.miss, p.gauge_type, p.gauge)
    const c = coeffTable[normalizeLampForScoring(lamp, disableMaxxive)] ?? 0.5
    if (c > bestCoeff) {
      bestCoeff = c
      best = lamp
    }
  }
  return best
}

export function buildMapsDbRows(db, userName, { scoresTable, chartsTable }, mdbIndex, opts) {
  const chartByHash = loadCharts(db, chartsTable)
  const playsByChart = loadPlaysByChart(db, userName, scoresTable, chartsTable)

  const rows = []
  let skipped = 0

  for (const [chartHash, plays] of playsByChart) {
    const chart = chartByHash.get(chartHash)
    if (!chart) continue

    const key = normalizeTitleArtist(chart.title) + "|" + normalizeTitleArtist(chart.artist)
    const mdbSong = mdbIndex.get(key) ?? findFuzzyMatch(chart.title, chart.artist, mdbIndex)

    if (!mdbSong) {
      console.log("not found: " + chart.title + " " + chart.artist)
      skipped += 1
      continue
    }

    const level = roundLevelForMode(getLevelFromMdb(mdbSong, chart.diff_index), opts.exceed)
    const bestScorePlay = plays.reduce((a, b) => b.score > a.score ? b : a, plays[0])
    const score = bestScorePlay.score
    const grade = gradeFromScore(score)
    const lamp = bestLamp(plays, opts)

    rows.push({
      chart_hash: chartHash,
      songId: mdbSong.mid,
      title: chart.title,
      diff: (chart.diff_shortname || "NOV").toUpperCase(),
      level,
      score,
      grade,
      lamp,
      vf: calculateVFWithMode({ level, score, grade, lamp }, opts.exceed, opts.disableMaxxive),
      // maps.db stores Unix seconds
      timeAchieved: bestScorePlay.timestamp ? bestScorePlay.timestamp * 1000 : null,
    })
  }

  return { rows, skipped }
}
