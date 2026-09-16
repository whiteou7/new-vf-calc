<template>
  <div class="app">
    <div class="container">
      <header class="header">
        <h1 class="title">SDVX B50 Calculator</h1>
      </header>

      <div class="input-card">
        <div class="input-row">
          <input
            v-model="userId"
            placeholder="Enter Tachi Username"
            class="input"
          />
          <button
            class="btn btn-primary"
            @click="loadData"
            :disabled="loading || !mdbReady"
          >
            {{ loading ? "Loading..." : !mdbReady ? "Loading database..." : "Calculate" }}
          </button>
          <span class="or">or</span>
          <input
            ref="dbFileInput"
            type="file"
            accept=".db,application/x-sqlite3"
            class="file-input"
            @change="onDbFileSelected"
          />
          <button
            type="button"
            class="btn btn-secondary"
            :disabled="loading || !mdbReady"
            @click="$refs.dbFileInput?.click()"
          >
            Upload maps.db
          </button>
        </div>
        <label class="checkbox-row">
          <input type="checkbox" v-model="pendingExceedGear" />
          Calculate Exceed Gear VF
        </label>
        <label class="checkbox-row">
          <input type="checkbox" v-model="pendingDisableMaxxive" />
          Disable Maxxive Scores
        </label>
      </div>

      <div v-if="playerSelect.visible" class="player-select card">
        <p class="player-select-label">More than one player in database. Choose a player:</p>
        <div class="player-select-row">
          <select v-model="playerSelect.selected" class="select">
            <option value="" disabled>Select player</option>
            <option
              v-for="name in playerSelect.players"
              :key="name ?? '__null__'"
              :value="name"
            >
              {{ name ?? "(no user)" }}
            </option>
          </select>
          <button
            class="btn btn-primary"
            @click="confirmPlayerAndCalculate"
            :disabled="!playerSelect.selected"
          >
            Calculate VF
          </button>
        </div>
      </div>

      <div v-if="error" class="error card">{{ error }}</div>

      <section v-if="best50.length" class="results">
        <div class="results-header card">
          <h2 class="vf-display">{{ appliedExceedGear ? "Exceed Gear VF:" : "Nabla VF:" }} <span class="vf-value">{{ totalVF.toFixed(3) }}</span></h2>
          <button type="button" class="btn btn-secondary export-csv-btn" @click="exportToCsv">
            Export to CSV
          </button>
          <button type="button" class="btn btn-secondary export-csv-btn" @click="generateImage" :disabled="generatingImage">
            {{ generatingImage ? "Generating… might take a while" : "Generate Image" }}
          </button>
        </div>

        <div v-if="generatedImageUrl" style="padding-bottom: 16px;">
          <img :src="generatedImageUrl" alt="B50 result card" class="generated-image" />
        </div>

        <div class="table-card card">
          <table class="b50-table">
            <thead>
              <tr>
                <th class="col-rank">#</th>
                <th class="col-song">Song</th>
                <th class="col-diff">Diff</th>
                <th class="col-level">Level</th>
                <th class="col-score">Score</th>
                <th class="col-grade">Grade</th>
                <th class="col-clear">Clear</th>
                <th class="col-vf">VF</th>
              </tr>
            </thead>
            <tbody>
              <tr
                v-for="(row, i) in best50"
                :key="row.chartID ?? row.chart_hash ?? i"
                class="row"
              >
                <td class="col-rank">{{ i + 1 }}</td>
                <td class="col-song">
                  <div class="song-cell">
                    <div class="jacket-wrap">
                      <img
                        v-if="row.songId && !jacketFailed(row.songId)"
                        :src="jacketUrl(row.songId)"
                        :alt="row.title"
                        class="jacket"
                        loading="lazy"
                        @error="onJacketError"
                      />
                      <div
                        v-show="!row.songId || jacketFailed(row.songId)"
                        class="jacket jacket-placeholder"
                      >
                        <span class="jacket-placeholder-icon">♪</span>
                      </div>
                    </div>
                    <span class="song-title">{{ row.title }}</span>
                  </div>
                </td>
                <td class="col-diff"><span :class="['diff-badge', 'diff-' + (row.diff || '').toLowerCase()]">{{ (row.diff || '').toUpperCase() }}</span></td>
                <td class="col-level">{{ row.level }}</td>
                <td class="col-score">{{ formatScore(row.score) }}</td>
                <td class="col-grade"><span :class="['grade-badge', 'grade-' + gradeClass(row.grade)]">{{ row.grade }}</span></td>
                <td class="col-clear lamp-cell">{{ effectiveLamp(row.lamp) }}</td>
                <td class="col-vf"><strong>{{ row.vf.toFixed(3) }}</strong></td>
              </tr>
            </tbody>
          </table>
        </div>
      </section>
    </div>
  </div>

