const KEY_PREFIX = 'codeflow:brainstorm-path:'

export function defaultPath(repo) {
  return `~/github/${repo.split('/').pop()}`
}

export function loadPath(repo) {
  try {
    return localStorage.getItem(KEY_PREFIX + repo) || defaultPath(repo)
  } catch {
    return defaultPath(repo)
  }
}

export function savePath(repo, value) {
  try {
    localStorage.setItem(KEY_PREFIX + repo, value)
  } catch {
    return
  }
}
