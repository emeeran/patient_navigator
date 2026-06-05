import api from "./client";
import type {
  Patient,
  Case,
  Document,
  Hospital,
  FundingProgram,
  FollowUp,
  PaginatedResponse,
  AIResponse,
} from "../types";

// ── Patients ────────────────────────────────────────────
export const patientsApi = {
  list: (params?: Record<string, unknown>) =>
    api.get<PaginatedResponse<Patient>>("/patients", { params }),
  get: (id: string) => api.get<Patient>(`/patients/${id}`),
  create: (data: Partial<Patient>) => api.post<Patient>("/patients", data),
  update: (id: string, data: Partial<Patient>) =>
    api.patch<Patient>(`/patients/${id}`, data),
  archive: (id: string) => api.delete(`/patients/${id}`),
};

// ── Cases ───────────────────────────────────────────────
export const casesApi = {
  list: (params?: Record<string, unknown>) =>
    api.get<PaginatedResponse<Case>>("/cases", { params }),
  listForPatient: (patientId: string, params?: Record<string, unknown>) =>
    api.get<PaginatedResponse<Case>>(`/patients/${patientId}/cases`, { params }),
  get: (id: string) => api.get<Case>(`/cases/${id}`),
  create: (patientId: string, data: Partial<Case>) =>
    api.post<Case>(`/patients/${patientId}/cases`, data),
  update: (id: string, data: Partial<Case>) =>
    api.patch<Case>(`/cases/${id}`, data),
  transitionStatus: (id: string, status: string) =>
    api.patch<Case>(`/cases/${id}/status`, { status }),
};

// ── Documents ──────────────────────────────────────────
export const documentsApi = {
  list: (caseId: string, params?: Record<string, unknown>) =>
    api.get<PaginatedResponse<Document>>(`/cases/${caseId}/documents`, { params }),
  get: (id: string) => api.get<Document>(`/documents/${id}`),
  upload: (caseId: string, file: File) => {
    const form = new FormData();
    form.append("file", file);
    return api.post<Document>(`/cases/${caseId}/documents/upload`, form, {
      headers: { "Content-Type": "multipart/form-data" },
    });
  },
  download: (id: string) =>
    api.get(`/documents/${id}/download`, { responseType: "blob" }),
  triggerOcr: (id: string) => api.post(`/documents/${id}/ocr`),
  delete: (id: string) => api.delete(`/documents/${id}`),
};

// ── Hospitals ──────────────────────────────────────────
export const hospitalsApi = {
  list: (params?: Record<string, unknown>) =>
    api.get<PaginatedResponse<Hospital>>("/hospitals", { params }),
  get: (id: string) => api.get<Hospital>(`/hospitals/${id}`),
  create: (data: Partial<Hospital>) =>
    api.post<Hospital>("/hospitals", data),
  update: (id: string, data: Partial<Hospital>) =>
    api.put<Hospital>(`/hospitals/${id}`, data),
  archive: (id: string) => api.delete(`/hospitals/${id}`),
};

// ── Funding ────────────────────────────────────────────
export const fundingApi = {
  list: (params?: Record<string, unknown>) =>
    api.get<PaginatedResponse<FundingProgram>>("/funding", { params }),
  get: (id: string) => api.get<FundingProgram>(`/funding/${id}`),
  create: (data: Partial<FundingProgram>) =>
    api.post<FundingProgram>("/funding", data),
  update: (id: string, data: Partial<FundingProgram>) =>
    api.patch<FundingProgram>(`/funding/${id}`, data),
  archive: (id: string) => api.delete(`/funding/${id}`),
};

// ── Follow-Ups ─────────────────────────────────────────
export const followUpsApi = {
  list: (caseId: string, params?: Record<string, unknown>) =>
    api.get<PaginatedResponse<FollowUp>>(`/cases/${caseId}/followups`, {
      params,
    }),
  upcoming: (params?: Record<string, unknown>) =>
    api.get<PaginatedResponse<FollowUp>>("/followups/upcoming", { params }),
  get: (id: string) => api.get<FollowUp>(`/followups/${id}`),
  create: (caseId: string, data: Partial<FollowUp>) =>
    api.post<FollowUp>(`/cases/${caseId}/followups`, data),
  update: (id: string, data: Partial<FollowUp>) =>
    api.put<FollowUp>(`/followups/${id}`, data),
  complete: (id: string) =>
    api.post<FollowUp>(`/followups/${id}/complete`),
};

// ── AI ─────────────────────────────────────────────────
export const aiApi = {
  summarize: (caseId: string, documentIds?: string[]) =>
    api.post<AIResponse>("/ai/summarize", {
      case_id: caseId,
      document_ids: documentIds,
    }),
  explain: (text: string) =>
    api.post<AIResponse>("/ai/explain", { text }),
  suggestSpecialist: (caseId: string, diagnosis?: string) =>
    api.post<AIResponse>("/ai/suggest-specialist", {
      case_id: caseId,
      diagnosis,
    }),
  questionsForDoctor: (caseId: string, context?: string) =>
    api.post<AIResponse>("/ai/questions-for-doctor", {
      case_id: caseId,
      context,
    }),
};