</template>

<script setup>
import { ref, computed, onMounted } from "vue"
import initSqlJs from "sql.js"
import musicDbUrl from "@/assets/music_db.xml?url"
import { calculateVF, clearCoeff, clearCoeffExceed, normalizeLampForScoring } from "./scoring.js"

const mdb = ref({})
const mdbReady = ref(false)

const userId = ref("")
const loading = ref(false)
const error = ref("")
const best50 = ref([])
const totalVF = ref(0)
const pendingExceedGear = ref(false)
const pendingDisableMaxxive = ref(false)
const appliedExceedGear = ref(false)
const appliedDisableMaxxive = ref(false)
let msg = ""
let skippedCount = 0

const playerSelect = ref({
  visible: false,
  players: [],
  selected: "",
  dbBuffer: null
})

const generatingImage = ref(false)
const generatedImageUrl = ref("")
const activePlayerName = ref("")

const failedJackets = ref(new Set())
const JACKET_BASE = "https://sdvx.dev/api/cover"
function jacketUrl(songId) {
  if (!songId) return ""
  return `${JACKET_BASE}/${songId}_novice.webp`
}

function onJacketError(e) {
  const img = e.target
  const src = img?.src
  if (src) {
    const m = src.match(/\/([^/]+)\/NOV\.png$/)
    if (m?.[1]) failedJackets.value.add(m[1])
    failedJackets.value = new Set(failedJackets.value)
  }
  img?.style?.setProperty("display", "none")
}

function jacketFailed(songId) {
  return songId && failedJackets.value.has(String(songId))
}

function formatScore(score) {
  const n = Number(score)
  if (n >= 10_000_000) return "10,000,000"
  return n.toLocaleString()
}

function effectiveLamp(lamp) {
  return normalizeLampForScoring(lamp, appliedDisableMaxxive.value)
}

function gradeClass(grade) {
  return (grade || "").toLowerCase().replace("+", "plus")
}

function escapeCsvField(val) {
  const s = String(val ?? "")
  if (s.includes(",") || s.includes('"') || s.includes("\n")) {
    return '"' + s.replace(/"/g, '""') + '"'
  }
  return s
}

function exportToCsv() {
  const headers = ["#", "Song", "Diff", "Level", "Score", "Grade", "Clear", "VF"]
  const lines = [headers.map(escapeCsvField).join(",")]
  for (let i = 0; i < best50.value.length; i++) {
    const row = best50.value[i]
    lines.push(
      [
        i + 1,
        row.title ?? "",
        (row.diff ?? "").toUpperCase(),
        row.level ?? "",
        formatScore(row.score),
        row.grade ?? "",
        effectiveLamp(row.lamp),
        row.vf != null ? row.vf.toFixed(3) : ""
      ].map(escapeCsvField).join(",")
    )
  }
  const csv = lines.join("\n")
  const blob = new Blob(["\uFEFF" + csv], { type: "text/csv;charset=utf-8" })
  const url = URL.createObjectURL(blob)
  const a = document.createElement("a")
  a.href = url
  a.download = "b50-export.csv"
  a.click()
  URL.revokeObjectURL(url)
}

const BACKEND_URL = "https://b50-api.whiteou7.id.vn"

async function generateImage() {
  generatingImage.value = true
  try {
    const payload = {
      username: activePlayerName.value || "Player",
      vf: totalVF.value,
      mode: appliedExceedGear.value ? "exceed" : "nabla",
      scores: best50.value.map((r) => ({
        title: r.title,
        diff: r.diff,
        level: r.level,
        score: r.score,
        grade: r.grade,
        lamp: effectiveLamp(r.lamp),
        vf: r.vf,
        songId: r.songId,
        timeAchieved: r.timeAchieved ?? null,
      })),
    }
    const res = await fetch(`${BACKEND_URL}/api/generate-b50`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    })
    if (!res.ok) {
      const err = await res.json().catch(() => ({ error: res.statusText }))
      throw new Error(err.error || res.statusText)
    }
    const blob = await res.blob()
    if (generatedImageUrl.value) URL.revokeObjectURL(generatedImageUrl.value)
    generatedImageUrl.value = URL.createObjectURL(blob)
  } catch (e) {
    error.value = "Image generation failed: " + (e?.message || String(e))
  } finally {
    generatingImage.value = false
  }
}

