import React, { useState } from 'react';

// ─── Minimal markdown renderer (mirrors AgentOutput) ─────────────────────────
function inlineMd(text) {
  return text
    .replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;')
    .replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>')
    .replace(/\*(.+?)\*/g,    '<em>$1</em>')
    .replace(/`(.+?)`/g,      '<code>$1</code>');
}

function renderMarkdown(text) {
  if (!text) return null;
  const elements = [];
  let listBuffer = [], listType = null, keyIdx = 0;
  const flushList = () => {
    if (!listBuffer.length) return;
    const Tag = listType;
    elements.push(
      <Tag key={`l-${keyIdx++}`} className="md-list">
        {listBuffer.map((item, i) => (
          <li key={i} dangerouslySetInnerHTML={{ __html: inlineMd(item) }} />
        ))}
      </Tag>
    );
    listBuffer = []; listType = null;
  };
  text.split('\n').forEach((line) => {
    if (/^###\s+/.test(line)) { flushList(); elements.push(<h3 key={keyIdx++} className="md-h3">{line.replace(/^###\s+/, '')}</h3>); return; }
    if (/^##\s+/.test(line))  { flushList(); elements.push(<h2 key={keyIdx++} className="md-h2">{line.replace(/^##\s+/,  '')}</h2>); return; }
    if (/^#\s+/.test(line))   { flushList(); elements.push(<h1 key={keyIdx++} className="md-h1">{line.replace(/^#\s+/,   '')}</h1>); return; }
    const ul = line.match(/^[-*]\s+(.*)/);
    if (ul) { if (listType === 'ol') flushList(); listType = 'ul'; listBuffer.push(ul[1]); return; }
    const ol = line.match(/^\d+\.\s+(.*)/);
    if (ol) { if (listType === 'ul') flushList(); listType = 'ol'; listBuffer.push(ol[1]); return; }
    if (!line.trim()) { flushList(); elements.push(<br key={keyIdx++} />); return; }
    flushList();
    elements.push(<p key={keyIdx++} className="md-p" dangerouslySetInnerHTML={{ __html: inlineMd(line) }} />);
  });
  flushList();
  return elements;
}

// ─── Evaluator meta ───────────────────────────────────────────────────────────
const EVALUATOR_META = {
  stage3a: { avatar: 'NE', label: 'Neutral Evaluator', color: 'blue'   },
  stage3b: { avatar: 'PC', label: 'Phoenix Citizen',   color: 'amber'  },
  stage3c: { avatar: 'AQ', label: 'ADEQ Analyst',      color: 'purple' },
};

// ─── Skeleton ─────────────────────────────────────────────────────────────────
function Skeleton() {
  return (
    <div className="ev-skeleton" aria-busy="true">
      {[75, 55, 85, 45].map((w, i) => (
        <span key={i} className="ev-skeleton-line" style={{ width: `${w}%` }} />
      ))}
    </div>
  );
}

// ─── Individual evaluator card ────────────────────────────────────────────────
function EvaluatorCard({ stageKey, data, compact = false }) {
  const [open, setOpen] = useState(true);
  const meta = EVALUATOR_META[stageKey] ?? { avatar: '??', label: stageKey, color: 'gray' };
  const status = data ? 'done' : 'waiting';

  return (
    <div className={`ev-card ev-card--${meta.color}${compact ? ' ev-card--compact' : ''}`}>
      {/* Header */}
      <button className="ev-card-header" onClick={() => setOpen((o) => !o)} aria-expanded={open}>
        <span className={`ev-avatar ev-avatar--${meta.color}`}>{meta.avatar}</span>
        <span className="ev-card-title">{meta.label}</span>
        <span className={`ev-status-badge ev-status-badge--${status}`}>
          {status === 'done' ? 'Done' : 'Pending'}
        </span>
        <span className="ev-chevron">{open ? '▲' : '▼'}</span>
      </button>

      {/* Body */}
      {open && (
        <div className="ev-card-body">
          {status === 'done' ? (
            <div className="ev-findings">
              {Object.entries(data.findings ?? {}).length > 0
                ? Object.entries(data.findings).map(([k, v]) => (
                    <div key={k} className="ev-finding-row">
                      <p className="ev-finding-label">{k.replace(/_/g, ' ')}</p>
                      <p className="ev-finding-value">{v}</p>
                    </div>
                  ))
                : <div className="ao-markdown">{renderMarkdown(data.raw_output)}</div>
              }
            </div>
          ) : (
            <Skeleton />
          )}
        </div>
      )}
    </div>
  );
}

// ─── EvaluatorPanel ──────────────────────────────────────────────────────────
/**
 * EvaluatorPanel
 *
 * Props:
 *   stage3a    {EvaluatorFeedback|null}
 *   stage3b    {EvaluatorFeedback|null}
 *   stage3c    {EvaluatorFeedback|null}
 *   synthesis  {SynthesisReport|null}
 *   compact    {boolean}  – slim mode for the right sidebar
 */
export default function EvaluatorPanel({ stage3a, stage3b, stage3c, synthesis, compact = false }) {
  return (
    <div className={`evp-root${compact ? ' evp-root--compact' : ''}`}>
      {/* ── Three evaluator cards ── */}
      <div className="evp-grid">
        <EvaluatorCard stageKey="stage3a" data={stage3a} compact={compact} />
        <EvaluatorCard stageKey="stage3b" data={stage3b} compact={compact} />
        <EvaluatorCard stageKey="stage3c" data={stage3c} compact={compact} />
      </div>

      {/* ── Synthesis card ── */}
      {!compact && (
        <div className={`evp-synthesis${synthesis ? ' evp-synthesis--done' : ''}`}>
          <div className="evp-synthesis-header">
            <span className="evp-synthesis-icon">⚡</span>
            <span className="evp-synthesis-title">Synthesis</span>
            <span className={`ev-status-badge ev-status-badge--${synthesis ? 'done' : 'waiting'}`}>
              {synthesis ? 'Done' : 'Pending'}
            </span>
          </div>

          {synthesis ? (
            <div className="evp-synthesis-body">
              {synthesis.consensus_concerns?.length > 0 && (
                <div className="evp-synth-section">
                  <p className="evp-synth-label">Consensus Concerns</p>
                  <ul className="evp-synth-list">
                    {synthesis.consensus_concerns.map((c, i) => <li key={i}>{c}</li>)}
                  </ul>
                </div>
              )}
              {synthesis.divergent_concerns?.length > 0 && (
                <div className="evp-synth-section">
                  <p className="evp-synth-label">Divergent Concerns</p>
                  <ul className="evp-synth-list">
                    {synthesis.divergent_concerns.map((c, i) => <li key={i}>{c}</li>)}
                  </ul>
                </div>
              )}
              {synthesis.priority_revisions?.length > 0 && (
                <div className="evp-synth-section">
                  <p className="evp-synth-label">Priority Revisions</p>
                  <ul className="evp-synth-list">
                    {synthesis.priority_revisions.map((r, i) => <li key={i}>{r}</li>)}
                  </ul>
                </div>
              )}
              {synthesis.overall_readiness && (
                <div className="evp-synth-readiness">
                  <span className="evp-synth-label">Overall Readiness</span>
                  <span className="evp-synth-readiness-text">{synthesis.overall_readiness}</span>
                </div>
              )}
            </div>
          ) : (
            <div className="evp-synthesis-body">
              <Skeleton />
            </div>
          )}
        </div>
      )}
    </div>
  );
}
