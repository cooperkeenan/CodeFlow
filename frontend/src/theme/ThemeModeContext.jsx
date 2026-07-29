import React, { createContext, useContext, useEffect, useState } from 'react'

const STORAGE_KEY = 'codeflow_theme'
const ThemeModeContext = createContext(null)

export function ThemeModeProvider({ children }) {
  const [mode, setModeState] = useState(() => {
    const stored = localStorage.getItem(STORAGE_KEY)
    return stored === 'light' ? 'light' : 'dark'
  })

  useEffect(() => {
    document.documentElement.dataset.theme = mode
    localStorage.setItem(STORAGE_KEY, mode)
  }, [mode])

  function setMode(next) {
    setModeState(next)
  }

  function toggle() {
    setModeState(prev => (prev === 'dark' ? 'light' : 'dark'))
  }

  return (
    <ThemeModeContext.Provider value={{ mode, toggle, setMode }}>
      {children}
    </ThemeModeContext.Provider>
  )
}

export function useThemeMode() {
  return useContext(ThemeModeContext)
}