function parseMusicDbXml(xmlText) {
  const parser = new DOMParser()
  const doc = parser.parseFromString(xmlText, "application/xml")

  // Check for parser errors
  const parserError = doc.querySelector("parsererror")
  if (parserError) {
    throw new Error("Invalid XML")
  }

  const out = {}
  const musicList = doc.querySelectorAll("mdb > music")
  const diffNames = ["novice", "advanced", "exhaust", "infinite", "maximum", "ultimate"]

  for (const music of musicList) {
    const id = music.getAttribute("id")
    if (!id) continue

    const title =
      music.querySelector("info > title_name")?.textContent?.trim() ?? ""

    const artist =
      music.querySelector("info > artist_name")?.textContent?.trim() ?? ""

    const difficulty = diffNames.map((name) => {
      const el = music.querySelector(`difficulty > ${name} > difnum`)
      const n = el?.textContent?.trim()
      return (n ? parseInt(n, 10) : 0) / 10
    })

    out[id] = {
      title,
      artist,
      difficulty,
      mid: id,
    }
  }

  return out
}

onMounted(async () => {
  try {
    const response = await fetch(musicDbUrl)

    // Get raw bytes
    const buffer = await response.arrayBuffer()

    // Decode using Shift-JIS
    const decoder = new TextDecoder("shift-jis")
    const xmlText = decoder.decode(buffer)

    mdb.value = parseMusicDbXml(xmlText)
    mdbReady.value = true
  } catch (e) {
    console.error("Failed to load music_db.xml", e)
    error.value = "Failed to load music database."
  }
})

function normalizeTitleArtist(str) {
  return (str ?? "").toString().trim().toLowerCase()
}

// ChatGPT wrote ts shit
function levenshtein(a, b) {
  if (a === b) return 0
  if (!a.length) return b.length
  if (!b.length) return a.length

  const matrix = Array.from({ length: b.length + 1 }, () =>
    new Array(a.length + 1)
  )

  for (let i = 0; i <= a.length; i++) matrix[0][i] = i
  for (let j = 0; j <= b.length; j++) matrix[j][0] = j

  for (let j = 1; j <= b.length; j++) {
    for (let i = 1; i <= a.length; i++) {
      const cost = a[i - 1] === b[j - 1] ? 0 : 1
      matrix[j][i] = Math.min(
        matrix[j - 1][i] + 1,        // deletion
        matrix[j][i - 1] + 1,        // insertion
        matrix[j - 1][i - 1] + cost  // substitution
      )
    }
  }

  return matrix[b.length][a.length]
}

function similarity(a, b) {
  if (!a.length && !b.length) return 1
  const distance = levenshtein(a, b)
  const maxLen = Math.max(a.length, b.length)
  return 1 - distance / maxLen
}

function isCloseMatch(a, b, threshold = 0.75) {
  return similarity(a, b) >= threshold
}

function findFuzzyMatch(title, artist, map) {
  const normTitle = normalizeTitleArtist(title)
  const normArtist = normalizeTitleArtist(artist)

  const THRESHOLD = 0.75

  let bestMatch = null
  let bestScore = 0

  for (const entry of map.values()) {
    const t = normalizeTitleArtist(entry.title)
    const a = normalizeTitleArtist(entry.artist)

    const score = similarity(
      normTitle + " " + normArtist,
      t + " " + a
    )

    if (score > bestScore) {
      bestScore = score
      bestMatch = entry
    }
  }

  return bestScore >= THRESHOLD ? bestMatch : null
}

const mdbByTitleArtist = computed(() => {
  const map = new Map()
  for (const [mid, entry] of Object.entries(mdb.value)) {
    if (!entry || !entry.title) continue
    const key = normalizeTitleArtist(entry.title) + "|" + normalizeTitleArtist(entry.artist ?? "")
    if (!map.has(key)) map.set(key, { ...entry, mid })
  }
  return map
})

function gradeFromScore(score) {
  const s = Number(score) || 0
  if (s >= 10_000_000) return "PUC"
  if (s >= 9_900_000) return "S"
  if (s >= 9_800_000) return "AAA+"
  if (s >= 9_700_000) return "AAA"
  if (s >= 9_500_000) return "AA+"
  if (s >= 9_300_000) return "AA"
  if (s >= 9_000_000) return "A+"
  if (s >= 8_700_000) return "A"
  if (s >= 7_500_000) return "B"
  if (s >= 6_500_000) return "C"
  return "D"
}

