import React from 'react'
import ReactDOM from 'react-dom/client'
import App from './App.jsx'
import './index.css'
import { installGlobalAxios401Interceptor } from './context/api'

installGlobalAxios401Interceptor()

const nativeFetch = window.fetch.bind(window)
window.fetch = (input, init = {}) => {
  const nextInit = typeof init === 'object' && init !== null ? { ...init } : {}
  if (!Object.prototype.hasOwnProperty.call(nextInit, 'credentials')) {
    nextInit.credentials = 'include'
  }
  return nativeFetch(input, nextInit)
}

ReactDOM.createRoot(document.getElementById('root')).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>,
)
