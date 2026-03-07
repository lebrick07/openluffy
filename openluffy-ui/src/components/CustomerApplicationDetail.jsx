import { useState, useEffect } from 'react'
import { useParams, useNavigate, Link } from 'react-router-dom'
import './CustomerApplicationDetail.css'

function CustomerApplicationDetail() {
  const { customerId, environment } = useParams()
  const navigate = useNavigate()
  const deploymentId = `${customerId}-${environment}`
  
  const [deployment, setDeployment] = useState(null)
  const [syncStatus, setSyncStatus] = useState(null)
  const [loading, setLoading] = useState(true)
  const [actionLoading, setActionLoading] = useState(false)
  const [activeTab, setActiveTab] = useState('overview')
  
  useEffect(() => {
    fetchDeploymentDetails()
    const interval = setInterval(fetchDeploymentDetails, 10000) // Refresh every 10s
    return () => clearInterval(interval)
  }, [deploymentId])
  
  const fetchDeploymentDetails = async () => {
    try {
      const [detailsRes, statusRes] = await Promise.all([
        fetch(`/api/deployments/${deploymentId}/details`),
        fetch(`/api/v1/deployments/${deploymentId}/sync-status`)
      ])
      
      const detailsData = await detailsRes.json()
      const statusData = await statusRes.json()
      
      setDeployment(detailsData)
      setSyncStatus(statusData)
    } catch (error) {
      console.error('Error fetching deployment:', error)
    } finally {
      setLoading(false)
    }
  }
  
  const handleSync = async () => {
    if (!confirm(`Deploy latest version of ${customerId}-${environment}?`)) return
    
    setActionLoading(true)
    try {
      const response = await fetch(
        `/api/v1/deployments/${deploymentId}/deploy`,
        { 
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ revision: 'HEAD' })
        }
      )
      
      if (!response.ok) throw new Error('Deploy failed')
      
      const result = await response.json()
      alert(`✓ ${result.message}`)
      fetchDeploymentDetails()
    } catch (error) {
      alert(`✗ Deploy failed: ${error.message}`)
    } finally {
      setActionLoading(false)
    }
  }
  
  const handleRollback = async () => {
    if (!confirm(`Rollback ${customerId}-${environment} to previous version?`)) return
    
    setActionLoading(true)
    try {
      const response = await fetch(
        `/api/v1/deployments/${deploymentId}/rollback`,
        { 
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ to_revision: 'previous' })
        }
      )
      
      if (!response.ok) throw new Error('Rollback failed')
      
      const result = await response.json()
      alert(`✓ ${result.message}`)
      fetchDeploymentDetails()
    } catch (error) {
      alert(`✗ Rollback failed: ${error.message}`)
    } finally {
      setActionLoading(false)
    }
  }
  
  const handleScale = async () => {
    const current = deployment?.deployment?.replicas?.desired || 1
    const replicas = prompt('How many replicas? (0-20)', current)
    if (!replicas || isNaN(replicas)) return
    
    setActionLoading(true)
    try {
      const response = await fetch(
        `/api/v1/deployments/${deploymentId}/scale`,
        { 
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ replicas: parseInt(replicas) })
        }
      )
      
      if (!response.ok) throw new Error('Scale failed')
      
      const result = await response.json()
      alert(`✓ ${result.message}`)
      fetchDeploymentDetails()
    } catch (error) {
      alert(`✗ Scale failed: ${error.message}`)
    } finally {
      setActionLoading(false)
    }
  }
  
  const handleRestart = async () => {
    if (!confirm(`Restart all pods for ${customerId}-${environment}?`)) return
    
    setActionLoading(true)
    try {
      const response = await fetch(
        `/api/v1/deployments/${deploymentId}/restart`,
        { method: 'POST', headers: { 'Content-Type': 'application/json' } }
      )
      
      if (!response.ok) throw new Error('Restart failed')
      
      const result = await response.json()
      alert(`✓ ${result.message}`)
      fetchDeploymentDetails()
    } catch (error) {
      alert(`✗ Restart failed: ${error.message}`)
    } finally {
      setActionLoading(false)
    }
  }
  
  if (loading && !deployment) {
    return <div className="detail-loading">Loading application details...</div>
  }
  
  if (!deployment) {
    return (
      <div className="detail-error">
        <p>Application not found</p>
        <Link to="/" className="back-link">← Back to Applications</Link>
      </div>
    )
  }
  
  const { replicas = {} } = deployment.deployment || {}
  const healthStatus = syncStatus?.health || 'Unknown'
  const syncStatusText = syncStatus?.status || 'Unknown'
  
  return (
    <div className="app-detail-page">
      {/* Header */}
      <div className="detail-header">
        <Link to="/" className="back-link">← Back to Applications</Link>
        
        <div className="detail-title-section">
          <h1 className="detail-title">
            🚀 {customerId}
          </h1>
          <div className="detail-badges">
            <span className={`env-badge env-${environment}`}>
              {environment.toUpperCase()}
            </span>
            <span className={`health-badge health-${healthStatus.toLowerCase()}`}>
              {healthStatus} {healthStatus === 'Healthy' ? '✓' : '⚠'}
            </span>
            <span className={`sync-badge sync-${syncStatusText.toLowerCase()}`}>
              {syncStatusText}
            </span>
          </div>
          <div className="detail-subtitle">
            Last deployed: {deployment.deployment?.created || 'Unknown'}
          </div>
        </div>
        
        {/* Action Buttons */}
        <div className="detail-actions">
          <button className="action-btn-primary" onClick={handleSync} disabled={actionLoading}>
            🔄 Sync Now
          </button>
          <button className="action-btn-secondary" onClick={handleRollback} disabled={actionLoading}>
            ⏮️ Rollback
          </button>
          <button className="action-btn-secondary" onClick={handleScale} disabled={actionLoading}>
            📊 Scale
          </button>
          <button className="action-btn-danger" onClick={handleRestart} disabled={actionLoading}>
            🔁 Restart
          </button>
        </div>
      </div>
      
      {/* Tabs */}
      <div className="detail-tabs">
        <button 
          className={activeTab === 'overview' ? 'tab active' : 'tab'}
          onClick={() => setActiveTab('overview')}
        >
          Overview
        </button>
        <button 
          className={activeTab === 'pods' ? 'tab active' : 'tab'}
          onClick={() => setActiveTab('pods')}
        >
          Pods ({deployment.pods?.length || 0})
        </button>
        <button 
          className={activeTab === 'events' ? 'tab active' : 'tab'}
          onClick={() => setActiveTab('events')}
        >
          Events
        </button>
      </div>
      
      {/* Tab Content */}
      <div className="detail-content">
        {activeTab === 'overview' && (
          <div className="overview-tab">
            {/* Replicas Card */}
            <div className="detail-card">
              <h3>📊 Replicas</h3>
              <div className="replicas-grid">
                <div className="replica-stat">
                  <span className="stat-label">Desired</span>
                  <span className="stat-value">{replicas.desired || 0}</span>
                </div>
                <div className="replica-stat">
                  <span className="stat-label">Current</span>
                  <span className="stat-value">{replicas.current || 0}</span>
                </div>
                <div className="replica-stat">
                  <span className="stat-label">Ready</span>
                  <span className="stat-value">{replicas.ready || 0}</span>
                </div>
                <div className="replica-stat">
                  <span className="stat-label">Available</span>
                  <span className="stat-value">{replicas.available || 0}</span>
                </div>
              </div>
            </div>
            
            {/* Pods Table */}
            <div className="detail-card">
              <h3>🎯 Pods ({deployment.pods?.length || 0})</h3>
              <table className="pods-table">
                <thead>
                  <tr>
                    <th>Name</th>
                    <th>Status</th>
                    <th>Restarts</th>
                    <th>IP</th>
                    <th>Node</th>
                  </tr>
                </thead>
                <tbody>
                  {deployment.pods?.map(pod => (
                    <tr key={pod.name}>
                      <td><code>{pod.name}</code></td>
                      <td>
                        <span className={`pod-status status-${pod.status.toLowerCase()}`}>
                          {pod.status}
                        </span>
                      </td>
                      <td>{pod.restarts}</td>
                      <td><code>{pod.ip}</code></td>
                      <td>{pod.node}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
            
            {/* Image Info */}
            <div className="detail-card">
              <h3>📦 Image</h3>
              <code className="image-display">{deployment.image || 'Unknown'}</code>
            </div>
            
            {/* Config */}
            <div className="detail-card">
              <h3>⚙️ Configuration</h3>
              <div className="config-grid">
                <div className="config-item">
                  <span className="config-label">Strategy:</span>
                  <span className="config-value">{deployment.deployment?.strategy || 'RollingUpdate'}</span>
                </div>
                <div className="config-item">
                  <span className="config-label">Namespace:</span>
                  <span className="config-value">{deployment.deployment?.namespace}</span>
                </div>
              </div>
            </div>
          </div>
        )}
        
        {activeTab === 'pods' && (
          <div className="pods-tab">
            <div className="detail-card">
              <table className="pods-detail-table">
                <thead>
                  <tr>
                    <th>Pod Name</th>
                    <th>Status</th>
                    <th>Restarts</th>
                    <th>IP</th>
                    <th>Node</th>
                    <th>Containers</th>
                    <th>Age</th>
                  </tr>
                </thead>
                <tbody>
                  {deployment.pods?.map(pod => (
                    <tr key={pod.name}>
                      <td><code>{pod.name}</code></td>
                      <td>
                        <span className={`pod-status status-${pod.status.toLowerCase()}`}>
                          {pod.status}
                        </span>
                      </td>
                      <td>{pod.restarts}</td>
                      <td><code>{pod.ip}</code></td>
                      <td>{pod.node}</td>
                      <td>
                        {pod.containers?.map(c => (
                          <div key={c.name} className="container-info">
                            {c.name} {c.ready ? '✓' : '✗'}
                          </div>
                        ))}
                      </td>
                      <td>{pod.age}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}
        
        {activeTab === 'events' && (
          <div className="events-tab">
            <div className="detail-card">
              <h3>📋 Recent Events</h3>
              <div className="events-timeline">
                {deployment.events?.map((event, idx) => (
                  <div key={idx} className={`event-item event-${event.type?.toLowerCase()}`}>
                    <span className="event-time">{event.timestamp}</span>
                    <span className="event-type">{event.type}</span>
                    <span className="event-reason">{event.reason}</span>
                    <p className="event-message">{event.message}</p>
                  </div>
                ))}
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}

export default CustomerApplicationDetail
