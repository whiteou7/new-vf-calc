<template>
  <div class="error card">{{ message }}</div>
</template>

<script setup>
defineProps({ message: { type: String, required: true } })
</script>

<style scoped>
.error {
  color: var(--danger);
  border-color: rgba(207, 122, 122, 0.3);
  background: var(--danger-bg);
  font-size: 0.875rem;
}
</style>
