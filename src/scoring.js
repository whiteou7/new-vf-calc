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
