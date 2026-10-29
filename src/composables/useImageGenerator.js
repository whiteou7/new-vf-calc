import { ref } from "vue"
import { useResults } from "./useResults.js"

const BACKEND_URL = "https://b50-api.whiteou7.id.vn"

const generatingImage = ref(false)

export function useImageGenerator() {
  const { error, best50, totalVF, appliedExceedGear, activePlayerName, generatedImageUrl, effectiveLamp } = useResults()

  async function generateImage() {
    generatingImage.value = true
    try {
      const payload = {
        username: activePlayerName.value || "Player",
        vf: totalVF.value,
        mode: appliedExceedGear.value ? "exceed" : "nabla",
        scores: best50.value.map((r) => ({
          title: r.title,
          diff: r.diff,
          level: r.level,
          score: r.score,
          grade: r.grade,
          lamp: effectiveLamp(r.lamp),
          vf: r.vf,
          songId: r.songId,
          timeAchieved: r.timeAchieved ?? null,
        })),
      }
      const res = await fetch(`${BACKEND_URL}/api/generate-b50`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      })
      if (!res.ok) {
        const err = await res.json().catch(() => ({ error: res.statusText }))
        throw new Error(err.error || res.statusText)
      }
      const blob = await res.blob()
      if (generatedImageUrl.value) URL.revokeObjectURL(generatedImageUrl.value)
      generatedImageUrl.value = URL.createObjectURL(blob)
    } catch (e) {
      error.value = "Image generation failed: " + (e?.message || String(e))
    } finally {
      generatingImage.value = false
    }
  }

  return { generatingImage, generateImage }
}
