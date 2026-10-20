
import { useEffect, useState, type FormEvent } from 'react'

type KPIResult = {
  metric: string
  unit: string
  direction: 'higher' | 'lower'
  previous_value: number | null
  current_value: number | null
  target: number | null
  absolute_change: number | null
  percentage_change: number | null
  target_met: boolean | null
  status: string
  alerts: string[]
  sources: Record<string, string>
}

type Analysis = {
  case_id: number
  metrics: KPIResult[]
  summary: Record<string, number>
  warnings: string[]
}

type CaseItem = {
  id: number
  customer_name: string
  quarter: string
  year: number
}

export default function KPIWorkspace() {
  const [cases, setCases] = useState<CaseItem[]>([])
  const [caseId, setCaseId] = useState('')
  const [period, setPeriod] = useState('current')
  const [file, setFile] = useState<File | null>(null)
  const [analysis, setAnalysis] = useState<Analysis | null>(null)
  const [message, setMessage] = useState('')
  const [loading, setLoading] = useState(false)

  async function loadCases() {
    try {
      const response = await fetch('/api/cases')
      if (!response.ok) throw new Error('Could not load workspaces')
      const data: CaseItem[] = await response.json()
      setCases(data)
      setCaseId((previous) => previous || String(data[0]?.id ?? ''))
    } catch (error) {
      setMessage(
        error instanceof Error ? error.message : 'Unable to load cases'
      )
    }
  }

  useEffect(() => {
    void loadCases()
  }, [])

  async function loadAnalysis(id: string) {
    if (!id) return

    try {
      const response = await fetch(`/api/cases/${id}/analytics`)
      if (!response.ok) throw new Error('Could not load KPI analysis')
      const data: Analysis = await response.json()
      setAnalysis(data)
    } catch (error) {
      setAnalysis(null)
      setMessage(
        error instanceof Error ? error.message : 'Analysis failed'
      )
    }
  }

  useEffect(() => {
    setAnalysis(null)
    if (caseId) void loadAnalysis(caseId)
  }, [caseId])

  async function handleUpload(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()

    if (!caseId || !file) {
      setMessage('Select a workspace and Excel file.')
      return
    }

    setLoading(true)
    setMessage('')

    try {
      const formData = new FormData()
      formData.append('file', file)

      const response = await fetch(
        `/api/cases/${caseId}/upload?period=${period}`,
        {
          method: 'POST',
          body: formData,
        }
      )

      const result = await response.json()

      if (!response.ok) {
        throw new Error(
          typeof result.detail === 'string'
            ? result.detail
            : 'Upload failed'
        )
      }

      setMessage(
        `${result.records_imported} KPIs imported from ${result.filename}.`
      )

      setFile(null)
      const fileInput = document.getElementById(
        'kpi-file'
      ) as HTMLInputElement | null
      if (fileInput) fileInput.value = ''

      await loadAnalysis(caseId)
    } catch (error) {
      setMessage(
        error instanceof Error ? error.message : 'Upload failed'
      )
    } finally {
      setLoading(false)
    }
  }

  function formatValue(value: number | null, unit: string) {
    if (value === null) return 'N/A'
    const formatted = value.toLocaleString(undefined, {
      maximumFractionDigits: 2,
    })
    return unit === '%' ? `${formatted}%` : `${formatted} ${unit}`
  }

  return (
    <section className="workspace-panel">
      <h2>KPI Analytics Workspace</h2>
      <p>
        Upload previous and current quarter spreadsheets to analyze
        customer performance.
      </p>

      <form className="kpi-upload-form" onSubmit={handleUpload}>
        <label>
          Customer Workspace
          <select
            value={caseId}
            onChange={(event) => {
              setCaseId(event.target.value)
              setMessage('')
            }}
            required
          >
            <option value="">Select workspace</option>
            {cases.map((item) => (
              <option key={item.id} value={item.id}>
                {item.customer_name} — {item.quarter} {item.year}
              </option>
            ))}
          </select>
        </label>

        <label>
          Reporting Period
          <select
            value={period}
            onChange={(event) => setPeriod(event.target.value)}
          >
            <option value="previous">Previous Quarter</option>
            <option value="current">Current Quarter</option>
          </select>
        </label>

        <label>
          Excel File (.xlsx)
          <input
            id="kpi-file"
            type="file"
            accept=".xlsx"
            onChange={(event) =>
              setFile(event.target.files?.[0] ?? null)
            }
            required
          />
        </label>

        <button type="submit" disabled={loading || !caseId}>
          {loading ? 'Uploading...' : 'Upload KPIs'}
        </button>
      </form>

      {message && (
        <p role="status" className="form-message">{message}</p>
      )}

      {analysis && (
        <div className="analysis-results">
          <h3>Quarterly KPI Analysis</h3>

          <div className="analysis-summary">
            <div>
              <strong>{analysis.summary.total_metrics}</strong>
              <span>Total KPIs</span>
            </div>
            <div>
              <strong>{analysis.summary.improved}</strong>
              <span>Improved</span>
            </div>
            <div>
              <strong>{analysis.summary.declined}</strong>
              <span>Declined</span>
            </div>
            <div>
              <strong>{analysis.summary.target_breaches}</strong>
              <span>Target Breaches</span>
            </div>
          </div>

          {analysis.warnings.length > 0 && (
            <div className="analysis-warnings">
              <strong>Data quality warnings</strong>
              <ul>
                {analysis.warnings.map((warning, index) => (
                  <li key={index}>{warning}</li>
                ))}
              </ul>
            </div>
          )}

          <div className="kpi-table-scroll">
            <table className="kpi-table">
              <thead>
                <tr>
                  <th>KPI</th>
                  <th>Previous</th>
                  <th>Current</th>
                  <th>Change</th>
                  <th>Target</th>
                  <th>Status</th>
                </tr>
              </thead>
              <tbody>
                {analysis.metrics.map((item) => (
                  <tr key={item.metric}>
                    <td>
                      <strong>{item.metric}</strong>
                      {item.alerts.map((alert, index) => (
                        <small className="kpi-alert" key={index}>
                          {alert}
                        </small>
                      ))}
                      {Object.entries(item.sources).map(
                        ([sourcePeriod, source]) => (
                          <small className="kpi-source" key={sourcePeriod}>
                            {sourcePeriod}: {source}
                          </small>
                        )
                      )}
                    </td>
                    <td>
                      {formatValue(item.previous_value, item.unit)}
                    </td>
                    <td>
                      {formatValue(item.current_value, item.unit)}
                    </td>
                    <td>
                      {item.absolute_change === null
                        ? 'N/A'
                        : `${item.absolute_change > 0 ? '+' : ''}${item.absolute_change.toLocaleString()}${item.unit === '%' ? ' pp' : ` ${item.unit}`}`}
                      <small>
                        {item.percentage_change === null
                          ? ''
                          : `(${item.percentage_change > 0 ? '+' : ''}${item.percentage_change}%)`}
                      </small>
                    </td>
                    <td>{formatValue(item.target, item.unit)}</td>
                    <td>
                      <span
                        className={
                          item.status === 'improved'
                            ? 'kpi-good'
                            : item.status === 'declined'
                              ? 'kpi-bad'
                              : ''
                        }
                      >
                        {item.status.replaceAll('_', ' ')}
                      </span>
                      <small>
                        {item.target_met === null
                          ? 'Target unknown'
                          : item.target_met
                            ? 'Target met'
                            : 'Target missed'}
                      </small>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          {analysis.metrics.length === 0 && (
            <p>Upload a spreadsheet to see KPI results.</p>
          )}
        </div>
      )}
    </section>
  )
}
