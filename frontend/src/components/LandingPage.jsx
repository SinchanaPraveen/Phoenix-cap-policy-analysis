import React from 'react';

/**
 * LandingPage – introductory screen shown before the tool.
 *
 * Props:
 *   onLaunch()  called when the user clicks "Launch the tool"
 */
export default function LandingPage({ onLaunch }) {
  return (
    <div className="lp-shell">
      {/* ── Hero ─────────────────────────────────────────── */}
      <div className="lp-hero">
        <p className="lp-eyebrow">Arizona State University</p>
        <h1 className="lp-title">Policy Analysis System with GenAI</h1>
        <p className="lp-tagline">
          Multi-agent AI evaluation of climate policy ideas,
          grounded in Phoenix's 2021 Climate Action Plan.
        </p>
        <button className="lp-launch-btn" onClick={onLaunch}>
          Launch the tool →
        </button>
      </div>

      {/* ── Three feature columns ────────────────────────── */}
      <div className="lp-steps-header">
        <p className="lp-steps-label">Steps to follow</p>
      </div>
      <div className="lp-features">
        <div className="lp-feature">
          <p className="lp-feature-number">01</p>
          <p className="lp-feature-title">Submit an idea</p>
          <p className="lp-feature-desc">
            Enter any climate policy idea for Phoenix and set
            your evaluation priorities.
          </p>
        </div>
        <div className="lp-feature">
          <p className="lp-feature-number">02</p>
          <p className="lp-feature-title">AI pipeline runs</p>
          <p className="lp-feature-desc">
            Up to five specialized agents assess feasibility,
            equity, and political viability against the CAP.
          </p>
        </div>
        <div className="lp-feature">
          <p className="lp-feature-number">03</p>
          <p className="lp-feature-title">Export your summary</p>
          <p className="lp-feature-desc">
            Receive an original CAP-grounded summary
            ready to export as .docx or Markdown.
          </p>
        </div>
      </div>

      {/* ── About the Research ───────────────────────────── */}
      <div className="lp-about">
        {/* Top bar */}
        <div className="lp-about-header">
          <p className="lp-about-eyebrow">About the research</p>
          <h2 className="lp-about-title">
            GenAI-Assisted Policy Solution{' '}
            <span className="lp-about-title-italic">Generation and Evaluation</span>
          </h2>
        </div>

        {/* Two-column body */}
        <div className="lp-about-grid">
          {/* Left: The gap we close */}
          <div className="lp-about-col lp-about-col--left">
            <p className="lp-about-col-label">The gap we close</p>
            <p className="lp-about-body">
              Urban challenges like climate adaptation demand context-specific
              approaches. Yet current GenAI applications lack the evaluative
              rigor necessary for governmental decision-making.
            </p>
            <p className="lp-about-body">
              This project develops a GenAI-assisted policy analysis prototype
              that both generates and evaluates policy solutions starting with
              the Phoenix Climate Action Plan.
            </p>
          </div>

          {/* Right: Funding & Team */}
          <div className="lp-about-col lp-about-col--right">
            <p className="lp-about-col-label">Funding &amp; Team</p>
            <p className="lp-about-body">
              This project is funded by ASU Learning Engineering Institute, 2025–2026.
              The project team includes Dr. Yushim Kim (PI), Dr. Jieun Kim (Co-PI),
              Sinchana Parveen, Madumita Karthikeyan, and Saria Abedin.
            </p>
          </div>
        </div>
      </div>

    </div>
  );
}
