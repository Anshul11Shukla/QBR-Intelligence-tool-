
import { useEffect, useState, type FormEvent } from 'react'

type CaseItem = {
  id: number
  customer_name: string
  quarter: string
  year: number
}

type DocumentItem = {
  id: number
  filename: string
  document_type: string
  chunk_count: number
  uploaded_at: string
}

type EvidenceHit = {
  chunk_id: number
  document_id: number
  filename: string
  source_location: string
  excerpt: string
  citation: string
  relevance_score: number
}

type Commitment = {
  id: number
  title: string
  owner: string
  due_date: string | null
  status: string
  source_document_id: number | null
  source_location: string | null
}

const statuses = [
  'open',
  'in_progress',
  'completed',
  'blocked',
]

async function apiRequest<T>(
  url: string,
  options?: RequestInit
): Promise<T> {
  const response = await fetch(url, options)
  const data = await response.json()

  if (!response.ok) {
    throw new Error(
      typeof data.detail === 'string'
        ? data.detail
        : 'Request failed'
    )
  }

  return data as T
}

export default function EvidenceWorkspace() {
  const [cases, setCases] = useState<CaseItem[]>([])
  const [caseId, setCaseId] = useState('')
  const [documents, setDocuments] = useState<DocumentItem[]>([])
  const [file, setFile] = useState<File | null>(null)
  const [query, setQuery] = useState('')
  const [results, setResults] = useState<EvidenceHit[]>([])
  const [searched, setSearched] = useState(false)
  const [commitments, setCommitments] = useState<Commitment[]>([])
  const [title, setTitle] = useState('')
  const [owner, setOwner] = useState('')
  const [dueDate, setDueDate] = useState('')
  const [sourceDocumentId, setSourceDocumentId] = useState('')
  const [sourceLocation, setSourceLocation] = useState('')
  const [message, setMessage] = useState('')
  const [busy, setBusy] = useState(false)

  useEffect(() => {
    apiRequest<CaseItem[]>('/api/cases')
      .then((items) => {
        setCases(items)
        setCaseId(String(items[0]?.id ?? ''))
      })
      .catch((error) => setMessage(String(error)))
  }, [])

  useEffect(() => {
    setDocuments([])
    setCommitments([])
    setResults([])
    setSearched(false)
    setMessage('')
    setSourceDocumentId('')

    if (!caseId) return

    void Promise.all([
      apiRequest<DocumentItem[]>(`/api/cases/${caseId}/documents`),
      apiRequest<Commitment[]>(`/api/cases/${caseId}/commitments`),
    ])
      .then(([docs, items]) => {
        setDocuments(docs)
        setCommitments(items)
      })
      .catch((error) => setMessage(String(error)))
  }, [caseId])

  async function uploadFile(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    if (!file || !caseId) return

    setBusy(true)
    setMessage('')

    try {
      const formData = new FormData()
      formData.append('file', file)

      const uploaded = await apiRequest<DocumentItem>(
        `/api/cases/${caseId}/documents`,
        { method: 'POST', body: formData }
      )

      setDocuments((previous) => [uploaded, ...previous])
      setFile(null)
      setMessage(
        `Uploaded ${uploaded.filename}: ${uploaded.chunk_count} searchable chunks.`
      )

      const input = document.getElementById(
        'evidence-file'
      ) as HTMLInputElement | null
      if (input) input.value = ''
    } catch (error) {
      setMessage(String(error))
    } finally {
      setBusy(false)
    }
  }

  async function search(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    if (!caseId) return

    setBusy(true)
    setMessage('')
    setSearched(false)

    try {
      const params = new URLSearchParams({ q: query })
      const data = await apiRequest<{ results: EvidenceHit[] }>(
        `/api/cases/${caseId}/evidence/search?${params}`
      )
      setResults(data.results)
      setSearched(true)
    } catch (error) {
      setMessage(String(error))
    } finally {
      setBusy(false)
    }
  }

  async function addCommitment(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    if (!caseId) return

    setBusy(true)
    setMessage('')

    try {
      const created = await apiRequest<Commitment>(
        `/api/cases/${caseId}/commitments`,
        {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            title,
            owner,
            due_date: dueDate || null,
            status: 'open',
            source_document_id: sourceDocumentId
              ? Number(sourceDocumentId)
              : null,
            source_location: sourceLocation || null,
          }),
        }
      )

      setCommitments((previous) => [...previous, created])
      setTitle('')
      setOwner('')
      setDueDate('')
      setSourceDocumentId('')
      setSourceLocation('')
      setMessage('Commitment saved successfully.')
    } catch (error) {
      setMessage(String(error))
    } finally {
      setBusy(false)
    }
  }

  async function changeStatus(id: number, status: string) {
    if (!caseId) return

    setBusy(true)
    setMessage('')

    try {
      const updated = await apiRequest<Commitment>(
        `/api/cases/${caseId}/commitments/${id}`,
        {
          method: 'PATCH',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ status }),
        }
      )

      setCommitments((previous) =>
        previous.map((item) =>
          item.id === id ? updated : item
        )
      )
    } catch (error) {
      setMessage(String(error))
    } finally {
      setBusy(false)
    }
  }

  return (
    <section className="workspace-panel evidence-workspace">
      <h2>Evidence & Historical Context Center</h2>
      <p>
        Search customer documents and track commitments with
        traceable source references.
      </p>

      <label className="evidence-field">
        Customer Workspace
        <select
          value={caseId}
          onChange={(event) => setCaseId(event.target.value)}
        >
          <option value="">Select a workspace</option>
          {cases.map((item) => (
            <option key={item.id} value={item.id}>
              {item.customer_name} — {item.quarter} {item.year}
            </option>
          ))}
        </select>
      </label>

      {message && (
        <p className="form-message" role="status">{message}</p>
      )}

      <div className="evidence-section">
        <h3>1. Upload Historical Documents</h3>
        <form className="evidence-form" onSubmit={uploadFile}>
          <label className="evidence-field">
            PDF, DOCX, TXT or Markdown
            <input
              id="evidence-file"
              type="file"
              accept=".pdf,.docx,.txt,.md"
              onChange={(event) =>
                setFile(event.target.files?.[0] ?? null)
              }
              required
            />
          </label>
          <button disabled={!caseId || busy || !file}>
            Upload Document
          </button>
        </form>

        <div className="evidence-list">
          {documents.map((doc) => (
            <div className="evidence-item" key={doc.id}>
              <strong>{doc.filename}</strong>
              <span>
                Document #{doc.id} · {doc.chunk_count} chunks
              </span>
            </div>
          ))}
          {documents.length === 0 && (
            <p>No documents uploaded yet.</p>
          )}
        </div>
      </div>

      <div className="evidence-section">
        <h3>2. Search Customer Evidence</h3>
        <form className="evidence-form" onSubmit={search}>
          <label className="evidence-field">
            Search query
            <input
              value={query}
              onChange={(event) => setQuery(event.target.value)}
              placeholder="e.g. SLA incident response delays"
              minLength={2}
              required
            />
          </label>
          <button disabled={!caseId || busy}>
            Search Evidence
          </button>
        </form>

        {searched && results.length === 0 && (
          <p>No matching evidence found in this workspace.</p>
        )}

        <div className="evidence-list">
          {results.map((hit) => (
            <article className="evidence-item" key={hit.chunk_id}>
              <strong>{hit.filename}</strong>
              <span>{hit.source_location}</span>
              <p>{hit.excerpt}</p>
              <code>{hit.citation}</code>
              <button
                type="button"
                className="evidence-secondary-button"
                onClick={async () => {
                  try {
                    const chunk = await apiRequest<{
                      content: string
                    }>(
                      `/api/cases/${caseId}/evidence/chunks/${hit.chunk_id}`
                    )
                    window.alert(chunk.content)
                  } catch (error) {
                    setMessage(String(error))
                  }
                }}
              >
                View Full Passage
              </button>
            </article>
          ))}
        </div>
      </div>

      <div className="evidence-section">
        <h3>3. Historical Customer Commitments</h3>
        <form className="commitment-form" onSubmit={addCommitment}>
          <label className="evidence-field">
            Commitment
            <input
              value={title}
              onChange={(event) => setTitle(event.target.value)}
              placeholder="Improve incident response time"
              minLength={3}
              required
            />
          </label>

          <label className="evidence-field">
            Owner
            <input
              value={owner}
              onChange={(event) => setOwner(event.target.value)}
              placeholder="Operations Team"
              required
            />
          </label>

          <label className="evidence-field">
            Due Date
            <input
              type="date"
              value={dueDate}
              onChange={(event) => setDueDate(event.target.value)}
            />
          </label>

          <label className="evidence-field">
            Supporting Document (optional)
            <select
              value={sourceDocumentId}
              onChange={(event) =>
                setSourceDocumentId(event.target.value)
              }
            >
              <option value="">No linked document</option>
              {documents.map((doc) => (
                <option key={doc.id} value={doc.id}>
                  {doc.filename} (#{doc.id})
                </option>
              ))}
            </select>
          </label>

          <label className="evidence-field">
            Source Location (optional)
            <input
              value={sourceLocation}
              onChange={(event) =>
                setSourceLocation(event.target.value)
              }
              placeholder="Page 2 or Paragraph 5"
            />
          </label>

          <button disabled={!caseId || busy}>
            Add Commitment
          </button>
        </form>

        <div className="evidence-list">
          {commitments.map((item) => (
            <article className="evidence-item" key={item.id}>
              <strong>{item.title}</strong>
              <p>
                Owner: {item.owner} · Due: {item.due_date ?? 'Not set'}
              </p>
              {item.source_document_id && (
                <span>
                  Source document #{item.source_document_id}
                  {item.source_location
                    ? ` · ${item.source_location}`
                    : ''}
                </span>
              )}
              <label className="evidence-field">
                Status
                <select
                  value={item.status}
                  disabled={busy}
                  onChange={(event) =>
                    void changeStatus(item.id, event.target.value)
                  }
                >
                  {statuses.map((status) => (
                    <option key={status} value={status}>
                      {status.replaceAll('_', ' ')}
                    </option>
                  ))}
                </select>
              </label>
            </article>
          ))}
          {commitments.length === 0 && (
            <p>No commitments recorded yet.</p>
          )}
        </div>
      </div>
    </section>
  )
}
