<template>
  <span :class="['grade-badge', 'grade-' + gradeClass(grade)]">{{ grade }}</span>
</template>

<script setup>
import { gradeClass } from "@/utils/format.js"

defineProps({ grade: { type: String, default: "" } })
</script>

<style scoped>
.grade-badge {
  display: inline-block;
  padding: 0.15rem 0.4rem;
  border-radius: var(--radius);
  font-size: 0.75rem;
  font-weight: 700;
  font-family: var(--font-mono);
}

.grade-puc    { color: #d6b85a; }
.grade-s      { color: #d6ac6e; }
.grade-aaaplus,
.grade-aaa    { color: #7ea2d6; }
.grade-aaplus,
.grade-aa     { color: #7ec08c; }
.grade-aplus,
.grade-a      { color: var(--text-muted); }
.grade-b      { color: #b8987a; }
.grade-c,
.grade-d      { color: var(--text-muted); }
</style>
