import React from 'react';

// ─── Badge colors per finding type ───────────────────────────────────────────
const FINDING_META = {
  alignment_finding:   { label: 'Alignment',   color: 'teal'   },
  conflict_finding:    { label: 'Conflict',     color: 'red'    },
  equity_finding:      { label: 'Equity',       color: 'purple' },
  feasibility_finding: { label: 'Feasibility',  color: 'blue'   },
};

// ─── Mini progress bar ────────────────────────────────────────────────────────
function MiniBar({ color, value = 70 }) {
  return (
    <div className="ep-mini-bar-track">
      <div className={`ep-mini-bar-fill ep-mini-bar-fill--${color}`} style={{ width: `${value}%` }} />
    </div>
  );
}

// ─── Finding badge ────────────────────────────────────────────────────────────
function FindingBadge({ color, label }) {
  return <span className={`ep-badge ep-badge--${color}`}>{label}</span>;
}

/**
 * EvidencePanel
 *
 * Props:
 *   stage1  {AssessmentReport|null}
 *   stage2  {ImplementationRoadmap|null}
 */
export default function EvidencePanel({ stage1, stage2 }) {
  // Collect all citations
  const allCitations = [
    ...(stage1?.citations ?? []),
  ].filter(Boolean);
  const uniqueCitations = [...new Set(allCitations)];

  return (
    <div className="ep-root">
      {/* ── Stage 1 score summary ── */}
      {stage1 && (
        <div className="ep-section">
          <p className="ep-section-heading">Stage 1 — Assessment Findings</p>

          <div className="ep-findings">
            {Object.entries(FINDING_META).map(([key, { label, color }]) =>
              stage1[key] ? (
                <div key={key} className="ep-finding-row">
                  <FindingBadge color={color} label={label} />
                  <div className="ep-finding-text">{stage1[key]}</div>
                  <MiniBar color={color} />
                </div>
              ) : null
            )}
          </div>

          {stage1.overall_verdict && (
            <div className="ep-verdict">
              <span className="ep-verdict-label">Overall Verdict</span>
              <p className="ep-verdict-text">{stage1.overall_verdict}</p>
            </div>
          )}
        </div>
      )}

      {/* ── CAP citations ── */}
      {uniqueCitations.length > 0 && (
        <div className="ep-section">
          <p className="ep-section-heading">CAP Citations ({uniqueCitations.length})</p>
          <div className="ep-citation-pills">
            {uniqueCitations.map((c, i) => (
              <span key={i} className="ep-citation-pill" title={c}>
                {c.length > 70 ? `${c.slice(0, 67)}…` : c}
              </span>
            ))}
          </div>
        </div>
      )}

      {/* ── Stage 2 summary ── */}
      {stage2 && (
        <div className="ep-section">
          <p className="ep-section-heading">Stage 2 — Implementation Summary</p>
          <div className="ep-roadmap-grid">
            <RoadmapColumn
              title="Quick Wins"
              items={stage2.quick_wins}
              color="teal"
              icon="⚡"
            />
            <RoadmapColumn
              title="Medium Term"
              items={stage2.medium_term}
              color="amber"
              icon="📅"
            />
            <RoadmapColumn
              title="Long Term"
              items={stage2.long_term}
              color="purple"
              icon="🎯"
            />
          </div>

          {stage2.equity_checklist?.length > 0 && (
            <div className="ep-equity">
              <p className="ep-equity-label">Equity Checklist</p>
              <ul className="ep-equity-list">
                {stage2.equity_checklist.map((item, i) => (
                  <li key={i}>{item}</li>
                ))}
              </ul>
            </div>
          )}
        </div>
      )}
    </div>
  );
}

// ─── Roadmap column ───────────────────────────────────────────────────────────
function RoadmapColumn({ title, items = [], color, icon }) {
  return (
    <div className={`ep-roadmap-col ep-roadmap-col--${color}`}>
      <p className="ep-roadmap-col-title">
        <span>{icon}</span> {title}
      </p>
      {items.length > 0 ? (
        <ul className="ep-roadmap-list">
          {items.map((item, i) => (
            <li key={i}>{item}</li>
          ))}
        </ul>
      ) : (
        <p className="ep-roadmap-empty">—</p>
      )}
    </div>
  );
}
