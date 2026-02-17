import { useState, useEffect } from 'react'
import { useCustomer } from '../contexts/CustomerContext'
import './PendingApprovals.css'
import DeploymentProgress from './DeploymentProgress'

function PendingApprovals() {
  const { activeCustomer } = useCustomer()
  const [approvals, setApprovals] = useState([])
  const [loading, setLoading] = useState(true)
  const [promoting, setPromoting] = useState(null)
  const [showProgress, setShowProgress] = useState(null)

  useEffect(() => {
    fetchApprovals()
    // Poll every 30 seconds
    const interval = setInterval(fetchApprovals, 30000)
    return () => clearInterval(interval)
  }, [])

  const fetchApprovals = async () => {
    try {
      const response = await fetch('/api/approvals/pending')
      if (!response.ok) throw new Error('Failed to fetch')
      const data = await response.json()
      setApprovals(data.approvals || [])
    } catch (error) {
      console.error('Error fetching approvals:', error)
    } finally {
      setLoading(false)
    }
  }

  const handleApprove = async (customerId) => {
    if (!confirm(`Promote ${customerId} to PRODUCTION?\n\nThis will deploy the preprod version to production.`)) {
      return
    }

    setPromoting(customerId)
    try {
      const response = await fetch(`/customers/${customerId}/promote-to-prod`, {
        method: 'POST'
      })
      
      if (!response.ok) throw new Error('Promotion failed')
      
      // Show progress modal
      setShowProgress(customerId)
      
      // Refresh approvals list
      setTimeout(fetchApprovals, 2000)
    } catch (error) {
      console.error('Error promoting:', error)
      alert(`❌ Failed to promote ${customerId}: ${error.message}`)
    } finally {
      setPromoting(null)
    }
  }

  const handleProgressClose = () => {
    setShowProgress(null)
    fetchApprovals() // Refresh approvals when closing
  }

  if (loading) {
    return (
      <div className="pending-approvals">
        <h3>🔔 Pending Approvals</h3>
        <div className="loading-approvals">Loading...</div>
      </div>
    )
  }

  const filteredApprovals = activeCustomer
    ? approvals.filter(a => a.customer_id === activeCustomer.id)
    : approvals

  if (filteredApprovals.length === 0) {
    return (
      <div className="pending-approvals no-approvals">
        <h3>🔔 Pending Approvals</h3>
        <div className="no-approvals-message">
          <span className="check-icon">✓</span>
          <p>
            {!activeCustomer 
              ? 'Select a customer to view their pending approvals'
              : `All environments in sync for ${activeCustomer.name}. No pending approvals.`
            }
          </p>
        </div>
      </div>
    )
  }

  return (
    <div className="pending-approvals has-approvals">
      <div className="approvals-header">
        <h3>🔔 Pending Approvals</h3>
        <span className="approval-count">{filteredApprovals.length}</span>
      </div>
      
      <div className="approvals-list">
        {filteredApprovals.map(approval => (
          <div key={approval.customer_id} className="approval-card">
            <div className="approval-header">
              <div>
                <h4>{approval.customer_name}</h4>
                <span className="approval-status">PREPROD ready for PRODUCTION</span>
              </div>
              <button 
                className={`btn-approve ${promoting === approval.customer_id ? 'promoting' : ''}`}
                onClick={() => handleApprove(approval.customer_id)}
                disabled={promoting === approval.customer_id}
              >
                {promoting === approval.customer_id ? '⏳ Promoting...' : '✓ Approve for Production'}
              </button>
            </div>

            <div className="approval-details">
              <div className="env-comparison">
                <div className="env-box env-preprod">
                  <div className="env-label">PREPROD (ready to promote)</div>
                  <div className="env-image">{approval.preprod_image}</div>
                  <div className="env-status">
                    {approval.preprod_ready} replica{approval.preprod_ready !== 1 ? 's' : ''} ready
                  </div>
                </div>

                <div className="arrow">→</div>

                <div className="env-box env-prod">
                  <div className="env-label">PROD (current)</div>
                  <div className="env-image">{approval.prod_image}</div>
                  <div className="env-status">
                    {approval.prod_ready} replica{approval.prod_ready !== 1 ? 's' : ''} ready
                  </div>
                </div>
              </div>

              <div className="approval-actions">
                <a 
                  href={`http://argocd.local/applications/${approval.customer_id}-prod`}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="link-argocd"
                >
                  View in ArgoCD →
                </a>
              </div>
            </div>
          </div>
        ))}
      </div>

      {showProgress && (
        <DeploymentProgress 
          customerId={showProgress}
          onClose={handleProgressClose}
        />
      )}
    </div>
  )
}

export default PendingApprovals
