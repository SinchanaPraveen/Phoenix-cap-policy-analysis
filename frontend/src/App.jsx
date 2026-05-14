import React, { useState } from 'react';
import './App.css';

import LandingPage    from './components/LandingPage.jsx';
import IdeaInput      from './components/IdeaInput.jsx';
import WeightSliders  from './components/WeightSliders.jsx';
import AgentOutput    from './components/AgentOutput.jsx';
import EvaluatorPanel from './components/EvaluatorPanel.jsx';
import EvidencePanel  from './components/EvidencePanel.jsx';
import MemoPanel      from './components/MemoPanel.jsx';
import PipelineStatus from './components/PipelineStatus.jsx';

import { runPipeline, exportDocx, exportMarkdown } from './api/client.js';

// ─── Constants ───────────────────────────────────────────────────────────────
const DEFAULT_WEIGHTS = {
  effectiveness:              5,
  efficiency:                 5,
  equity:                     5,
  liberty:                    5,
  political_feasibility:      5,
  social_acceptability:       5,
  administrative_feasibility: 5,
};

const CRITERIA = [
  { key: 'effectiveness',              label: 'Effectiveness' },
  { key: 'efficiency',                 label: 'Efficiency' },
  { key: 'equity',                     label: 'Equity' },
  { key: 'liberty',                    label: 'Liberty / Freedom' },
  { key: 'political_feasibility',      label: 'Political Feasibility' },
  { key: 'social_acceptability',       label: 'Social Acceptability' },
  { key: 'administrative_feasibility', label: 'Administrative Feasibility' },
];

// Tabs available in results view
const ALL_TABS = [
  { key: 'memo',       label: 'Summary'      },
  { key: 'stage1',     label: 'Stage 1'      },
  { key: 'stage2',     label: 'Stage 2'      },
  { key: 'evaluators', label: 'Evaluators',  fullOnly: true },
  { key: 'synthesis',  label: 'Synthesis',   fullOnly: true },
  { key: 'evidence',   label: 'Evidence'     },
];

// ─── App ─────────────────────────────────────────────────────────────────────
export default function App() {
  // ── view state ──────────────────────────────────────
  const [view, setView] = useState('landing'); // 'landing' | 'input' | 'weights' | 'results'

  // ── form state ──────────────────────────────────────
  const [idea,    setIdea]    = useState('');
  const [mode,    setMode]    = useState('mvp');
  const [weights, setWeights] = useState(DEFAULT_WEIGHTS);

  // ── pipeline state ──────────────────────────────────
  const [pipelineResult, setPipelineResult] = useState(null);
  const [isLoading,      setIsLoading]      = useState(false);
  const [currentStage,   setCurrentStage]   = useState('');
  const [error,          setError]          = useState(null);

  // ── handlers ────────────────────────────────────────
  const handleIdeaSubmit = (submittedIdea, submittedMode) => {
    if (!submittedIdea.trim()) return;
    setIdea(submittedIdea);
    setMode(submittedMode);
    setView('weights');
  };

  const handleWeightsSubmit = async (submittedWeights) => {
    setWeights(submittedWeights);
    setIsLoading(true);
    setError(null);
    setPipelineResult(null);
    setCurrentStage('Stage 1: Assessment');
    setView('results');

    try {
      const data = await runPipeline(idea.trim(), mode, submittedWeights);
      if (data.error) {
        setError(data.error);
      } else {
        setPipelineResult(data);
        setCurrentStage('Complete');
        // Surface any partial stage errors as a non-fatal warning
        if (data.stage_errors && Object.keys(data.stage_errors).length > 0) {
          const failedStages = Object.keys(data.stage_errors).join(', ');
          setError(`Some stages had errors (${failedStages}). Partial results shown below.`);
        }
      }
    } catch (err) {
      setError(err.message ?? 'An unexpected error occurred.');
    } finally {
      setIsLoading(false);
    }
  };

  const handleNewIdea = () => {
    setIdea('');
    setMode('mvp');
    setWeights(DEFAULT_WEIGHTS);
    setPipelineResult(null);
    setError(null);
    setCurrentStage('');
    setView('input');
  };

  // ── render ──────────────────────────────────────────
  return (
    <div className="app-shell">
      {/* ── Header ─────────────────────────────────── */}
      <header className="app-header">
        <h1>Phoenix CAP Policy Analysis System</h1>
        <span className="subtitle">
          Multi-agent GenAI evaluation · 2021 Climate Action Plan · ASU
        </span>
      </header>

      {/* ── Views ──────────────────────────────────── */}
      {view === 'landing' && <LandingPage onLaunch={() => setView('input')} />}
      {view === 'input'   && <IdeaInput onSubmit={handleIdeaSubmit} />}
      {view === 'weights' && (
        <WeightSliders
          idea={idea}
          onSubmit={handleWeightsSubmit}
          onBack={() => setView('input')}
        />
      )}
      {view === 'results' && (
        <ResultsView
          idea={idea}
          mode={mode}
          weights={weights}
          isLoading={isLoading}
          currentStage={currentStage}
          pipelineResult={pipelineResult}
          error={error}
          onNewIdea={handleNewIdea}
        />
      )}

      {/* ── Footer ─────────────────────────────────── */}
      <footer className="app-footer">
        Phoenix CAP Policy Analysis System · ASU Research Project · {new Date().getFullYear()}
      </footer>
    </div>
  );
}

