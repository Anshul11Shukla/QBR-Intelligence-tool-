
export interface SourceReference {
  period?: string;
  source?: string;
  document_id?: number;
  source_location?: string | null;
}

export interface QAQuestion {
  question_id: number;
  category: string;
  metric: string | null;
  severity: string;
  customer_question: string;
  suggested_answer: string;
  follow_up_question: string;
  coaching_tip: string;
  answer_readiness: string;
  executive_talking_points: string[];
  evidence_gaps: string[];
  preparation_actions: string[];
  source_references: SourceReference[];
  related_commitments: Record<string, unknown>[];
  document_evidence: Record<string, unknown>[];
}

export interface QACoachResponse {
  case_id: number;
  total_questions: number;
  questions: QAQuestion[];
  generation_mode: string;
}

const API_BASE_URL = (
  import.meta.env.VITE_API_BASE_URL ||
  "http://127.0.0.1:8000"
).replace(/\/$/, "");

export async function fetchQACoach(
  caseId: number
): Promise<QACoachResponse> {
  const response = await fetch(
    `${API_BASE_URL}/api/cases/${caseId}/qa-coach`
  );

  if (!response.ok) {
    throw new Error(
      `Unable to load Q&A Coach (HTTP ${response.status})`
    );
  }

  return response.json() as Promise<QACoachResponse>;
}
