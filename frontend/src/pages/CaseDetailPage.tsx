import { useState, useEffect } from "react";
import { useParams, Link } from "react-router-dom";
import { casesApi, documentsApi, followUpsApi, aiApi, patientsApi, reviewsApi } from "../api";
import type { Case, Document as DocType, FollowUp, AIResponse, Patient } from "../types";
import AIResultCard from "../components/AIResultCard";
import Modal from "../components/Modal";
import DocumentUploadModal from "../components/DocumentUploadModal";

const FOLLOW_UP_TYPES = [
  { value: "appointment", label: "Appointment" },
  { value: "checkup", label: "Checkup" },
  { value: "lab_test", label: "Lab Test" },
  { value: "imaging", label: "Imaging" },
  { value: "referral", label: "Referral" },
];

const CASE_STATUSES = ["new", "under_review", "in_treatment", "closed"];

interface TimelineEvent { id: string; action: string; description: string; created_at: string }
interface Review { id: string; reviewer_id: string; summary_text: string; status: string; reviewer_comments: string | null; created_at: string }

export default function CaseDetailPage() {
  const { caseId } = useParams<{ caseId: string }>();
  const [caseData, setCaseData] = useState<Case | null>(null);
  const [patient, setPatient] = useState<Patient | null>(null);
  const [documents, setDocuments] = useState<DocType[]>([]);
  const [followUps, setFollowUps] = useState<FollowUp[]>([]);
  const [timeline, setTimeline] = useState<TimelineEvent[]>([]);
  const [reviews, setReviews] = useState<Review[]>([]);
  const [loading, setLoading] = useState(true);

  // Active section tab
  const [activeSection, setActiveSection] = useState<"documents" | "followups" | "timeline" | "reviews">("documents");

  // Document states
  const [showUpload, setShowUpload] = useState(false);
  const [ocrLoading, setOcrLoading] = useState<string | null>(null);
  const [ocrTexts, setOcrTexts] = useState<Record<string, string>>({});
  const [deleteLoading, setDeleteLoading] = useState<string | null>(null);
  const [ocrLang, setOcrLang] = useState<"english" | "tamil">("english");

  // Follow-up states
  const [showFollowUp, setShowFollowUp] = useState(false);
  const [fuForm, setFuForm] = useState({ scheduled_date: "", follow_up_type: "", notes: "" });
  const [fuSaving, setFuSaving] = useState(false);
  const [fuError, setFuError] = useState("");

  // AI states
  const [aiResult, setAiResult] = useState<AIResponse | null>(null);
  const [aiLoading, setAiLoading] = useState(false);
  const [aiLang, setAiLang] = useState<"english" | "tamil">("english");

  // Review modal state
  const [showReview, setShowReview] = useState(false);
  const [reviewForm, setReviewForm] = useState({ summary_text: "", ai_disclaimer_acknowledged: false });
  const [reviewSaving, setReviewSaving] = useState(false);
  const [reviewError, setReviewError] = useState("");

  const loadAll = async () => {
    setLoading(true);
    try {
      const [caseRes, docsRes, fuRes, tlRes, revRes] = await Promise.all([
        casesApi.get(caseId!),
        documentsApi.list(caseId!, { per_page: 100 }),
        followUpsApi.list(caseId!, { per_page: 100 }),
        casesApi.timeline(caseId!).catch(() => ({ data: { items: [] } })),
        reviewsApi.list(caseId!).catch(() => ({ data: { items: [] as Review[] } })),
      ]);
      setCaseData(caseRes.data);
      setDocuments(docsRes.data.items);
      setFollowUps(fuRes.data.items);
      setTimeline((tlRes as { data: { items: TimelineEvent[] } }).data.items || []);
      setReviews((revRes as { data: { items: Review[] } }).data.items || []);

      if (caseRes.data.patient_id) {
        patientsApi.get(caseRes.data.patient_id).then((r) => setPatient(r.data)).catch(() => {});
      }
    } catch { /* interceptor */ }
    setLoading(false);
  };

  useEffect(() => {
    if (caseId) loadAll();
  }, [caseId]);

  // ── Status transition ──
  const handleStatusChange = async (newStatus: string) => {
    try {
      await casesApi.transitionStatus(caseId!, newStatus);
      setCaseData((prev) => prev ? { ...prev, status: newStatus } : prev);
    } catch { /* interceptor */ }
  };

  // ── Archive case ──
  const handleArchiveCase = async () => {
    if (!confirm("Archive this case? This will soft-delete the record.")) return;
    try {
      await casesApi.archive(caseId!);
      window.history.back();
    } catch {
      /* interceptor */
    }
  };

  // ── Document actions ──
  const handleOcr = async (docId: string) => {
    setOcrLoading(docId);
    try {
      const lang = ocrLang === "tamil" ? "tamil" : undefined;
      const { data } = await documentsApi.triggerOcr(docId, lang);
      if (data.ocr_text) setOcrTexts((prev) => ({ ...prev, [docId]: data.ocr_text! }));
      const docsRes = await documentsApi.list(caseId!, { per_page: 100 });
      setDocuments(docsRes.data.items);
    } catch { /* ignore */ }
    setOcrLoading(null);
  };

  const handlePreview = async (docId: string) => {
    if (ocrTexts[docId] !== undefined) {
      setOcrTexts((prev) => { const n = { ...prev }; delete n[docId]; return n; });
      return;
    }
    try {
      const { data } = await documentsApi.preview(docId);
      setOcrTexts((prev) => ({ ...prev, [docId]: data.ocr_text || "" }));
    } catch { /* ignore */ }
  };

  const handleDownload = async (docId: string, filename: string) => {
    try {
      const { data } = await documentsApi.download(docId);
      const url = URL.createObjectURL(data);
      const a = document.createElement("a");
      a.href = url; a.download = filename; a.click();
      URL.revokeObjectURL(url);
    } catch { /* ignore */ }
  };

  const handleDeleteDoc = async (docId: string) => {
    if (!confirm("Delete this document?")) return;
    setDeleteLoading(docId);
    try {
      await documentsApi.delete(docId);
      const docsRes = await documentsApi.list(caseId!, { per_page: 100 });
      setDocuments(docsRes.data.items);
    } catch { /* ignore */ }
    setDeleteLoading(null);
  };

  // ── Follow-up actions ──
  const handleAddFollowUp = async (e: { preventDefault: () => void }) => {
    e.preventDefault();
    setFuSaving(true);
    setFuError("");
    try {
      await followUpsApi.create(caseId!, {
        scheduled_date: fuForm.scheduled_date,
        follow_up_type: fuForm.follow_up_type,
        notes: fuForm.notes || undefined,
      });
      setShowFollowUp(false);
      setFuForm({ scheduled_date: "", follow_up_type: "", notes: "" });
      const fuRes = await followUpsApi.list(caseId!, { per_page: 100 });
      setFollowUps(fuRes.data.items);
    } catch (err: unknown) {
      const msg = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail;
      setFuError(msg || "Failed to schedule");
    } finally { setFuSaving(false); }
  };

  const handleCompleteFollowUp = async (fuId: string) => {
    try {
      await followUpsApi.complete(fuId);
      const fuRes = await followUpsApi.list(caseId!, { per_page: 100 });
      setFollowUps(fuRes.data.items);
    } catch { /* ignore */ }
  };

  // ── AI actions ──
  const handleAI = async (type: "summarize" | "specialist" | "questions") => {
    setAiLoading(true);
    setAiResult(null);
    const lang = aiLang === "tamil" ? "tamil" : undefined;
    try {
      let res;
      switch (type) {
        case "summarize": res = await aiApi.summarize(caseId!, undefined, lang); break;
        case "specialist": res = await aiApi.suggestSpecialist(caseId!, undefined, lang); break;
        case "questions": res = await aiApi.questionsForDoctor(caseId!, undefined, lang); break;
      }
      setAiResult(res!.data);
    } catch { /* ignore */ }
    setAiLoading(false);
  };

  // ── Review actions ──
  const handleCreateReview = async (e: { preventDefault: () => void }) => {
    e.preventDefault();
    setReviewSaving(true);
    setReviewError("");
    try {
      await reviewsApi.create(caseId!, reviewForm);
      setShowReview(false);
      setReviewForm({ summary_text: "", ai_disclaimer_acknowledged: false });
      const revRes = await reviewsApi.list(caseId!).catch(() => ({ data: { items: [] as Review[] } }));
      setReviews((revRes as { data: { items: Review[] } }).data.items || []);
    } catch (err: unknown) {
      const msg = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail;
      setReviewError(msg || "Failed to create review");
    } finally { setReviewSaving(false); }
  };

  const handleReviewStatus = async (reviewId: string, status: string) => {
    try {
      await reviewsApi.update(reviewId, { status });
      const revRes = await reviewsApi.list(caseId!).catch(() => ({ data: { items: [] as Review[] } }));
      setReviews((revRes as { data: { items: Review[] } }).data.items || []);
    } catch { /* ignore */ }
  };

  // ── Helpers ──
  const fuStatusColor = (status: string) => {
    const map: Record<string, string> = { scheduled: "bg-blue-100 text-blue-700", completed: "bg-green-100 text-green-700", overdue: "bg-red-100 text-red-700", cancelled: "bg-gray-100 text-gray-600" };
    return map[status] || "bg-gray-100 text-gray-600";
  };
  const formatBytes = (b: number) => b < 1024 ? `${b} B` : b < 1024 * 1024 ? `${(b / 1024).toFixed(1)} KB` : `${(b / (1024 * 1024)).toFixed(1)} MB`;

  if (loading) return <p className="text-gray-500">Loading case...</p>;
  if (!caseData) return <p className="text-red-500">Case not found.</p>;

  return (
    <div className="space-y-6">
      <Link to="/cases" className="text-sm text-blue-600 hover:underline">← Back to Cases</Link>

      {/* ── Case Header ── */}
      <div className="bg-white rounded-xl border border-gray-200 p-6">
        <div className="flex items-start justify-between">
          <div>
            <h2 className="text-2xl font-bold text-gray-900">{caseData.diagnosis}</h2>
            <p className="text-sm text-gray-500 mt-1">
              Patient: <Link to={`/patients/${caseData.patient_id}`} className="text-blue-600 hover:underline">{patient?.full_name || "Unknown"}</Link>
              {" · "}Case ID: {caseData.id.slice(0, 8)}...
            </p>
            {caseData.notes && <p className="text-sm text-gray-600 mt-2">{caseData.notes}</p>}
          </div>
          <div className="flex items-center gap-3">
            {caseData.status !== "closed" && (
              <button
                onClick={handleArchiveCase}
                className="px-4 py-2 bg-red-50 text-red-600 text-sm font-medium rounded-lg hover:bg-red-100"
              >
                Archive
              </button>
            )}
            <select
              value={caseData.status}
              onChange={(e) => handleStatusChange(e.target.value)}
              className="px-3 py-1.5 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-blue-500"
            >
              {CASE_STATUSES.map((s) => (
                <option key={s} value={s}>{s.replace("_", " ")}</option>
              ))}
            </select>
            <span className={`text-sm font-medium capitalize ${
              caseData.priority === "high" ? "text-red-600"
              : caseData.priority === "critical" ? "text-red-800"
              : caseData.priority === "medium" ? "text-yellow-600"
              : "text-green-600"
            }`}>{caseData.priority}</span>
          </div>
        </div>
      </div>

      {/* ── AI Quick Actions ── */}
      <div className="bg-gradient-to-r from-blue-50 to-indigo-50 rounded-xl border border-blue-200 p-6">
        <div className="flex items-center justify-between mb-3">
          <h3 className="font-semibold text-gray-900">🤖 AI Tools</h3>
          <div className="flex items-center gap-2">
            <span className="text-xs text-gray-500">Language:</span>
            <div className="flex bg-white rounded-lg p-0.5 border border-gray-200">
              <button
                type="button"
                onClick={() => setAiLang("english")}
                className={`px-2.5 py-1 text-xs font-medium rounded-md transition-colors ${
                  aiLang === "english" ? "bg-blue-600 text-white" : "text-gray-500 hover:text-gray-700"
                }`}
              >
                English
              </button>
              <button
                type="button"
                onClick={() => setAiLang("tamil")}
                className={`px-2.5 py-1 text-xs font-medium rounded-md transition-colors ${
                  aiLang === "tamil" ? "bg-blue-600 text-white" : "text-gray-500 hover:text-gray-700"
                }`}
              >
                தமிழ்
              </button>
            </div>
          </div>
        </div>
        <div className="flex flex-wrap gap-3">
          <button onClick={() => handleAI("summarize")} disabled={aiLoading}
            className="px-4 py-2 bg-blue-600 text-white text-sm font-medium rounded-lg hover:bg-blue-700 disabled:opacity-50">
            {aiLoading ? `Generating${aiLang === "tamil" ? " in தமிழ்..." : "..."}` : "📋 Summarize"}
          </button>
          <button onClick={() => handleAI("specialist")} disabled={aiLoading}
            className="px-4 py-2 bg-purple-600 text-white text-sm font-medium rounded-lg hover:bg-purple-700 disabled:opacity-50">
            🩺 Specialist
          </button>
          <button onClick={() => handleAI("questions")} disabled={aiLoading}
            className="px-4 py-2 bg-green-600 text-white text-sm font-medium rounded-lg hover:bg-green-700 disabled:opacity-50">
            ❓ Questions
          </button>
          {aiResult && (
            <button onClick={() => { setReviewForm({ ...reviewForm, summary_text: aiResult.content }); setShowReview(true); }}
              className="px-4 py-2 bg-amber-600 text-white text-sm font-medium rounded-lg hover:bg-amber-700">
              📝 Create Review from Result
            </button>
          )}
        </div>
        {aiResult && (
          <div className="mt-4">
            <AIResultCard result={aiResult} title="AI Analysis" />
          </div>
        )}
      </div>

      {/* ── Section Tabs ── */}
      <div className="flex gap-1 bg-gray-100 rounded-lg p-1">
        {([
          { key: "documents", label: `📄 Documents (${documents.length})` },
          { key: "followups", label: `📅 Follow-Ups (${followUps.length})` },
          { key: "timeline", label: `🕐 Timeline (${timeline.length})` },
          { key: "reviews", label: `📝 Reviews (${reviews.length})` },
        ] as const).map((tab) => (
          <button key={tab.key} onClick={() => setActiveSection(tab.key)}
            className={`flex-1 px-3 py-2 text-sm font-medium rounded-md transition-colors ${
              activeSection === tab.key ? "bg-white text-gray-900 shadow-sm" : "text-gray-500 hover:text-gray-700"
            }`}>
            {tab.label}
          </button>
        ))}
      </div>

      {/* ── Documents Section ── */}
      {activeSection === "documents" && (
        <div>
          <div className="flex items-center justify-between mb-3">
            <div className="flex items-center gap-2">
              <span className="text-xs text-gray-500">OCR Language:</span>
              <div className="flex bg-gray-100 rounded-lg p-0.5">
                <button
                  type="button"
                  onClick={() => setOcrLang("english")}
                  className={`px-2.5 py-1 text-xs font-medium rounded-md transition-colors ${
                    ocrLang === "english" ? "bg-blue-600 text-white" : "text-gray-500 hover:text-gray-700"
                  }`}
                >
                  English
                </button>
                <button
                  type="button"
                  onClick={() => setOcrLang("tamil")}
                  className={`px-2.5 py-1 text-xs font-medium rounded-md transition-colors ${
                    ocrLang === "tamil" ? "bg-blue-600 text-white" : "text-gray-500 hover:text-gray-700"
                  }`}
                >
                  தமிழ்
                </button>
              </div>
            </div>
            <button onClick={() => setShowUpload(true)}
              className="px-4 py-2 bg-blue-600 text-white text-sm font-medium rounded-lg hover:bg-blue-700">
              + Upload Document
            </button>
          </div>
          {documents.length === 0 ? (
            <div className="bg-white rounded-xl border border-gray-200 p-8 text-center text-gray-500">
              No documents uploaded yet.
            </div>
          ) : (
            <div className="space-y-3">
              {documents.map((doc) => (
                <div key={doc.id} className="bg-white rounded-xl border border-gray-200 p-4">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-3">
                      <div className="w-10 h-10 bg-gray-100 rounded-lg flex items-center justify-center text-sm font-medium text-gray-500 uppercase">
                        {doc.file_type}
                      </div>
                      <div>
                        <p className="text-sm font-medium text-gray-900">{doc.original_filename}</p>
                        <p className="text-xs text-gray-500">{formatBytes(doc.file_size_bytes)} · {new Date(doc.created_at).toLocaleDateString()}</p>
                      </div>
                    </div>
                    <div className="flex items-center gap-2">
                      <span className={`px-2 py-1 text-xs font-medium rounded-full ${
                        doc.ocr_status === "completed" ? "bg-green-100 text-green-700"
                        : doc.ocr_status === "processing" ? "bg-yellow-100 text-yellow-700"
                        : doc.ocr_status === "failed" ? "bg-red-100 text-red-700"
                        : "bg-gray-100 text-gray-600"
                      }`}>OCR: {doc.ocr_status}</span>
                      {doc.ocr_status === "pending" && (
                        <button onClick={() => handleOcr(doc.id)} disabled={ocrLoading === doc.id}
                          className="px-3 py-1 text-xs font-medium bg-indigo-50 text-indigo-700 rounded-lg hover:bg-indigo-100 disabled:opacity-50">
                          {ocrLoading === doc.id ? "Processing..." : "Run OCR"}
                        </button>
                      )}
                      {doc.ocr_status === "completed" && (
                        <button onClick={() => handlePreview(doc.id)}
                          className="px-3 py-1 text-xs font-medium bg-blue-50 text-blue-700 rounded-lg hover:bg-blue-100">
                          {ocrTexts[doc.id] ? "Hide Text" : "View Text"}
                        </button>
                      )}
                      <button onClick={() => handleDownload(doc.id, doc.original_filename)}
                        className="px-3 py-1 text-xs font-medium bg-green-50 text-green-700 rounded-lg hover:bg-green-100">
                        Download
                      </button>
                      <button onClick={() => handleDeleteDoc(doc.id)} disabled={deleteLoading === doc.id}
                        className="px-3 py-1 text-xs font-medium bg-red-50 text-red-700 rounded-lg hover:bg-red-100 disabled:opacity-50">
                        {deleteLoading === doc.id ? "..." : "Delete"}
                      </button>
                    </div>
                  </div>
                  {ocrTexts[doc.id] !== undefined && (
                    <div className="mt-3 p-3 bg-gray-50 rounded-lg">
                      <p className="text-xs font-medium text-gray-600 mb-1">Extracted Text:</p>
                      {ocrTexts[doc.id] ? (
                        <p className="text-sm text-gray-700 whitespace-pre-wrap">{ocrTexts[doc.id]}</p>
                      ) : (
                        <p className="text-sm text-amber-600 italic">No text was extracted. The OCR engine may be unavailable or the image contains no readable text.</p>
                      )}
                    </div>
                  )}
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {/* ── Follow-ups Section ── */}
      {activeSection === "followups" && (
        <div>
          <div className="flex justify-end mb-3">
            <button onClick={() => setShowFollowUp(true)}
              className="px-4 py-2 bg-indigo-600 text-white text-sm font-medium rounded-lg hover:bg-indigo-700">
              + Schedule Follow-Up
            </button>
          </div>
          {followUps.length === 0 ? (
            <div className="bg-white rounded-xl border border-gray-200 p-8 text-center text-gray-500">No follow-ups scheduled.</div>
          ) : (
            <div className="space-y-2">
              {followUps.map((fu) => (
                <div key={fu.id} className="bg-white rounded-xl border border-gray-200 p-4 flex items-center justify-between">
                  <div>
                    <p className="text-sm font-medium text-gray-900 capitalize">{fu.follow_up_type.replace("_", " ")}</p>
                    <p className="text-xs text-gray-500">
                      {new Date(fu.scheduled_date).toLocaleDateString("en-US", { weekday: "short", month: "short", day: "numeric", hour: "2-digit", minute: "2-digit" })}
                      {fu.notes && ` · ${fu.notes}`}
                    </p>
                  </div>
                  <div className="flex items-center gap-2">
                    <span className={`px-2 py-1 text-xs font-medium rounded-full ${fuStatusColor(fu.status)}`}>{fu.status}</span>
                    {fu.status === "scheduled" && (
                      <button onClick={() => handleCompleteFollowUp(fu.id)}
                        className="px-3 py-1 text-xs font-medium bg-green-50 text-green-700 rounded-lg hover:bg-green-100">
                        ✓ Complete
                      </button>
                    )}
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {/* ── Timeline Section ── */}
      {activeSection === "timeline" && (
        <div className="space-y-3">
          {timeline.length === 0 ? (
            <div className="bg-white rounded-xl border border-gray-200 p-8 text-center text-gray-500">No timeline events.</div>
          ) : (
            timeline.map((evt) => (
              <div key={evt.id} className="bg-white rounded-xl border border-gray-200 p-4 flex gap-4">
                <div className="w-2 h-2 mt-2 rounded-full bg-blue-500 shrink-0" />
                <div className="flex-1">
                  <p className="text-sm font-medium text-gray-900">{evt.action}</p>
                  {evt.description && <p className="text-xs text-gray-600 mt-0.5">{evt.description}</p>}
                  <p className="text-xs text-gray-400 mt-1">{new Date(evt.created_at).toLocaleString()}</p>
                </div>
              </div>
            ))
          )}
        </div>
      )}

      {/* ── Reviews Section ── */}
      {activeSection === "reviews" && (
        <div>
          <div className="flex justify-end mb-3">
            <button onClick={() => setShowReview(true)}
              className="px-4 py-2 bg-amber-600 text-white text-sm font-medium rounded-lg hover:bg-amber-700">
              + Add Review
            </button>
          </div>
          {reviews.length === 0 ? (
            <div className="bg-white rounded-xl border border-gray-200 p-8 text-center text-gray-500">No clinician reviews.</div>
          ) : (
            <div className="space-y-3">
              {reviews.map((rev) => (
                <div key={rev.id} className="bg-white rounded-xl border border-gray-200 p-5">
                  <div className="flex items-start justify-between">
                    <div className="flex-1">
                      <p className="text-sm text-gray-700 whitespace-pre-wrap">{rev.summary_text}</p>
                      {rev.reviewer_comments && (
                        <p className="text-sm text-gray-500 mt-2 italic">"{rev.reviewer_comments}"</p>
                      )}
                      <p className="text-xs text-gray-400 mt-2">{new Date(rev.created_at).toLocaleString()}</p>
                    </div>
                    <div className="flex items-center gap-2 ml-4">
                      <span className={`px-2 py-1 text-xs font-medium rounded-full ${
                        rev.status === "approved" ? "bg-green-100 text-green-700"
                        : rev.status === "rejected" ? "bg-red-100 text-red-700"
                        : "bg-yellow-100 text-yellow-700"
                      }`}>{rev.status}</span>
                      {rev.status === "draft" && (
                        <>
                          <button onClick={() => handleReviewStatus(rev.id, "approved")}
                            className="px-3 py-1 text-xs font-medium bg-green-50 text-green-700 rounded-lg hover:bg-green-100">
                            ✓ Approve
                          </button>
                          <button onClick={() => handleReviewStatus(rev.id, "rejected")}
                            className="px-3 py-1 text-xs font-medium bg-red-50 text-red-700 rounded-lg hover:bg-red-100">
                            ✗ Reject
                          </button>
                        </>
                      )}
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {/* ── Modals ── */}
      <DocumentUploadModal open={showUpload} onClose={() => setShowUpload(false)} caseId={caseId!} onUploaded={loadAll} />

      <Modal open={showFollowUp} onClose={() => setShowFollowUp(false)} title="Schedule Follow-Up">
        {fuError && <div className="mb-4 p-3 bg-red-50 text-red-700 text-sm rounded-lg">{fuError}</div>}
        <form onSubmit={handleAddFollowUp} className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Type *</label>
            <select required value={fuForm.follow_up_type} onChange={(e) => setFuForm({ ...fuForm, follow_up_type: e.target.value })}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-blue-500">
              <option value="">Select type...</option>
              {FOLLOW_UP_TYPES.map((t) => <option key={t.value} value={t.value}>{t.label}</option>)}
            </select>
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Date & Time *</label>
            <input type="datetime-local" required value={fuForm.scheduled_date} onChange={(e) => setFuForm({ ...fuForm, scheduled_date: e.target.value })}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-blue-500" />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Notes</label>
            <textarea rows={2} value={fuForm.notes} onChange={(e) => setFuForm({ ...fuForm, notes: e.target.value })}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-blue-500" />
          </div>
          <div className="flex justify-end gap-3 pt-2">
            <button type="button" onClick={() => setShowFollowUp(false)} className="px-4 py-2 text-sm text-gray-600 hover:text-gray-800">Cancel</button>
            <button type="submit" disabled={fuSaving} className="px-4 py-2 bg-indigo-600 text-white text-sm font-medium rounded-lg hover:bg-indigo-700 disabled:opacity-50">
              {fuSaving ? "Saving..." : "Schedule"}
            </button>
          </div>
        </form>
      </Modal>

      <Modal open={showReview} onClose={() => setShowReview(false)} title="Add Clinician Review">
        {reviewError && <div className="mb-4 p-3 bg-red-50 text-red-700 text-sm rounded-lg">{reviewError}</div>}
        <form onSubmit={handleCreateReview} className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Summary *</label>
            <textarea rows={5} required value={reviewForm.summary_text}
              onChange={(e) => setReviewForm({ ...reviewForm, summary_text: e.target.value })}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-blue-500"
              placeholder="Clinical summary or review notes..." />
          </div>
          <div className="flex items-center gap-2">
            <input type="checkbox" id="disclaimer" checked={reviewForm.ai_disclaimer_acknowledged}
              onChange={(e) => setReviewForm({ ...reviewForm, ai_disclaimer_acknowledged: e.target.checked })}
              className="rounded border-gray-300" />
            <label htmlFor="disclaimer" className="text-sm text-gray-700">
              I acknowledge this may contain AI-generated content and have reviewed it for accuracy
            </label>
          </div>
          <div className="flex justify-end gap-3 pt-2">
            <button type="button" onClick={() => setShowReview(false)} className="px-4 py-2 text-sm text-gray-600 hover:text-gray-800">Cancel</button>
            <button type="submit" disabled={reviewSaving} className="px-4 py-2 bg-amber-600 text-white text-sm font-medium rounded-lg hover:bg-amber-700 disabled:opacity-50">
              {reviewSaving ? "Saving..." : "Submit Review"}
            </button>
          </div>
        </form>
      </Modal>
    </div>
  );
}
