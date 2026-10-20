
import { useState } from 'react'

interface QBRCase {
  id: number
  customer_name: string
  quarter: string
  year: number
}

interface QBRExportProps {
  cases: QBRCase[]
}

export default function QBRExport({ cases }: QBRExportProps) {
  const [selectedCaseId, setSelectedCaseId] = useState<number | null>(null)

  const activeCaseId =
    selectedCaseId !== null && cases.some((item) => item.id === selectedCaseId)
      ? selectedCaseId
      : cases[0]?.id ?? null

  function handleDownload() {
    if (activeCaseId === null) return

    window.location.assign(
      `/api/cases/${activeCaseId}/export/pptx`
    )
  }

  return (
    <section className="workspace-panel qbr-export">
      <h2>Export QBR Presentation</h2>

      <p>
        Generate and download your quarterly business review
        as a PowerPoint presentation.
      </p>

      <div className="qbr-export-controls">
        <label htmlFor="qbr-export-case">
          Select Customer Workspace
        </label>

        <select
          id="qbr-export-case"
          value={activeCaseId ?? ''}
          onChange={(event) =>
            setSelectedCaseId(Number(event.target.value))
          }
          disabled={cases.length === 0}
        >
          {cases.length === 0 && (
            <option value="">No workspaces available</option>
          )}

          {cases.map((item) => (
            <option key={item.id} value={item.id}>
              {item.customer_name} — {item.quarter} {item.year}
            </option>
          ))}
        </select>

        <button
          type="button"
          onClick={handleDownload}
          disabled={activeCaseId === null}
        >
          Download QBR PowerPoint
        </button>
      </div>
    </section>
  )
}
