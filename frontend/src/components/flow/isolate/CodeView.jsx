import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter'
import { vscDarkPlus } from 'react-syntax-highlighter/dist/esm/styles/prism'
import { MONO, SURFACE_2, BORDER, TEXT_MUTED } from '../styles'
import './isolate-code.css'

const HEADER_STYLE = {
  fontFamily: MONO,
  fontSize: 10,
  color: TEXT_MUTED,
  padding: '4px 8px',
  borderBottom: `1px solid ${BORDER}`,
  whiteSpace: 'nowrap',
  overflow: 'hidden',
  textOverflow: 'ellipsis',
  flexShrink: 0,
}

const PLACEHOLDER_STYLE = {
  fontFamily: MONO,
  fontSize: 10,
  color: TEXT_MUTED,
  padding: 12,
}

const CODE_STYLE = {
  ...vscDarkPlus,
  'pre[class*="language-"]': {
    ...vscDarkPlus['pre[class*="language-"]'],
    background: SURFACE_2,
    margin: 0,
  },
  'code[class*="language-"]': {
    ...vscDarkPlus['code[class*="language-"]'],
    background: SURFACE_2,
  },
}

const LINE_NUMBER_STYLE = {
  color: TEXT_MUTED,
  minWidth: '1.6em',
  marginRight: 6,
  paddingRight: 0,
  opacity: 0.7,
  userSelect: 'none',
}

const PANE_STYLE = {
  background: SURFACE_2,
  border: `1px solid ${BORDER}`,
  borderRadius: 3,
  height: '100%',
  display: 'flex',
  flexDirection: 'column',
  minHeight: 0,
}

export default function CodeView({ fqn, name, source }) {
  if (!fqn) {
    return (
      <div data-testid="code-view" data-fqn="" style={PLACEHOLDER_STYLE}>
        select a method to view its code
      </div>
    )
  }
  return (
    <div data-testid="code-view" data-fqn={fqn} style={PANE_STYLE}>
      <div style={HEADER_STYLE} title={fqn}>{name || fqn}</div>
      <SyntaxHighlighter
        language="python"
        style={CODE_STYLE}
        showLineNumbers
        lineNumberStyle={LINE_NUMBER_STYLE}
        className="nowheel isolate-code-pane"
        customStyle={{ fontSize: 10, margin: 0, padding: 8, background: SURFACE_2, flex: 1, minHeight: 0, overflow: 'auto' }}
      >
        {source || ''}
      </SyntaxHighlighter>
    </div>
  )
}
