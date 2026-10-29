<template>
  <div class="results-header card">
    <h2 class="vf-display">
      {{ appliedExceedGear ? "Exceed Gear VF:" : "Nabla VF:" }}
      <span class="vf-value">{{ totalVF.toFixed(3) }}</span>
    </h2>
    <button type="button" class="btn btn-secondary export-csv-btn" @click="exportToCsv(best50, effectiveLamp)">
      Export to CSV
    </button>
    <button type="button" class="btn btn-secondary export-csv-btn" @click="generateImage" :disabled="generatingImage">
      {{ generatingImage ? "Generating… might take a while" : "Generate Image" }}
    </button>
  </div>
</template>

<script setup>
import { useImageGenerator } from "@/composables/useImageGenerator.js"
import { useResults } from "@/composables/useResults.js"
import { exportToCsv } from "@/utils/csv.js"

const { best50, totalVF, appliedExceedGear, effectiveLamp } = useResults()
const { generatingImage, generateImage } = useImageGenerator()
</script>

<style scoped>
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
  font-family: var(--font-mono);
  color: var(--accent);
  font-size: 1.35rem;
  font-weight: 600;
}
</style>
