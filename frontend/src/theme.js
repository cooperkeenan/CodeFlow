import { createTheme } from '@mui/material/styles'

const MONO = "'IBM Plex Mono', monospace"
const SANS = "'Instrument Sans', sans-serif"

const theme = createTheme({
  palette: {
    mode: 'dark',
    primary: { main: '#39FF14', contrastText: '#0A1F0D' },
    secondary: { main: '#64B5F6' },
    error: { main: '#FF6B6B' },
    warning: { main: '#FFB84D' },
    info: { main: '#64B5F6' },
    success: { main: '#39FF14' },
    background: { default: '#121212', paper: '#1A1A1A' },
    divider: '#242424',
    text: {
      primary: 'rgba(255,255,255,0.87)',
      secondary: 'rgba(255,255,255,0.60)',
      disabled: 'rgba(255,255,255,0.38)',
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
        root: { backgroundImage: 'none', border: '1px solid #242424' },
      },
    },
    MuiButton: { defaultProps: { disableElevation: true } },
  },
})

export default theme
