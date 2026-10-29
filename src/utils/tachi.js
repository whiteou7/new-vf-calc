import { calculateVFWithMode, roundLevelForMode } from "@/scoring.js"
import { getLevel } from "./musicDb.js"

export async function fetchTachiPbs(userId) {
  const res = await fetch(`https://kamai.tachi.ac/api/v1/users/${userId}/games/sdvx/pbs/all`)
  const { body, description } = await res.json()
  return { description, pbs: body?.pbs, charts: body?.charts }
}

export function buildTachiRows(pbs, charts, mdb, { exceed, disableMaxxive }) {
  const chartMap = Object.fromEntries(charts.map((c) => [c.chartID, c]))
  const rows = []
  let skipped = 0

  for (const pb of pbs) {
    const chart = chartMap[pb.chartID]
    if (!chart) continue

    const mdbSong = mdb[String(chart.data.inGameID)]
    if (!mdbSong) {
      skipped += 1
      continue
    }

    const level = roundLevelForMode(getLevel(chart, mdbSong), exceed)
    const { score, grade, lamp } = pb.scoreData

    rows.push({
      chartID: pb.chartID,
      songId: chart.data?.inGameID ?? chart.data?.songID ?? null,
      title: chart.song?.title ?? mdbSong.title,
      diff: chart.difficulty,
      level,
      score,
      grade,
      lamp,
      vf: calculateVFWithMode({ level, score, grade, lamp }, exceed, disableMaxxive),
      timeAchieved: pb.timeAchieved ?? null,
    })
  }

  return { rows, skipped }
}
