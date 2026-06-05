import { useState, useRef, type FormEvent } from "react";
import { documentsApi } from "../api";

const ACCEPTED_TYPES = [
  "application/pdf",
  "image/jpeg",
  "image/png",
  "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
];

const ACCEPTED_EXTENSIONS = ".pdf,.jpg,.jpeg,.png,.docx";
const MAX_SIZE_MB = 25;

interface DocumentUploadModalProps {
  open: boolean;
  onClose: () => void;
  caseId: string;
  onUploaded: () => void;
}

export default function DocumentUploadModal({
  open,
  onClose,
  caseId,
  onUploaded,
}: DocumentUploadModalProps) {
  const [file, setFile] = useState<File | null>(null);
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState("");
  const inputRef = useRef<HTMLInputElement>(null);

  if (!open) return null;

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const f = e.target.files?.[0];
    setError("");
    if (!f) return;

    if (!ACCEPTED_TYPES.includes(f.type)) {
      setError("Unsupported file type. Accepted: PDF, JPEG, PNG, DOCX.");
      return;
    }

    if (f.size > MAX_SIZE_MB * 1024 * 1024) {
      setError(`File too large. Maximum size: ${MAX_SIZE_MB}MB.`);
      return;
    }

    setFile(f);
  };

  const handleUpload = async (e: FormEvent) => {
    e.preventDefault();
    if (!file) return;

    setUploading(true);
    setError("");
    try {
      await documentsApi.upload(caseId, file);
      setFile(null);
      if (inputRef.current) inputRef.current.value = "";
      onUploaded();
      onClose();
    } catch (err: unknown) {
      const msg = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail;
      setError(msg || "Upload failed");
    } finally {
      setUploading(false);
    }
  };

  const formatSize = (bytes: number) => {
    if (bytes < 1024) return `${bytes} B`;
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
    return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center">
      <div className="absolute inset-0 bg-black/40" onClick={onClose} />
      <div className="relative bg-white rounded-xl shadow-xl w-full max-w-md mx-4">
        <div className="flex items-center justify-between px-6 py-4 border-b border-gray-200">
          <h3 className="text-lg font-semibold text-gray-900">Upload Document</h3>
          <button onClick={onClose} className="text-gray-400 hover:text-gray-600 text-xl leading-none">
            &times;
          </button>
        </div>
        <div className="p-6">
          {error && (
            <div className="mb-4 p-3 bg-red-50 text-red-700 text-sm rounded-lg">{error}</div>
          )}

          <form onSubmit={handleUpload} className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Select File
              </label>
              <input
                ref={inputRef}
                type="file"
                accept={ACCEPTED_EXTENSIONS}
                onChange={handleFileChange}
                className="w-full text-sm text-gray-500 file:mr-4 file:py-2 file:px-4 file:rounded-lg file:border-0 file:text-sm file:font-medium file:bg-blue-50 file:text-blue-700 hover:file:bg-blue-100"
              />
              <p className="text-xs text-gray-400 mt-1">
                Accepted: PDF, JPEG, PNG, DOCX (max {MAX_SIZE_MB}MB)
              </p>
            </div>

            {file && (
              <div className="p-3 bg-gray-50 rounded-lg">
                <p className="text-sm font-medium text-gray-700">{file.name}</p>
                <p className="text-xs text-gray-500">{formatSize(file.size)} — {file.type}</p>
              </div>
            )}

            <div className="flex justify-end gap-3 pt-2">
              <button
                type="button"
                onClick={onClose}
                className="px-4 py-2 text-sm text-gray-600 hover:text-gray-800"
              >
                Cancel
              </button>
              <button
                type="submit"
                disabled={!file || uploading}
                className="px-4 py-2 bg-blue-600 text-white text-sm font-medium rounded-lg hover:bg-blue-700 disabled:opacity-50 transition-colors"
              >
                {uploading ? "Uploading..." : "Upload"}
              </button>
            </div>
          </form>
        </div>
      </div>
    </div>
  );
}
