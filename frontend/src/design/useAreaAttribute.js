import { useEffect } from 'react'
import { useLocation } from 'react-router-dom'
import areaForPath from './areaForPath'

export default function useAreaAttribute() {
  const { pathname } = useLocation()
  useEffect(() => {
    document.documentElement.dataset.area = areaForPath(pathname)
  }, [pathname])
}
