import { useState, useEffect } from 'react'
import './PipelinesView.css'

function PipelinesView() {
  const [pipelines, setPipelines] = useState([])
  const [selectedPipeline, setSelectedPipeline] = useState(null)
  const [runs, setRuns] = useState(null)
  const [jobs, setJobs] = useState(null)
  const [loadingRuns, setLoadingRuns] = useState(false)
  const [loadingJobs, setLoadingJobs] = useState(false)

  useEffect(() => {
    fetchPipelines()
    const interval = setInterval(fetchPipelines, 30000)
    return () => clearInterval(interval)
  }, [])

  const fetchPipelines = async () => {
    try {
      const response = await fetch('/api/pipelines/status')
      if (!response.ok) throw new Error('Failed to fetch')
      const data = await response.json()
      setPipelines(data.pipelines || [])
    } catch (error) {
      console.error('Error fetching pipelines:', error)
    }
  }

  const fetchRuns = async (customerId, deploymentId) => {
    setLoadingRuns(true)
    try {
      const response = await fetch(`/api/deployments/${deploymentId}/pipeline`)
      if (!response.ok) throw new Error('Failed to fetch')
      const data = await response.json()
      setRuns(data)
      setSelectedPipeline(customerId)
    } catch (error) {
      console.error('Error fetching runs:', error)
    } finally {
      setLoadingRuns(false)
    }
  }

  const fetchJobsForRun = async (deploymentId, runId) => {
    setLoadingJobs(true)
    try {
      const response = await fetch(`/api/deployments/${deploymentId}/pipeline/${runId}/jobs`)
      if (!response.ok) throw new Error('Failed to fetch')
      const data = await response.json()
      setJobs({ runId, ...data })
    } catch (error) {
      console.error('Error fetching jobs:', error)
    } finally {
      setLoadingJobs(false)
    }
  }

  const getStatusIcon = (status, conclusion) => {
    if (status === 'completed') {
      if (conclusion === 'success') return '✓'
      if (conclusion === 'failure') return '✗'
      if (conclusion === 'cancelled') return '⊘'
      return '●'
    }
    if (status === 'in_progress') return '⟳'
    if (status === 'queued') return '⋯'
    return '○'
  }

  const getStatusClass = (status, conclusion) => {
    if (status === 'completed') {
      if (conclusion === 'success') return 'status-success'
      if (conclusion === 'failure') return 'status-failure'
      if (conclusion === 'cancelled') return 'status-cancelled'
    }
    if (status === 'in_progress') return 'status-running'
    return 'status-queued'
  }

  const formatDuration = (seconds) => {
    if (!seconds) return '—'
    const mins = Math.floor(seconds / 60)
    const secs = seconds % 60
    return `${mins}m ${secs}s`
  }

  const formatTime = (isoString) => {
    if (!isoString) return '—'
    const date = new Date(isoString)
    const now = new Date()
    const diffMs = now - date
    const diffMins = Math.floor(diffMs / 60000)
    
    if (diffMins < 1) return 'just now'
    if (diffMins < 60) return `${diffMins}m ago`
    if (diffMins < 1440) return `${Math.floor(diffMins / 60)}h ago`
    return `${Math.floor(diffMins / 1440)}d ago`
  }

  return (
    <div className="pipelines-view-page">
      <div className="pipelines-header">
        <h1>🚀 CI/CD Pipelines</h1>
        <p className="pipelines-subtitle">
          GitHub Actions workflows and deployment status
        </p>
      </div>

      <div className="pipelines-grid">
        {pipelines.map(pipeline => (
          <div 
            key={pipeline.customer_id}
            className={`pipeline-card ${getStatusClass(pipeline.status, pipeline.conclusion)}`}
            onClick={() => fetchRuns(pipeline.customer_id, `${pipeline.customer_id}-dev-${pipeline.customer_id}-api`)}
          >
            <div className="pipeline-card-header">
              <div className="pipeline-status-icon">
                {getStatusIcon(pipeline.status, pipeline.conclusion)}
              </div>
              <div className="pipeline-info">
                <h3>{pipeline.customer_id.replace('-', ' ').toUpperCase()}</h3>
                <a 
                  href={`https://github.com/${pipeline.repo}`}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="pipeline-repo-link"
                  onClick={(e) => e.stopPropagation()}
                >
                  📦 {pipeline.repo}
                </a>
              </div>
            </div>

            {pipeline.commit_sha && (
              <div className="pipeline-details">
                <div className="detail-row">
                  <span className="detail-label">Branch:</span>
                  <span className="detail-value detail-branch">{pipeline.branch}</span>
                </div>
                <div className="detail-row">
                  <span className="detail-label">Commit:</span>
                  <span className="detail-value detail-commit">{pipeline.commit_sha}</span>
                </div>
                <div className="detail-row">
                  <span className="detail-label">Updated:</span>
                  <span className="detail-value">{formatTime(pipeline.created_at)}</span>
                </div>
              </div>
            )}

            <div className="pipeline-footer">
              <button className="btn-view-runs">
                View Workflow Runs →
              </button>
            </div>
          </div>
        ))}
      </div>

      {selectedPipeline && runs && (
        <div className="pipeline-modal" onClick={() => {setSelectedPipeline(null); setRuns(null); setJobs(null);}}>
          <div className="modal-content" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <h2>Workflow Runs - {selectedPipeline.toUpperCase()}</h2>
              <button className="btn-close" onClick={() => {setSelectedPipeline(null); setRuns(null); setJobs(null);}}>×</button>
            </div>

            <div className="modal-body">
              {loadingRuns ? (
                <div className="loading-message">Loading workflow runs...</div>
              ) : (
                <div className="workflow-runs">
                  {runs.runs && runs.runs.length === 0 ? (
                    <div className="loading-message">No workflow runs found</div>
                  ) : (
                    runs.runs.map(run => (
                      <div key={run.id} className="workflow-run">
                        <div className="run-header">
                          <div className="run-info">
                            <div className="run-commit">{run.commit_sha}</div>
                            <div className="run-meta">
                              ⎇ {run.branch} · by {run.author} · {formatTime(run.created_at)}
                              {run.duration && ` · ${formatDuration(run.duration)}`}
                            </div>
                          </div>
                          <div className={`run-status ${getStatusClass(run.status, run.conclusion)}`}>
                            {run.status === 'completed' ? run.conclusion : run.status}
                          </div>
                        </div>

                        {jobs && jobs.runId === run.id && (
                          <div className="run-jobs">
                            {loadingJobs ? (
                              <div className="loading-message">Loading jobs...</div>
                            ) : (
                              <>
                                {jobs.jobs && jobs.jobs.map(job => (
                                  <div key={job.id} className="job-item">
                                    <div className="job-name">
                                      <span className={`job-status-icon ${getStatusClass(job.status, job.conclusion).replace('status-', '')}`}>
                                        {getStatusIcon(job.status, job.conclusion)}
                                      </span>
                                      {job.name}
                                    </div>
                                    {job.duration && (
                                      <div className="job-duration">{formatDuration(job.duration)}</div>
                                    )}
                                  </div>
                                ))}
                              </>
                            )}
                          </div>
                        )}
                      </div>
                    ))
                  )}
                </div>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

export default PipelinesView
