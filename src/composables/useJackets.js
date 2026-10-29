import { ref } from "vue"

const JACKET_BASE = "https://sdvx.dev/api/cover"

const failedJackets = ref(new Set())

export function jacketUrl(songId) {
  if (!songId) return ""
  return `${JACKET_BASE}/${songId}_novice.webp`
}

export function useJackets() {
  function onJacketError(e) {
    const img = e.target
    const src = img?.src
    if (src) {
      const m = src.match(/\/([^/]+)\/NOV\.png$/)
      if (m?.[1]) failedJackets.value.add(m[1])
      failedJackets.value = new Set(failedJackets.value)
    }
    img?.style?.setProperty("display", "none")
  }

  function jacketFailed(songId) {
    return songId && failedJackets.value.has(String(songId))
  }

  function resetJackets() {
    failedJackets.value = new Set()
  }

  return { onJacketError, jacketFailed, resetJackets }
}