// ─── Loading Card ─────────────────────────────────────────────────────────────
const MVP_STAGES = [
  { key: 'stage1', label: 'Stage 1: Assessment'  },
  { key: 'stage2', label: 'Stage 2: Planning'    },
  { key: 'stage4', label: 'Stage 4: Summary'     },
];

const FULL_STAGES = [
  { key: 'stage1',  label: 'Stage 1: Assessment'      },
  { key: 'stage2',  label: 'Stage 2: Planning'         },
  { key: 'stage3a', label: 'Stage 3a: Neutral Eval'    },
  { key: 'stage3b', label: 'Stage 3b: Citizen Eval'    },
  { key: 'stage3c', label: 'Stage 3c: ADEQ Eval'       },
  { key: 'stage5',  label: 'Stage 5: Synthesis'        },
  { key: 'stage4',  label: 'Stage 4: Summary'         },
];

function LoadingCard({ mode, result }) {
  const stages = mode === 'full' ? FULL_STAGES : MVP_STAGES;
  return (
    <div className="lc-overlay">
      <div className="lc-card">
        <div className="lc-spinner" aria-hidden="true" />
        <p className="lc-title">Running Phoenix CAP pipeline…</p>
        <p className="lc-subtitle">
          {mode === 'mvp'
            ? 'This takes 30–60 seconds for MVP'
            : 'This takes 2–3 minutes for full pipeline'}
        </p>
        <div className="lc-stages">
          {stages.map(({ key, label }) => {
            const done = !!(result?.[key]);
            return (
              <div key={key} className={`lc-stage${done ? ' lc-stage--done' : ''}`}>
                <span className={`lc-stage-dot${done ? ' lc-stage-dot--done' : ''}`} />
                <span className="lc-stage-label">{label}</span>
                {done && <span className="lc-stage-check">✓</span>}
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
}

// ─── View: Results ────────────────────────────────────────────────────────────
function ResultsView({ idea, mode, weights, isLoading, currentStage, pipelineResult, error, onNewIdea }) {
  const visibleTabs = ALL_TABS.filter((t) => !t.fullOnly || mode === 'full');
  const [activeTab, setActiveTab] = useState('memo');

  const r = pipelineResult;

  // Derived statuses for agent cards
  const stageStatus = (key) => {
    if (r?.[key])   return 'done';
    if (isLoading && currentStage === key) return 'running';
    return 'waiting';
  };

  // CAP citation count (stage1 + stage4)
  const citationCount = [
    ...(r?.stage1?.citations ?? []),
    ...(r?.stage4?.citations ?? []),
  ].filter(Boolean).length;

  const wordCount   = r?.stage4?.word_count ?? 0;
  const readiness   = r?.stage5?.overall_readiness ?? r?.stage1?.overall_verdict ?? null;

  const wcColor =
    wordCount >= 400 && wordCount <= 450 ? '#2E7D32'
    : wordCount > 450                    ? 'var(--color-amber)'
    :                                      'var(--color-text-tertiary)';

  return (
    <div className="rv-shell">
      {/* ── Loading overlay ── */}
      {isLoading && <LoadingCard mode={mode} result={r} />}

      {/* ── Top bar ── */}
      <div className="rv-topbar">
        <p className="rv-topbar-idea">
          <strong>Idea: </strong>{idea}
        </p>
        <button className="btn-new-idea" onClick={onNewIdea} disabled={isLoading}>+ New idea</button>
      </div>

      {/* ── Pipeline progress bar (spans full width) ── */}
      <div className="rv-pipeline-bar">
        <PipelineStatus
          currentStage={currentStage}
          mode={mode}
          result={r}
          isLoading={isLoading}
          onTabSelect={setActiveTab}
          activeTab={activeTab}
        />
      </div>

      {/* ── Three-column body ── */}
      <div className={`rv-body${mode === 'full' ? ' rv-body--full' : ''}`}>

        {/* ── LEFT SIDEBAR ── */}
        <aside className="rv-sidebar-left">
          <p className="rv-sidebar-heading">Sections</p>
          <nav className="rv-sidenav">
            {visibleTabs.map(({ key, label }) => (
              <button
                key={key}
                className={`rv-sidenav-btn${activeTab === key ? ' rv-sidenav-btn--active' : ''}`}
                onClick={() => setActiveTab(key)}
              >
                <span className={`rv-sidenav-dot rv-sidenav-dot--${stageStatus(key === 'memo' ? 'stage4' : key === 'evaluators' ? 'stage3a' : key === 'synthesis' ? 'stage5' : key)}`} />
                {label}
              </button>
            ))}
          </nav>
        </aside>

        {/* ── MAIN CONTENT ── */}
        <main className="rv-main">
          {/* Error banner */}
          {error && (
            <div className="rv-error-banner">
              <strong>Error: </strong>{error}
            </div>
          )}

          {/* Tab bar */}
          <div className="rv-tab-bar" role="tablist">
            {visibleTabs.map(({ key, label }) => (
              <button
                key={key}
                role="tab"
                aria-selected={activeTab === key}
                className={`rv-tab${activeTab === key ? ' rv-tab--active' : ''}`}
                onClick={() => setActiveTab(key)}
              >
                {label}
              </button>
            ))}
          </div>

          {/* Tab content */}
          <div className="rv-tab-content" role="tabpanel">
            {activeTab === 'memo' && (
              <MemoPanel memo={r?.stage4 ?? null} isLoading={isLoading && !r?.stage4} weights={weights} />
            )}

            {activeTab === 'stage1' && (
              <AgentOutput
                title="Stage 1 — Idea Assessment"
                status={stageStatus('stage1')}
                output={r?.stage1?.raw_output ?? null}
              />
            )}

            {activeTab === 'stage2' && (
              <AgentOutput
                title="Stage 2 — Implementation Roadmap"
                status={stageStatus('stage2')}
                output={r?.stage2?.raw_output ?? null}
              />
            )}

            {activeTab === 'evaluators' && mode === 'full' && (
              <EvaluatorPanel
                stage3a={r?.stage3a ?? null}
                stage3b={r?.stage3b ?? null}
                stage3c={r?.stage3c ?? null}
                synthesis={r?.stage5 ?? null}
              />
            )}

            {activeTab === 'synthesis' && mode === 'full' && (
              <AgentOutput
                title="Stage 5 — Synthesis"
                status={stageStatus('stage5')}
                output={r?.stage5?.raw_output ?? null}
              />
            )}

            {activeTab === 'evidence' && (
              <EvidencePanel
                stage1={r?.stage1 ?? null}
                stage2={r?.stage2 ?? null}
              />
            )}
          </div>
        </main>

        {/* ── RIGHT SIDEBAR (full mode only) ── */}
        {mode === 'full' && (
          <aside className="rv-sidebar-right">
            <p className="rv-sidebar-heading">Evaluators</p>
            <EvaluatorPanel
              stage3a={r?.stage3a ?? null}
              stage3b={r?.stage3b ?? null}
              stage3c={r?.stage3c ?? null}
              synthesis={null}
              compact
            />
          </aside>
        )}
      </div>

      {/* ── Bottom bar ── */}
      <div className="rv-bottom-bar">
        <div className="rv-bottom-stats">
          {citationCount > 0 && (
            <span className="rv-stat">
              <span className="rv-stat-dot rv-stat-dot--teal" />
              {citationCount} citations
            </span>
          )}
          {wordCount > 0 && (
            <span className="rv-stat" style={{ color: wcColor }}>
              <span className="rv-stat-dot rv-stat-dot--memo" />
              {wordCount} words
            </span>
          )}
          {readiness && (
            <span className="rv-stat rv-stat--readiness" title={readiness}>
              Readiness: {readiness.length > 60 ? `${readiness.slice(0, 57)}…` : readiness}
            </span>
          )}
        </div>

        <div className="rv-bottom-actions">
          {r?.stage4 && (
            <>
              <ExportButton result={r} memo={r.stage4} format="docx" disabled={isLoading} />
              <ExportButton result={r} memo={r.stage4} format="md"   disabled={isLoading} />
            </>
          )}
        </div>
      </div>
    </div>
  );
}

// ─── Bottom-bar export button ─────────────────────────────────────────────────
function ExportButton({ result, memo, format, disabled = false }) {
  const [busy, setBusy] = useState(false);

  const handleClick = async () => {
    setBusy(true);
    try {
      if (format === 'docx') {
        await exportDocx(result ?? { stage4: memo });
      } else {
        const text = buildMd(memo);
        const blob = new Blob([text], { type: 'text/markdown' });
        const url  = URL.createObjectURL(blob);
        const a    = document.createElement('a');
        a.href = url; a.download = 'policy_memo.md'; a.click();
        URL.revokeObjectURL(url);
      }
    } finally {
      setBusy(false);
    }
  };

  return (
    <button className="rv-export-btn" onClick={handleClick} disabled={busy || disabled}>
      {busy ? '…' : `Export .${format}`}
    </button>
  );
}

function buildMd(memo) {
  return [
    '# MEMORANDUM',
    '',
    `**TO:** ${memo.to_recipient}`,
    `**CC:** ${memo.cc_recipient}`,
    `**DATE:** ${memo.date}`,
    `**RE:** ${memo.re_subject}`,
    '',
    '---',
    '',
    '## ISSUE',
    memo.issue ?? '',
    '',
    '## BACKGROUND',
    memo.background ?? '',
    '',
    '## KEY FINDINGS',
    ...(memo.key_findings ?? []).map((f) => `- ${f}`),
    '',
    '## RECOMMENDATION',
    memo.recommendation ?? '',
    '',
    '## NEXT STEPS',
    ...(memo.next_steps ?? []).map((s, i) => `${i + 1}. ${s}`),
    '',
    '---',
    `*Word count: ${memo.word_count}*`,
  ].join('\n');
}

