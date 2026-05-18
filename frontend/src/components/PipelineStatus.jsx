import React, { useEffect, useState } from 'react';

// ─── Stage definitions ────────────────────────────────────────────────────────
const MVP_STAGES = [
  { key: 'stage1', short: 'Idea Assessment',        label: 'Idea Assessment'        },
  { key: 'stage2', short: 'Implementation Roadmap', label: 'Implementation Roadmap' },
  { key: 'stage4', short: 'Summary',                 label: 'Summary'                },
];

const FULL_STAGES = [
  { key: 'stage1',  short: 'Idea Assessment',        label: 'Idea Assessment'        },
  { key: 'stage2',  short: 'Implementation Roadmap', label: 'Implementation Roadmap' },
  { key: 'stage3a', short: 'Neutral Evaluator',      label: 'Neutral Evaluator'      },
  { key: 'stage3b', short: 'Citizen Evaluator',      label: 'Citizen Evaluator'      },
  { key: 'stage3c', short: 'ADEQ Analyst',           label: 'ADEQ Analyst'           },
  { key: 'stage5',  short: 'Synthesis',              label: 'Synthesis'              },
  { key: 'stage4',  short: 'Summary',                label: 'Summary'                },
];

/**
 * PipelineStatus — horizontal progress bar with stage dots.
 *
 * Props:
 *   currentStage  {string}       – stage key currently running, e.g. "stage1"
 *   mode          {'mvp'|'full'}
 *   result        {Object|null}  – PipelineResult (null while loading)
 *   isLoading     {boolean}
 *   onTabSelect   {(key)=>void}  – optional: navigate to tab
 *   activeTab     {string}       – currently selected tab key
 */
export default function PipelineStatus({
  currentStage,
  mode,
  result,
  isLoading,
  onTabSelect,
  activeTab,
}) {
  const stages = mode === 'full' ? FULL_STAGES : MVP_STAGES;

  // ── Elapsed timer ──────────────────────────────────────
  const [elapsed, setElapsed]   = useState(0);
  const [startTime, setStartTime] = useState(null);

  useEffect(() => {
    if (isLoading && !startTime) {
      setStartTime(Date.now());
      setElapsed(0);
    }
    if (!isLoading) {
      setStartTime(null);
    }
  }, [isLoading]); // eslint-disable-line react-hooks/exhaustive-deps

  useEffect(() => {
    if (!isLoading) return;
    const id = setInterval(() => {
      setElapsed(Math.floor((Date.now() - (startTime ?? Date.now())) / 1000));
    }, 1000);
    return () => clearInterval(id);
  }, [isLoading, startTime]);

  // ── Stage status helper ────────────────────────────────
  const getStatus = (key) => {
    if (result?.[key])                      return 'done';
    if (isLoading && currentStage === key)  return 'running';
    return 'waiting';
  };

  const formatTime = (s) => {
    if (s < 60) return `${s}s`;
    return `${Math.floor(s / 60)}m ${s % 60}s`;
  };

  return (
    <div className="ps-root">
      {/* ── Horizontal progress bar ── */}
      <div className="ps-bar" role="list">
        {stages.map(({ key, short, label }, idx) => {
          const status   = getStatus(key);
          const isLast   = idx === stages.length - 1;
          const isActive = onTabSelect && activeTab === key;
          return (
            <React.Fragment key={key}>
              <button
                role="listitem"
                aria-label={label}
                className={`ps-dot-wrap${isActive ? ' ps-dot-wrap--active' : ''}`}
                onClick={() => onTabSelect?.(key)}
                disabled={!onTabSelect}
              >
                <span className={`ps-dot ps-dot--${status}`}>
                  {status === 'done' && (
                    <svg viewBox="0 0 10 10" width="8" height="8">
                      <polyline
                        points="1.5,5 4,8 8.5,2"
                        fill="none"
                        stroke="currentColor"
                        strokeWidth="2"
                        strokeLinecap="round"
                        strokeLinejoin="round"
                      />
                    </svg>
                  )}
                  {status === 'running' && <span className="ps-dot-ring" />}
                </span>
                <span className={`ps-dot-label ps-dot-label--${status}`}>{short}</span>
                {status === 'running' && isLoading && (
                  <span className="ps-elapsed">{formatTime(elapsed)}</span>
                )}
              </button>
              {!isLast && (
                <span
                  className={`ps-connector${
                    status === 'done' ? ' ps-connector--on' : ' ps-connector--off'
                  }`}
                />
              )}
            </React.Fragment>
          );
        })}
      </div>

      {/* ── Running message ── */}
      {isLoading && currentStage && (
        <div className="ps-running-msg">
          <span className="ps-spinner" />
          <span>
            Running{' '}
            <strong>
              {stages.find((s) => s.key === currentStage)?.label ?? currentStage}
            </strong>
            …
          </span>
        </div>
      )}
    </div>
  );
}
