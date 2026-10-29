import { ref } from "vue"
import { buildMapsDbRows, inspectDb, openDb } from "@/utils/mapsDb.js"
import { useMusicDb } from "./useMusicDb.js"
import { useResults } from "./useResults.js"

const emptyPlayerSelect = () => ({ visible: false, players: [], selected: "", dbBuffer: null })

const playerSelect = ref(emptyPlayerSelect())

export function useMapsDbImport() {
  const { mdbIndex } = useMusicDb()
  const { loading, error, appliedExceedGear, appliedDisableMaxxive, resetResults, applyOptions, setRows } = useResults()

  function calculate(db, userName, tables) {
    const { rows, skipped } = buildMapsDbRows(db, userName, tables, mdbIndex.value, {
      exceed: appliedExceedGear.value,
      disableMaxxive: appliedDisableMaxxive.value,
    })
    setRows(rows)
    if (skipped > 0) {
      error.value = `Skipped ${skipped} chart(s) (no match in mdb by title+artist).`
    }
  }

  async function onDbFileSelected(ev) {
    const file = ev.target?.files?.[0]
    if (!file) return
    ev.target.value = ""
    resetResults()
    loading.value = true
    try {
      const buffer = await file.arrayBuffer()
      const db = await openDb(buffer)
      const info = inspectDb(db)
      if (info.error) {
        error.value = info.error
        return
      }

      const { players, scoresTable, chartsTable } = info
      if (players.length === 1) {
        applyOptions(players[0] ?? "")
        calculate(db, players[0], { scoresTable, chartsTable })
      } else {
        playerSelect.value = { visible: true, players, selected: "", dbBuffer: buffer, scoresTable, chartsTable }
      }
      db.close()
    } catch (e) {
      error.value = "Failed to read maps.db: " + (e?.message || String(e))
    } finally {
      loading.value = false
    }
  }

  async function confirmPlayerAndCalculate() {
    const { selected, dbBuffer, scoresTable, chartsTable } = playerSelect.value
    if (!selected || !dbBuffer) return
    applyOptions(selected)
    playerSelect.value = emptyPlayerSelect()
    loading.value = true
    resetResults()
    try {
      const db = await openDb(dbBuffer)
      calculate(db, selected, { scoresTable, chartsTable })
      db.close()
    } catch (e) {
      error.value = "Failed to calculate: " + (e?.message || String(e))
    } finally {
      loading.value = false
    }
  }

  return { playerSelect, onDbFileSelected, confirmPlayerAndCalculate }
}
