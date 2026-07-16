import { MONO, BADGE_GLYPH } from './styles'

export default function NodeBadges({ badges, guardSource }) {
  if (!badges?.length) return null
  return (
    <div style={{ display: 'flex', gap: 3, marginTop: 4 }}>
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
              fontSize: 10,
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
