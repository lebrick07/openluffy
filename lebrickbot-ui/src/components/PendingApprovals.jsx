import { useState, useEffect } from 'react'
import './PendingApprovals.css'

function PendingApprovals() {
  const [approvals, setApprovals] = useState([])
  const [loading, setLoading] = useState(true)
  const [promoting, setPromoting] = useState(null)

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
      const response = await fetch(`/api/customers/${customerId}/promote-to-prod`, {
        method: 'POST'
      })
      
      if (!response.ok) throw new Error('Promotion failed')
      
      const result = await response.json()
      
      alert(`✅ Production deployment initiated for ${customerId}!\n\nCheck ArgoCD for sync status: http://argocd.local`)
      
      // Refresh approvals list
      fetchApprovals()
    } catch (error) {
      console.error('Error promoting:', error)
      alert(`❌ Failed to promote ${customerId}: ${error.message}`)
    } finally {
      setPromoting(null)
    }
  }

  if (loading) {
    return (
      <div className="pending-approvals">
        <h3>🔔 Pending Approvals</h3>
        <div className="loading-approvals">Loading...</div>
      </div>
    )
  }

  if (approvals.length === 0) {
    return (
      <div className="pending-approvals no-approvals">
        <h3>🔔 Pending Approvals</h3>
        <div className="no-approvals-message">
          <span className="check-icon">✓</span>
          <p>All environments in sync. No pending approvals.</p>
        </div>
      </div>
    )
  }

  return (
    <div className="pending-approvals has-approvals">
      <div className="approvals-header">
        <h3>🔔 Pending Approvals</h3>
        <span className="approval-count">{approvals.length}</span>
      </div>
      
      <div className="approvals-list">
        {approvals.map(approval => (
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
    </div>
  )
}

export default PendingApprovals