function getLamp(score, miss, gaugeType, gauge) {
  const s = Number(score) || 0
  const noMiss = miss == null || Number(miss) === 0
  const gt = Number(gaugeType) ?? 0
  const g = Number(gauge) ?? 0

  if (s >= 10_000_000 && noMiss) return "PERFECT ULTIMATE CHAIN"
  if (noMiss) return "ULTIMATE CHAIN"
  if (gt === 1 && g > 0) return "EXCESSIVE CLEAR" // HARD clear
  if (gt === 0 && g >= .70) return "CLEAR" // NORMAL clear
  return "FAILED" // PLAYED
}

function getLevel(chart, chartMeta) {
  if (!chartMeta) return 0

  const diffIndexMap = {
    nov: 0,
    adv: 1,
    exh: 2,
    inf: 3,
    grv: 3,
    hvn: 3,
    vvd: 3,
    xcd: 3,
    mxm: 4,
    ult: 4
  }

  const idx = diffIndexMap[chart.difficulty.toLowerCase()]
  return chartMeta.difficulty[idx] || 0
}

// Exceed Gear only had whole-number chart levels
function roundLevelForMode(level, exceed) {
  return exceed ? Math.trunc(level) : level
}

function calculateVFWithMode({ level, score, grade, lamp }, exceed = false) {
  return calculateVF({ level: roundLevelForMode(level, exceed), score, grade, lamp }, exceed, appliedDisableMaxxive.value)
}

function getLevelFromMdb(mdbSong, diffIndex) {
  if (!mdbSong || !Array.isArray(mdbSong.difficulty)) return 0
  const idx = Math.min(Number(diffIndex) || 0, mdbSong.difficulty.length - 1)
  const level = Number(mdbSong.difficulty[idx])
  if (level != 0) return level
  // LMAO
  if (idx == 3) return Number(mdbSong.difficulty[4])
  if (idx == 4) return Number(mdbSong.difficulty[3])
  console.log("warning: level not found")
  return 0
}

async function onDbFileSelected(ev) {
  const file = ev.target?.files?.[0]
  if (!file) return
  ev.target.value = ""
  error.value = ""
  best50.value = []
  totalVF.value = 0
  failedJackets.value = new Set()
  generatedImageUrl.value = ""
  loading.value = true
  try {
    const buffer = await file.arrayBuffer()
    const SQL = await initSqlJs({ locateFile: (f) => import.meta.env.BASE_URL + f })
    const db = new SQL.Database(new Uint8Array(buffer))

    const tableCheck = db.exec("SELECT name FROM sqlite_master WHERE type='table' AND (name='scores' OR name='Scores' OR name='charts' OR name='Charts')")
    const tables = (tableCheck[0]?.values ?? []).map((r) => r[0])
    const hasScores = tables.some((t) => t.toLowerCase() === "scores")
    const hasCharts = tables.some((t) => t.toLowerCase() === "charts")
    if (!hasScores || !hasCharts) {
      error.value = "Invalid maps.db: missing Scores or Charts table."
      loading.value = false
      return
    }

    const scoresTable = tables.find((t) => t.toLowerCase() === "scores") || "Scores"
    const chartsTable = tables.find((t) => t.toLowerCase() === "charts") || "Charts"

    // Collect all distinct users, including null / empty which we treat as one player.
    const usersResult = db.exec(`SELECT DISTINCT user_name FROM ${scoresTable}`)
    const rawPlayers = (usersResult[0]?.values ?? []).map((r) => r[0])
    // Normalize empty strings to null so that "no user" is treated as a single player.
    const players = Array.from(
      new Set(
        rawPlayers.map((u) => {
          const v = u == null ? null : String(u).trim()
          return v === "" ? null : v
        })
      )
    )

    if (players.length === 0) {
      error.value = "No players found in maps.db."
      loading.value = false
      return
    }

    if (players.length === 1) {
      activePlayerName.value = players[0] ?? ""
      appliedExceedGear.value = pendingExceedGear.value
      appliedDisableMaxxive.value = pendingDisableMaxxive.value
      await calculateFromDb(db, players[0], scoresTable, chartsTable)
    } else {
      playerSelect.value = {
        visible: true,
        players,
        selected: "",
        dbBuffer: buffer,
        scoresTable,
        chartsTable
      }
    }
    db.close()
  } catch (e) {
    error.value = "Failed to read maps.db: " + (e?.message || String(e))
  } finally {
    loading.value = false
  }
}

