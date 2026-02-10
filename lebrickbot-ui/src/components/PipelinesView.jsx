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

            <div className="pipeline-card-footer">
              <button className="btn-view-runs">
                View Workflow Runs →
              </button>
            </div>
          </div>
        ))}
      </div>

      {selectedPipeline && runs && (
        <div className="pipeline-runs-modal" onClick={() => {setSelectedPipeline(null); setRuns(null); setJobs(null);}}>
          <div className="runs-modal-content" onClick={(e) => e.stopPropagation()}>
            <div className="runs-modal-header">
              <h2>Workflow Runs - {selectedPipeline.toUpperCase()}</h2>
              <button className="modal-close" onClick={() => {setSelectedPipeline(null); setRuns(null); setJobs(null);}}>×</button>
            </div>

            {loadingRuns ? (
              <div className="modal-loading">Loading workflow runs...</div>
            ) : (
              <div className="runs-list">
                {runs.runs && runs.runs.length === 0 ? (
                  <div className="no-runs">No workflow runs found</div>
                ) : (
                  runs.runs.map(run => (
                    <div key={run.id} className="run-item">
                      <div className={`run-header ${getStatusClass(run.status, run.conclusion)}`}>
                        <div className="run-status-icon">
                          {getStatusIcon(run.status, run.conclusion)}
                        </div>
                        <div className="run-info-details">
                          <div className="run-name">{run.name}</div>
                          <div className="run-meta">
                            <span className="run-branch">⎇ {run.branch}</span>
                            <span className="run-commit">{run.commit_sha}</span>
                            <span className="run-author">{run.author}</span>
                            <span className="run-time">{formatTime(run.created_at)}</span>
                          </div>
                        </div>
                        <div className="run-actions">
                          {run.duration && (
                            <span className="run-duration">{formatDuration(run.duration)}</span>
                          )}
                          <button 
                            className="btn-view-jobs"
                            onClick={() => fetchJobsForRun(runs.deployment_id, run.id)}
                          >
                            View Jobs
                          </button>
                          <a 
                            href={run.url}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="btn-github"
                          >
                            GitHub →
                          </a>
                        </div>
                      </div>

                      {jobs && jobs.runId === run.id && (
                        <div className="run-jobs-section">
                          {loadingJobs ? (
                            <div className="jobs-loading">Loading jobs...</div>
                          ) : (
                            <div className="jobs-list-inline">
                              {jobs.jobs && jobs.jobs.map(job => (
                                <div key={job.id} className="job-card">
                                  <div className={`job-header ${getStatusClass(job.status, job.conclusion)}`}>
                                    <span className="job-status-icon">
                                      {getStatusIcon(job.status, job.conclusion)}
                                    </span>
                                    <span className="job-name">{job.name}</span>
                                  </div>
                                  <div className="job-steps">
                                    {job.steps && job.steps.map((step, idx) => (
                                      <div key={idx} className={`step-item ${getStatusClass(step.status, step.conclusion)}`}>
                                        <span className="step-number">{step.number}</span>
                                        <span className="step-icon">{getStatusIcon(step.status, step.conclusion)}</span>
                                        <span className="step-name">{step.name}</span>
                                      </div>
                                    ))}
                                  </div>
                                </div>
                              ))}
                            </div>
                          )}
                        </div>
                      )}

                      <div className="run-commit-message">{run.commit_message}</div>
                    </div>
                  ))
                )}
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  )
}

export default PipelinesView
