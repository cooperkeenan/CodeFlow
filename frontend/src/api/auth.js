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

export const forgotPassword = (email) =>
  request('/auth/forgot-password', {
    method: 'POST',
    body: JSON.stringify({ email }),
  })

export const resetPassword = (token, password) =>
  request('/auth/reset-password', {
    method: 'POST',
    body: JSON.stringify({ token, password }),
  })
