import { useState, useEffect } from 'react'
import './PipelineStatus.css'

function PipelineStatus({ customerId }) {
  const [status, setStatus] = useState(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    fetchStatus()
    const interval = setInterval(fetchStatus, 30000) // Refresh every 30s
    return () => clearInterval(interval)
  }, [customerId])

  const fetchStatus = async () => {
    try {
      const response = await fetch('/api/pipelines/status')
      if (!response.ok) throw new Error('Failed to fetch')
      const data = await response.json()
      const customerStatus = data.pipelines?.find(p => p.customer_id === customerId)
      setStatus(customerStatus)
    } catch (error) {
      console.error('Error fetching pipeline status:', error)
    } finally {
      setLoading(false)
    }
  }

  if (loading || !status) {
    return (
      <div className="pipeline-status">
        <div className="pipeline-stages">
          <div className="stage stage-unknown">
            <div className="stage-icon">○</div>
            <span className="stage-name">Pipeline</span>
          </div>
        </div>
      </div>
    )
  }

  const getStageStatus = () => {
    if (status.status === 'no_runs' || status.status === 'error') {
      return { test: 'idle', build: 'idle', deploy: 'idle' }
    }

    if (status.status === 'completed') {
      if (status.conclusion === 'success') {
        return { test: 'success', build: 'success', deploy: 'success' }
      } else if (status.conclusion === 'failure') {
        // Assume failure in test stage for now
        return { test: 'failure', build: 'idle', deploy: 'idle' }
      }
    }

    if (status.status === 'in_progress') {
      // Show as running
      return { test: 'success', build: 'running', deploy: 'idle' }
    }

    return { test: 'idle', build: 'idle', deploy: 'idle' }
  }

  const stages = getStageStatus()

  const getStageIcon = (stageStatus) => {
    switch (stageStatus) {
      case 'success': return '✓'
      case 'failure': return '✗'
      case 'running': return '⟳'
      default: return '○'
    }
  }

  const getStageClass = (stageStatus) => {
    return `stage stage-${stageStatus}`
  }

  return (
    <div className="pipeline-status">
      <div className="pipeline-header-mini">
        <span className="pipeline-label">CI/CD Pipeline</span>
        {status.commit_sha && (
          <a 
            href={status.url}
            target="_blank"
            rel="noopener noreferrer"
            className="pipeline-link-mini"
          >
            {status.commit_sha} →
          </a>
        )}
      </div>
      <div className="pipeline-stages">
        <div className={getStageClass(stages.test)}>
          <div className="stage-icon">{getStageIcon(stages.test)}</div>
          <span className="stage-name">Test</span>
        </div>
        <div className="stage-separator">→</div>
        <div className={getStageClass(stages.build)}>
          <div className="stage-icon">{getStageIcon(stages.build)}</div>
          <span className="stage-name">Build</span>
        </div>
        <div className="stage-separator">→</div>
        <div className={getStageClass(stages.deploy)}>
          <div className="stage-icon">{getStageIcon(stages.deploy)}</div>
          <span className="stage-name">Deploy</span>
        </div>
      </div>
    </div>
  )
}

export default PipelineStatus
