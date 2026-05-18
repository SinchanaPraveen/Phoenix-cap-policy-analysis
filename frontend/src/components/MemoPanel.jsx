import React, { useState } from 'react';
import { exportDocx, exportMarkdown } from '../api/client.js';

// ─── Word count badge ─────────────────────────────────────────────────────────
function WordCountBadge({ count }) {
  if (!count) return null;
  if (count >= 400 && count <= 450) {
    return (
      <span className="mp-wc-badge mp-wc-badge--ok">
        Word count: {count} ✓
      </span>
    );
  }
  if (count > 450) {
    return (
      <span className="mp-wc-badge mp-wc-badge--warn">
        ⚠ Memo exceeds 450 words — may need editing ({count} words)
      </span>
    );
  }
  return (
    <span className="mp-wc-badge mp-wc-badge--warn">
      ⚠ Memo is under 400 words — may be too brief ({count} words)
    </span>
  );
}

// ─── Skeleton placeholder ─────────────────────────────────────────────────────
function MemoSkeleton() {
  return (
    <div className="mp-skeleton" aria-busy="true">
      {[90, 60, 80, 70, 55, 85, 65, 75].map((w, i) => (
        <span key={i} className="mp-skeleton-line" style={{ width: `${w}%` }} />
      ))}
    </div>
  );
}

/**
 * MemoPanel – formatted policy memorandum.
 *
 * Props:
 *   memo       {PolicyMemo|null}
 *   isLoading  {boolean}
 *   weights    {object|null}  – evaluation weights used for this run
 */
