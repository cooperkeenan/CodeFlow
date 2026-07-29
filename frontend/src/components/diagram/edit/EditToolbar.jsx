import { Panel } from 'reactflow'
import NearMeIcon from '@mui/icons-material/NearMe'
import TextFieldsIcon from '@mui/icons-material/TextFields'
import DeleteOutlineIcon from '@mui/icons-material/DeleteOutline'
import ArrowRightAltIcon from '@mui/icons-material/ArrowRightAlt'
import RemoveIcon from '@mui/icons-material/Remove'
import CallMadeIcon from '@mui/icons-material/CallMade'

const TEXT_COLORS = ['#ffffff', '#39FF14', '#64B5F6', '#FF6B6B', '#FFD166']

const pill = (active, disabled = false) => ({
  display: 'inline-flex',
  alignItems: 'center',
  gap: 4,
  fontFamily: 'IBM Plex Mono, monospace',
  fontSize: 10,
  fontWeight: 600,
  letterSpacing: '0.08em',
  padding: '3px 9px',
  borderRadius: 3,
  border: active ? '1px solid var(--accent)' : '1px solid var(--border-hi)',
  background: active ? 'rgba(57,255,20,0.12)' : 'transparent',
  color: disabled ? 'var(--text-disabled)' : active ? 'var(--accent)' : 'var(--text-medium)',
  cursor: disabled ? 'not-allowed' : 'pointer',
  userSelect: 'none',
})

const sep = {
  width: 1,
  height: 18,
  background: 'var(--border-hi)',
  margin: '0 4px',
  display: 'inline-block',
  verticalAlign: 'middle',
}

const wrapper = {
  display: 'flex',
  alignItems: 'center',
  gap: 4,
  background: 'var(--surface)',
  border: '1px solid var(--border)',
  borderRadius: 4,
  padding: '5px 8px',
  boxShadow: '0 2px 8px rgba(0,0,0,0.6)',
}

export default function EditToolbar({
  activeTool,
  hasSelection,
  hasEdgeSelection,
  hasTextSelection,
  onSelectTool,
  onAddText,
  onDelete,
  onSetArrowhead,
  onSetLineStyle,
  onBumpFont,
  onSetColor,
}) {
  return (
    <Panel position="top-center">
      <div style={wrapper}>
        <button style={pill(activeTool === 'select')} onClick={() => onSelectTool('select')}>
          <NearMeIcon style={{ fontSize: 12 }} /> Select
        </button>
        <button style={pill(activeTool === 'text')} onClick={() => { onSelectTool('text'); onAddText() }}>
          <TextFieldsIcon style={{ fontSize: 12 }} /> Text
        </button>
        <button
          style={pill(false, !hasSelection)}
          onClick={() => { if (hasSelection) onDelete() }}
          disabled={!hasSelection}
        >
          <DeleteOutlineIcon style={{ fontSize: 12 }} /> Delete
        </button>

        <span style={sep} />

        <button
          style={pill(false, !hasEdgeSelection)}
          onClick={() => { if (hasEdgeSelection) onSetArrowhead('none') }}
          disabled={!hasEdgeSelection}
          title="No arrowhead"
        >
          <RemoveIcon style={{ fontSize: 12 }} /> None
        </button>
        <button
          style={pill(false, !hasEdgeSelection)}
          onClick={() => { if (hasEdgeSelection) onSetArrowhead('open') }}
          disabled={!hasEdgeSelection}
          title="Open arrowhead"
        >
          <CallMadeIcon style={{ fontSize: 12 }} /> Open
        </button>
        <button
          style={pill(false, !hasEdgeSelection)}
          onClick={() => { if (hasEdgeSelection) onSetArrowhead('closed') }}
          disabled={!hasEdgeSelection}
          title="Filled arrowhead"
        >
          <ArrowRightAltIcon style={{ fontSize: 12 }} /> Filled
        </button>

        <span style={sep} />

        <button
          style={pill(false, !hasEdgeSelection)}
          onClick={() => { if (hasEdgeSelection) onSetLineStyle('solid') }}
          disabled={!hasEdgeSelection}
        >
          Solid
        </button>
        <button
          style={pill(false, !hasEdgeSelection)}
          onClick={() => { if (hasEdgeSelection) onSetLineStyle('dashed') }}
          disabled={!hasEdgeSelection}
        >
          Dashed
        </button>

        {hasTextSelection && (
          <>
            <span style={sep} />
            <button style={pill(false, false)} onClick={() => onBumpFont(-2)}>A-</button>
            <button style={pill(false, false)} onClick={() => onBumpFont(2)}>A+</button>
            <span style={sep} />
            {TEXT_COLORS.map(c => (
              <button
                key={c}
                title={c}
                onClick={() => onSetColor(c)}
                style={{
                  width: 14,
                  height: 14,
                  borderRadius: '50%',
                  background: c,
                  border: '2px solid var(--border-hi)',
                  cursor: 'pointer',
                  padding: 0,
                  flexShrink: 0,
                }}
              />
            ))}
          </>
        )}
      </div>
    </Panel>
  )
}
