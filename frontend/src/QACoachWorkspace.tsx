
import { useEffect, useState } from 'react'
import {
  fetchQACoach,
  type QAQuestion,
} from './services/qaCoachApi'

export default function QACoachWorkspace() {
  const [caseId, setCaseId] = useState(1)
  const [questions, setQuestions] = useState<QAQuestion[]>([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [loaded, setLoaded] = useState(false)
  const [expanded, setExpanded] = useState<number | null>(null)

  async function loadQuestions(id: number) {
    setLoading(true)
    setError('')

    try {
      const data = await fetchQACoach(id)
      setQuestions(data.questions)
      setLoaded(true)
      setExpanded(null)
    } catch (err) {
      setError(
        err instanceof Error
          ? err.message
          : 'Unable to load Q&A questions'
      )
      setLoaded(false)
      setQuestions([])
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    void loadQuestions(1)
  }, [])

  const highRisk = questions.filter(
    (q) => q.severity === 'high'
  ).length

  const mediumRisk = questions.filter(
    (q) => q.severity === 'medium'
  ).length

  function toggleQuestion(id: number) {
    setExpanded((current) =>
      current === id ? null : id
    )
  }

  return (
    <section className="workspace-panel qa-workspace">
      <div className="qa-heading">
        <div>
          <span className="eyebrow">
            PHASE 6 · CUSTOMER PREPARATION
          </span>
          <h2>Customer Q&A Coach</h2>
          <p>
            Prepare for difficult customer questions using
            verified KPI insights and historical commitments.
          </p>
        </div>
        <span className="qa-mode">Evidence-aware</span>
      </div>

      <div className="qa-controls">
        <label>
          Workspace ID
          <input
            type="number"
            min={1}
            value={caseId}
            onChange={(event) =>
              setCaseId(Number(event.target.value))
            }
          />
        </label>

        <button
          type="button"
          disabled={loading || caseId < 1}
          onClick={() => void loadQuestions(caseId)}
        >
          {loading ? 'Generating...' : 'Generate Q&A'}
        </button>
      </div>

      {error && (
        <p className="qa-error" role="alert">
          {error}
        </p>
      )}

      {loaded && (
        <>
          <div className="qa-stats">
            <div className="qa-stat">
              <strong>{questions.length}</strong>
              <span>Customer Questions</span>
            </div>

            <div className="qa-stat">
              <strong>{highRisk}</strong>
              <span>High Priority</span>
            </div>

            <div className="qa-stat">
              <strong>{mediumRisk}</strong>
              <span>Medium Priority</span>
            </div>
          </div>

          {questions.length === 0 ? (
            <p>
              No priority questions were generated for
              this workspace.
            </p>
          ) : (
            <div className="qa-question-list">
              {questions.map((question) => (
                <QuestionCard
                  key={question.question_id}
                  question={question}
                  expanded={
                    expanded === question.question_id
                  }
                  onToggle={() =>
                    toggleQuestion(question.question_id)
                  }
                />
              ))}
            </div>
          )}
        </>
      )}
    </section>
  )
}

type QuestionCardProps = {
  question: QAQuestion
  expanded: boolean
  onToggle: () => void
}

function QuestionCard({
  question,
  expanded,
  onToggle,
}: QuestionCardProps) {
  return (
    <article className="qa-question-card">
      <button
        type="button"
        className="qa-question-toggle"
        onClick={onToggle}
        aria-expanded={expanded}
      >
        <div>
          <span className="qa-question-number">
            QUESTION {question.question_id}
          </span>

          <h3>{question.customer_question}</h3>

          <div className="qa-badges">
            <span
              className={`qa-severity ${question.severity}`}
            >
              {question.severity} priority
            </span>

            <span className="qa-readiness">
              {question.answer_readiness.replaceAll(
                '_',
                ' '
              )}
            </span>
          </div>
        </div>

        <span className="qa-expand-icon">
          {expanded ? '−' : '+'}
        </span>
      </button>

      {expanded && (
        <div className="qa-question-content">
          <div className="qa-answer">
            <h4>Suggested Customer Answer</h4>
            <p>{question.suggested_answer}</p>
          </div>

          <div className="qa-content-grid">
            <div>
              <h4>Executive Talking Points</h4>
              <ul>
                {question.executive_talking_points.map(
                  (point, index) => (
                    <li key={index}>{point}</li>
                  )
                )}
              </ul>
            </div>

            <div>
              <h4>Preparation Actions</h4>
              <ul>
                {question.preparation_actions.map(
                  (action, index) => (
                    <li key={index}>{action}</li>
                  )
                )}
              </ul>
            </div>
          </div>

          <div className="qa-evidence-gaps">
            <h4>Evidence Gaps</h4>
            <ul>
              {question.evidence_gaps.map(
                (gap, index) => (
                  <li key={index}>{gap}</li>
                )
              )}
            </ul>
          </div>

          <div className="qa-followup">
            <h4>Likely Follow-up Question</h4>
            <p>{question.follow_up_question}</p>
          </div>

          <div className="qa-coaching-tip">
            <strong>Presentation Tip</strong>
            <p>{question.coaching_tip}</p>
          </div>

          {question.source_references.length > 0 && (
            <div className="qa-sources">
              <h4>Source References</h4>

              {question.source_references.map(
                (reference, index) => (
                  <p key={index}>
                    {reference.period
                      ? `${reference.period}: `
                      : ''}
                    {reference.source ||
                      reference.source_location ||
                      'Document reference'}
                  </p>
                )
              )}
            </div>
          )}

          {question.document_evidence.length > 0 && (
            <div className="qa-sources">
              <h4>Retrieved Document Evidence</h4>
              {question.document_evidence.map(
                (hit, index) => (
                  <p key={index}>
                    {String(
                      hit.citation ??
                      hit.excerpt ??
                      'Document evidence'
                    )}
                  </p>
                )
              )}
            </div>
          )}
        </div>
      )}
    </article>
  )
}
