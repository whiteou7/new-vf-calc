<template>
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
        <tr v-for="(row, i) in rows" :key="row.chartID ?? row.chart_hash ?? i" class="row">
          <td class="col-rank">{{ i + 1 }}</td>
          <td class="col-song"><SongCell :song-id="row.songId" :title="row.title" /></td>
          <td class="col-diff"><DiffBadge :diff="row.diff" /></td>
          <td class="col-level">{{ row.level }}</td>
          <td class="col-score">{{ formatScore(row.score) }}</td>
          <td class="col-grade"><GradeBadge :grade="row.grade" /></td>
          <td class="col-clear">{{ effectiveLamp(row.lamp) }}</td>
          <td class="col-vf"><strong>{{ row.vf.toFixed(3) }}</strong></td>
        </tr>
      </tbody>
    </table>
  </div>
</template>

<script setup>
import DiffBadge from "@/components/DiffBadge.vue"
import GradeBadge from "@/components/GradeBadge.vue"
import SongCell from "@/components/SongCell.vue"
import { useResults } from "@/composables/useResults.js"
import { formatScore } from "@/utils/format.js"

defineProps({ rows: { type: Array, required: true } })

const { effectiveLamp } = useResults()
</script>

<style scoped>
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
  font-family: var(--font-mono);
  font-size: 0.8rem;
}

.col-song {
  min-width: 200px;
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
  font-family: var(--font-mono);
}

.col-clear {
  font-size: 0.8rem;
  color: var(--text-muted);
  max-width: 140px;
}
</style>
