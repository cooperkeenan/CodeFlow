import { useEffect, useState } from 'react'
import { MONO, TEXT_MUTED, KIND_ACCENT } from '../styles'

const PAGE_SIZE = 4
const DEFAULT_MARKER = '▸'

const HEAD_ROW = { display: 'flex', alignItems: 'center', justifyContent: 'space-between', margin: '12px 0 5px' }
const HEAD = { fontSize: 9, letterSpacing: '0.12em', textTransform: 'uppercase', color: TEXT_MUTED }
const PAGER = { display: 'flex', alignItems: 'center', gap: 8, fontFamily: MONO, fontSize: 10, color: TEXT_MUTED }
const ARROW_BASE = { cursor: 'pointer', userSelect: 'none', padding: '0 6px', fontSize: 16, lineHeight: 1 }
const MARKER_STYLE = {
  fontSize: 8,
  color: KIND_ACCENT.entry,
  marginRight: 5,
  flexShrink: 0,
}
const NAME_STYLE = {
  fontFamily: MONO,
  fontSize: 11,
  color: KIND_ACCENT.entry,
  flex: '0 0 200px',
  whiteSpace: 'nowrap',
  overflow: 'hidden',
  textOverflow: 'ellipsis',
  display: 'flex',
  alignItems: 'center',
}

const SUMMARY_STYLE = {
  fontFamily: 'Instrument Sans, sans-serif',
  fontSize: 11,
  color: 'rgba(255,255,255,0.6)',
  lineHeight: 1.5,
  flex: 1,
  minWidth: 0,
}

function rowKey(attr, item) {
  return attr === 'data-method' ? item.name : item.fqn
}

export default function SymbolList({ heading, items, attr, onSelect, selectedFqn, marker = DEFAULT_MARKER }) {
  const [page, setPage] = useState(0)

  useEffect(() => { setPage(0) }, [items])

  if (!items?.length) return null

  const pageCount = Math.ceil(items.length / PAGE_SIZE)
  const current = Math.min(page, pageCount - 1)
  const start = current * PAGE_SIZE
  const visible = items.slice(start, start + PAGE_SIZE)
  const showPager = items.length > PAGE_SIZE
  const atFirst = current === 0
  const atLast = current === pageCount - 1

  return (
    <>
      <div style={HEAD_ROW}>
        <div style={HEAD}>{heading}</div>
        {showPager && (
          <div style={PAGER}>
            <span
              className="nodrag nopan"
              data-testid="symbol-page-prev"
              style={{ ...ARROW_BASE, opacity: atFirst ? 0.3 : 1, cursor: atFirst ? 'default' : 'pointer' }}
              onPointerDown={event => {
                event.stopPropagation()
                event.preventDefault()
                if (!atFirst) setPage(current - 1)
              }}
              onClick={event => { event.stopPropagation(); event.preventDefault() }}
            >
              ‹
            </span>
            <span data-testid="symbol-page">{current + 1}/{pageCount}</span>
            <span
              className="nodrag nopan"
              data-testid="symbol-page-next"
              style={{ ...ARROW_BASE, opacity: atLast ? 0.3 : 1, cursor: atLast ? 'default' : 'pointer' }}
              onPointerDown={event => {
                event.stopPropagation()
                event.preventDefault()
                if (!atLast) setPage(current + 1)
              }}
              onClick={event => { event.stopPropagation(); event.preventDefault() }}
            >
              ›
            </span>
          </div>
        )}
      </div>
      {visible.map(item => (
        <div
          key={item.fqn || item.name}
          {...{ [attr]: rowKey(attr, item) }}
          className="nodrag nopan"
          style={{
            display: 'flex',
            alignItems: 'flex-start',
            gap: 10,
            padding: '4px 0',
            cursor: 'pointer',
            background: selectedFqn === item.fqn ? 'rgba(255,255,255,0.06)' : 'transparent',
          }}
          onPointerDown={event => {
            event.stopPropagation()
            event.preventDefault()
            onSelect?.(item.fqn)
          }}
          onClick={event => {
            event.stopPropagation()
            event.preventDefault()
          }}
        >
          <span title={item.name} style={NAME_STYLE}>
            <span style={MARKER_STYLE}>{marker}</span>
            <span style={{ overflow: 'hidden', textOverflow: 'ellipsis' }}>{item.name}</span>
          </span>
          <span title={item.summary} style={SUMMARY_STYLE}>{item.summary}</span>
        </div>
      ))}
    </>
  )
}
