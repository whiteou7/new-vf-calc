import { normalizeTitleArtist } from "./fuzzy.js"

const DIFF_NAMES = ["novice", "advanced", "exhaust", "infinite", "maximum", "ultimate"]

const DIFF_INDEX = {
  nov: 0,
  adv: 1,
  exh: 2,
  inf: 3,
  grv: 3,
  hvn: 3,
  vvd: 3,
  xcd: 3,
  mxm: 4,
  ult: 4
}

export function parseMusicDbXml(xmlText) {
  const doc = new DOMParser().parseFromString(xmlText, "application/xml")
  if (doc.querySelector("parsererror")) {
    throw new Error("Invalid XML")
  }

  const out = {}
  for (const music of doc.querySelectorAll("mdb > music")) {
    const id = music.getAttribute("id")
    if (!id) continue

    const text = (selector) => music.querySelector(selector)?.textContent?.trim() ?? ""

    out[id] = {
      title: text("info > title_name"),
      artist: text("info > artist_name"),
      difficulty: DIFF_NAMES.map((name) => {
        const n = music.querySelector(`difficulty > ${name} > difnum`)?.textContent?.trim()
        return (n ? parseInt(n, 10) : 0) / 10
      }),
      mid: id,
    }
  }
  return out
}

export async function fetchMusicDb(url) {
  const response = await fetch(url)
  const buffer = await response.arrayBuffer()
  return parseMusicDbXml(new TextDecoder("shift-jis").decode(buffer))
}

export function indexByTitleArtist(mdb) {
  const map = new Map()
  for (const [mid, entry] of Object.entries(mdb)) {
    if (!entry || !entry.title) continue
    const key = normalizeTitleArtist(entry.title) + "|" + normalizeTitleArtist(entry.artist ?? "")
    if (!map.has(key)) map.set(key, { ...entry, mid })
  }
  return map
}

export function getLevel(chart, chartMeta) {
  if (!chartMeta) return 0
  const idx = DIFF_INDEX[chart.difficulty.toLowerCase()]
  return chartMeta.difficulty[idx] || 0
}

export function getLevelFromMdb(mdbSong, diffIndex) {
  if (!mdbSong || !Array.isArray(mdbSong.difficulty)) return 0
  const idx = Math.min(Number(diffIndex) || 0, mdbSong.difficulty.length - 1)
  const level = Number(mdbSong.difficulty[idx])
  if (level != 0) return level
  // ?????
  if (idx == 3) return Number(mdbSong.difficulty[4])
  if (idx == 4) return Number(mdbSong.difficulty[3])
  console.log("warning: level not found")
  return 0
}
