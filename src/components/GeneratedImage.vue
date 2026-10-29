<template>
  <div class="generated-image-wrap">
    <img :src="src" alt="B50 result card" class="generated-image" />
  </div>
</template>

<script setup>
defineProps({ src: { type: String, required: true } })
</script>

<style scoped>
.generated-image-wrap {
  padding-bottom: 16px;
}

.generated-image {
  display: block;
  max-width: 100%;
  height: auto;
  border: 1px solid var(--border);
  border-radius: var(--radius);
}
</style>
