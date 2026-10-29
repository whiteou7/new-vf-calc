<template>
  <div class="song-cell">
    <div class="jacket-wrap">
      <img
        v-if="songId && !jacketFailed(songId)"
        :src="jacketUrl(songId)"
        :alt="title"
        class="jacket"
        loading="lazy"
        @error="onJacketError"
      />
      <div v-show="!songId || jacketFailed(songId)" class="jacket jacket-placeholder">
        <span class="jacket-placeholder-icon">♪</span>
      </div>
    </div>
    <span class="song-title">{{ title }}</span>
  </div>
</template>

<script setup>
import { jacketUrl, useJackets } from "@/composables/useJackets.js"

defineProps({
  songId: { type: [String, Number], default: null },
  title: { type: String, default: "" },
})

const { onJacketError, jacketFailed } = useJackets()
</script>

<style scoped>
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
</style>
