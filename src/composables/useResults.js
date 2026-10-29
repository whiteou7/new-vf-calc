import { ref } from "vue"
import { normalizeLampForScoring } from "@/scoring.js"
import { useJackets } from "./useJackets.js"

const loading = ref(false)
const error = ref("")
const best50 = ref([])
const totalVF = ref(0)
const generatedImageUrl = ref("")
const activePlayerName = ref("")

// options as ticked in the UI vs. as used for the results currently shown
const pendingExceedGear = ref(false)
const pendingDisableMaxxive = ref(false)
const appliedExceedGear = ref(false)
const appliedDisableMaxxive = ref(false)

export function useResults() {
  const { resetJackets } = useJackets()

  function resetResults() {
    error.value = ""
    best50.value = []
    totalVF.value = 0
    generatedImageUrl.value = ""
    resetJackets()
  }

  function applyOptions(playerName) {
    activePlayerName.value = playerName
    appliedExceedGear.value = pendingExceedGear.value
    appliedDisableMaxxive.value = pendingDisableMaxxive.value
  }

  function setRows(rows) {
    rows.sort((a, b) => b.vf - a.vf)
    best50.value = rows.slice(0, 50)
    totalVF.value = best50.value.reduce((s, r) => s + r.vf, 0)
  }

  function effectiveLamp(lamp) {
    return normalizeLampForScoring(lamp, appliedDisableMaxxive.value)
  }

  return {
    loading,
    error,
    best50,
    totalVF,
    generatedImageUrl,
    activePlayerName,
    pendingExceedGear,
    pendingDisableMaxxive,
    appliedExceedGear,
    appliedDisableMaxxive,
    resetResults,
    applyOptions,
    setRows,
    effectiveLamp,
  }
}
