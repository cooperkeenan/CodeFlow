const AREA_BY_PATH = {
  '/': 'maps',
  '/settings': 'plain',
  '/tour': 'tour',
  '/login': 'plain',
  '/signup': 'plain',
  '/forgot-password': 'plain',
  '/reset-password': 'plain',
  '/repo': 'explore',
  '/repo-fixture': 'explore',
  '/endpoint': 'explore',
  '/endpoint-fixture': 'explore',
  '/flow': 'explore',
  '/flow-fixture': 'explore',
}

export default function areaForPath(pathname) {
  return AREA_BY_PATH[pathname] ?? 'maps'
}
