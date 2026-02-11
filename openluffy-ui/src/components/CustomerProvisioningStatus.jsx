import { useState, useEffect } from 'react'
import './CustomerProvisioningStatus.css'

function CustomerProvisioningStatus({ customerId, onClose }) {
  const [status, setStatus] = useState(null)
  const [loading, setLoading] = useState(true)
  const [complete, setComplete] = useState(false)

  useEffect(() => {
    fetchStatus()
    const interval = setInterval(fetchStatus, 3000) // Poll every 3 seconds
    return () => clearInterval(interval)
  }, [customerId])

  const fetchStatus = async () => {
    try {
      const response = await fetch(`/api/customers/${customerId}/provisioning/status`)
      if (!response.ok) throw new Error('Failed to fetch')
      const data = await response.json()
      
      setStatus(data)
      setLoading(false)
      
      // Check if all steps are complete
      const allComplete = data.steps.every(s => 
        s.status === 'success' || s.status === 'error'
      )
      setComplete(allComplete)
    } catch (error) {
      console.error('Error fetching provisioning status:', error)
      setLoading(false)
    }
  }

  const getStepIcon = (status) => {
    if (status === 'success') return '✅'
    if (status === 'error') return '❌'
    if (status === 'running') return '⏳'
    return '⏸️'
  }

  if (loading) {
    return (
      <div className="provisioning-modal">
        <div className="provisioning-content">
          <h2>Loading...</h2>
        </div>
      </div>
    )
  }

  return (
    <div className="provisioning-modal" onClick={complete ? onClose : undefined}>
      <div className="provisioning-content" onClick={(e) => e.stopPropagation()}>
        <div className="provisioning-header">
          <h2>
            {complete ? '🎉 Customer Infrastructure Ready' : '⚙️ Provisioning Infrastructure'}
          </h2>
          {complete && (
            <button className="btn-close" onClick={onClose}>×</button>
          )}
        </div>

        <div className="provisioning-body">
          <h3>{status?.customer_name || customerId}</h3>
          <p className="provisioning-subtitle">
            {complete 
              ? 'All systems operational. Your customer is ready to deploy.'
              : 'Setting up GitHub, Kubernetes, and ArgoCD resources...'}
          </p>

          <div className="provisioning-steps">
            {status?.steps?.map((step, index) => (
              <div key={index} className={`provision-step ${step.status}`}>
                <div className="step-icon">{getStepIcon(step.status)}</div>
                <div className="step-details">
                  <div className="step-name">{step.message}</div>
                  {step.status === 'running' && (
                    <div className="step-progress">
                      <div className="progress-bar">
                        <div className="progress-fill"></div>
                      </div>
                    </div>
                  )}
                  {step.timestamp && (
                    <div className="step-timestamp">
                      {new Date(step.timestamp).toLocaleTimeString()}
                    </div>
                  )}
                </div>
              </div>
            ))}
          </div>

          {complete && (
            <div className="next-steps">
              <h4>📋 Next Steps:</h4>
              <ol>
                <li>Push code to GitHub repository</li>
                <li>CI/CD will build and deploy automatically</li>
                <li>Monitor deployments in Applications view</li>
                <li>Check application health in K8s Insights</li>
              </ol>
            </div>
          )}
        </div>

        {complete && (
          <div className="provisioning-footer">
            <button className="btn-done" onClick={onClose}>
              ✅ Done
            </button>
          </div>
        )}
      </div>
    </div>
  )
}

export default CustomerProvisioningStatus
