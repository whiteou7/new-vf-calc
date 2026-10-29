// chatgpt wrote ts shit

export function normalizeTitleArtist(str) {
  return (str ?? "").toString().trim().toLowerCase()
}

function levenshtein(a, b) {
  if (a === b) return 0
  if (!a.length) return b.length
  if (!b.length) return a.length

  const matrix = Array.from({ length: b.length + 1 }, () => new Array(a.length + 1))

  for (let i = 0; i <= a.length; i++) matrix[0][i] = i
  for (let j = 0; j <= b.length; j++) matrix[j][0] = j

  for (let j = 1; j <= b.length; j++) {
    for (let i = 1; i <= a.length; i++) {
      const cost = a[i - 1] === b[j - 1] ? 0 : 1
      matrix[j][i] = Math.min(
        matrix[j - 1][i] + 1,
        matrix[j][i - 1] + 1,
        matrix[j - 1][i - 1] + cost
      )
    }
  }

  return matrix[b.length][a.length]
}

function similarity(a, b) {
  if (!a.length && !b.length) return 1
  const maxLen = Math.max(a.length, b.length)
  return 1 - levenshtein(a, b) / maxLen
}

const THRESHOLD = 0.75

export function findFuzzyMatch(title, artist, map) {
  const needle = normalizeTitleArtist(title) + " " + normalizeTitleArtist(artist)

  let bestMatch = null
  let bestScore = 0

  for (const entry of map.values()) {
    const score = similarity(
      needle,
      normalizeTitleArtist(entry.title) + " " + normalizeTitleArtist(entry.artist)
    )
    if (score > bestScore) {
      bestScore = score
      bestMatch = entry
    }
  }

  return bestScore >= THRESHOLD ? bestMatch : null
}
