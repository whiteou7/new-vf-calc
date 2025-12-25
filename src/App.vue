<template>
  <div class="container">
    <h1>SDVX (New) B50 Calculator</h1>

    <div class="input-row">
      <input
        v-model="userId"
        placeholder="Enter Tachi Username"
      />
      <button @click="loadData" :disabled="loading">
        {{ loading ? "Loading..." : "Calculate" }}
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
          <tr v-for="(row, i) in best50" :key="row.chartID">
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
import { ref } from "vue"
import mdb from "@/assets/mdb.json"

const userId = ref("")
const loading = ref(false)
const error = ref("")
const best50 = ref([])
const totalVF = ref(0)
let msg = ""
let skippedCount = 0

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

async function loadData() {
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

      const mdbSong = mdb[String(chart.data.inGameID)]
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
  margin-bottom: 20px;
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
