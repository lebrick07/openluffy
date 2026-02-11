import { useState, useEffect, useCallback } from 'react'
import './PipelineView.css'

function PipelineView({ deploymentId }) {
  const [pipeline, setPipeline] = useState(null)
  const [loading, setLoading] = useState(true)
  const [selectedRun, setSelectedRun] = useState(null)
  const [jobs, setJobs] = useState(null)
  const [loadingJobs, setLoadingJobs] = useState(false)

  const fetchPipeline = useCallback(async () => {
    setLoading(true)
    try {
      const response = await fetch(`/api/deployments/${deploymentId}/pipeline`)
      if (!response.ok) throw new Error('Failed to fetch')
      const data = await response.json()
      setPipeline(data)
    } catch (error) {
      console.error('Error fetching pipeline:', error)
    } finally {
      setLoading(false)
    }
  }, [deploymentId])

  useEffect(() => {
    if (deploymentId) {
      fetchPipeline()
      const interval = setInterval(fetchPipeline, 30000) // Refresh every 30s
      return () => clearInterval(interval)
    }
  }, [deploymentId, fetchPipeline])

  const fetchJobs = async (runId) => {
    setLoadingJobs(true)
    setSelectedRun(runId)
    try {
      const response = await fetch(`/api/deployments/${deploymentId}/pipeline/${runId}/jobs`)
      if (!response.ok) throw new Error('Failed to fetch')
      const data = await response.json()
      setJobs(data)
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

  if (loading) {
    return <div className="pipeline-loading">Loading pipeline data...</div>
  }

  if (!pipeline || pipeline.error) {
    return (
      <div className="pipeline-error">
        <p>⚠️ {pipeline?.error || 'Failed to load pipeline'}</p>
        {pipeline?.repo && (
          <a 
            href={`https://github.com/${pipeline.repo}/actions`}
            target="_blank"
            rel="noopener noreferrer"
            className="link-github-actions"
          >
            View on GitHub →
          </a>
        )}
      </div>
    )
  }

  return (
    <div className="pipeline-view">
      <div className="pipeline-header">
        <div className="pipeline-info">
          <h4>CI/CD Pipeline</h4>
          <p className="pipeline-repo">
            <span className="repo-icon">📦</span>
            <a 
              href={`https://github.com/${pipeline.repo}`}
              target="_blank"
              rel="noopener noreferrer"
            >
              {pipeline.repo}
            </a>
          </p>
        </div>
        <div className="pipeline-stats">
          <span className="stat">
            <strong>{pipeline.total}</strong> runs
          </span>
        </div>
      </div>

      <div className="pipeline-runs">
        {pipeline.runs && pipeline.runs.length === 0 ? (
          <div className="no-runs">No pipeline runs found</div>
        ) : (
          pipeline.runs.map((run) => (
            <div key={run.id} className="pipeline-run">
              <div 
                className={`run-header ${getStatusClass(run.status, run.conclusion)}`}
                onClick={() => fetchJobs(run.id)}
              >
                <div className="run-status">
                  <span className="status-icon">
                    {getStatusIcon(run.status, run.conclusion)}
                  </span>
                  <div className="run-info">
                    <div className="run-name">{run.name}</div>
                    <div className="run-meta">
                      <span className="run-branch">
                        <span className="branch-icon">⎇</span>
                        {run.branch}
                      </span>
                      <span className="run-commit">{run.commit_sha}</span>
                      <span className="run-author">{run.author}</span>
                      <span className="run-time">{formatTime(run.created_at)}</span>
                    </div>
                  </div>
                </div>
                <div className="run-actions">
                  {run.duration && (
                    <span className="run-duration">{formatDuration(run.duration)}</span>
                  )}
                  <a 
                    href={run.url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="run-link"
                    onClick={(e) => e.stopPropagation()}
                  >
                    View on GitHub →
                  </a>
                </div>
              </div>

              {selectedRun === run.id && (
                <div className="run-jobs">
                  {loadingJobs ? (
                    <div className="jobs-loading">Loading jobs...</div>
                  ) : jobs && jobs.jobs ? (
                    <div className="jobs-list">
                      {jobs.jobs.map((job) => (
                        <div key={job.id} className="job-item">
                          <div className={`job-header ${getStatusClass(job.status, job.conclusion)}`}>
                            <span className="status-icon">
                              {getStatusIcon(job.status, job.conclusion)}
                            </span>
                            <span className="job-name">{job.name}</span>
                            <a 
                              href={job.url}
                              target="_blank"
                              rel="noopener noreferrer"
                              className="job-link"
                            >
                              →
                            </a>
                          </div>
                          <div className="job-steps">
                            {job.steps.map((step, idx) => (
                              <div 
                                key={idx} 
                                className={`step-item ${getStatusClass(step.status, step.conclusion)}`}
                              >
                                <span className="step-number">{step.number}</span>
                                <span className="step-icon">
                                  {getStatusIcon(step.status, step.conclusion)}
                                </span>
                                <span className="step-name">{step.name}</span>
                              </div>
                            ))}
                          </div>
                        </div>
                      ))}
                    </div>
                  ) : (
                    <div className="jobs-error">Failed to load jobs</div>
                  )}
                </div>
              )}

              <div className="run-commit-msg">{run.commit_message}</div>
            </div>
          ))
        )}
      </div>
    </div>
  )
}

export default PipelineView
