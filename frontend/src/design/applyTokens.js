import { CSS_VARS } from './tokens'

export default function applyTokens(root = document.documentElement) {
  for (const [name, value] of Object.entries(CSS_VARS)) {
    root.style.setProperty(name, value)
  }
}
