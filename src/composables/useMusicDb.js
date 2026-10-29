import { computed, ref } from "vue"
import musicDbUrl from "@/assets/music_db.xml?url"
import { fetchMusicDb, indexByTitleArtist } from "@/utils/musicDb.js"
import { useResults } from "./useResults.js"

const mdb = ref({})
const mdbReady = ref(false)
const mdbIndex = computed(() => indexByTitleArtist(mdb.value))

export function useMusicDb() {
  const { error } = useResults()

  async function loadMusicDb() {
    try {
      mdb.value = await fetchMusicDb(musicDbUrl)
      mdbReady.value = true
    } catch (e) {
      console.error("Failed to load music_db.xml", e)
      error.value = "Failed to load music database."
    }
  }

  return { mdb, mdbReady, mdbIndex, loadMusicDb }
}
