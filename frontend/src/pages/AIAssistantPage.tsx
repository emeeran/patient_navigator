import { useState, useEffect, type FormEvent } from "react";
import { aiApi, casesApi } from "../api";
import type { Case, AIResponse } from "../types";

type Tab = "summarize" | "explain" | "specialist" | "questions";

const TABS: { key: Tab; label: string; icon: string }[] = [
  { key: "summarize", label: "Summarize Case", icon: "📋" },
  { key: "explain", label: "Explain Terms", icon: "📖" },
  { key: "specialist", label: "Suggest Specialist", icon: "🩺" },
  { key: "questions", label: "Questions for Doctor", icon: "❓" },
];

export default function AIAssistantPage() {
  const [activeTab, setActiveTab] = useState<Tab>("explain");
  const [cases, setCases] = useState<Case[]>([]);
  const [selectedCase, setSelectedCase] = useState("");
  const [explainText, setExplainText] = useState("");
  const [context, setContext] = useState("");
  const [result, setResult] = useState<AIResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    casesApi.list({ per_page: 100 }).then(({ data }) => setCases(data.items)).catch(() => {});
  }, []);

  const handleGenerate = async (e: FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setResult(null);
    setError("");

    try {
      let res: { data: AIResponse };
      switch (activeTab) {
        case "summarize":
          res = await aiApi.summarize(selectedCase);
          break;
        case "explain":
          res = await aiApi.explain(explainText);
          break;
        case "specialist":
          res = await aiApi.suggestSpecialist(selectedCase);
          break;
        case "questions":
          res = await aiApi.questionsForDoctor(selectedCase, context || undefined);
          break;
      }
      setResult(res!.data);
    } catch (err: unknown) {
      const msg = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail;
      setError(msg || "AI request failed. Make sure Ollama is running.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div>
      <div className="mb-6">
        <h2 className="text-2xl font-bold text-gray-900">AI Assistant</h2>
        <p className="text-gray-500 mt-1">
          AI-powered tools to help with medical summaries, term explanations, and care planning.
        </p>
      </div>

      {/* Tabs */}
      <div className="flex gap-1 mb-6 bg-gray-100 rounded-lg p-1">
        {TABS.map((tab) => (
          <button
            key={tab.key}
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
        <form onSubmit={handleGenerate} className="space-y-4">
          {(activeTab === "summarize" || activeTab === "specialist" || activeTab === "questions") && (
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Select Case *</label>
              <select
                required
                value={selectedCase}
                onChange={(e) => setSelectedCase(e.target.value)}
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
          )}

          {activeTab === "explain" && (
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Medical Text to Explain *</label>
              <textarea
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
              <label className="block text-sm font-medium text-gray-700 mb-1">Additional Context</label>
              <textarea
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
                <span className="animate-spin">⏳</span> Generating...
              </span>
            ) : (
              "Generate"
            )}
          </button>
        </form>
      </div>

      {/* Error */}
      {error && (
        <div className="mb-6 p-4 bg-red-50 border border-red-200 rounded-xl">
          <p className="text-sm text-red-700">{error}</p>
        </div>
      )}

      {/* Result */}
      {result && (
        <div className="bg-white rounded-xl border border-gray-200 overflow-hidden">
          <div className="p-6">
            <h3 className="font-semibold text-gray-900 mb-3">
              {TABS.find((t) => t.key === activeTab)?.icon}{" "}
              {TABS.find((t) => t.key === activeTab)?.label} — Result
            </h3>
            <div className="prose prose-sm max-w-none">
              <p className="text-gray-700 whitespace-pre-wrap">{result.content}</p>
            </div>
            {result.model && (
              <p className="text-xs text-gray-400 mt-4">Model: {result.model}</p>
            )}
          </div>
          <div className="px-6 py-3 bg-amber-50 border-t border-amber-200">
            <p className="text-xs text-amber-800">
              ⚠️ <strong>Medical Disclaimer:</strong> {result.disclaimer}
            </p>
          </div>
        </div>
      )}
    </div>
  );
}
