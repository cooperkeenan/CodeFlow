import { Box, Tooltip } from '@mui/material'
import { ACTION, HUE, NEUTRAL, STATUS, TEXT } from '../../design/tokens'

const BAR_HEIGHT = 10
const NOTCH_HEIGHT = 6

const NOTCH_COLOUR = {
  done: HUE.green.base,
  active: TEXT.primary,
  pending: NEUTRAL.surface5,
}

const stripe = `repeating-linear-gradient(115deg, ${NEUTRAL.surface4} 0 6px, ${NEUTRAL.surface3} 6px 12px)`

export default function RunProgressBar({ percent, ceiling, points = [], failed }) {
  const fill = failed ? STATUS.danger : ACTION
  return (
    <Box sx={{ mb: 1 }}>
      <Box
        sx={{
          position: 'relative',
          height: BAR_HEIGHT,
          borderRadius: 0.5,
          overflow: 'hidden',
          backgroundColor: NEUTRAL.surface2,
        }}
      >
        {!failed && (
          <Box
            sx={{
              position: 'absolute',
              inset: 0,
              width: `${ceiling}%`,
              background: stripe,
              backgroundSize: '17px 100%',
              animation: 'runProgressStripe 1.1s linear infinite',
              '@keyframes runProgressStripe': {
                from: { backgroundPosition: '0 0' },
                to: { backgroundPosition: '17px 0' },
              },
            }}
          />
        )}
        <Box
          data-testid="progress-fill"
          sx={{
            position: 'absolute',
            inset: 0,
            width: `${percent}%`,
            backgroundColor: fill,
            transition: 'width 400ms ease',
          }}
        />
      </Box>
      <Box sx={{ position: 'relative', height: NOTCH_HEIGHT, mt: '2px' }}>
        {points.map(point => (
          <Tooltip key={point.key} title={point.label} placement="bottom" arrow>
            <Box
              data-testid={`progress-tick-${point.key}`}
              sx={{
                position: 'absolute',
                left: `${point.at}%`,
                top: 0,
                width: point.state === 'active' ? 3 : 2,
                height: point.state === 'active' ? NOTCH_HEIGHT : NOTCH_HEIGHT - 2,
                borderRadius: '1px',
                backgroundColor: failed && point.state === 'active'
                  ? STATUS.danger
                  : NOTCH_COLOUR[point.state] ?? NOTCH_COLOUR.pending,
              }}
            />
          </Tooltip>
        ))}
      </Box>
    </Box>
  )
}
