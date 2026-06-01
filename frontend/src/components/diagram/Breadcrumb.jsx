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
            {i > 0 && <span style={{ color: '#252525', userSelect: 'none' }}>/</span>}
            <button
              style={{ ...BASE, color: isActive ? '#c8f135' : '#3a3a3a' }}
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