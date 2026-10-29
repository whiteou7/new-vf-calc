<template>
  <div class="player-select card">
    <p class="player-select-label">More than one player in database. Choose a player:</p>
    <div class="player-select-row">
      <select v-model="playerSelect.selected" class="select">
        <option value="" disabled>Select player</option>
        <option v-for="name in playerSelect.players" :key="name ?? '__null__'" :value="name">
          {{ name ?? "(no user)" }}
        </option>
      </select>
      <button class="btn btn-primary" @click="confirmPlayerAndCalculate" :disabled="!playerSelect.selected">
        Calculate VF
      </button>
    </div>
  </div>
</template>

<script setup>
import { useMapsDbImport } from "@/composables/useMapsDbImport.js"

const { playerSelect, confirmPlayerAndCalculate } = useMapsDbImport()
</script>

<style scoped>
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
</style>