function confirmPlayerAndCalculate() {
  const { selected, dbBuffer, scoresTable, chartsTable } = playerSelect.value
  if (!selected || !dbBuffer) return
  activePlayerName.value = selected
  appliedExceedGear.value = pendingExceedGear.value
  appliedDisableMaxxive.value = pendingDisableMaxxive.value
  playerSelect.value = { visible: false, players: [], selected: "", dbBuffer: null }
  loading.value = true
  error.value = ""
  best50.value = []
  totalVF.value = 0
  failedJackets.value = new Set()
  generatedImageUrl.value = ""
  ;(async () => {
    try {
      const SQL = await initSqlJs({ locateFile: (f) => import.meta.env.BASE_URL + f })
      const db = new SQL.Database(new Uint8Array(dbBuffer))
      await calculateFromDb(db, selected, scoresTable, chartsTable)
      db.close()
    } catch (e) {
      error.value = "Failed to calculate: " + (e?.message || String(e))
    } finally {
      loading.value = false
    }
  })()
}

async function calculateFromDb(db, userName, scoresTable, chartsTable) {
  skippedCount = 0
  const map = mdbByTitleArtist.value

  const pathFilter = "LOWER(path) LIKE '%sdvx%' OR LOWER(path) LIKE '%sound voltex%'"
  const chartsQuery = `SELECT hash, title, artist, path, diff_index, diff_shortname FROM ${chartsTable} WHERE (${pathFilter})`
  let chartsRows = []
  try {
    const r = db.exec(chartsQuery)
    chartsRows = r[0]?.values ?? []
  } catch (e) {
    error.value = "Charts query failed. Check table/column names: " + (e?.message || String(e))
    return
  }

  const chartByHash = new Map()
  for (const row of chartsRows) {
    const [hash, title, artist, path, diff_index, diff_shortname] = row
    chartByHash.set(String(hash ?? "").trim(), {
      hash: String(hash ?? "").trim(),
      title: String(title ?? "").trim(),
      artist: String(artist ?? "").trim(),
      path: String(path ?? ""),
      diff_index: Number(diff_index) ?? 0,
      diff_shortname: String(diff_shortname ?? "").trim()
    })
  }

  const userCondition =
    userName == null
      ? "(s.user_name IS NULL OR s.user_name = '')"
      : "s.user_name = ?"

  const bestScoresQuery = `
    SELECT s.chart_hash, s.score, s.miss, s.gauge_type, s.gauge, s.timestamp
    FROM ${scoresTable} s
    INNER JOIN ${chartsTable} c ON c.hash = s.chart_hash AND (${pathFilter})
    WHERE ${userCondition}
  `
  const stmt = db.prepare(bestScoresQuery)
  if (userName != null) {
    stmt.bind([userName])
  }
  const allScores = []
  while (stmt.step()) {
    allScores.push(stmt.getAsObject())
  }
  stmt.free()

  // Group all plays by chart_hash
  const playsByChart = new Map()
  for (const row of allScores) {
    const h = String(row.chart_hash ?? "").trim()
    if (!playsByChart.has(h)) playsByChart.set(h, [])
    playsByChart.get(h).push({
      chart_hash: h,
      score: Number(row.score) || 0,
      miss: row.miss,
      gauge_type: row.gauge_type,
      gauge: row.gauge,
      timestamp: row.timestamp ?? null,
    })
  }

  const rows = []
  for (const [chartHash, plays] of playsByChart) {
    const chart = chartByHash.get(chartHash)
    if (!chart) continue

    const key = normalizeTitleArtist(chart.title) + "|" + normalizeTitleArtist(chart.artist)
    let mdbSong = map.get(key)
    // Fuzzy fallback if exact match fails
    if (!mdbSong) {
      mdbSong = findFuzzyMatch(chart.title, chart.artist, map)
    }

    if (!mdbSong) {
      console.log("not found: " + chart.title + " " + chart.artist)
      skippedCount += 1
      continue
    }

    const level = roundLevelForMode(getLevelFromMdb(mdbSong, chart.diff_index), appliedExceedGear.value)
    const diff = (chart.diff_shortname || "NOV").toUpperCase()

    // PB = best score + best lamp (from any play on this chart)
    const bestScorePlay = plays.reduce((a, b) => b.score > a.score ? b : a, plays[0])
    const bestScore = bestScorePlay.score
    // timestamp is stored in Unix seconds in maps.db; convert to ms for consistency
    const bestTimestamp = bestScorePlay.timestamp ? bestScorePlay.timestamp * 1000 : null
    let bestLamp = "FAILED"
    let bestLampCoeff = clearCoeff["FAILED"]

    for (const p of plays) {
      const lamp = getLamp(p.score, p.miss, p.gauge_type, p.gauge)
      const effectiveLamp = normalizeLampForScoring(lamp, appliedDisableMaxxive.value)
      const coeffTable = appliedExceedGear.value ? clearCoeffExceed : clearCoeff
      const c = coeffTable[effectiveLamp] ?? 0.5
      if (c > bestLampCoeff) {
        bestLampCoeff = c
        bestLamp = lamp
      }
    }

    const grade = gradeFromScore(bestScore)
    const vf = calculateVFWithMode({ level, score: bestScore, grade, lamp: bestLamp }, appliedExceedGear.value)

    rows.push({
      chart_hash: chartHash,
      songId: mdbSong.mid,
      title: chart.title,
      diff,
      level,
      score: bestScore,
      grade,
      lamp: bestLamp,
      vf,
      timeAchieved: bestTimestamp,
    })
  }

  rows.sort((a, b) => b.vf - a.vf)
  best50.value = rows.slice(0, 50)
  totalVF.value = best50.value.reduce((s, r) => s + r.vf, 0)
  if (skippedCount > 0) {
    error.value = `Skipped ${skippedCount} chart(s) (no match in mdb by title+artist).`
  }
}

