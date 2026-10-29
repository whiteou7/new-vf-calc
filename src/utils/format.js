export function formatScore(score) {
  const n = Number(score)
  if (n >= 10_000_000) return "10,000,000"
  return n.toLocaleString()
}

export function gradeClass(grade) {
  return (grade || "").toLowerCase().replace("+", "plus")
}
