import { PrismLight as SyntaxHighlighter } from 'react-syntax-highlighter'
import python from 'react-syntax-highlighter/dist/esm/languages/prism/python'
import vscDarkPlus from 'react-syntax-highlighter/dist/esm/styles/prism/vsc-dark-plus'
import Handles from '../Handles'
import { KIND_ACCENT, SURFACE, SURFACE_2, TEXT_MUTED, MONO, shellStyle } from '../styles'
import { GEOMETRY_FALLBACK } from '../geometryFallback'

SyntaxHighlighter.registerLanguage('python', python)

export default function SnippetNode({ data, selected, sourcePosition, targetPosition }) {
  const { width, height } = data.geometry ?? GEOMETRY_FALLBACK.snippet
  const base = {
    width,
    minHeight: height,
    borderRadius: 6,
    background: SURFACE,
    display: 'flex',
    flexDirection: 'column',
    overflow: 'hidden',
    boxSizing: 'border-box',
  }
  const style = shellStyle(base, KIND_ACCENT.snippet, {
    selected,
    highlighted: data.highlighted,
    dashed: data.dashed,
    focused: data.focused,
    dimmed: data.dimmed,
    adjacent: data.adjacent,
    entering: data.entering,
    enterDelay: data.enterDelay,
  })
  return (
    <div style={style}>
      <Handles target={targetPosition} source={sourcePosition} />
      <div style={{
        fontFamily: MONO,
        fontSize: 11.5,
        color: TEXT_MUTED,
        background: SURFACE_2,
        padding: '7px 14px',
        borderBottom: '1px solid rgba(255,255,255,0.08)',
        whiteSpace: 'nowrap',
        overflow: 'hidden',
        textOverflow: 'ellipsis',
        flexShrink: 0,
      }}>
        {data.provenance}
      </div>
      <div style={{ flex: 1, overflow: 'hidden', padding: '10px 14px' }}>
        <SyntaxHighlighter
          language={data.codeLang || 'python'}
          style={vscDarkPlus}
          customStyle={{ background: 'transparent', padding: 0, margin: 0 }}
          codeTagProps={{ style: { fontFamily: MONO, fontSize: 11, lineHeight: 1.5 } }}
        >
          {data.code || ''}
        </SyntaxHighlighter>
      </div>
    </div>
  )
}
