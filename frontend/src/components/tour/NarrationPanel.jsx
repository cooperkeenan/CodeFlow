import { MONO, SURFACE_2, BORDER, TEXT, TEXT_MUTED, KIND_ACCENT } from '../flow/styles'
import { Branches, Facts, Refs, Section } from './PanelSections'

const SANS = 'Instrument Sans, sans-serif'
const MAX_STAGGER = 40

function Words({ text }) {
  return text.split(' ').map((word, index) => (
    <span key={index} className="tour-word" style={{ '--i': Math.min(index, MAX_STAGGER) }}>
      {word}{' '}
    </span>
  ))
}

export default function NarrationPanel({ step, index, count, repoUrl }) {
  if (!step) return null
  const node = step.node ?? {}
  const accent = KIND_ACCENT[node.kind] ?? KIND_ACCENT.step
  return (
    <aside
      key={step.id}
      style={{
        position: 'absolute', top: 0, right: 0, bottom: 0, width: '30%', minWidth: 340,
        zIndex: 8, overflowY: 'auto', background: SURFACE_2,
        borderLeft: `1px solid ${BORDER}`, padding: '22px 26px 96px',
        animation: 'tourBubbleIn 320ms ease both',
      }}
    >
      <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
        <span style={{ width: 7, height: 7, borderRadius: 4, background: accent, flexShrink: 0 }} />
        <span style={{ fontFamily: MONO, fontSize: 10, letterSpacing: '0.12em', color: TEXT_MUTED }}>
          {step.phase}
        </span>
        <span style={{ marginLeft: 'auto', fontFamily: MONO, fontSize: 10, color: 'rgba(255,255,255,0.3)' }}>
          {String(index + 1).padStart(2, '0')} / {String(count).padStart(2, '0')}
        </span>
      </div>

      <h2 style={{ fontFamily: MONO, fontSize: 17, fontWeight: 600, color: TEXT, lineHeight: 1.35, margin: '14px 0 0' }}>
        {step.title}
      </h2>

      <p style={{ fontFamily: SANS, fontSize: 14, color: 'rgba(255,255,255,0.72)', lineHeight: 1.7, margin: '14px 0 0' }}>
        <Words text={step.body} />
      </p>

      {step.detail && (
        <p style={{ fontFamily: SANS, fontSize: 13, color: 'rgba(255,255,255,0.5)', lineHeight: 1.7, margin: '12px 0 0' }}>
          {step.detail}
        </p>
      )}

      {step.facts?.length > 0 && <Section title="at a glance"><Facts facts={step.facts} /></Section>}

      <Section title="this node">
        <div style={{ fontFamily: MONO, fontSize: 12, color: TEXT, lineHeight: 1.5 }}>{node.label}</div>
        <div style={{ fontFamily: MONO, fontSize: 9, color: accent, letterSpacing: '0.1em', marginTop: 4 }}>
          {node.kind}
        </div>
        {node.oneLiner && (
          <div style={{ fontFamily: SANS, fontSize: 12, color: TEXT_MUTED, lineHeight: 1.6, marginTop: 8 }}>
            {node.oneLiner}
          </div>
        )}
        {node.backing?.map(name => (
          <div key={name} style={{ fontFamily: MONO, fontSize: 10, color: TEXT_MUTED, marginTop: 6, wordBreak: 'break-all' }}>
            {name}()
          </div>
        ))}
      </Section>

      {step.branches?.length > 0 && (
        <Section title={`branches (${step.branches.length})`}>
          <Branches branches={step.branches} />
        </Section>
      )}

      {node.refs?.length > 0 && (
        <Section title="source">
          <Refs refs={node.refs} repoUrl={repoUrl} />
        </Section>
      )}
    </aside>
  )
}
