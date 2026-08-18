// Empty in dev so requests stay relative and go through the Vite proxy.
// In production set VITE_API_BASE to the deployed backend origin.
export const API_URL = import.meta.env.VITE_API_BASE || ''
export const GITHUB_CLIENT_ID = 'Ov23liff91VGCpUNWcXc'
export const REDIRECT_URI = window.location.origin