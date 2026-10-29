import { ref } from "vue"
import { buildTachiRows, fetchTachiPbs } from "@/utils/tachi.js"
import { useMusicDb } from "./useMusicDb.js"
import { useResults } from "./useResults.js"

const userId = ref("")

export function useTachiImport() {
  const { mdb } = useMusicDb()
  const { loading, error, appliedExceedGear, appliedDisableMaxxive, resetResults, applyOptions, setRows } = useResults()

  async function loadData() {
    resetResults()

    if (!userId.value) {
      error.value = "User ID required"
      return
    }

    applyOptions(userId.value)
    loading.value = true

    let message = ""
    let skipped = 0
    try {
      const { description, pbs, charts } = await fetchTachiPbs(userId.value)
      message = description
      const built = buildTachiRows(pbs, charts, mdb.value, {
        exceed: appliedExceedGear.value,
        disableMaxxive: appliedDisableMaxxive.value,
      })
      skipped = built.skipped
      setRows(built.rows)
    } catch (e) {
      message += String(e)
    } finally {
      if (skipped != 0) message += " Skipped " + skipped + " plays due to mismatch (konaste exclusive, deleted songs etc.)."
      error.value = message
      loading.value = false
    }
  }

  return { userId, loadData }
}
