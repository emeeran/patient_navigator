import { useState, useRef } from "react";
import type { AIResponse } from "../types";

interface AIResultCardProps {
  result: AIResponse;
  title?: string;
}

export default function AIResultCard({ result, title }: AIResultCardProps) {
  const [copied, setCopied] = useState(false);
  const contentRef = useRef<HTMLDivElement>(null);

  const handleCopy = async () => {
    if (!result.content) return;
    try {
      await navigator.clipboard.writeText(result.content);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch {
      setCopied(false);
    }
  };

  const handlePrint = () => {
    if (!contentRef.current) return;
    const pw = window.open("", "_blank");
    if (!pw) return;

    pw.document.title = `${title || "AI Result"} — Patient Navigator`;
    const style = pw.document.createElement("style");
    style.textContent = `
      body { font-family: "Noto Sans", "Noto Sans Tamil", system-ui, sans-serif; max-width: 700px; margin: 40px auto; padding: 0 20px; color: #1a1a1a; }
      h1 { font-size: 18px; margin-bottom: 4px; }
      .meta { font-size: 12px; color: #888; margin-bottom: 20px; }
      .content { white-space: pre-wrap; line-height: 1.6; font-size: 14px; }
      .disclaimer { margin-top: 24px; padding: 12px; background: #fffbeb; border: 1px solid #fde68a; border-radius: 8px; font-size: 12px; color: #92400e; }
    `;
    pw.document.head.appendChild(style);

    const h1 = pw.document.createElement("h1");
    h1.textContent = title || "AI Result";
    pw.document.body.appendChild(h1);

    const meta = pw.document.createElement("div");
    meta.className = "meta";
    meta.textContent = `Generated: ${new Date().toLocaleString()}${result.model ? ` | Model: ${result.model}` : ""}${result.provider ? ` | Provider: ${result.provider}` : ""}`;
    pw.document.body.appendChild(meta);

    const content = pw.document.createElement("div");
    content.className = "content";
    content.textContent = result.content;
    pw.document.body.appendChild(content);

    if (result.disclaimer) {
      const d = pw.document.createElement("div");
      d.className = "disclaimer";
      d.innerHTML = `⚠️ <strong>Medical Disclaimer:</strong> ${result.disclaimer}`;
      pw.document.body.appendChild(d);
    }

    pw.print();
  };

  return (
    <div className="bg-white rounded-xl border border-gray-200 overflow-hidden">
      <div className="p-6" ref={contentRef}>
        {/* Header with actions */}
        <div className="flex items-center justify-between mb-3">
          <div>
            {title && (
              <h3 className="font-semibold text-gray-900">{title}</h3>
            )}
            <div className="flex items-center gap-2 mt-0.5">
              {result.provider && (
                <span className="inline-flex items-center text-xs text-gray-400">
                  via {result.provider}
                </span>
              )}
              {result.model && (
                <span className="text-xs text-gray-400">• {result.model}</span>
              )}
            </div>
          </div>
          <div className="flex items-center gap-2">
            <button
              onClick={handleCopy}
              className="inline-flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium text-gray-600 bg-gray-100 rounded-lg hover:bg-gray-200 transition-colors"
              aria-label="Copy to clipboard"
            >
              {copied ? "✓ Copied" : "📋 Copy"}
            </button>
            <button
              onClick={handlePrint}
              className="inline-flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium text-gray-600 bg-gray-100 rounded-lg hover:bg-gray-200 transition-colors"
              aria-label="Print result"
            >
              🖨️ Print
            </button>
          </div>
        </div>

        {/* Content */}
        <div className="prose prose-sm max-w-none">
          <p className="text-gray-700 whitespace-pre-wrap">{result.content}</p>
        </div>
      </div>

      {/* Disclaimer */}
      {result.disclaimer && (
        <div className="px-6 py-3 bg-amber-50 border-t border-amber-200">
          <p className="text-xs text-amber-800">
            ⚠️ <strong>Medical Disclaimer:</strong> {result.disclaimer}
          </p>
        </div>
      )}
    </div>
  );
}
