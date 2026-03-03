<template>
  <div class="container">
    <h1>SDVX (New) B50 Calculator</h1>

    <div class="input-row">
      <input
        v-model="userId"
        placeholder="Enter Tachi Username"
      />
      <button @click="loadData" :disabled="loading || !mdbReady">
        {{ loading ? "Loading..." : !mdbReady ? "Loading database..." : "Calculate" }}
      </button>
      <span class="or">or</span>
      <input
        ref="dbFileInput"
        type="file"
        accept=".db,application/x-sqlite3"
        style="display: none"
        @change="onDbFileSelected"
      />
      <button type="button" :disabled="loading || !mdbReady" @click="$refs.dbFileInput?.click()">
        Upload your maps.db
      </button>
    </div>

    <div v-if="playerSelect.visible" class="player-select">
      <p>More than one player in database. Choose a player:</p>
      <select v-model="playerSelect.selected" class="player-select-input">
        <option value="" disabled>Select player</option>
        <option
          v-for="name in playerSelect.players"
          :key="name ?? '__null__'"
          :value="name"
        >
          {{ name ?? "(no user)" }}
        </option>
      </select>
      <button @click="confirmPlayerAndCalculate" :disabled="!playerSelect.selected">
        Calculate VF
      </button>
    </div>

    <div v-if="error" class="error">{{ error }}</div>

    <div v-if="best50.length">
      <h2>New VF: {{ totalVF.toFixed(3) }}</h2>

      <table>
        <thead>
          <tr>
            <th>#</th>
            <th>Song</th>
            <th>Diff</th>
            <th>Level</th>
            <th>Score</th>
            <th>Grade</th>
            <th>Clear</th>
            <th>VF</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="(row, i) in best50" :key="row.chartID ?? row.chart_hash ?? i">
            <td>{{ i + 1 }}</td>
            <td>{{ row.title }}</td>
            <td>{{ row.diff.toUpperCase() }}</td>
            <td>{{ row.level }}</td>
            <td>{{ row.score }}</td>
            <td>{{ row.grade }}</td>
            <td>{{ row.lamp }}</td>
            <td>{{ row.vf.toFixed(3) }}</td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from "vue"
import initSqlJs from "sql.js"
import musicDbUrl from "@/assets/music_db.xml?url"

const mdb = ref({})
const mdbReady = ref(false)

const userId = ref("")
const loading = ref(false)
const error = ref("")
const best50 = ref([])
const totalVF = ref(0)
let msg = ""
let skippedCount = 0

const playerSelect = ref({
  visible: false,
  players: [],
  selected: "",
  dbBuffer: null
})

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

function lampFromScore(score, miss, gaugeType) {
  const s = Number(score) || 0
  const noMiss = miss == null || Number(miss) === 0
  const gt = Number(gaugeType) ?? 0

  if (s >= 10_000_000 && noMiss) return "PERFECT ULTIMATE CHAIN"
  if (noMiss) return "ULTIMATE CHAIN"
  if (gt === 1) return "EXCESSIVE CLEAR" // HARD clear
  if (gt === 0) return "CLEAR" // NORMAL clear
  return "FAILED" // PLAYED
}

const gradeCoeff = {
  "PUC": 1.05,
  "S": 1.05,
  "AAA+": 1.02,
  "AAA": 1.0,
  "AA+": 0.97,
  "AA": 0.94,
  "A+": 0.91,
  "A": 0.88,
  "B": 0.85,
  "C": 0.82,
  "D": 0.8
}

const clearCoeff = {
  "PERFECT ULTIMATE CHAIN": 1.10,
  "ULTIMATE CHAIN": 1.06,
  "MAXXIVE CLEAR": 1.04,
  "EXCESSIVE CLEAR": 1.02,
  "CLEAR": 1.0,
  "FAILED": 0.5
}

function getLevel(chart, chartMeta) {
  if (!chartMeta) return 0

  const diffIndexMap = {
    nov: 0,
    adv: 1,
    exh: 2,
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

function calculateVF({ level, score, grade, lamp }) {
  const g = gradeCoeff[grade] ?? 1
  const c = clearCoeff[lamp] ?? 1

  const base =
    level *
    (score / 10_000_000) *
    g *
    c *
    20

  return Math.floor(base) * 0.001
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
  playerSelect.value = { visible: false, players: [], selected: "", dbBuffer: null }
  loading.value = true
  error.value = ""
  best50.value = []
  totalVF.value = 0
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
    SELECT s.chart_hash, s.score, s.miss, s.gauge_type
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
      gauge_type: row.gauge_type
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

    const level = getLevelFromMdb(mdbSong, chart.diff_index)
    const diff = (chart.diff_shortname || "NOV").toUpperCase()

    // PB = best score + best lamp (from any play on this chart)
    const bestScore = Math.max(...plays.map((p) => p.score))
    let bestLamp = "FAILED"
    let bestLampCoeff = clearCoeff["FAILED"]
    for (const p of plays) {
      const lamp = lampFromScore(p.score, p.miss, p.gauge_type)
      const c = clearCoeff[lamp] ?? 0.5
      if (c > bestLampCoeff) {
        bestLampCoeff = c
        bestLamp = lamp
      }
    }

    const grade = gradeFromScore(bestScore)
    const vf = calculateVF({ level, score: bestScore, grade, lamp: bestLamp })

    rows.push({
      chart_hash: chartHash,
      title: mdbSong.title,
      diff,
      level,
      score: bestScore,
      grade,
      lamp: bestLamp,
      vf
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

  if (!userId.value) {
    error.value = "User ID required"
    return
  }

  loading.value = true

  try {
    const res = await fetch(
      `https://kamai.tachi.ac/api/v1/users/${userId.value}/games/sdvx/Single/pbs/all`
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

      const level = getLevel(chart, mdbSong)

      const vf = calculateVF({
        level,
        score: pb.scoreData.score,
        grade: pb.scoreData.grade,
        lamp: pb.scoreData.lamp
      })

      rows.push({
        chartID: pb.chartID,
        title: mdbSong.title,
        diff: chart.difficulty,
        level,
        score: pb.scoreData.score,
        grade: pb.scoreData.grade,
        lamp: pb.scoreData.lamp,
        vf
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
.container {
  margin: auto;
  padding: 20px;
}

.input-row {
  display: flex;
  gap: 10px;
  align-items: center;
  margin-bottom: 20px;
  flex-wrap: wrap;
}

.or {
  color: #666;
  font-weight: 500;
}

.player-select {
  margin-bottom: 16px;
  padding: 12px;
  background: #f5f5f5;
  border-radius: 8px;
}

.player-select p {
  margin: 0 0 8px 0;
}

.player-select-input {
  margin-right: 8px;
  padding: 6px 8px;
}

input {
  padding: 6px;
  width: 200px;
}

button {
  padding: 6px 12px;
}

table {
  width: 100%;
  border-collapse: collapse;
}

th, td {
  border: 1px solid #ddd;
  padding: 6px;
  text-align: center;
}

.error {
  color: red;
  margin-bottom: 10px;
}
</style>
