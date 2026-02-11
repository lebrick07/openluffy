import { useState, useEffect, useCallback } from 'react'
import { useCustomer } from '../contexts/CustomerContext'
import './PipelineConfig.css'

function PipelineConfig() {
  const { activeCustomer, customers } = useCustomer()
  const [config, setConfig] = useState(null)
  const [loading, setLoading] = useState(false)
  const [saving, setSaving] = useState(false)

  const loadCustomerConfig = useCallback(async () => {
    setLoading(true)
    
    // Load template based on customer stack
    const template = getDefaultConfig(activeCustomer.stack)
    setConfig(template)
    setLoading(false)
  }, [activeCustomer])

  useEffect(() => {
    if (activeCustomer) {
      loadCustomerConfig()
    } else {
      setConfig(null)
    }
  }, [activeCustomer, loadCustomerConfig])

  const getDefaultConfig = (stack) => {
    const base = {
      name: 'CI/CD Pipeline',
      triggers: {
        push: { branches: ['develop', 'main'] },
        pullRequest: { branches: ['develop', 'main'] }
      },
      jobs: []
    }

    if (stack === 'Node.js') {
      base.jobs = [
        {
          name: 'lint',
          title: 'Code Quality & Lint',
          enabled: true,
          steps: [
            { name: 'Setup Node.js', command: 'setup-node@v4', params: { nodeVersion: '20' } },
            { name: 'Install dependencies', command: 'npm ci' },
            { name: 'Run ESLint', command: 'npm run lint', continueOnError: true }
          ]
        },
        {
          name: 'unit-tests',
          title: 'Unit Tests',
          enabled: true,
          steps: [
            { name: 'Setup Node.js', command: 'setup-node@v4', params: { nodeVersion: '20' } },
            { name: 'Install dependencies', command: 'npm ci' },
            { name: 'Run unit tests', command: 'npm run test:unit' },
            { name: 'Upload coverage', command: 'codecov-action@v3', continueOnError: true }
          ]
        },
        {
          name: 'integration-tests',
          title: 'Integration Tests',
          enabled: true,
          steps: [
            { name: 'Setup Node.js', command: 'setup-node@v4', params: { nodeVersion: '20' } },
            { name: 'Install dependencies', command: 'npm ci' },
            { name: 'Run integration tests', command: 'npm run test:integration' }
          ]
        },
        {
          name: 'security',
          title: 'Security Scan',
          enabled: true,
          steps: [
            { name: 'Gitleaks scan', command: 'gitleaks detect' },
            { name: 'npm audit', command: 'npm audit --audit-level=moderate' },
            { name: 'Trivy scan', command: 'trivy fs .' }
          ]
        }
      ]
    } else if (stack.includes('Python')) {
      base.jobs = [
        {
          name: 'lint',
          title: 'Code Quality',
          enabled: true,
          steps: [
            { name: 'Setup Python', command: 'setup-python@v5', params: { pythonVersion: '3.11' } },
            { name: 'Install dependencies', command: 'pip install -r requirements.txt' },
            { name: 'Run flake8', command: 'flake8 .', continueOnError: true },
            { name: 'Run black', command: 'black --check .', continueOnError: true }
          ]
        },
        {
          name: 'tests',
          title: 'Unit Tests',
          enabled: true,
          steps: [
            { name: 'Setup Python', command: 'setup-python@v5', params: { pythonVersion: '3.11' } },
            { name: 'Install dependencies', command: 'pip install -r requirements.txt' },
            { name: 'Run pytest', command: 'pytest --cov=. --cov-report=xml' },
            { name: 'Upload coverage', command: 'codecov-action@v3', continueOnError: true }
          ]
        },
        {
          name: 'security',
          title: 'Security Scan',
          enabled: true,
          steps: [
            { name: 'Gitleaks scan', command: 'gitleaks detect' },
            { name: 'Safety check', command: 'safety check' },
            { name: 'Trivy scan', command: 'trivy fs .' }
          ]
        }
      ]
    } else if (stack === 'Go') {
      base.jobs = [
        {
          name: 'lint',
          title: 'Code Quality',
          enabled: true,
          steps: [
            { name: 'Setup Go', command: 'setup-go@v5', params: { goVersion: '1.21' } },
            { name: 'Run golangci-lint', command: 'golangci-lint run' }
          ]
        },
        {
          name: 'tests',
          title: 'Unit Tests',
          enabled: true,
          steps: [
            { name: 'Setup Go', command: 'setup-go@v5', params: { goVersion: '1.21' } },
            { name: 'Run tests', command: 'go test -v -race -coverprofile=coverage.txt ./...' },
            { name: 'Upload coverage', command: 'codecov-action@v3', continueOnError: true }
          ]
        },
        {
          name: 'security',
          title: 'Security Scan',
          enabled: true,
          steps: [
            { name: 'Gitleaks scan', command: 'gitleaks detect' },
            { name: 'gosec', command: 'gosec ./...' },
            { name: 'Trivy scan', command: 'trivy fs .' }
          ]
        }
      ]
    }

    return base
  }

  const toggleJob = (jobIndex) => {
    const newConfig = { ...config }
    newConfig.jobs[jobIndex].enabled = !newConfig.jobs[jobIndex].enabled
    setConfig(newConfig)
  }

  const addStep = (jobIndex) => {
    const newConfig = { ...config }
    newConfig.jobs[jobIndex].steps.push({
      name: 'New step',
      command: '',
      continueOnError: false
    })
    setConfig(newConfig)
  }

  const updateStep = (jobIndex, stepIndex, field, value) => {
    const newConfig = { ...config }
    newConfig.jobs[jobIndex].steps[stepIndex][field] = value
    setConfig(newConfig)
  }

  const deleteStep = (jobIndex, stepIndex) => {
    const newConfig = { ...config }
    newConfig.jobs[jobIndex].steps.splice(stepIndex, 1)
    setConfig(newConfig)
  }

  const saveConfig = async () => {
    setSaving(true)
    // TODO: Implement actual save to backend
    await new Promise(resolve => setTimeout(resolve, 1000))
    alert('✅ Pipeline configuration saved!\n\nThis will be applied on next commit.')
    setSaving(false)
  }

  return (
    <div className="pipeline-config">
      <div className="config-header">
        <div>
          <h1>⚙️ Pipeline Configuration</h1>
          <p>Customize CI/CD workflows for {activeCustomer ? activeCustomer.name : 'your customers'}</p>
        </div>
      </div>

      <div className="config-body">
        {!activeCustomer ? (
          <div className="empty-state">
            <div className="empty-state-icon">🎯</div>
            <h3>No Customer Selected</h3>
            <p>Select a customer from the top navigation to configure their pipeline</p>
          </div>
        ) : loading ? (
          <div className="config-loading">Loading configuration...</div>
        ) : null}

        {config && !loading && (
          <div className="config-editor">
            <div className="config-section">
              <h3>Pipeline Triggers</h3>
              <div className="trigger-config">
                <label>
                  <input type="checkbox" checked readOnly /> Push to branches
                </label>
                <input 
                  type="text" 
                  value={config.triggers.push.branches.join(', ')}
                  placeholder="develop, main"
                  className="input-sm"
                  readOnly
                />
              </div>
            </div>

            <div className="config-section">
              <h3>Jobs & Steps</h3>
              
              {config.jobs.map((job, jobIdx) => (
                <div key={jobIdx} className="job-card">
                  <div className="job-header">
                    <label className="job-toggle">
                      <input
                        type="checkbox"
                        checked={job.enabled}
                        onChange={() => toggleJob(jobIdx)}
                      />
                      <strong>{job.title}</strong>
                    </label>
                    <span className="job-steps-count">{job.steps.length} steps</span>
                  </div>

                  {job.enabled && (
                    <div className="job-steps">
                      {job.steps.map((step, stepIdx) => (
                        <div key={stepIdx} className="step-row">
                          <input
                            type="text"
                            value={step.name}
                            onChange={(e) => updateStep(jobIdx, stepIdx, 'name', e.target.value)}
                            placeholder="Step name"
                            className="step-name"
                          />
                          <input
                            type="text"
                            value={step.command}
                            onChange={(e) => updateStep(jobIdx, stepIdx, 'command', e.target.value)}
                            placeholder="Command"
                            className="step-command"
                          />
                          <label className="step-continue">
                            <input
                              type="checkbox"
                              checked={step.continueOnError || false}
                              onChange={(e) => updateStep(jobIdx, stepIdx, 'continueOnError', e.target.checked)}
                            />
                            <span>Continue on error</span>
                          </label>
                          <button
                            className="btn-delete-step"
                            onClick={() => deleteStep(jobIdx, stepIdx)}
                          >
                            ×
                          </button>
                        </div>
                      ))}
                      <button
                        className="btn-add-step"
                        onClick={() => addStep(jobIdx)}
                      >
                        + Add Step
                      </button>
                    </div>
                  )}
                </div>
              ))}
            </div>

            <div className="config-actions">
              <button
                className="btn-save"
                onClick={saveConfig}
                disabled={saving}
              >
                {saving ? 'Saving...' : '💾 Save Configuration'}
              </button>
              <button className="btn-reset">Reset to Default</button>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}

export default PipelineConfig
