import { useState } from 'react'
import './CreateCustomerModal.css'

function CreateCustomerModal({ onClose, onCustomerCreated }) {
  const [step, setStep] = useState(1)
  const [creating, setCreating] = useState(false)
  const [formData, setFormData] = useState({
    name: '',
    icon: '🏢',
    deploymentModel: 'monolith',
    runtime: 'nodejs',
    cicdStyle: 'github-actions',
    environments: ['dev', 'preprod', 'prod'],
    approvalStrategy: 'gated',
    observability: ['logs', 'metrics']
  })

  const handleChange = (field, value) => {
    setFormData(prev => ({ ...prev, [field]: value }))
  }

  const toggleEnvironment = (env) => {
    setFormData(prev => ({
      ...prev,
      environments: prev.environments.includes(env)
        ? prev.environments.filter(e => e !== env)
        : [...prev.environments, env]
    }))
  }

  const toggleObservability = (tool) => {
    setFormData(prev => ({
      ...prev,
      observability: prev.observability.includes(tool)
        ? prev.observability.filter(t => t !== tool)
        : [...prev.observability, tool]
    }))
  }

  const handleSubmit = async () => {
    setCreating(true)
    
    try {
      const response = await fetch('/customers/create', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(formData)
      })
      
      if (!response.ok) throw new Error('Failed to create customer')
      
      const data = await response.json()
      onCustomerCreated(data.customer)
      onClose()
    } catch (error) {
      console.error('Error creating customer:', error)
      alert('Failed to create customer. Check logs for details.')
    } finally {
      setCreating(false)
    }
  }

  const renderStep1 = () => (
    <div className="wizard-step">
      <h3>Basic Information</h3>
      
      <div className="form-group">
        <label>Customer Name *</label>
        <input
          type="text"
          value={formData.name}
          onChange={(e) => handleChange('name', e.target.value)}
          placeholder="e.g., Acme Corp, TechStart, WidgetCo"
          className="input-full"
          autoFocus
        />
      </div>

      <div className="form-group">
        <label>Icon</label>
        <div className="icon-picker">
          {['🏢', '🚀', '⚡', '🔥', '💎', '🌟', '🎯', '🛡️'].map(icon => (
            <button
              key={icon}
              className={`icon-option ${formData.icon === icon ? 'selected' : ''}`}
              onClick={() => handleChange('icon', icon)}
            >
              {icon}
            </button>
          ))}
        </div>
      </div>

      <div className="form-group">
        <label>Deployment Model *</label>
        <div className="radio-group">
          <label>
            <input
              type="radio"
              name="deployment"
              value="monolith"
              checked={formData.deploymentModel === 'monolith'}
              onChange={(e) => handleChange('deploymentModel', e.target.value)}
            />
            <span>Monolith - Single application</span>
          </label>
          <label>
            <input
              type="radio"
              name="deployment"
              value="microservices"
              checked={formData.deploymentModel === 'microservices'}
              onChange={(e) => handleChange('deploymentModel', e.target.value)}
            />
            <span>Microservices - Multiple services</span>
          </label>
          <label>
            <input
              type="radio"
              name="deployment"
              value="serverless"
              checked={formData.deploymentModel === 'serverless'}
              onChange={(e) => handleChange('deploymentModel', e.target.value)}
            />
            <span>Serverless - Functions & managed services</span>
          </label>
        </div>
      </div>

      <div className="form-group">
        <label>Primary Runtime *</label>
        <select
          value={formData.runtime}
          onChange={(e) => handleChange('runtime', e.target.value)}
          className="input-full"
        >
          <option value="nodejs">Node.js</option>
          <option value="python">Python</option>
          <option value="go">Go</option>
          <option value="java">Java / Spring</option>
          <option value="dotnet">.NET / C#</option>
          <option value="ruby">Ruby</option>
          <option value="php">PHP</option>
        </select>
      </div>
    </div>
  )

  const renderStep2 = () => (
    <div className="wizard-step">
      <h3>CI/CD & Environments</h3>

      <div className="form-group">
        <label>CI/CD Platform *</label>
        <select
          value={formData.cicdStyle}
          onChange={(e) => handleChange('cicdStyle', e.target.value)}
          className="input-full"
        >
          <option value="github-actions">GitHub Actions + ArgoCD</option>
          <option value="gitlab-ci">GitLab CI/CD</option>
          <option value="jenkins">Jenkins</option>
          <option value="circleci">CircleCI</option>
          <option value="azure-devops">Azure DevOps</option>
        </select>
      </div>

      <div className="form-group">
        <label>Environments *</label>
        <div className="checkbox-group">
          <label>
            <input
              type="checkbox"
              checked={formData.environments.includes('dev')}
              onChange={() => toggleEnvironment('dev')}
            />
            <span>DEV - Development</span>
          </label>
          <label>
            <input
              type="checkbox"
              checked={formData.environments.includes('staging')}
              onChange={() => toggleEnvironment('staging')}
            />
            <span>STAGING - Pre-production testing</span>
          </label>
          <label>
            <input
              type="checkbox"
              checked={formData.environments.includes('preprod')}
              onChange={() => toggleEnvironment('preprod')}
            />
            <span>PREPROD - Final validation</span>
          </label>
          <label>
            <input
              type="checkbox"
              checked={formData.environments.includes('prod')}
              onChange={() => toggleEnvironment('prod')}
            />
            <span>PROD - Production</span>
          </label>
        </div>
      </div>

      <div className="form-group">
        <label>Approval Strategy *</label>
        <div className="radio-group">
          <label>
            <input
              type="radio"
              name="approval"
              value="auto"
              checked={formData.approvalStrategy === 'auto'}
              onChange={(e) => handleChange('approvalStrategy', e.target.value)}
            />
            <span>Auto - Promote to prod automatically</span>
          </label>
          <label>
            <input
              type="radio"
              name="approval"
              value="gated"
              checked={formData.approvalStrategy === 'gated'}
              onChange={(e) => handleChange('approvalStrategy', e.target.value)}
            />
            <span>Gated - Require approval for prod</span>
          </label>
          <label>
            <input
              type="radio"
              name="approval"
              value="manual"
              checked={formData.approvalStrategy === 'manual'}
              onChange={(e) => handleChange('approvalStrategy', e.target.value)}
            />
            <span>Manual - All promotions require approval</span>
          </label>
        </div>
      </div>
    </div>
  )

  const renderStep3 = () => (
    <div className="wizard-step">
      <h3>Observability & Monitoring</h3>

      <div className="form-group">
        <label>Enable Tools</label>
        <div className="checkbox-group">
          <label>
            <input
              type="checkbox"
              checked={formData.observability.includes('logs')}
              onChange={() => toggleObservability('logs')}
            />
            <span>📋 Log Aggregation (Loki / ELK)</span>
          </label>
          <label>
            <input
              type="checkbox"
              checked={formData.observability.includes('metrics')}
              onChange={() => toggleObservability('metrics')}
            />
            <span>📊 Metrics (Prometheus / Grafana)</span>
          </label>
          <label>
            <input
              type="checkbox"
              checked={formData.observability.includes('traces')}
              onChange={() => toggleObservability('traces')}
            />
            <span>🔍 Distributed Tracing (Jaeger / Tempo)</span>
          </label>
          <label>
            <input
              type="checkbox"
              checked={formData.observability.includes('alerts')}
              onChange={() => toggleObservability('alerts')}
            />
            <span>🚨 Alerting (AlertManager / PagerDuty)</span>
          </label>
        </div>
      </div>

      <div className="form-group">
        <h4>What Happens Next?</h4>
        <div className="ai-preview">
          <p>🤖 <strong>AI will generate:</strong></p>
          <ul>
            <li>✅ GitHub repository with {formData.runtime} starter template</li>
            <li>✅ Multi-environment CI/CD pipeline ({formData.cicdStyle})</li>
            <li>✅ Kubernetes manifests for {formData.environments.join(', ')}</li>
            <li>✅ ArgoCD applications for GitOps deployment</li>
            <li>✅ Ingresses with automatic DNS (*.local)</li>
            {formData.approvalStrategy === 'gated' && (
              <li>✅ Production approval workflow</li>
            )}
            {formData.observability.length > 0 && (
              <li>✅ Observability stack: {formData.observability.join(', ')}</li>
            )}
          </ul>
          <p className="ai-note">
            Estimated setup time: <strong>~2-3 minutes</strong>
          </p>
        </div>
      </div>
    </div>
  )

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal-content" onClick={(e) => e.stopPropagation()}>
        <div className="modal-header">
          <h2>🏴‍☠️ Create New Customer</h2>
          <button className="modal-close" onClick={onClose}>×</button>
        </div>

        <div className="wizard-progress">
          <div className={`progress-step ${step >= 1 ? 'active' : ''}`}>1. Basics</div>
          <div className={`progress-step ${step >= 2 ? 'active' : ''}`}>2. CI/CD</div>
          <div className={`progress-step ${step >= 3 ? 'active' : ''}`}>3. Observability</div>
        </div>

        <div className="modal-body">
          {step === 1 && renderStep1()}
          {step === 2 && renderStep2()}
          {step === 3 && renderStep3()}
        </div>

        <div className="modal-footer">
          {step > 1 && (
            <button className="btn-secondary" onClick={() => setStep(step - 1)}>
              ← Back
            </button>
          )}
          
          <div className="spacer"></div>

          {step < 3 ? (
            <button 
              className="btn-primary"
              onClick={() => setStep(step + 1)}
              disabled={!formData.name}
            >
              Next →
            </button>
          ) : (
            <button 
              className="btn-primary"
              onClick={handleSubmit}
              disabled={creating || !formData.name}
            >
              {creating ? '🤖 AI Generating...' : '🚀 Create Customer'}
            </button>
          )}
        </div>
      </div>
    </div>
  )
}

export default CreateCustomerModal
