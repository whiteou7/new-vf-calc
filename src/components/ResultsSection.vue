<template>
  <section class="results">
    <ResultsHeader />
    <GeneratedImage v-if="generatedImageUrl" :src="generatedImageUrl" />
    <B50Table :rows="best50" />
  </section>
</template>

<script setup>
import B50Table from "@/components/B50Table.vue"
import GeneratedImage from "@/components/GeneratedImage.vue"
import ResultsHeader from "@/components/ResultsHeader.vue"
import { useResults } from "@/composables/useResults.js"

const { best50, generatedImageUrl } = useResults()
</script>

<style scoped>
.results {
  margin-top: 1rem;
  flex: 1;
  width: 100%;
  min-width: 0; /* allow shrink so table-card doesn't overflow on mobile */
}
</style>
