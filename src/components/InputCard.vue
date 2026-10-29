<template>
  <div class="input-card">
    <div class="input-row">
      <input v-model="userId" placeholder="Enter Tachi Username" class="input" />
      <button class="btn btn-primary" @click="loadData" :disabled="loading || !mdbReady">
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
        @click="dbFileInput?.click()"
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
</template>

<script setup>
import { ref } from "vue"
import { useMapsDbImport } from "@/composables/useMapsDbImport.js"
import { useMusicDb } from "@/composables/useMusicDb.js"
import { useResults } from "@/composables/useResults.js"
import { useTachiImport } from "@/composables/useTachiImport.js"

const dbFileInput = ref(null)
const { loading, pendingExceedGear, pendingDisableMaxxive } = useResults()
const { mdbReady } = useMusicDb()
const { userId, loadData } = useTachiImport()
const { onDbFileSelected } = useMapsDbImport()
</script>

<style scoped>
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

.or {
  color: var(--text-muted);
  font-size: 0.825rem;
}
</style>