async function loadData() {
  skippedCount = 0
  error.value = ""
  best50.value = []
  totalVF.value = 0
  failedJackets.value = new Set()
  generatedImageUrl.value = ""

  if (!userId.value) {
    error.value = "User ID required"
    return
  }

  activePlayerName.value = userId.value
  appliedExceedGear.value = pendingExceedGear.value
  appliedDisableMaxxive.value = pendingDisableMaxxive.value
  loading.value = true

  try {
    const res = await fetch(
      `https://kamai.tachi.ac/api/v1/users/${userId.value}/games/sdvx/pbs/all`
    )
    const { body, description } = await res.json()
    msg = description
    const { pbs, charts } = body

    const chartMap = Object.fromEntries(
      charts.map(c => [c.chartID, c])
    )

    const rows = []

    for (const pb of pbs) {
      const chart = chartMap[pb.chartID]
      if (!chart) continue

      const mdbSong = mdb.value[String(chart.data.inGameID)]
      if (!mdbSong) {
        skippedCount += 1
        continue
      }

      const level = roundLevelForMode(getLevel(chart, mdbSong), appliedExceedGear.value)

      const vf = calculateVFWithMode({
        level,
        score: pb.scoreData.score,
        grade: pb.scoreData.grade,
        lamp: pb.scoreData.lamp
      }, appliedExceedGear.value)

      rows.push({
        chartID: pb.chartID,
        songId: chart.data?.inGameID ?? chart.data?.songID ?? null,
        title: chart.song?.title ?? mdbSong.title,
        diff: chart.difficulty,
        level,
        score: pb.scoreData.score,
        grade: pb.scoreData.grade,
        lamp: pb.scoreData.lamp,
        vf,
        timeAchieved: pb.timeAchieved ?? null,
      })
    }

    rows.sort((a, b) => b.vf - a.vf)

    best50.value = rows.slice(0, 50)
    totalVF.value = best50.value.reduce((s, r) => s + r.vf, 0)
  } catch (e) {
    msg += String(e)
  } finally {
    if (skippedCount != 0) msg += " Skipped " + skippedCount + " plays due to mismatch (konaste exclusive, deleted songs etc.)."
    error.value = msg
    loading.value = false
  }
}
</script>

<style scoped>
.app {
  --bg: #0d0e11;
  --surface: #16171c;
  --surface-raised: #1b1c22;
  --border: #2a2c34;
  --text: #e3e4e8;
  --text-muted: #82869a;
  --accent: #5aa9a3;
  --accent-text: #0d0e11;
  --danger: #cf7a7a;
  --danger-bg: rgba(207, 122, 122, 0.08);
  --radius: 3px;

  min-height: 100vh;
  background: var(--bg);
  color: var(--text);
  font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Helvetica, Arial, sans-serif;
  padding: 2.5rem 1rem 4rem;
}

.mono {
  font-family: ui-monospace, "SF Mono", "Cascadia Code", Menlo, Consolas, monospace;
}

