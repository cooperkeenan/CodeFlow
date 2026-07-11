import { request } from './client'

export const signup = (email, password) =>
  request('/auth/signup', {
    method: 'POST',
    body: JSON.stringify({ email, password }),
  })

export const login = (email, password) =>
  request('/auth/login', {
    method: 'POST',
    body: JSON.stringify({ email, password }),
  })
