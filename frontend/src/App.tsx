import QBRExport from './QBRExport'
import QACoachWorkspace from './QACoachWorkspace'
import KPIWorkspace from './KPIWorkspace'
import { useEffect, useState, type FormEvent } from 'react'
import EvidenceWorkspace from './EvidenceWorkspace'

type HealthResponse = {
  status: string
  app: string
}

type QBRCase = {
  id: number
  customer_name: string
  quarter: string
  year: number
  created_at: string
}

export default function App() {
  const [health, setHealth] = useState<HealthResponse | null>(null)
  const [cases, setCases] = useState<QBRCase[]>([])
  const [customerName, setCustomerName] = useState('')
  const [quarter, setQuarter] = useState('Q3')
  const [year, setYear] = useState(2026)
  const [message, setMessage] = useState('')
  const [saving, setSaving] = useState(false)

  async function loadCases() {
    try {
      const response = await fetch('/api/cases')
      if (!response.ok) throw new Error('Unable to load workspaces')
      setCases(await response.json())
    } catch {
      setMessage('Unable to load customer workspaces.')
    }
  }

  useEffect(() => {
    fetch('/api/health')
      .then(async (response) => {
        if (!response.ok) throw new Error('Backend unavailable')
        return response.json() as Promise<HealthResponse>
      })
      .then(setHealth)
      .catch(() => setHealth(null))

    void loadCases()
  }, [])

  async function handleCreateCase(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    setSaving(true)
    setMessage('')

    try {
      const response = await fetch('/api/cases', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          customer_name: customerName,
          quarter,
          year,
        }),
      })

      if (!response.ok) {
        const errorData = await response.json()
        throw new Error(
          typeof errorData.detail === 'string'
            ? errorData.detail
            : 'Unable to create workspace'
        )
      }

      setCustomerName('')
      setMessage('Workspace created successfully!')
      await loadCases()
    } catch (error) {
      setMessage(
        error instanceof Error ? error.message : 'Unexpected error'
      )
    } finally {
      setSaving(false)
    }
  }

  return (
    <main className="app">
      <header className="topbar">
        <div className="brand-mark">Q</div>
        <div>
          <strong>QBR Intelligence Studio</strong>
          <p>Agentic customer review workspace</p>
        </div>
      </header>

      <section className="hero">
        <span className="eyebrow">QUARTERLY BUSINESS REVIEW</span>
        <h1>Turn customer data into decisions.</h1>
        <p>
          Create customer workspaces, analyze KPIs, generate
          executive-ready reports, and prepare for customer Q&A.
        </p>
      </section>

      <section className="status-card">
        <div>
          <span className="eyebrow">SYSTEM STATUS</span>
          <h2>Backend connection</h2>
          <p>
            {health
              ? `${health.app} is responding successfully.`
              : 'Backend connection unavailable.'}
          </p>
        </div>
        <span className={`status ${health ? 'online' : 'offline'}`}>
          {health ? 'Connected' : 'Offline'}
        </span>
      </section>

      <section className="workspace-panel">
        <h2>Create QBR Workspace</h2>
        <p>Start a quarterly business review for a customer.</p>

        <form className="workspace-form" onSubmit={handleCreateCase}>
          <label>
            Customer Name
            <input
              value={customerName}
              onChange={(event) => setCustomerName(event.target.value)}
              placeholder="e.g. ABC Technologies"
              minLength={2}
              maxLength={150}
              required
            />
          </label>

          <label>
            Quarter
            <select
              value={quarter}
              onChange={(event) => setQuarter(event.target.value)}
            >
              <option value="Q1">Q1</option>
              <option value="Q2">Q2</option>
              <option value="Q3">Q3</option>
              <option value="Q4">Q4</option>
            </select>
          </label>

          <label>
            Year
            <input
              type="number"
              value={year}
              min={2020}
              max={2100}
              onChange={(event) => setYear(Number(event.target.value))}
              required
            />
          </label>

          <button type="submit" disabled={saving}>
            {saving ? 'Creating...' : 'Create Workspace'}
          </button>
        </form>

        {message && <p role="status" className="form-message">{message}</p>}
      </section>

      <section className="workspace-panel">
        <h2>Customer Workspaces</h2>

        {cases.length === 0 ? (
          <p>No customer workspaces loaded yet.</p>
        ) : (
          <div className="case-list">
            {cases.map((item) => (
              <article className="case-row" key={item.id}>
                <div>
                  <strong>{item.customer_name}</strong>
                  <p>Workspace #{item.id}</p>
                </div>
                <span className="case-period">
                  {item.quarter} {item.year}
                </span>
              </article>
            ))}
          </div>
        )}
      </section>
            <KPIWorkspace />

      <EvidenceWorkspace />

      <QACoachWorkspace />

      <QBRExport cases={cases} />

      <footer>QBR Intelligence Studio · Phase 6</footer>
    </main>
  )
}
