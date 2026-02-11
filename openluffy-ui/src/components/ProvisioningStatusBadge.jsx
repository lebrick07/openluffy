import { useEffect, useState } from 'react'
import './ProvisioningStatusBadge.css'

function ProvisioningStatusBadge({ customerId, onClick }) {
  const [status, setStatus] = useState('checking')
  
  useEffect(() => {
    if (!customerId) return
    
    checkProvisioningStatus()
    // Poll every 5 seconds if provisioning
    const interval = setInterval(() => {
      if (status === 'provisioning' || status === 'checking') {
        checkProvisioningStatus()
      }
    }, 5000)
    
    return () => clearInterval(interval)
  }, [customerId, status])
  
  const checkProvisioningStatus = async () => {
    try {
      const response = await fetch(`/api/customers/${customerId}/provisioning/status`)
      if (!response.ok) {
        setStatus('complete') // Assume complete if endpoint doesn't exist
        return
      }
      
      const data = await response.json()
      setStatus(data.status) // provisioning, complete, error
    } catch (error) {
      console.error('Error checking provisioning status:', error)
      setStatus('complete')
    }
  }
  
  if (status === 'complete') {
    return null // Don't show badge when complete
  }
  
  const getBadgeClass = () => {
    if (status === 'provisioning') return 'provisioning-badge provisioning'
    if (status === 'error') return 'provisioning-badge error'
    return 'provisioning-badge checking'
  }
  
  const getBadgeIcon = () => {
    if (status === 'provisioning') return '⏳'
    if (status === 'error') return '❌'
    return '⏸️'
  }
  
  const getBadgeText = () => {
    if (status === 'provisioning') return 'Provisioning...'
    if (status === 'error') return 'Error'
    return 'Pending'
  }
  
  return (
    <button 
      className={getBadgeClass()}
      onClick={(e) => {
        e.stopPropagation()
        if (onClick) onClick()
      }}
      title="Click to view provisioning progress"
    >
      <span className="badge-icon">{getBadgeIcon()}</span>
      <span className="badge-text">{getBadgeText()}</span>
    </button>
  )
}

export default ProvisioningStatusBadge
