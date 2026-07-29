import { useState, useRef, useEffect, useCallback } from 'react'
import { Handle, Position } from 'reactflow'

const BASE_BOX = {
  minWidth: 80,
  minHeight: 28,
  padding: '5px 9px',
  borderRadius: 3,
  boxSizing: 'border-box',
  fontFamily: 'IBM Plex Mono, monospace',
  lineHeight: 1.4,
  wordBreak: 'break-word',
  whiteSpace: 'pre-wrap',
}

const HANDLE_STYLE = {
  opacity: 0,
  width: 1,
  height: 1,
  border: 'none',
  background: 'transparent',
  minWidth: 0,
  minHeight: 0,
}

export default function TextNode({ id, data, selected }) {
  const [editing, setEditing] = useState(false)
  const [draft, setDraft] = useState(data.text ?? '')
  const inputRef = useRef(null)

  const fontSize = data.fontSize ?? 13
  const color = data.color ?? 'rgba(255,255,255,0.87)'

  useEffect(() => {
    if (editing && inputRef.current) inputRef.current.focus()
  }, [editing])

  const commit = useCallback(() => {
    setEditing(false)
    const trimmed = draft.trim()
    if (trimmed !== (data.text ?? '') && data.onCommit) {
      data.onCommit(id, trimmed || (data.text ?? ''))
    }
  }, [draft, data, id])

  const handleDoubleClick = useCallback((e) => {
    e.stopPropagation()
    setDraft(data.text ?? '')
    setEditing(true)
  }, [data.text])

  const handleKeyDown = useCallback((e) => {
    if (e.key === 'Enter') { e.preventDefault(); commit() }
    if (e.key === 'Escape') { setEditing(false); setDraft(data.text ?? '') }
  }, [commit, data.text])

  const borderColor = selected ? 'rgba(255,255,255,0.4)' : 'rgba(255,255,255,0.12)'
  const background = selected ? 'rgba(255,255,255,0.06)' : 'transparent'

  return (
    <div
      className="cf-node cf-text-node"
      onDoubleClick={handleDoubleClick}
      style={{ ...BASE_BOX, fontSize, color, border: `1px solid ${borderColor}`, background, cursor: editing ? 'text' : 'default' }}
    >
      <Handle id="top" type="target" position={Position.Top} style={HANDLE_STYLE} />
      <Handle id="left" type="target" position={Position.Left} style={HANDLE_STYLE} />

      {editing ? (
        <textarea
          ref={inputRef}
          value={draft}
          onChange={e => setDraft(e.target.value)}
          onBlur={commit}
          onKeyDown={handleKeyDown}
          style={{
            background: 'transparent',
            border: 'none',
            outline: 'none',
            color,
            fontFamily: 'IBM Plex Mono, monospace',
            fontSize,
            lineHeight: 1.4,
            resize: 'none',
            width: '100%',
            minWidth: 60,
            padding: 0,
          }}
          rows={Math.max(1, draft.split('\n').length)}
          placeholder="Text"
        />
      ) : (
        <span style={{ display: 'block' }}>
          {data.text || <span style={{ color: 'rgba(255,255,255,0.25)' }}>Text</span>}
        </span>
      )}

      <Handle id="bottom" type="source" position={Position.Bottom} style={HANDLE_STYLE} />
      <Handle id="right" type="source" position={Position.Right} style={HANDLE_STYLE} />
    </div>
  )
}
