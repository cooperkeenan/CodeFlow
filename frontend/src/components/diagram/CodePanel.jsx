import { useState, useEffect } from 'react'
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter'
import { vscDarkPlus } from 'react-syntax-highlighter/dist/esm/styles/prism'
import { fetchCode } from '../../api/code'

const MIN_WIDTH = 320

const HEADER_LABEL = {
  fontFamily: 'IBM Plex Mono, monospace',
  fontSize: 12,
  fontWeight: 600,
  color: 'rgba(255,255,255,0.87)',
  lineHeight: 1.4,
}
const FILE_PATH = {
  fontFamily: 'IBM Plex Mono, monospace',
  fontSize: 10,
  color: '#39FF14',
  wordBreak: 'break-all',
  marginTop: 2,
}
const CLOSE_BTN = {
  background: 'none',
  border: 'none',
  color: 'rgba(255,255,255,0.38)',
  cursor: 'pointer',
  fontSize: 16,
  lineHeight: 1,
  padding: 0,
  flexShrink: 0,
  marginLeft: 8,
}
const MUTED = {
  fontFamily: 'IBM Plex Mono, monospace',
  fontSize: 11,
  color: 'rgba(255,255,255,0.38)',
  padding: '1rem',
}
const DRAG_HANDLE = {
  position: 'absolute',
  left: 0,
  top: 0,
  bottom: 0,
  width: 6,
  cursor: 'col-resize',
  zIndex: 1,
  borderLeft: '2px solid rgba(255,255,255,0.08)',
}

export default function CodePanel({ repo, label, file_path, start_line, end_line, onClose }) {
  const [width, setWidth] = useState(() => Math.round(window.innerWidth * 0.4))
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [code, setCode] = useState('')
  const [language, setLanguage] = useState('python')

  useEffect(() => {
    if (!repo || !file_path) return
    setLoading(true)
    setError(null)
    fetchCode(repo, file_path)
      .then(data => {
        setCode(data.content)
        setLanguage(data.language || 'python')
        setLoading(false)
      })
      .catch(() => {
        setError(true)
        setLoading(false)
      })
  }, [repo, file_path])

  useEffect(() => {
    if (!loading && !error && code) {
      document.getElementById('code-focus-line')?.scrollIntoView({ block: 'center' })
    }
  }, [loading, error, code])

  const lineProps = (ln) => {
    const highlighted = start_line != null && end_line != null && ln >= start_line && ln <= end_line
    const style = { display: 'block', ...(highlighted ? { background: 'rgba(57,255,20,0.12)' } : {}) }
    if (ln === start_line) return { id: 'code-focus-line', style }
    return { style }
  }

  const handleDragStart = (e) => {
    e.preventDefault()
    const startX = e.clientX
    const startW = width
    const maxW = Math.round(window.innerWidth * 0.8)
    const onMove = (ev) => {
      setWidth(Math.max(MIN_WIDTH, Math.min(maxW, startW + (startX - ev.clientX))))
    }
    const onUp = () => {
      window.removeEventListener('mousemove', onMove)
      window.removeEventListener('mouseup', onUp)
    }
    window.addEventListener('mousemove', onMove)
    window.addEventListener('mouseup', onUp)
  }

  return (
    <aside style={{
      position: 'relative',
      width,
      flexShrink: 0,
      background: '#121212',
      border: '1px solid #242424',
      borderRadius: 3,
      overflow: 'hidden',
      display: 'flex',
      flexDirection: 'column',
    }}>
      <div onMouseDown={handleDragStart} style={DRAG_HANDLE} />
      <div style={{
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'flex-start',
        padding: '0.9rem 1.1rem',
        borderBottom: '1px solid #242424',
        flexShrink: 0,
      }}>
        <div>
          <div style={HEADER_LABEL}>{label}</div>
          {file_path && <div style={FILE_PATH}>{file_path}</div>}
        </div>
        <button onClick={onClose} style={CLOSE_BTN}>×</button>
      </div>
      <div style={{ flex: 1, overflow: 'auto' }}>
        {loading && <div style={MUTED}>loading…</div>}
        {!loading && error && <div style={MUTED}>source unavailable</div>}
        {!loading && !error && (
          <SyntaxHighlighter
            language={language || 'python'}
            style={vscDarkPlus}
            showLineNumbers
            wrapLines
            lineProps={lineProps}
            customStyle={{ margin: 0, fontSize: 11, fontFamily: 'IBM Plex Mono, monospace', background: 'transparent' }}
          >
            {code}
          </SyntaxHighlighter>
        )}
      </div>
    </aside>
  )
}