export default function MemoPanel({ memo, isLoading = false, weights = null }) {
  const [exportError, setExportError]   = useState(null);
  const [exporting,   setExporting]     = useState(false);
  const [weightsOpen, setWeightsOpen]   = useState(false);

  const handleExportMd = async () => {
    try {
      setExportError(null);
      setExporting(true);
      let text;
      try {
        text = await exportMarkdown({ stage4: memo });
      } catch {
        text = buildMarkdown(memo);
      }
      downloadText(text, 'phoenix_cap_policy_memo.md', 'text/markdown');
    } catch (err) {
      setExportError(err.message);
    } finally {
      setExporting(false);
    }
  };

  const handleExportDocx = async () => {
    try {
      setExportError(null);
      setExporting(true);
      await exportDocx({ stage4: memo });
    } catch (err) {
      setExportError(err.message);
    } finally {
      setExporting(false);
    }
  };

  return (
    <div className="mp-root">
      {/* ── Memorandum header ── */}
      <div className="mp-official-header">
        <span className="mp-official-seal">🏛</span>
        <div>
          <p className="mp-memorandum-label">MEMORANDUM</p>
          <p className="mp-memorandum-sub">City of Phoenix · Climate Action Plan</p>
        </div>
      </div>

      {isLoading && !memo && <MemoSkeleton />}

      {memo && (
        <>
          {/* ── Body sections ── */}
          <div className="mp-body">
            <MemoSection title="ISSUE">
              <p>{memo.issue}</p>
            </MemoSection>

            <MemoSection title="BACKGROUND">
              <p>{memo.background}</p>
            </MemoSection>

            {memo.key_findings?.length > 0 && (
              <MemoSection title="KEY FINDINGS">
                <ul className="mp-findings-list">
                  {memo.key_findings.map((f, i) => (
                    <li key={i}>{f}</li>
                  ))}
                </ul>
              </MemoSection>
            )}

            <MemoSection title="RECOMMENDATION">
              <p>{memo.recommendation}</p>
            </MemoSection>

            {memo.next_steps?.length > 0 && (
              <MemoSection title="NEXT STEPS">
                <ol className="mp-steps-list">
                  {memo.next_steps.map((s, i) => (
                    <li key={i}>{s}</li>
                  ))}
                </ol>
              </MemoSection>
            )}
          </div>

          {/* ── Footer: citations + word count ── */}
          <div className="mp-footer">
            {memo.citations?.length > 0 && (
              <div className="mp-citations">
                <span className="mp-citations-label">CAP Citations</span>
                <div className="mp-citation-pills">
                  {memo.citations.map((c, i) => (
                    <span key={i} className="mp-citation-pill" title={c}>
                      {c.length > 60 ? `${c.slice(0, 57)}…` : c}
                    </span>
                  ))}
                </div>
              </div>
            )}

            <div className="mp-footer-bar">
              <WordCountBadge count={memo.word_count} />

              <div className="mp-export-btns">
                <button
                  className="mp-export-btn"
                  onClick={handleExportDocx}
                  disabled={exporting}
                  title="Export as Word document"
                >
                  Export .docx
                </button>
                <button
                  className="mp-export-btn"
                  onClick={handleExportMd}
                  disabled={exporting}
                  title="Export as Markdown"
                >
                  Export .md
                </button>
              </div>
            </div>

            {exportError && (
              <p className="mp-export-error">{exportError}</p>
            )}

            {/* ── Evaluation weights used (collapsible) ── */}
            {weights && (
              <div className="mp-weights-section">
                <button
                  className="mp-weights-toggle"
                  onClick={() => setWeightsOpen((o) => !o)}
                  aria-expanded={weightsOpen}
                >
                  <span className="mp-weights-toggle-icon">{weightsOpen ? '▾' : '▸'}</span>
                  Evaluation weights used
                </button>
                {weightsOpen && (
                  <div className="mp-weights-grid">
                    {Object.entries(weights).map(([key, val]) => (
                      <div key={key} className="mp-weight-row">
                        <span className="mp-weight-label">
                          {key.replace(/_/g, ' ').replace(/\b\w/g, (c) => c.toUpperCase())}
                        </span>
                        <span className="mp-weight-bar-track">
                          <span
                            className="mp-weight-bar-fill"
                            style={{ width: `${(val / 10) * 100}%` }}
                          />
                        </span>
                        <span className="mp-weight-val">{val}/10</span>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            )}
          </div>
        </>
      )}
    </div>
  );
}

// ─── MemoSection helper ───────────────────────────────────────────────────────
function MemoSection({ title, children }) {
  return (
    <div className="mp-section">
      <p className="mp-section-title">{title}</p>
      <div className="mp-section-content">{children}</div>
    </div>
  );
}

// ─── Build markdown string ────────────────────────────────────────────────────
function buildMarkdown(memo) {
  const lines = [
    `# MEMORANDUM`,
    ``,
    `**TO:** ${memo.to_recipient}`,
    `**CC:** ${memo.cc_recipient}`,
    `**FROM:** Phoenix CAP Policy Analysis System`,
    `**DATE:** ${memo.date}`,
    `**RE:** ${memo.re_subject}`,
    ``,
    `---`,
    ``,
    `## ISSUE`,
    memo.issue,
    ``,
    `## BACKGROUND`,
    memo.background,
    ``,
    `## KEY FINDINGS`,
    ...(memo.key_findings || []).map((f) => `- ${f}`),
    ``,
    `## RECOMMENDATION`,
    memo.recommendation,
    ``,
    `## NEXT STEPS`,
    ...(memo.next_steps || []).map((s, i) => `${i + 1}. ${s}`),
  ];

  if (memo.citations?.length) {
    lines.push(``, `## CITATIONS`, ...memo.citations.map((c) => `- ${c}`));
  }

  lines.push(``, `---`, `*Word count: ${memo.word_count}*`);
  return lines.join('\n');
}

function downloadText(content, filename, mimeType) {
  const blob = new Blob([content], { type: mimeType });
  const url  = URL.createObjectURL(blob);
  const a    = document.createElement('a');
  a.href     = url;
  a.download = filename;
  a.click();
  URL.revokeObjectURL(url);
}
