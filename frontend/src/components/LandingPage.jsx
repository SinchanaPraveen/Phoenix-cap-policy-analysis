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
        <h1 className="lp-title">Phoenix CAP<br />Policy Analysis System</h1>
        <p className="lp-tagline">
          Multi-agent AI evaluation of climate policy ideas,
          grounded in Phoenix's 2021 Climate Action Plan.
        </p>
        <button className="lp-launch-btn" onClick={onLaunch}>
          Launch the tool →
        </button>
      </div>

      {/* ── Three feature columns ────────────────────────── */}
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

          {/* Right: What makes this different */}
          <div className="lp-about-col lp-about-col--right">
            <p className="lp-about-col-label">What makes this different</p>
            <ul className="lp-about-bullets">
              <li className="lp-about-bullet">
                <span className="lp-bullet-dot" />
                <span>
                  <strong>Dual-functioning system</strong> — not just generation,
                  but structured evaluation grounded in policy analysis criteria.
                </span>
              </li>
              <li className="lp-about-bullet">
                <span className="lp-bullet-dot" />
                <span>
                  <strong>Evaluative rigor</strong> — agents critique outputs across
                  equity, feasibility, regulatory alignment, and community voice.
                </span>
              </li>
              <li className="lp-about-bullet">
                <span className="lp-bullet-dot" />
                <span>
                  <strong>Human-in-the-loop</strong> — user-defined weights from
                  Kraft &amp; Furlong Ch. 6 shape every agent's reasoning.
                </span>
              </li>
              <li className="lp-about-bullet">
                <span className="lp-bullet-dot" />
                <span>
                  <strong>CTDS · School of Public Affairs</strong> — developed at
                  the Center on Technology, Data, and Society.
                </span>
              </li>
            </ul>
          </div>
        </div>
      </div>

      {/* ── Quote ────────────────────────────────────────── */}
      <div className="lp-attribution">
        <blockquote className="lp-quote">
          <p className="lp-quote-text">
            "Students will co-design this dual-functioning GenAI system, learning
            to critically assess GenAI outputs rather than accept them at face
            value. The pedagogical approach transforms students from passive GenAI
            consumers into architects of evaluative systems."
          </p>
          <cite className="lp-quote-attr">
            SURE Research Program · School of Public Affairs · ASU
          </cite>
        </blockquote>
      </div>
    </div>
  );
}
