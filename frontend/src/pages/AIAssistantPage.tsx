import { useState, useEffect } from "react";
import { aiApi, casesApi } from "../api";
import type { Case, AIResponse } from "../types";
import AIResultCard from "../components/AIResultCard";

type Tab = "summarize" | "explain" | "specialist" | "questions";
type Language = "english" | "tamil";

const TABS: { key: Tab; label: string; icon: string }[] = [
  { key: "summarize", label: "Summarize Case", icon: "📋" },
  { key: "explain", label: "Explain Terms", icon: "📖" },
  { key: "specialist", label: "Suggest Specialist", icon: "🩺" },
  { key: "questions", label: "Questions for Doctor", icon: "❓" },
];

export default function AIAssistantPage() {
  const [activeTab, setActiveTab] = useState<Tab>("explain");
  const [language, setLanguage] = useState<Language>("english");
  const [cases, setCases] = useState<Case[]>([]);
  const [selectedCase, setSelectedCase] = useState("");
  const [selectedCaseData, setSelectedCaseData] = useState<Case | null>(null);
  const [explainText, setExplainText] = useState("");
  const [context, setContext] = useState("");
  const [result, setResult] = useState<AIResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    casesApi.list({ per_page: 100 }).then(({ data }) => setCases(data.items)).catch(() => {});
  }, []);

  const handleCaseChange = (caseId: string) => {
    setSelectedCase(caseId);
    setSelectedCaseData(cases.find((c) => c.id === caseId) || null);
  };

  const langParam = language === "tamil" ? "tamil" : undefined;

  const handleGenerate = async (e: { preventDefault: () => void }) => {
    e.preventDefault();
    setLoading(true);
    setResult(null);
    setError("");

    try {
      let res: { data: AIResponse };
      switch (activeTab) {
        case "summarize":
          res = await aiApi.summarize(selectedCase, undefined, langParam);
          break;
        case "explain":
          res = await aiApi.explain(explainText, langParam);
          break;
        case "specialist":
          res = await aiApi.suggestSpecialist(selectedCase, undefined, langParam);
          break;
        case "questions":
          res = await aiApi.questionsForDoctor(selectedCase, context || undefined, langParam);
          break;
      }
      setResult(res!.data);
    } catch (err: unknown) {
      const msg = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail;
      setError(msg || "AI request failed. Try again or check Settings for cloud provider keys.");
    } finally {
      setLoading(false);
    }
  };

  const resultTitle = TABS.find((t) => t.key === activeTab)?.label
    ? `${TABS.find((t) => t.key === activeTab)?.icon} ${TABS.find((t) => t.key === activeTab)?.label} — Result${language === "tamil" ? " (தமிழ்)" : ""}`
    : undefined;

  return (
    <div>
      <div className="mb-6">
        <h2 className="text-2xl font-bold text-gray-900">AI Assistant</h2>
        <p className="text-gray-500 mt-1">
          AI-powered tools to help with medical summaries, term explanations, and care planning.
        </p>
      </div>

      {/* Tabs */}
      <div className="flex gap-1 mb-6 bg-gray-100 rounded-lg p-1" role="tablist" aria-label="AI tools">
        {TABS.map((tab) => (
          <button
            key={tab.key}
            role="tab"
            aria-selected={activeTab === tab.key}
            onClick={() => { setActiveTab(tab.key); setResult(null); setError(""); }}
            className={`flex-1 px-4 py-2.5 text-sm font-medium rounded-md transition-colors ${
              activeTab === tab.key
                ? "bg-white text-gray-900 shadow-sm"
                : "text-gray-500 hover:text-gray-700"
            }`}
          >
            {tab.icon} {tab.label}
          </button>
        ))}
      </div>

      {/* Input Form */}
      <div className="bg-white rounded-xl border border-gray-200 p-6 mb-6">
        <form onSubmit={handleGenerate} className="space-y-4" aria-label="AI request form">

          {/* Language Toggle */}
          <div className="flex items-center gap-3">
            <span className="text-sm font-medium text-gray-700">Output language:</span>
            <div className="flex bg-gray-100 rounded-lg p-0.5">
              <button
                type="button"
                onClick={() => setLanguage("english")}
                className={`px-3 py-1.5 text-sm font-medium rounded-md transition-colors ${
                  language === "english" ? "bg-white text-gray-900 shadow-sm" : "text-gray-500"
                }`}
              >
                English
              </button>
              <button
                type="button"
                onClick={() => setLanguage("tamil")}
                className={`px-3 py-1.5 text-sm font-medium rounded-md transition-colors ${
                  language === "tamil" ? "bg-white text-gray-900 shadow-sm" : "text-gray-500"
                }`}
              >
                தமிழ்
              </button>
            </div>
          </div>

          {(activeTab === "summarize" || activeTab === "specialist" || activeTab === "questions") && (
            <>
              <div>
                <label htmlFor="case-select" className="block text-sm font-medium text-gray-700 mb-1">Select Case *</label>
                <select
                  id="case-select"
                  required
                  value={selectedCase}
                  onChange={(e) => handleCaseChange(e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-blue-500"
                >
                  <option value="">Choose a case...</option>
                  {cases.map((c) => (
                    <option key={c.id} value={c.id}>
                      {c.diagnosis} ({c.status.replace("_", " ")})
                    </option>
                  ))}
                </select>
              </div>

              {selectedCaseData && (
                <div className="bg-blue-50 rounded-lg p-4 space-y-1">
                  <h4 className="text-xs font-semibold text-blue-700 uppercase">Case Info (from profile)</h4>
                  <div className="grid grid-cols-2 gap-2 text-sm">
                    <div>
                      <span className="text-gray-500">Diagnosis:</span>{" "}
                      <span className="font-medium text-gray-900">{selectedCaseData.diagnosis}</span>
                    </div>
                    <div>
                      <span className="text-gray-500">Priority:</span>{" "}
                      <span className="font-medium text-gray-900 capitalize">{selectedCaseData.priority}</span>
                    </div>
                    <div>
                      <span className="text-gray-500">Status:</span>{" "}
                      <span className="font-medium text-gray-900 capitalize">{selectedCaseData.status.replace("_", " ")}</span>
                    </div>
                    {selectedCaseData.notes && (
                      <div className="col-span-2">
                        <span className="text-gray-500">Notes:</span>{" "}
                        <span className="text-gray-700">{selectedCaseData.notes}</span>
                      </div>
                    )}
                  </div>
                </div>
              )}
            </>
          )}

          {activeTab === "explain" && (
            <div>
              <label htmlFor="explain-text" className="block text-sm font-medium text-gray-700 mb-1">Medical Text to Explain *</label>
              <textarea
                id="explain-text"
                required
                rows={5}
                value={explainText}
                onChange={(e) => setExplainText(e.target.value)}
                placeholder="Paste medical terms, diagnosis text, or lab results..."
                className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-blue-500"
              />
            </div>
          )}

          {activeTab === "questions" && (
            <div>
              <label htmlFor="context-text" className="block text-sm font-medium text-gray-700 mb-1">Additional Context</label>
              <textarea
                id="context-text"
                rows={3}
                value={context}
                onChange={(e) => setContext(e.target.value)}
                placeholder="Any additional context for generating questions..."
                className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-blue-500"
              />
            </div>
          )}

          <button
            type="submit"
            disabled={loading}
            className="px-6 py-2.5 bg-blue-600 text-white text-sm font-medium rounded-lg hover:bg-blue-700 disabled:opacity-50 transition-colors"
          >
            {loading ? (
              <span className="flex items-center gap-2">
                <span className="animate-spin">⏳</span> Generating{language === "tamil" ? " in தமிழ்..." : "..."}
              </span>
            ) : (
              `Generate${language === "tamil" ? " in தமிழ்" : ""}`
            )}
          </button>
        </form>
      </div>

      {/* Error */}
      {error && (
        <div className="mb-6 p-4 bg-red-50 border border-red-200 rounded-xl" role="alert">
          <p className="text-sm text-red-700">{error}</p>
        </div>
      )}

      {/* Result */}
      {result && (
        <div className="mb-6">
          <AIResultCard result={result} title={resultTitle} />
        </div>
      )}
    </div>
  );
}
