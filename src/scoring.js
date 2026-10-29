export const gradeCoeff = {
  PUC: 1.05,
  S: 1.05,
  'AAA+': 1.02,
  AAA: 1.0,
  'AA+': 0.97,
  AA: 0.94,
  'A+': 0.91,
  A: 0.88,
  B: 0.85,
  C: 0.82,
  D: 0.8,
}

export const clearCoeff = {
  'PERFECT ULTIMATE CHAIN': 1.10,
  'ULTIMATE CHAIN': 1.06,
  'MAXXIVE CLEAR': 1.04,
  'EXCESSIVE CLEAR': 1.02,
  CLEAR: 1.0,
  FAILED: 0.5,
}

export const clearCoeffExceed = {
  ...clearCoeff,
  'ULTIMATE CHAIN': 1.05,
}

export function normalizeLampForScoring(lamp, disableMaxxive = false) {
  const normalized = typeof lamp === 'string' ? lamp.trim().toUpperCase() : ''
  if (disableMaxxive && normalized === 'MAXXIVE CLEAR') {
    return 'EXCESSIVE CLEAR'
  }
  return normalized || lamp || ''
}

export function calculateVF({ level, score, grade, lamp }, exceed = false, disableMaxxive = false) {
  const g = gradeCoeff[grade] ?? 1
  const effectiveLamp = normalizeLampForScoring(lamp, disableMaxxive)
  const c = (exceed ? clearCoeffExceed : clearCoeff)[effectiveLamp] ?? 1
  const lvl = exceed ? Math.trunc(level) : level

  const base = lvl * (score / 10_000_000) * g * c * 20

  return Math.floor(base) * 0.001
}

// Exceed Gear only had whole-number chart levels
export function roundLevelForMode(level, exceed) {
  return exceed ? Math.trunc(level) : level
}

export function calculateVFWithMode({ level, score, grade, lamp }, exceed, disableMaxxive) {
  return calculateVF({ level: roundLevelForMode(level, exceed), score, grade, lamp }, exceed, disableMaxxive)
}

export function gradeFromScore(score) {
  const s = Number(score) || 0
  if (s >= 10_000_000) return 'PUC'
  if (s >= 9_900_000) return 'S'
  if (s >= 9_800_000) return 'AAA+'
  if (s >= 9_700_000) return 'AAA'
  if (s >= 9_500_000) return 'AA+'
  if (s >= 9_300_000) return 'AA'
  if (s >= 9_000_000) return 'A+'
  if (s >= 8_700_000) return 'A'
  if (s >= 7_500_000) return 'B'
  if (s >= 6_500_000) return 'C'
  return 'D'
}

export function getLamp(score, miss, gaugeType, gauge) {
  const s = Number(score) || 0
  const noMiss = miss == null || Number(miss) === 0
  const gt = Number(gaugeType) ?? 0
  const g = Number(gauge) ?? 0

  if (s >= 10_000_000 && noMiss) return 'PERFECT ULTIMATE CHAIN'
  if (noMiss) return 'ULTIMATE CHAIN'
  if (gt === 1 && g > 0) return 'EXCESSIVE CLEAR'
  if (gt === 0 && g >= 0.7) return 'CLEAR'
  return 'FAILED'
}
