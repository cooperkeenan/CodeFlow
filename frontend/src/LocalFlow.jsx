import React from 'react'

const STAGES = [
  {
    id: 'profiler',
    label: 'Profiler → Tracer → Render',
    desc: 'Full pipeline from scratch',
    badge: 'FULL',
  },
  {
    id: 'tracer',
    label: 'Tracer → Render',
    desc: 'Uses stored profiler_output.json',
    badge: 'SKIP PROFILER',
  },
  {
    id: 'render',
    label: 'Render only',
    desc: 'Uses stored tracer_output.json',
    badge: 'RENDER ONLY',
  },
]

export default function LocalFlow({ loading, onRun, onBack }) {
  return (
    <div className="flow-page">
      <button className="back-btn" onClick={onBack}>← back</button>
      <h2 className="flow-title">Generate from Output</h2>
      <p className="flow-sub">Choose which stage to start from</p>
      <div className="stage-list">
        {STAGES.map(stage => (
          <button
            key={stage.id}
            className="stage-card"
            disabled={loading}
            onClick={() => onRun(stage.id)}
          >
            <span className="stage-badge">{stage.badge}</span>
            <span className="stage-label">{stage.label}</span>
            <span className="stage-desc">{stage.desc}</span>
          </button>
        ))}
      </div>
      {loading && <div className="loading-bar"><span /></div>}
    </div>
  )
}
