const BASE = {
  background: 'none',
  border: 'none',
  fontFamily: 'IBM Plex Mono, monospace',
  fontSize: 11,
  padding: 0,
  cursor: 'pointer',
  transition: 'color 120ms ease',
}

export default function Breadcrumb({ viewStack, onNavigate }) {
  const crumbs = [
    { label: 'system', index: 0 },
    ...viewStack.map((entry, i) => ({ label: entry.id, index: i + 1 })),
  ]

  return (
    <nav style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
      {crumbs.map((crumb, i) => {
        const isActive = i === crumbs.length - 1
        return (
          <span key={crumb.index} style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
            {i > 0 && <span style={{ color: '#333333', userSelect: 'none' }}>/</span>}
            <button
              style={{ ...BASE, color: isActive ? '#39FF14' : 'rgba(255,255,255,0.38)' }}
              onClick={() => !isActive && onNavigate(crumb.index)}
              disabled={isActive}
            >
              {crumb.label}
            </button>
          </span>
        )
      })}
    </nav>
  )
}