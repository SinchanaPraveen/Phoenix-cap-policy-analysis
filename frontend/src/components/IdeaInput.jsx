import React, { useState } from 'react';

const EXAMPLES = [
  "Expand urban tree canopy in heat-vulnerable neighborhoods by 2030",
  "Mandate cool roofs on all new commercial buildings in Phoenix",
  "Deploy 500 EV charging stations in underserved neighborhoods by 2028",
  "Create zero-waste pilot programs in 10 Phoenix neighborhoods",
  "Establish 100 cool corridors in heat-vulnerable communities by 2030",
];

/**
 * IdeaInput – Screen 1.
 *
 * Props:
 *   onSubmit(idea, mode)  called when user clicks "Continue →"
 */
export default function IdeaInput({ onSubmit, onBack }) {
  const [idea, setIdea] = useState('');
  const [mode, setMode] = useState('mvp');

  const handleKey = (e) => {
    if (e.key === 'Enter' && (e.metaKey || e.ctrlKey) && idea.trim()) {
      onSubmit(idea.trim(), mode);
    }
  };

  return (
    <div className="ii-shell">
      {/* ── LEFT COLUMN ─────────────────────────────── */}
      <div className="ii-left">
        {/* Back link */}
        {onBack && (
          <button className="ii-back-btn" onClick={onBack}>
            ← Back
          </button>
        )}

        {/* Branding */}
        <div className="ii-brand">
          <h1 className="ii-title">Policy Analysis System with GenAI</h1>
          <p className="ii-subtitle">
            Multi-agent GenAI policy evaluation&nbsp;·&nbsp;Arizona State University
          </p>
        </div>

        {/* Quote attribution */}
        <blockquote className="ii-quote">
          <p className="ii-quote-text">"AI-assisted policy evaluation grounded in Phoenix's 2021 Climate Action Plan."</p>
          <cite className="ii-quote-attr">School of Public Affairs · Arizona State University</cite>
        </blockquote>

        {/* Textarea */}
        <textarea
          className="ii-textarea"
          value={idea}
          onChange={(e) => setIdea(e.target.value)}
          onKeyDown={handleKey}
          placeholder="Enter your policy idea — e.g. 'Expand urban tree canopy in heat-vulnerable neighborhoods by 2030'"
          aria-label="Policy idea"
          autoFocus
        />

        {/* Quick examples */}
        <div className="ii-examples">
          <p className="ii-examples-label">Quick examples</p>
          <div className="ii-chips">
            {EXAMPLES.map((ex) => (
              <button
                key={ex}
                className={`ii-chip${idea === ex ? ' ii-chip--active' : ''}`}
                onClick={() => setIdea(ex)}
              >
                {ex}
              </button>
            ))}
          </div>
        </div>
      </div>

      {/* ── RIGHT COLUMN ────────────────────────────── */}
      <div className="ii-right">
        {/* Pipeline mode card */}
        <div className="ii-mode-card">
          <p className="ii-mode-card-heading">Choose your mode</p>

          {/* MVP option */}
          <label className={`ii-mode-option${mode === 'mvp' ? ' ii-mode-option--active' : ''}`}>
            <input
              type="radio"
              name="pipeline-mode"
              value="mvp"
              checked={mode === 'mvp'}
              onChange={() => setMode('mvp')}
              className="ii-mode-radio"
            />
            <div className="ii-mode-option-body">
              <div className="ii-mode-option-top">
                <span className="ii-mode-name">Fast mode</span>
                <span className="ii-mode-badge ii-mode-badge--fast">Fastest</span>
              </div>
              <p className="ii-mode-desc">Idea Generator only</p>
              <p className="ii-mode-note">No evaluators</p>
            </div>
          </label>

          {/* Full option */}
          <label className={`ii-mode-option${mode === 'full' ? ' ii-mode-option--active' : ''}`}>
            <input
              type="radio"
              name="pipeline-mode"
              value="full"
              checked={mode === 'full'}
              onChange={() => setMode('full')}
              className="ii-mode-radio"
            />
            <div className="ii-mode-option-body">
              <div className="ii-mode-option-top">
                <span className="ii-mode-name">Full Mode</span>
                <span className="ii-mode-badge ii-mode-badge--thorough">Most thorough</span>
              </div>
              <p className="ii-mode-desc">Idea generator &amp; Evaluator</p>
              <p className="ii-mode-note">Includes all evaluator perspectives</p>
            </div>
          </label>
        </div>

        {/* Continue button */}
        <button
          className="ii-continue-btn"
          disabled={!idea.trim()}
          onClick={() => onSubmit(idea.trim(), mode)}
        >
          Continue →
        </button>

        {/* Footer note */}
        <p className="ii-footer-note">
          Full CAP 2021 loaded&nbsp;·&nbsp;213 pages&nbsp;·&nbsp;All claims grounded in source
        </p>
      </div>
    </div>
  );
}
