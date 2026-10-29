<template>
  <span :class="['diff-badge', 'diff-' + (diff || '').toLowerCase()]">{{ (diff || '').toUpperCase() }}</span>
</template>

<script setup>
defineProps({ diff: { type: String, default: "" } })
</script>

<style scoped>
.diff-badge {
  display: inline-block;
  padding: 0.15rem 0.45rem;
  border-radius: var(--radius);
  font-size: 0.7rem;
  font-weight: 700;
  letter-spacing: 0.02em;
  border: 1px solid transparent;
}

.diff-nov {
  background: rgba(214, 116, 214, 0.12);
  color: #d68cd6;
  border-color: rgba(214, 116, 214, 0.25);
}

.diff-adv {
  background: rgba(214, 168, 84, 0.12);
  color: #d6ac6e;
  border-color: rgba(214, 168, 84, 0.25);
}

.diff-exh {
  background: rgba(214, 100, 100, 0.12);
  color: #d68080;
  border-color: rgba(214, 100, 100, 0.25);
}

.diff-mxm {
  background: rgba(160, 160, 160, 0.12);
  color: #a8a8a8;
  border-color: rgba(160, 160, 160, 0.25);
}

.diff-inf {
  background: rgba(160, 110, 214, 0.12);
  color: #b28ce0;
  border-color: rgba(160, 110, 214, 0.25);
}

.diff-grv {
  background: rgba(214, 140, 80, 0.12);
  color: #d69e6e;
  border-color: rgba(214, 140, 80, 0.25);
}

.diff-hvn {
  background: rgba(90, 180, 200, 0.12);
  color: #7ec0d6;
  border-color: rgba(90, 180, 200, 0.25);
}

.diff-vvd {
  background: rgba(214, 110, 160, 0.12);
  color: #d68cb8;
  border-color: rgba(214, 110, 160, 0.25);
}

.diff-xcd {
  background: rgba(90, 130, 214, 0.12);
  color: #7ea2d6;
  border-color: rgba(90, 130, 214, 0.25);
}

.diff-ult {
  background: rgba(200, 180, 90, 0.12);
  color: #d6c47e;
  border-color: rgba(200, 180, 90, 0.25);
}
</style>
