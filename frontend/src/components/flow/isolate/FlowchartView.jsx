import { useLayoutEffect, useRef, useState } from 'react'
import { layout } from './flowchartLayout'
import { FlowNode, FlowEdge } from './flowchartShapes'
import { MONO, SURFACE_2, BORDER, TEXT_MUTED } from '../styles'

const PADDING = 20

const ROOT_STYLE = {
  background: SURFACE_2,
  border: `1px solid ${BORDER}`,
  borderRadius: 3,
  height: '100%',
  minHeight: 0,
  overflow: 'auto',
  flex: 1,
  display: 'flex',
}

const PLACEHOLDER_STYLE = {
  fontFamily: MONO,
  fontSize: 10,
  color: TEXT_MUTED,
  padding: 12,
}

export default function FlowchartView({ steps, name }) {
  const hostRef = useRef(null)
  const [maxWidth, setMaxWidth] = useState(0)

  useLayoutEffect(() => {
    const host = hostRef.current
    if (host) setMaxWidth(host.clientWidth - PADDING * 2)
  }, [steps, name])

  if (!name) {
    return (
      <div data-testid="flowchart-view" data-nodes="0" data-edges="0" className="nowheel" style={{ ...ROOT_STYLE, ...PLACEHOLDER_STYLE }}>
        select a method to view its flowchart
      </div>
    )
  }
  if (steps === undefined) {
    return (
      <div data-testid="flowchart-view" data-nodes="0" data-edges="0" className="nowheel" style={{ ...ROOT_STYLE, ...PLACEHOLDER_STYLE }}>
        re-run the analysis to capture steps for this repo
      </div>
    )
  }
  if (steps.length === 0) {
    return (
      <div data-testid="flowchart-view" data-nodes="0" data-edges="0" className="nowheel" style={{ ...ROOT_STYLE, ...PLACEHOLDER_STYLE }}>
        this method makes no calls
      </div>
    )
  }

  const { nodes, edges, width, height } = layout(steps, name, maxWidth || undefined)
  const svgW = width + PADDING * 2
  const svgH = height + PADDING * 2

  return (
    <div ref={hostRef} data-testid="flowchart-view" data-nodes={nodes.length} data-edges={edges.length} className="nowheel" style={ROOT_STYLE}>
      <svg width={svgW} height={svgH} viewBox={`${-PADDING} ${-PADDING} ${svgW} ${svgH}`} style={{ margin: 'auto', flexShrink: 0 }}>
        <defs>
          <marker id="flowchart-arrow" markerWidth={8} markerHeight={8} refX={7} refY={4} orient="auto">
            <path d="M0,0 L8,4 L0,8 Z" fill={TEXT_MUTED} />
          </marker>
        </defs>
        {edges.map(edge => <FlowEdge key={edge.id} edge={edge} />)}
        {nodes.map(node => <FlowNode key={node.id} node={node} />)}
      </svg>
    </div>
  )
}
