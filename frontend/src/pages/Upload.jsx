// src/pages/Upload.jsx
import { useState } from "react";
import Container from "../components/Container";
import { uploadUserItem } from "../api";
import { useNavigate } from "react-router-dom";

export default function Upload() {
  const [file, setFile] = useState(null);
  const [name, setName] = useState("");
  const [error, setError] = useState("");
  const [duplicatePrompt, setDuplicatePrompt] = useState(null);

  const [bulkFiles, setBulkFiles] = useState([]);
  const [bulkAllowDuplicates, setBulkAllowDuplicates] = useState(false);
  const [bulkStatus, setBulkStatus] = useState(null);
  const [bulkUploading, setBulkUploading] = useState(false);

  const navigate = useNavigate();

  const user = getUser();
  if (!user) {
    navigate("/create-user", { replace: true });
    return null;
  }

  // ---------- single upload ----------

  async function handleUpload(e) {
    e.preventDefault();
    setError("");
    setBulkStatus(null);
    setDuplicatePrompt(null);

    if (!file) return;

    try {
      await uploadUserItem(user.id, { file, name, allowDuplicate: false });
      setFile(null);
      setName("");
      navigate("/dashboard");
    } catch (err) {
      const status = err?.response?.status;
      const detail = err?.response?.data?.detail;

      if (status === 409 && detail?.reason === "duplicate_item") {
        setDuplicatePrompt({
          message:
            detail?.message ||
            "It seems like this item already exists in your wardrobe.",
          file,
          name,
        });
        return;
      }

      console.error(err);
      setError("Upload failed. Please try again.");
    }
  }

  async function confirmDuplicateUpload() {
    if (!duplicatePrompt?.file) return;

    setError("");
    try {
      await uploadUserItem(user.id, {
        file: duplicatePrompt.file,
        name: duplicatePrompt.name,
        allowDuplicate: true,
      });
      setDuplicatePrompt(null);
      setFile(null);
      setName("");
      navigate("/dashboard");
    } catch (err) {
      console.error(err);
      setError("Upload failed even after confirming duplicate.");
    }
  }

  function cancelDuplicateUpload() {
    setDuplicatePrompt(null);
  }

  // ---------- bulk upload ----------

  async function handleBulkUpload(e) {
    e.preventDefault();
    setError("");
    setDuplicatePrompt(null);
    setBulkStatus(null);

    if (!bulkFiles.length) return;

    setBulkUploading(true);
    let uploaded = 0;
    let duplicates = 0;
    let failed = 0;

    for (const f of bulkFiles) {
      try {
        await uploadUserItem(user.id, {
          file: f,
          name: "",
          allowDuplicate: bulkAllowDuplicates,
        });
        uploaded += 1;
      } catch (err) {
        const status = err?.response?.status;
        const detail = err?.response?.data?.detail;

        if (!bulkAllowDuplicates && status === 409 && detail?.reason === "duplicate_item") {
          duplicates += 1;
          continue;
        }

        console.error("bulk upload error", err);
        failed += 1;
      }
    }

    setBulkUploading(false);
    setBulkFiles([]);

    setBulkStatus({
      uploaded,
      duplicates,
      failed,
      allowDuplicates: bulkAllowDuplicates,
    });
  }

  return (
    <Container className="max-w-2xl">
      <h2 className="text-2xl font-semibold mb-2">Upload</h2>
      <p className="text-sm text-text-muted mb-6">
        add new pieces from your real wardrobe. photos are classified
        automatically and show up in your dashboard.
      </p>

      {/* SINGLE UPLOAD */}
      <section className="space-y-4 mb-10">
        <h3 className="text-sm font-semibold">Single item</h3>
        <form onSubmit={handleUpload} className="space-y-4">
          <input
            className="input w-full"
            placeholder="Optional name for this item"
            value={name}
            onChange={(e) => setName(e.target.value)}
          />

          <div className="card p-6 space-y-3">
            <label
              htmlFor="file"
              className="flex items-center justify-between rounded-2xl border border-dashed border-accent/50 bg-panel/80 px-4 py-4 cursor-pointer hover:border-accent hover:bg-panel transition-all"
            >
              <div>
                <p className="text-sm font-medium">Choose file</p>
                <p className="text-xs text-text-muted">
                  {file ? file.name : "No file chosen yet"}
                </p>
              </div>
            </label>
            <input
              id="file"
              type="file"
              accept="image/*"
              onChange={(e) => setFile(e.target.files?.[0] || null)}
              className="hidden"
            />
            <p className="text-xs text-text-muted">
              AI classification runs automatically if enabled on the server.
            </p>
            <ul className="text-xs text-text-muted space-y-1 list-disc list-inside">
              <li>one main item per photo works best.</li>
              <li>try to avoid very busy backgrounds when you can.</li>
              <li>you can refine labe|s later from the wardrobe dashboard.</li>
            </ul>
          </div>

          <button
            className="btn btn-accent breathe w-full"
            disabled={!file}
          >
            Upload
          </button>
        </form>

        {/* inline duplicate prompt for single upload */}
        {duplicatePrompt && (
          <div className="mt-4 card p-4 border border-amber-400/60 bg-amber-500/10 text-xs">
            <p className="text-amber-100 mb-2">
              {duplicatePrompt.message}
            </p>
            <p className="text-amber-200 mb-3">
              If this is actually a different item or you want a second copy
              in your wardrobe, you can still upload it.
            </p>
            <div className="flex gap-2 justify-end">
              <button
                type="button"
                className="btn btn-muted text-xs"
                onClick={cancelDuplicateUpload}
              >
                Cancel
              </button>
              <button
                type="button"
                className="btn btn-accent text-xs"
                onClick={confirmDuplicateUpload}
              >
                Upload anyway
              </button>
            </div>
          </div>
        )}
      </section>

      {/* BULK UPLOAD SECTION */}
      <section className="space-y-4 mb-4">
        <h3 className="text-sm font-semibold">Bulk upload</h3>
        <p className="text-xs text-text-muted">
          select multiple photos at once to quickly rebuild or import a wardrobe.
        </p>

        <form onSubmit={handleBulkUpload} className="space-y-4">
          <div className="card p-6 space-y-3">
            <label
              htmlFor="bulk-files"
              className="flex items-center justify-between rounded-2xl border border-dashed border-border bg-panel/80 px-4 py-4 cursor-pointer hover:border-accent hover:bg-panel transition-all"
            >
              <div>
                <p className="text-sm font-medium">Choose files</p>
                <p className="text-xs text-text-muted">
                  {bulkFiles.length
                    ? `${bulkFiles.length} file${bulkFiles.length > 1 ? "s" : ""} selected`
                    : "No files chosen yet"}
                </p>
              </div>
            </label>
            <input
              id="bulk-files"
              type="file"
              multiple
              accept="image/*"
              onChange={(e) =>
                setBulkFiles(Array.from(e.target.files || []))
              }
              className="hidden"
            />

            <label className="flex items-center gap-2 text-xs text-text-muted">
              <input
                type="checkbox"
                className="rounded bg-panel border-border"
                checked={bulkAllowDuplicates}
                onChange={(e) => setBulkAllowDuplicates(e.target.checked)}
              />
              <span>
                Allow duplicates in this batch (skip detection and upload
                everything).
              </span>
            </label>
          </div>

          <button
            className="btn w-full"
            type="submit"
            disabled={!bulkFiles.length || bulkUploading}
          >
            {bulkUploading ? "Uploading…" : "Upload all"}
          </button>
        </form>

        {bulkStatus && (
          <div className="mt-3 text-[11px] text-text-muted">
            <p>
              Uploaded: <span className="text-text">{bulkStatus.uploaded}</span>
              {bulkStatus.duplicates > 0 && (
                <>
                  {" · "}Duplicates skipped:{" "}
                  <span className="text-text">
                    {bulkStatus.duplicates}
                  </span>
                </>
              )}
              {bulkStatus.failed > 0 && (
                <>
                  {" · "}Failed:{" "}
                  <span className="text-text">{bulkStatus.failed}</span>
                </>
              )}
            </p>
          </div>
        )}
      </section>

      {error && (
        <p className="mt-3 text-xs text-red-400">
          {error}
        </p>
      )}

      <div className="mt-8 text-xs text-text-muted space-y-1">
        <p className="font-medium text-text">
          what happens after you upload?
        </p>
        <p>
          we store the image, run the classifier, and drop the item into
          your wardrobe with season, color, and formality tags so it can
          be used in future outfits.
        </p>
      </div>
    </Container>
  );
}

function getUser() {
  try {
    const raw = localStorage.getItem("cp:user");
    return raw ? JSON.parse(raw) : null;
  } catch {
    return null;
  }
}
