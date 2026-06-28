import { useState, useEffect } from 'react'
import { exchangeCode, listRepos } from '../api/github'
import { REDIRECT_URI, GITHUB_CLIENT_ID } from '../constants'

export function useGitHub() {
  const [accessToken, setAccessToken] = useState(null)
  const [repos, setRepos] = useState([])
  const [loading, setLoading] = useState(false)

  useEffect(() => {
    const params = new URLSearchParams(window.location.search)
    const code = params.get('code')
    if (!code || accessToken) return

    exchangeCode(code)
      .then(d => {
        setAccessToken(d.access_token)
        window.history.replaceState({}, '', '/')
      })
      .catch(console.error)
  }, [])

  useEffect(() => {
    if (!accessToken) return
    setLoading(true)
    listRepos(accessToken)
      .then(d => setRepos(d.repositories.filter(r => r.language === 'Python')))
      .finally(() => setLoading(false))
  }, [accessToken])

  const login = () => {
    window.location.href =
      `https://github.com/login/oauth/authorize?client_id=${GITHUB_CLIENT_ID}&redirect_uri=${REDIRECT_URI}&scope=repo`
  }

  return { accessToken, repos, loading, login }
}