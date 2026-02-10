import { useState, useEffect } from 'react'
import './DeploymentProgress.css'

function DeploymentProgress({ customerId, onClose }) {
  const [status, setStatus] = useState('initiating')
  const [pipelineData, setPipelineData] = useState(null)
  const [error, setError] = useState(null)

  useEffect(() => {
    // Start polling for pipeline status
    const pollPipeline = async () => {
      try {
        // Get the latest pipeline run for this customer
        const response = await fetch(`/api/deployments/${customerId}-prod-${customerId}-api/pipeline`)
        if (!response.ok) throw new Error('Failed to fetch pipeline')
        
        const data = await response.json()
        setPipelineData(data)
        
        if (data.runs && data.runs.length > 0) {
          const latestRun = data.runs[0]
          
          if (latestRun.status === 'completed') {
            if (latestRun.conclusion === 'success') {
              setStatus('success')
              setTimeout(() => onClose(), 5000) // Auto-close after 5s
            } else {
              setStatus('failed')
              setError(latestRun.conclusion)
            }
            return // Stop polling
          } else if (latestRun.status === 'in_progress') {
            setStatus('deploying')
          } else if (latestRun.status === 'queued') {
            setStatus('queued')
          }
        } else {
          setStatus('waiting')
        }
      } catch (err) {
        console.error('Error polling pipeline:', err)
        setError(err.message)
      }
    }

    // Poll immediately, then every 5 seconds
    pollPipeline()
    const interval = setInterval(pollPipeline, 5000)
    
    // Stop polling after 5 minutes max
    const timeout = setTimeout(() => {
      clearInterval(interval)
      if (status === 'deploying' || status === 'queued' || status === 'waiting') {
        setStatus('timeout')
      }
    }, 300000)

    return () => {
      clearInterval(interval)
      clearTimeout(timeout)
    }
  }, [customerId])

  const getStatusInfo = () => {
    switch (status) {
      case 'initiating':
        return {
          icon: '🚀',
          title: 'Initiating Deployment',
          message: 'Starting production deployment...',
          color: '#3b82f6'
        }
      case 'waiting':
        return {
          icon: '⏳',
          title: 'Waiting for Pipeline',
          message: 'Waiting for GitHub Actions to start...',
          color: '#6b7280'
        }
      case 'queued':
        return {
          icon: '⏱️',
          title: 'Deployment Queued',
          message: 'Pipeline run is queued and will start soon...',
          color: '#f59e0b'
        }
      case 'deploying':
        return {
          icon: '⚙️',
          title: 'Deploying to Production',
          message: 'Pipeline is running...',
          color: '#3b82f6'
        }
      case 'success':
        return {
          icon: '✅',
          title: 'Deployment Successful!',
          message: 'Production deployment completed successfully.',
          color: '#22c55e'
        }
      case 'failed':
        return {
          icon: '❌',
          title: 'Deployment Failed',
          message: `Deployment failed: ${error || 'Unknown error'}`,
          color: '#ef4444'
        }
      case 'timeout':
        return {
          icon: '⏰',
          title: 'Monitoring Timeout',
          message: 'Pipeline is still running. Check ArgoCD for details.',
          color: '#f59e0b'
        }
      default:
        return {
          icon: '🔄',
          title: 'Processing',
          message: 'Processing deployment...',
          color: '#6b7280'
        }
    }
  }

  const statusInfo = getStatusInfo()
  const latestRun = pipelineData?.runs?.[0]

  return (
    <div className="deployment-progress-overlay" onClick={onClose}>
      <div className="deployment-progress-modal" onClick={(e) => e.stopPropagation()}>
        <div className="progress-header" style={{ borderTopColor: statusInfo.color }}>
          <div className="progress-icon" style={{ background: `${statusInfo.color}20`, color: statusInfo.color }}>
            {statusInfo.icon}
          </div>
          <div className="progress-title-section">
            <h2>{statusInfo.title}</h2>
            <p className="progress-customer">{customerId.replace('-', ' ').toUpperCase()} → PRODUCTION</p>
          </div>
          {(status === 'success' || status === 'failed' || status === 'timeout') && (
            <button className="progress-close" onClick={onClose}>×</button>
          )}
        </div>

        <div className="progress-body">
          <p className="progress-message">{statusInfo.message}</p>

          {(status === 'deploying' || status === 'queued') && (
            <div className="progress-spinner">
              <div className="spinner"></div>
            </div>
          )}

          {latestRun && (
            <div className="pipeline-info">
              <div className="pipeline-detail">
                <span className="detail-label">Branch:</span>
                <span className="detail-value">{latestRun.branch}</span>
              </div>
              <div className="pipeline-detail">
                <span className="detail-label">Commit:</span>
                <span className="detail-value">{latestRun.commit_sha}</span>
              </div>
              <div className="pipeline-detail">
                <span className="detail-label">Author:</span>
                <span className="detail-value">{latestRun.author}</span>
              </div>
              {latestRun.duration && (
                <div className="pipeline-detail">
                  <span className="detail-label">Duration:</span>
                  <span className="detail-value">{Math.floor(latestRun.duration / 60)}m {latestRun.duration % 60}s</span>
                </div>
              )}
            </div>
          )}

          <div className="progress-stages">
            <div className={`stage ${status !== 'initiating' && status !== 'waiting' ? 'completed' : 'active'}`}>
              <div className="stage-icon">1</div>
              <span className="stage-label">Trigger Deployment</span>
            </div>
            <div className="stage-connector"></div>
            <div className={`stage ${status === 'queued' || status === 'deploying' ? 'active' : status === 'success' || status === 'failed' ? 'completed' : ''}`}>
              <div className="stage-icon">2</div>
              <span className="stage-label">Run Pipeline</span>
            </div>
            <div className="stage-connector"></div>
            <div className={`stage ${status === 'success' ? 'completed' : status === 'deploying' ? 'active' : ''}`}>
              <div className="stage-icon">3</div>
              <span className="stage-label">Deploy to Production</span>
            </div>
          </div>

          <div className="progress-actions">
            {latestRun && (
              <a 
                href={latestRun.url}
                target="_blank"
                rel="noopener noreferrer"
                className="btn-view-github"
              >
                View Pipeline in GitHub →
              </a>
            )}
            <a 
              href={`http://argocd.local/applications/${customerId}-prod`}
              target="_blank"
              rel="noopener noreferrer"
              className="btn-view-argocd"
            >
              View in ArgoCD →
            </a>
          </div>

          {status === 'success' && (
            <div className="success-note">
              🎉 This window will close automatically in 5 seconds
            </div>
          )}
        </div>
      </div>
    </div>
  )
}

export default DeploymentProgress