.container {
  max-width: 900px;
  width: 100%;
  margin: 0 auto;
  display: flex;
  flex-direction: column;
  align-items: stretch;
  min-width: 0; /* allow flex child to shrink so table scroll works on mobile */
}

.header {
  margin-bottom: 1.75rem;
  padding-bottom: 1.25rem;
  border-bottom: 1px solid var(--border);
}

.title {
  font-size: 1.35rem;
  font-weight: 600;
  letter-spacing: 0;
  margin: 0;
  color: var(--text);
}

.card {
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: var(--radius);
  padding: 1rem 1.25rem;
}

.input-card {
  margin-bottom: 1.25rem;
}

.input-row {
  display: flex;
  gap: 0.6rem;
  align-items: center;
  flex-wrap: wrap;
}

.checkbox-row {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  margin-top: 0.75rem;
  color: var(--text-muted);
  font-size: 0.875rem;
  cursor: pointer;
  user-select: none;
}

.checkbox-row input[type="checkbox"] {
  width: 15px;
  height: 15px;
  accent-color: var(--accent);
  cursor: pointer;
}

.file-input {
  position: absolute;
  width: 0;
  height: 0;
  opacity: 0;
  pointer-events: none;
}

.input {
  padding: 0.55rem 0.75rem;
  width: 200px;
  max-width: 100%;
  border: 1px solid var(--border);
  border-radius: var(--radius);
  background: var(--bg);
  color: var(--text);
  font-size: 0.9rem;
  transition: border-color 0.15s;
}

.input::placeholder {
  color: var(--text-muted);
}

.input:focus {
  outline: none;
  border-color: var(--accent);
}

.or {
  color: var(--text-muted);
  font-size: 0.825rem;
}

.btn {
  padding: 0.55rem 1rem;
  border: 1px solid transparent;
  border-radius: var(--radius);
  font-size: 0.875rem;
  font-weight: 600;
  cursor: pointer;
  transition: background-color 0.15s, border-color 0.15s;
}

.btn:disabled {
  opacity: 0.45;
  cursor: not-allowed;
}

.btn-primary {
  background: var(--accent);
  color: var(--accent-text);
}

.btn-primary:not(:disabled):hover {
  background: #6bb8b2;
}

.btn-secondary {
  background: transparent;
  color: var(--text);
  border-color: var(--border);
}

.btn-secondary:not(:disabled):hover {
  border-color: var(--text-muted);
}

.player-select {
  margin-bottom: 1.25rem;
}

.player-select-label {
  margin: 0 0 0.75rem 0;
  font-size: 0.875rem;
  color: var(--text-muted);
}

.player-select-row {
  display: flex;
  gap: 0.6rem;
  align-items: center;
}

.select {
  padding: 0.5rem 0.65rem;
  border-radius: var(--radius);
  border: 1px solid var(--border);
  background: var(--bg);
  color: var(--text);
  font-size: 0.875rem;
  min-width: 160px;
}

.error {
  color: var(--danger);
  border-color: rgba(207, 122, 122, 0.3);
  background: var(--danger-bg);
  font-size: 0.875rem;
}

.results {
  margin-top: 1rem;
  flex: 1;
  width: 100%;
  min-width: 0; /* allow shrink so table-card doesn't overflow on mobile */
}

.results-header {
  margin-bottom: 1rem;
  display: flex;
  align-items: center;
  gap: 0.75rem;
  overflow-x: auto;
}

.export-csv-btn {
  flex-shrink: 0;
}

.vf-display {
  margin: 0;
  font-size: 1rem;
  font-weight: 500;
  color: var(--text-muted);
  gap: 0.5rem;
  white-space: nowrap;
}

.vf-value {
  font-family: ui-monospace, "SF Mono", "Cascadia Code", Menlo, Consolas, monospace;
  color: var(--accent);
  font-size: 1.35rem;
  font-weight: 600;
}

.generated-image-wrap {
  width: 100%;
  overflow-x: auto;
}

.generated-image {
  display: block;
  max-width: 100%;
  height: auto;
  border: 1px solid var(--border);
  border-radius: var(--radius);
}

.table-card {
  width: 100%;
  max-width: 100%;
  overflow-x: auto;
  overflow-y: hidden;
  padding: 0;
  -webkit-overflow-scrolling: touch; /* smooth scroll on iOS */
}

.b50-table {
  width: 100%;
  border-collapse: collapse;
  min-width: 700px;
  font-size: 0.875rem;
}

