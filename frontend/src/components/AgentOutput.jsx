import React, { useState } from 'react';

// ─── Minimal Markdown renderer ────────────────────────────────────────────────
// Handles: ## headers, **bold**, bullet lists (- / *), numbered lists
function renderMarkdown(text) {
  if (!text) return null;
  const lines = text.split('\n');
  const elements = [];
  let listBuffer = [];
  let listType   = null; // 'ul' | 'ol'
  let keyIdx     = 0;

  const flushList = () => {
    if (!listBuffer.length) return;
    const Tag = listType;
    elements.push(
      <Tag key={`list-${keyIdx++}`} className="md-list">
        {listBuffer.map((item, i) => (
          <li key={i} dangerouslySetInnerHTML={{ __html: inlineMarkdown(item) }} />
        ))}
      </Tag>
    );
    listBuffer = [];
    listType   = null;
  };

  lines.forEach((line) => {
    // H2 / H3
    if (/^###\s+/.test(line)) {
      flushList();
      elements.push(
        <h3 key={keyIdx++} className="md-h3">{line.replace(/^###\s+/, '')}</h3>
      );
      return;
    }
    if (/^##\s+/.test(line)) {
      flushList();
      elements.push(
        <h2 key={keyIdx++} className="md-h2">{line.replace(/^##\s+/, '')}</h2>
      );
      return;
    }
    if (/^#\s+/.test(line)) {
      flushList();
      elements.push(
        <h1 key={keyIdx++} className="md-h1">{line.replace(/^#\s+/, '')}</h1>
      );
      return;
    }
    // Unordered list
    const ulMatch = line.match(/^[-*]\s+(.*)/);
    if (ulMatch) {
      if (listType === 'ol') flushList();
      listType = 'ul';
      listBuffer.push(ulMatch[1]);
      return;
    }
    // Ordered list
    const olMatch = line.match(/^\d+\.\s+(.*)/);
    if (olMatch) {
      if (listType === 'ul') flushList();
      listType = 'ol';
      listBuffer.push(olMatch[1]);
      return;
    }
    // Empty line
    if (!line.trim()) {
      flushList();
      elements.push(<br key={keyIdx++} />);
      return;
    }
    // Paragraph
    flushList();
    elements.push(
      <p
        key={keyIdx++}
        className="md-p"
        dangerouslySetInnerHTML={{ __html: inlineMarkdown(line) }}
      />
    );
  });
  flushList();
  return elements;
}

// Inline: **bold**, *italic*, `code`
function inlineMarkdown(text) {
  return text
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>')
    .replace(/\*(.+?)\*/g, '<em>$1</em>')
    .replace(/`(.+?)`/g, '<code>$1</code>');
}

// ─── Skeleton placeholder ─────────────────────────────────────────────────────
function Skeleton() {
  return (
    <div className="ao-skeleton" aria-busy="true">
      {[80, 60, 90, 50].map((w, i) => (
        <span key={i} className="ao-skeleton-line" style={{ width: `${w}%` }} />
      ))}
    </div>
  );
}

// ─── Status badge ─────────────────────────────────────────────────────────────
function StatusBadge({ status }) {
  const labels  = { done: 'Done', running: 'Running', waiting: 'Pending' };
  return (
    <span className={`ao-badge ao-badge--${status}`}>{labels[status] ?? status}</span>
  );
}

// ─── AgentOutput ─────────────────────────────────────────────────────────────
/**
 * AgentOutput – collapsible card for a single pipeline agent.
 *
 * Props:
 *   title    {string}
 *   status   {'done'|'running'|'waiting'}
 *   output   {string|null}   – raw_output text, rendered as markdown when done
 */
export default function AgentOutput({ title, status = 'waiting', output = null }) {
  const [open, setOpen] = useState(status !== 'waiting');

  // Auto-open when status changes to done/running
  React.useEffect(() => {
    if (status === 'done' || status === 'running') setOpen(true);
  }, [status]);

  return (
    <div className={`ao-card ao-card--${status}`}>
      {/* ── Header ── */}
      <button
        className="ao-header"
        onClick={() => setOpen((o) => !o)}
        aria-expanded={open}
      >
        <span className={`ao-dot ao-dot--${status}`} />
        <span className="ao-title">{title}</span>
        <StatusBadge status={status} />
        <span className="ao-chevron">{open ? '▲' : '▼'}</span>
      </button>

      {/* ── Body ── */}
      {open && (
        <div className="ao-body">
          {status === 'done' && output && (
            <div className="ao-markdown">{renderMarkdown(output)}</div>
          )}
          {status === 'done' && !output && (
            <p className="ao-empty">No output available.</p>
          )}
          {status === 'running' && <Skeleton />}
          {status === 'waiting' && (
            <p className="ao-pending">Pending…</p>
          )}
        </div>
      )}
    </div>
  );
}
