/**
 * client.js – Fetch wrapper for the FastAPI backend.
 *
 * All requests go to http://localhost:8000/api (Vite proxy forwards /api in dev).
 */

const API_BASE = '/api';

// ─── Pipeline ────────────────────────────────────────────────────────────────

/**
 * Run the full agent pipeline.
 *
 * @param {string}          idea
 * @param {'mvp'|'full'}    mode
 * @param {Object}          weights  – { effectiveness, efficiency, … }
 * @returns {Promise<Object>}  PipelineResult
 */
export async function runPipeline(idea, mode, weights) {
  const response = await fetch(`${API_BASE}/run`, {
    method:  'POST',
    headers: { 'Content-Type': 'application/json' },
    body:    JSON.stringify({ idea, mode, weights }),
  });

  if (!response.ok) {
    const body = await response.json().catch(() => ({}));
    throw new Error(
      body.detail ?? `Server error ${response.status}: ${response.statusText}`
    );
  }

  return response.json();
}

// ─── Exports ─────────────────────────────────────────────────────────────────

/**
 * Export the pipeline result as a .docx file and trigger a download.
 *
 * @param {Object} result  – PipelineResult
 * @returns {Promise<Blob>}
 */
export async function exportDocx(result) {
  const response = await fetch(`${API_BASE}/export/docx`, {
    method:  'POST',
    headers: { 'Content-Type': 'application/json' },
    body:    JSON.stringify(result),
  });

  if (!response.ok) {
    const body = await response.json().catch(() => ({}));
    throw new Error(body.detail ?? `Export failed: ${response.status}`);
  }

  const blob = await response.blob();

  // Auto-trigger browser download
  const url  = URL.createObjectURL(blob);
  const link = document.createElement('a');
  link.href     = url;
  link.download = 'phoenix_cap_policy_memo.docx';
  link.click();
  URL.revokeObjectURL(url);

  return blob;
}

/**
 * Export the pipeline result as Markdown text.
 *
 * @param {Object} result  – PipelineResult
 * @returns {Promise<string>}
 */
export async function exportMarkdown(result) {
  const response = await fetch(`${API_BASE}/export/markdown`, {
    method:  'POST',
    headers: { 'Content-Type': 'application/json' },
    body:    JSON.stringify(result),
  });

  if (!response.ok) {
    const body = await response.json().catch(() => ({}));
    throw new Error(body.detail ?? `Export failed: ${response.status}`);
  }

  return response.text();
}

// ─── Health ──────────────────────────────────────────────────────────────────

/**
 * Health-check – verify the backend is reachable.
 * @returns {Promise<{status: string, model: string}>}
 */
export async function checkHealth() {
  const response = await fetch(`${API_BASE}/health`);
  if (!response.ok) throw new Error('Backend unreachable');
  return response.json();
}
