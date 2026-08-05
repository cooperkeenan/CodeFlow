import { MONO, BADGE_GLYPH } from './styles'

export default function NodeBadges({ badges, guardSource, scale = 1 }) {
  if (!badges?.length) return null
  return (
    <div style={{ display: 'flex', gap: Math.round(3 * scale), marginTop: Math.round(4 * scale) }}>
      {badges.map(badge => {
        const spec = BADGE_GLYPH[badge]
        if (!spec) return null
        const title = badge === 'guarded' && guardSource
          ? `guarded — ${guardSource}`
          : spec.title
        return (
          <span
            key={badge}
            title={title}
            style={{
              fontFamily: MONO,
              fontSize: Math.round(10 * scale * 10) / 10,
              lineHeight: 1,
              color: 'rgba(255,255,255,0.7)',
              cursor: 'default',
            }}
          >
            {spec.glyph}
          </span>
        )
      })}
    </div>
  )
}
