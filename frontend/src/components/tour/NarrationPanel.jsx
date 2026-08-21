import { MONO, SURFACE_2, BORDER, TEXT, TEXT_MUTED, KIND_ACCENT } from '../flow/styles'
import { Branches, Facts, Refs, Section } from './PanelSections'

const SANS = 'Instrument Sans, sans-serif'
const MAX_STAGGER = 40
export const NARRATION_HEIGHT = 300

const CLAMP_3 = {
  display: '-webkit-box', WebkitBoxOrient: 'vertical', WebkitLineClamp: 3, overflow: 'hidden',
}

const COLUMN = { flex: 1, minWidth: 0, overflow: 'hidden' }
const RULE = { borderLeft: '1px solid rgba(255,255,255,0.07)', paddingLeft: 32 }

function branchSummary(branches) {
  const total = branches.length
  const stops = branches.filter(branch => branch.terminal).length
  const rejoins = total - stops
  if (rejoins === total) return `${total} branches, all rejoin`
  if (stops === total) return `${total} branches, ${stops} stop`
  return `${total} branches, ${rejoins} rejoin · ${stops} stop`
}

function Words({ text }) {
  return text.split(' ').map((word, index) => (
    <span key={index} className="tour-word" style={{ '--i': Math.min(index, MAX_STAGGER) }}>{word}{' '}</span>
  ))
}

export default function NarrationPanel({ step, index, count, repoUrl, chapters = [] }) {
  if (!step) return null
  const node = step.node ?? {}
  const accent = KIND_ACCENT[node.kind] ?? KIND_ACCENT.step
  const chapter = chapters.find(c => c.id === step.chapter)
  const actNumber = chapter?.number ?? 1
  const actCount = chapter?.stepIds?.length ?? count
  const actPosition = step.chapterPosition ?? index + 1
  const isCard = step.shot === 'card'
  return (
    <aside
      key={step.id}
      style={{
        position: 'absolute', left: 0, right: 0, bottom: 0, height: NARRATION_HEIGHT,
        zIndex: 8, overflow: 'hidden', background: SURFACE_2,
        borderTop: `1px solid ${BORDER}`, padding: '20px 30px',
        animation: 'tourBubbleIn 320ms ease both',
      }}
    >
      <div style={{ display: 'flex', height: '100%', gap: 32 }}>
        <div style={{ ...COLUMN, flex: isCard ? 1 : 1.4 }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
            <span style={{ width: 7, height: 7, borderRadius: 4, background: accent, flexShrink: 0 }} />
            <span style={{ fontFamily: MONO, fontSize: 10, letterSpacing: '0.12em', color: TEXT_MUTED }}>
              {step.phase}
            </span>
            <span style={{ marginLeft: 'auto', fontFamily: MONO, fontSize: 10, color: 'rgba(255,255,255,0.3)' }}>
              ACT {actNumber} &middot; {actPosition} / {actCount}
              {'  '}
              <span style={{ fontSize: 9, color: 'rgba(255,255,255,0.2)', marginLeft: 8 }}>
                {String(index + 1).padStart(2, '0')} / {String(count).padStart(2, '0')}
              </span>
            </span>
          </div>

          <h2 style={{ fontFamily: MONO, fontSize: 16, fontWeight: 600, color: TEXT, lineHeight: 1.35, margin: '12px 0 0' }}>
            {step.title}
          </h2>

          <p style={{ ...CLAMP_3, fontFamily: SANS, fontSize: 13, color: 'rgba(255,255,255,0.72)', lineHeight: 1.6, margin: '10px 0 0' }}>
            <Words text={step.body} />
          </p>

          {step.detail && (
            <p style={{ ...CLAMP_3, fontFamily: SANS, fontSize: 12, color: 'rgba(255,255,255,0.5)', lineHeight: 1.6, margin: '8px 0 0' }}>
              {step.detail}
            </p>
          )}
        </div>

        {!isCard && <div style={{ ...COLUMN, ...RULE }}>
          <Section title="this node" compact>
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

          {step.facts?.length > 0 && <Section title="at a glance" compact><Facts facts={step.facts} /></Section>}
        </div>}

        {!isCard && <div style={{ ...COLUMN, ...RULE, overflowY: 'auto' }}>
          {step.branches?.length > 2 && (
            <Section title="branches" compact>
              <div style={{ fontFamily: MONO, fontSize: 11, color: TEXT_MUTED }}>
                {branchSummary(step.branches)}
              </div>
            </Section>
          )}

          {step.branches?.length > 0 && step.branches.length <= 2 && (
            <Section title={`branches (${step.branches.length})`} compact>
              <Branches branches={step.branches} />
            </Section>
          )}

          {node.refs?.length > 0 && (
            <Section title="source" compact>
              <Refs refs={node.refs} repoUrl={repoUrl} />
            </Section>
          )}
        </div>}
      </div>
    </aside>
  )
}
