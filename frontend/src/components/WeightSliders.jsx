import React, { useState } from 'react';

const CRITERIA = [
  {
    key: 'effectiveness',
    label: 'Effectiveness',
    definition: 'Likelihood of achieving stated policy goals and objectives',
  },
  {
    key: 'efficiency',
    label: 'Efficiency',
    definition: 'Largest benefit for a given cost, or lowest cost for a given benefit',
  },
  {
    key: 'equity',
    label: 'Equity',
    definition: 'Fairness of costs and benefits across population subgroups',
  },
  {
    key: 'liberty',
    label: 'Liberty / Freedom',
    definition: 'Extent the policy restricts individual rights and choices',
  },
  {
    key: 'political_feasibility',
    label: 'Political Feasibility',
    definition: 'Extent elected officials will accept and support the proposal',
  },
  {
    key: 'social_acceptability',
    label: 'Social Acceptability',
    definition: 'Likelihood the public will accept and support the proposal',
  },
  {
    key: 'administrative_feasibility',
    label: 'Administrative Feasibility',
    definition: 'Likelihood an agency can implement the policy well',
  },
];

const PRESETS = [
  {
    label: 'Equity-first',
    values: {
      equity: 10, effectiveness: 8, efficiency: 3, liberty: 2,
      political_feasibility: 5, social_acceptability: 7, administrative_feasibility: 6,
    },
  },
  {
    label: 'Fiscally conservative',
    values: {
      efficiency: 10, effectiveness: 8, equity: 4, liberty: 5,
      political_feasibility: 7, social_acceptability: 5, administrative_feasibility: 8,
    },
  },
  {
    label: 'Politically pragmatic',
    values: {
      political_feasibility: 10, social_acceptability: 9, effectiveness: 7,
      efficiency: 6, equity: 6, liberty: 4, administrative_feasibility: 7,
    },
  },
  {
    label: 'Balanced',
    values: {
      effectiveness: 5, efficiency: 5, equity: 5, liberty: 5,
      political_feasibility: 5, social_acceptability: 5, administrative_feasibility: 5,
    },
  },
];

const DEFAULT_WEIGHTS = {
  effectiveness: 5, efficiency: 5, equity: 5, liberty: 5,
  political_feasibility: 5, social_acceptability: 5, administrative_feasibility: 5,
};

function badge(val) {
  if (val >= 8) return { label: 'High',   cls: 'ws-badge ws-badge--high' };
  if (val >= 4) return { label: 'Medium', cls: 'ws-badge ws-badge--med' };
  return          { label: 'Low',    cls: 'ws-badge ws-badge--low' };
}

/**
 * WeightSliders – Screen 2.
 *
 * Props:
 *   onSubmit(weights)
 *   onBack()
 *   idea  {string}
 */
export default function WeightSliders({ onSubmit, onBack, idea }) {
  const [weights, setWeights] = useState(DEFAULT_WEIGHTS);

  const set = (key, val) =>
    setWeights((prev) => ({ ...prev, [key]: Number(val) }));

  const applyPreset = (values) => setWeights(values);

  // top-2 criteria by weight for "primary focus" line
  const sorted = [...CRITERIA].sort((a, b) => weights[b.key] - weights[a.key]);
  const top2 = sorted.slice(0, 2).map((c) => c.label);
  const totalWeight = Object.values(weights).reduce((s, v) => s + v, 0);

  return (
    <div className="ws-shell">
      {/* ── LEFT: sliders (2/3) ─────────────────────── */}
      <div className="ws-left">
        <div className="ws-header">
          <h2 className="ws-title">Evaluation Weights</h2>
          <p className="ws-subtitle">
            Adjust how much each criterion matters. Based on Ch. 6 policy analysis framework.
          </p>
        </div>

        {/* Idea pill */}
        {idea && (
          <div className="ws-idea-pill">
            <span className="ws-idea-pill-label">Idea:</span>
            <span className="ws-idea-pill-text">{idea}</span>
          </div>
        )}

        {/* Sliders */}
        <div className="ws-criteria">
          {CRITERIA.map(({ key, label, definition }) => {
            const b = badge(weights[key]);
            return (
              <div className="ws-criterion" key={key}>
                <div className="ws-criterion-top">
                  <div className="ws-criterion-name-wrap">
                    <span className="ws-criterion-name">{label}</span>
                    <span className={b.cls}>{b.label}</span>
                  </div>
                  <span className="ws-criterion-value">{weights[key]}</span>
                </div>
                <p className="ws-criterion-def">{definition}</p>
                <input
                  type="range"
                  min={0}
                  max={10}
                  step={1}
                  value={weights[key]}
                  onChange={(e) => set(key, e.target.value)}
                  aria-label={label}
                  className="ws-range"
                />
              </div>
            );
          })}
        </div>
      </div>

      {/* ── RIGHT: summary panel (1/3) ──────────────── */}
      <div className="ws-right">
        {/* Presets */}
        <div className="ws-panel">
          <p className="ws-panel-heading">Presets</p>
          <div className="ws-presets">
            {PRESETS.map((p) => (
              <button
                key={p.label}
                className="ws-preset-btn"
                onClick={() => applyPreset(p.values)}
              >
                {p.label}
              </button>
            ))}
          </div>
        </div>

        {/* Weight summary bars */}
        <div className="ws-panel">
          <p className="ws-panel-heading">Weight summary</p>
          <div className="ws-summary-bars">
            {CRITERIA.map(({ key, label }) => {
              const pct = totalWeight > 0 ? (weights[key] / totalWeight) * 100 : 0;
              return (
                <div className="ws-summary-row" key={key}>
                  <span className="ws-summary-label">{label}</span>
                  <div className="ws-bar-track">
                    <div
                      className="ws-bar-fill"
                      style={{ width: `${pct.toFixed(1)}%` }}
                    />
                  </div>
                  <span className="ws-summary-val">{weights[key]}</span>
                </div>
              );
            })}
          </div>
          <p className="ws-primary-focus">
            <span className="ws-primary-focus-label">Primary focus:</span>{' '}
            {top2.join(' · ')}
          </p>
        </div>

        {/* Actions */}
        <div className="ws-actions">
          <button className="ws-back-btn" onClick={onBack}>← Back</button>
          <button
            className="ws-run-btn"
            onClick={() => onSubmit(weights)}
          >
            Run pipeline →
          </button>
        </div>
      </div>
    </div>
  );
}
