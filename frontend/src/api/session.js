const TOKEN_KEY = 'codeflow_session_token'
const USER_KEY = 'codeflow_user'
const GITHUB_TOKEN_KEY = 'codeflow_github_token'

export const getSessionToken = () => localStorage.getItem(TOKEN_KEY)

export const getGithubToken = () => localStorage.getItem(GITHUB_TOKEN_KEY)

export const saveGithubToken = (token) => {
  if (token) localStorage.setItem(GITHUB_TOKEN_KEY, token)
}

export const getUser = () => {
  const raw = localStorage.getItem(USER_KEY)
  return raw ? JSON.parse(raw) : null
}

export const saveSession = (token, user) => {
  localStorage.setItem(TOKEN_KEY, token)
  localStorage.setItem(USER_KEY, JSON.stringify(user))
}

export const saveUser = (user) => {
  if (user) localStorage.setItem(USER_KEY, JSON.stringify(user))
}

export const clearSession = () => {
  localStorage.removeItem(TOKEN_KEY)
  localStorage.removeItem(USER_KEY)
  localStorage.removeItem(GITHUB_TOKEN_KEY)
}
