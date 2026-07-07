import { useState, useEffect } from 'react'
import { STAGES } from '../constants'

export default function LocalPage({ onBack, onRun, loading }) {
  const [recommendedStage, setRecommendedStage] = useState(null)

  useEffect(() => {
    fetch('/analyse/stage-status')
      .then(r => r.ok ? r.json() : null)
      .then(data => { if (data?.recommended_stage) setRecommendedStage(data.recommended_stage) })
      .catch(() => {})
  }, [])

  return (
    <main className="page">
      <button className="back" onClick={onBack}>← back</button>
      <h1 className="page-title">Generate from Output</h1>
      <p className="page-sub">Choose which stage to start from</p>
      {loading && <div className="loading-bar"><span /></div>}
      <div className="card-list">
        {STAGES.map(stage => (
          <button
            key={stage.id}
            className={`card${stage.id === recommendedStage ? ' card--recommended' : ''}`}
            disabled={loading}
            onClick={() => onRun(stage.endpoint)}
          >
            <span className="card-badge">
              {stage.badge}
              {stage.id === recommendedStage && <span className="card-badge-hint"> ● MODIFIED</span>}
            </span>
            <span className="card-title">{stage.label}</span>
            <span className="card-sub">{stage.desc}</span>
          </button>
        ))}
      </div>
    </main>
  )
}
