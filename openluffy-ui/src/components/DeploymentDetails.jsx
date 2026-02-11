import { useState, useEffect, useCallback } from 'react'
import './DeploymentDetails.css'
import PipelineView from './PipelineView'
import LogViewer from './LogViewer'

function DeploymentDetails({ deploymentId, onClose }) {
  const [details, setDetails] = useState(null)
  const [loading, setLoading] = useState(true)
  const [activeTab, setActiveTab] = useState('overview')

  const fetchDetails = useCallback(async () => {
    setLoading(true)
    try {
      const response = await fetch(`/api/deployments/${deploymentId}/details-v2`)
      if (!response.ok) throw new Error('Failed to fetch')
      const data = await response.json()
      setDetails(data)
    } catch (error) {
      console.error('Error fetching deployment details:', error)
    } finally {
      setLoading(false)
    }
  }, [deploymentId])

  useEffect(() => {
    if (deploymentId) {
      fetchDetails()
    }
  }, [deploymentId, fetchDetails])

  const fetchPodLogs = async (podName) => {
    setLoadingLogs(true)
    try {
      const response = await fetch(`/api/deployments/${deploymentId}/pods/${podName}/logs?lines=200`)
      if (!response.ok) throw new Error('Failed to fetch logs')
      const data = await response.json()
      setPodLogs(data.logs)
      setSelectedPod(podName)
    } catch (error) {
      console.error('Error fetching pod logs:', error)
      setPodLogs('Error loading logs')
    } finally {
      setLoadingLogs(false)
    }
  }

  if (loading) {
    return (
      <div className="deployment-details-modal">
        <div className="deployment-details-content">
          <div className="loading">Loading deployment details...</div>
        </div>
      </div>
    )
  }

  if (!details) {
    return null
  }

  const { deployment, pods, events, image } = details

  return (
    <div className="deployment-details-modal" onClick={onClose}>
      <div className="deployment-details-content" onClick={(e) => e.stopPropagation()}>
        <div className="details-header">
          <div className="header-content-section">
            <div className="deployment-title-section">
              <h2>{deployment.name}</h2>
              <div className="deployment-meta-badges">
                <span className="meta-badge namespace-badge">{deployment.namespace}</span>
                <span className={`meta-badge env-badge env-${deployment.namespace.split('-').pop()}`}>
                  {deployment.namespace.split('-').pop()?.toUpperCase()}
                </span>
                <span className={`meta-badge status-badge status-${deployment.replicas.ready === deployment.replicas.desired ? 'healthy' : 'warning'}`}>
                  {deployment.replicas.ready}/{deployment.replicas.desired} Ready
                </span>
              </div>
            </div>
            <div className="deployment-details-info">
              <div className="info-item">
                <span className="info-label">Customer:</span>
                <span className="info-value">{deployment.namespace.split('-')[0]}</span>
              </div>
              <div className="info-item">
                <span className="info-label">Image:</span>
                <span className="info-value info-code">{image}</span>
              </div>
            </div>
          </div>
          <button className="close-btn" onClick={onClose}>×</button>
        </div>

        <div className="details-tabs">
          <button 
            className={`tab-btn ${activeTab === 'overview' ? 'active' : ''}`}
            onClick={() => setActiveTab('overview')}
          >
            Overview
          </button>
          <button 
            className={`tab-btn ${activeTab === 'pods' ? 'active' : ''}`}
            onClick={() => setActiveTab('pods')}
          >
            Pods ({pods.length})
          </button>
          <button 
            className={`tab-btn ${activeTab === 'events' ? 'active' : ''}`}
            onClick={() => setActiveTab('events')}
          >
            Events ({events.length})
          </button>
          <button 
            className={`tab-btn ${activeTab === 'logs' ? 'active' : ''}`}
            onClick={() => setActiveTab('logs')}
          >
            Logs
          </button>
          <button 
            className={`tab-btn ${activeTab === 'pipeline' ? 'active' : ''}`}
            onClick={() => setActiveTab('pipeline')}
          >
            Pipeline
          </button>
        </div>

        <div className="details-body">
          {activeTab === 'overview' && (
            <div className="overview-tab">
              <div className="replica-status">
                <h3>Replica Status</h3>
                <div className="replica-grid">
                  <div className="replica-item">
                    <span className="replica-label">Desired</span>
                    <span className="replica-value">{deployment.replicas.desired}</span>
                  </div>
                  <div className="replica-item">
                    <span className="replica-label">Current</span>
                    <span className="replica-value">{deployment.replicas.current}</span>
                  </div>
                  <div className="replica-item">
                    <span className="replica-label">Ready</span>
                    <span className="replica-value replica-ready">{deployment.replicas.ready}</span>
                  </div>
                  <div className="replica-item">
                    <span className="replica-label">Available</span>
                    <span className="replica-value">{deployment.replicas.available}</span>
                  </div>
                </div>
              </div>

              <div className="deployment-meta">
                <h3>Deployment Info</h3>
                <div className="meta-grid">
                  <div className="meta-item">
                    <span className="meta-label">Strategy</span>
                    <span className="meta-value">{deployment.strategy}</span>
                  </div>
                  <div className="meta-item">
                    <span className="meta-label">Created</span>
                    <span className="meta-value">{new Date(deployment.created).toLocaleString()}</span>
                  </div>
                  <div className="meta-item">
                    <span className="meta-label">Namespace</span>
                    <span className="meta-value">{deployment.namespace}</span>
                  </div>
                </div>
              </div>

              <div className="quick-stats">
                <h3>Quick Stats</h3>
                <div className="stats-grid">
                  <div className="stat-card">
                    <span className="stat-icon">🟢</span>
                    <div>
                      <div className="stat-value">{pods.filter(p => p.status === 'Running').length}</div>
                      <div className="stat-label">Running Pods</div>
                    </div>
                  </div>
                  <div className="stat-card">
                    <span className="stat-icon">🔄</span>
                    <div>
                      <div className="stat-value">{pods.reduce((sum, p) => sum + p.restarts, 0)}</div>
                      <div className="stat-label">Total Restarts</div>
                    </div>
                  </div>
                  <div className="stat-card">
                    <span className="stat-icon">📦</span>
                    <div>
                      <div className="stat-value">{pods.reduce((sum, p) => sum + p.containers.length, 0)}</div>
                      <div className="stat-label">Containers</div>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          )}

          {activeTab === 'pods' && (
            <div className="pods-tab">
              <div className="pods-list">
                {pods.map(pod => (
                  <div key={pod.name} className={`pod-card pod-${pod.status.toLowerCase()}`}>
                    <div className="pod-header">
                      <div>
                        <h4>{pod.name}</h4>
                        <span className={`pod-status status-${pod.status.toLowerCase()}`}>
                          {pod.status}
                        </span>
                      </div>
                      <button 
                        className="btn-view-logs"
                        onClick={() => fetchPodLogs(pod.name)}
                      >
                        View Logs
                      </button>
                    </div>
                    <div className="pod-details-grid">
                      <div className="pod-detail">
                        <span className="detail-label">IP:</span>
                        <span className="detail-value">{pod.ip || 'N/A'}</span>
                      </div>
                      <div className="pod-detail">
                        <span className="detail-label">Node:</span>
                        <span className="detail-value">{pod.node}</span>
                      </div>
                      <div className="pod-detail">
                        <span className="detail-label">Restarts:</span>
                        <span className="detail-value">{pod.restarts}</span>
                      </div>
                      <div className="pod-detail">
                        <span className="detail-label">Age:</span>
                        <span className="detail-value">{new Date(pod.age).toLocaleString()}</span>
                      </div>
                    </div>
                    <div className="pod-containers">
                      <strong>Containers:</strong>
                      {pod.containers.map(container => (
                        <div key={container.name} className="container-item">
                          <span className={`container-status ${container.ready ? 'ready' : 'not-ready'}`}>
                            {container.ready ? '✓' : '✗'}
                          </span>
                          <span className="container-name">{container.name}</span>
                          <span className="container-restarts">({container.restarts} restarts)</span>
                        </div>
                      ))}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {activeTab === 'events' && (
            <div className="events-tab">
              <div className="events-list">
                {events.length === 0 ? (
                  <div className="no-events">No recent events</div>
                ) : (
                  events.map((event, index) => (
                    <div key={index} className={`event-item event-${event.type.toLowerCase()}`}>
                      <div className="event-time">
                        {new Date(event.timestamp).toLocaleString()}
                      </div>
                      <div className="event-content">
                        <div className="event-reason">{event.reason}</div>
                        <div className="event-message">{event.message}</div>
                      </div>
                      <div className={`event-type type-${event.type.toLowerCase()}`}>
                        {event.type}
                      </div>
                    </div>
                  ))
                )}
              </div>
            </div>
          )}

          {activeTab === 'logs' && (
            <LogViewer 
              deploymentId={deploymentId}
              deploymentName={deployment.name}
              namespace={deployment.namespace}
              customer={deployment.namespace.split('-')[0]}
            />
          )}

          {activeTab === 'pipeline' && (
            <PipelineView deploymentId={deploymentId} />
          )}
        </div>
      </div>
    </div>
  )
}

export default DeploymentDetails
