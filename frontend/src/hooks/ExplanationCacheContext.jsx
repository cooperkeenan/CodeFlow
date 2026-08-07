import { createContext, useCallback, useContext, useMemo, useRef } from 'react'

const ExplanationCacheContext = createContext(null)

export function ExplanationCacheProvider({ children }) {
  const cache = useRef(new Map())

  const get = useCallback(key => cache.current.get(key), [])
  const set = useCallback((key, value) => cache.current.set(key, value), [])
  const value = useMemo(() => ({ get, set }), [get, set])

  return (
    <ExplanationCacheContext.Provider value={value}>
      {children}
    </ExplanationCacheContext.Provider>
  )
}

export function useExplanationCache() {
  return useContext(ExplanationCacheContext)
}
