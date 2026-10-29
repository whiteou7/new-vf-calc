<template>
  <div class="app">
    <div class="container">
      <AppHeader />
      <InputCard />
      <PlayerSelect v-if="playerSelect.visible" />
      <ErrorCard v-if="error" :message="error" />
      <ResultsSection v-if="best50.length" />
    </div>
  </div>
</template>

<script setup>
import { onMounted } from "vue"
import AppHeader from "@/components/AppHeader.vue"
import ErrorCard from "@/components/ErrorCard.vue"
import InputCard from "@/components/InputCard.vue"
import PlayerSelect from "@/components/PlayerSelect.vue"
import ResultsSection from "@/components/ResultsSection.vue"
import { useMapsDbImport } from "@/composables/useMapsDbImport.js"
import { useMusicDb } from "@/composables/useMusicDb.js"
import { useResults } from "@/composables/useResults.js"

const { error, best50 } = useResults()
const { playerSelect } = useMapsDbImport()
const { loadMusicDb } = useMusicDb()

onMounted(loadMusicDb)
</script>

<style scoped>
.app {
  min-height: 100vh;
  background: var(--bg);
  color: var(--text);
  font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Helvetica, Arial, sans-serif;
  padding: 2.5rem 1rem 4rem;
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
</style>
