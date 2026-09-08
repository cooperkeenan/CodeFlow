import { createTheme } from '@mui/material/styles'
import { ACCENT, ACTION, NEUTRAL, STATUS, TEXT } from './design/tokens'

const MONO = "'IBM Plex Mono', monospace"
const SANS = "'Instrument Sans', sans-serif"

const theme = createTheme({
  palette: {
    mode: 'dark',
    primary: { main: ACCENT, contrastText: NEUTRAL.onAccent },
    secondary: { main: STATUS.info },
    error: { main: STATUS.danger },
    warning: { main: STATUS.warning },
    info: { main: STATUS.info },
    success: { main: ACTION, contrastText: NEUTRAL.onAction },
    background: { default: NEUTRAL.bg, paper: NEUTRAL.surface },
    divider: NEUTRAL.border,
    text: {
      primary: TEXT.primary,
      secondary: TEXT.secondary,
      disabled: TEXT.disabled,
    },
  },
  shape: { borderRadius: 4 },
  typography: {
    fontFamily: SANS,
    fontSize: 14,
    button: { fontFamily: MONO, textTransform: 'none', fontWeight: 500 },
    h1: { fontFamily: MONO },
    h2: { fontFamily: MONO },
    h3: { fontFamily: MONO },
    h4: { fontFamily: MONO },
    h5: { fontFamily: MONO },
    h6: { fontFamily: MONO },
    overline: { fontFamily: MONO, letterSpacing: '0.08em' },
  },
  components: {
    MuiPaper: {
      styleOverrides: {
        root: { backgroundImage: 'none', border: `1px solid ${NEUTRAL.border}` },
      },
    },
    MuiButton: { defaultProps: { disableElevation: true } },
  },
})

export default theme