.b50-table th {
  text-align: left;
  padding: 0.7rem 1rem;
  background: var(--surface-raised);
  color: var(--text-muted);
  font-weight: 600;
  font-size: 0.75rem;
  text-transform: uppercase;
  letter-spacing: 0.03em;
  border-bottom: 1px solid var(--border);
}

.b50-table td {
  padding: 0.55rem 1rem;
  border-bottom: 1px solid var(--border);
  vertical-align: middle;
}

.b50-table .row:hover {
  background: var(--surface-raised);
}

.col-rank {
  width: 2.5rem;
  text-align: center;
  color: var(--text-muted);
  font-family: ui-monospace, "SF Mono", "Cascadia Code", Menlo, Consolas, monospace;
  font-size: 0.8rem;
}

.col-song {
  min-width: 200px;
}

.song-cell {
  display: flex;
  align-items: center;
  gap: 0.75rem;
}

.jacket-wrap {
  flex-shrink: 0;
  width: 40px;
  aspect-ratio: 1 / 1;
  border-radius: var(--radius);
  overflow: hidden;
  border: 1px solid var(--border);
  background: var(--bg);
}

.jacket {
  width: 100%;
  height: 100%;
  object-fit: cover;
  display: block;
}

.jacket-placeholder {
  width: 100%;
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--surface-raised);
  color: var(--text-muted);
  font-size: 1.1rem;
}

.jacket-placeholder-icon {
  opacity: 0.6;
}

.song-title {
  font-weight: 500;
  color: var(--text);
  line-height: 1.3;
}

.col-diff,
.col-level,
.col-score,
.col-grade,
.col-vf {
  text-align: center;
  color: var(--text);
}

.col-level,
.col-score,
.col-vf {
  font-family: ui-monospace, "SF Mono", "Cascadia Code", Menlo, Consolas, monospace;
}

.col-clear {
  font-size: 0.8rem;
  color: var(--text-muted);
  max-width: 140px;
}

.diff-badge {
  display: inline-block;
  padding: 0.15rem 0.45rem;
  border-radius: var(--radius);
  font-size: 0.7rem;
  font-weight: 700;
  letter-spacing: 0.02em;
  border: 1px solid transparent;
}

.diff-nov {
  background: rgba(214, 116, 214, 0.12);
  color: #d68cd6;
  border-color: rgba(214, 116, 214, 0.25);
}

.diff-adv {
  background: rgba(214, 168, 84, 0.12);
  color: #d6ac6e;
  border-color: rgba(214, 168, 84, 0.25);
}

.diff-exh {
  background: rgba(214, 100, 100, 0.12);
  color: #d68080;
  border-color: rgba(214, 100, 100, 0.25);
}

.diff-mxm {
  background: rgba(160, 160, 160, 0.12);
  color: #a8a8a8;
  border-color: rgba(160, 160, 160, 0.25);
}

.diff-inf {
  background: rgba(160, 110, 214, 0.12);
  color: #b28ce0;
  border-color: rgba(160, 110, 214, 0.25);
}

.diff-grv {
  background: rgba(214, 140, 80, 0.12);
  color: #d69e6e;
  border-color: rgba(214, 140, 80, 0.25);
}

.diff-hvn {
  background: rgba(90, 180, 200, 0.12);
  color: #7ec0d6;
  border-color: rgba(90, 180, 200, 0.25);
}

.diff-vvd {
  background: rgba(214, 110, 160, 0.12);
  color: #d68cb8;
  border-color: rgba(214, 110, 160, 0.25);
}

.diff-xcd {
  background: rgba(90, 130, 214, 0.12);
  color: #7ea2d6;
  border-color: rgba(90, 130, 214, 0.25);
}

.diff-ult {
  background: rgba(200, 180, 90, 0.12);
  color: #d6c47e;
  border-color: rgba(200, 180, 90, 0.25);
}

.grade-badge {
  display: inline-block;
  padding: 0.15rem 0.4rem;
  border-radius: var(--radius);
  font-size: 0.75rem;
  font-weight: 700;
  font-family: ui-monospace, "SF Mono", "Cascadia Code", Menlo, Consolas, monospace;
}

.grade-puc    { color: #d6b85a; }
.grade-s      { color: #d6ac6e; }
.grade-aaaplus,
.grade-aaa    { color: #7ea2d6; }
.grade-aaplus,
.grade-aa     { color: #7ec08c; }
.grade-aplus,
.grade-a      { color: var(--text-muted); }
.grade-b      { color: #b8987a; }
.grade-c,
.grade-d      { color: var(--text-muted); }
</style>