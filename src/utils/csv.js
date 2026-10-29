import { formatScore } from "./format.js"

const HEADERS = ["#", "Song", "Diff", "Level", "Score", "Grade", "Clear", "VF"]

function escapeCsvField(val) {
  const s = String(val ?? "")
  if (s.includes(",") || s.includes('"') || s.includes("\n")) {
    return '"' + s.replace(/"/g, '""') + '"'
  }
  return s
}

const toLine = (fields) => fields.map(escapeCsvField).join(",")

export function exportToCsv(rows, effectiveLamp) {
  const lines = [toLine(HEADERS)]
  rows.forEach((row, i) => {
    lines.push(
      toLine([
        i + 1,
        row.title ?? "",
        (row.diff ?? "").toUpperCase(),
        row.level ?? "",
        formatScore(row.score),
        row.grade ?? "",
        effectiveLamp(row.lamp),
        row.vf != null ? row.vf.toFixed(3) : ""
      ])
    )
  })
  const blob = new Blob(["﻿" + lines.join("\n")], { type: "text/csv;charset=utf-8" })
  const url = URL.createObjectURL(blob)
  const a = document.createElement("a")
  a.href = url
  a.download = "b50-export.csv"
  a.click()
  URL.revokeObjectURL(url)
}
