import { useEffect, useState } from 'react'
import './Toast.css'

const toastIcons = {
  success: '✅',
  error: '❌',
  warning: '⚠️',
  info: 'ℹ️'
}

function Toast({ message, type = 'info' }) {
  const [visible, setVisible] = useState(false)

  useEffect(() => {
    // Fade in
    setTimeout(() => setVisible(true), 10)
    
    // Fade out before unmount
    const timer = setTimeout(() => setVisible(false), 3500)
    
    return () => clearTimeout(timer)
  }, [])

  return (
    <div className={`toast toast-${type} ${visible ? 'toast-visible' : ''}`}>
      <span className="toast-icon">{toastIcons[type]}</span>
      <span className="toast-message">{message}</span>
    </div>
  )
}

export default Toast
