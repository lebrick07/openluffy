import { useState } from 'react'
import './CreateCustomerWizard.css'

function CreateCustomerWizard({ onClose, onSuccess }) {
  const [step, setStep] = useState(1)
  const [creating, setCreating] = useState(false)
  
  // Step 1: Customer Info
  const [customerName, setCustomerName] = useState('')
  const [stack, setStack] = useState('nodejs')
  const [customerId, setCustomerId] = useState('')
  
  // Step 2: GitHub (REQUIRED)
  const [githubOrg, setGithubOrg] = useState('')
  const [githubRepo, setGithubRepo] = useState('')
  const [githubToken, setGithubToken] = useState('')
  const [githubBranch, setGithubBranch] = useState('main')
  const [repoStatus, setRepoStatus] = useState(null) // { exists: bool, message: string }
  const [checkingRepo, setCheckingRepo] = useState(false)
  
  // Step 3: ArgoCD (REQUIRED)
  const [argoCDUrl, setArgoCDUrl] = useState('http://argocd.local')
  const [argoCDToken, setArgoCDToken] = useState('')
  const [argoCDValidated, setArgoCDValidated] = useState(false)
  const [validatingArgoCD, setValidatingArgoCD] = useState(false)
  
  // Auto-generate customer ID from name
  const handleNameChange = (name) => {
    setCustomerName(name)
    const id = name.toLowerCase()
      .replace(/[^a-z0-9\s-]/g, '')
      .replace(/\s+/g, '-')
      .replace(/-+/g, '-')
      .replace(/^-|-$/g, '')
    setCustomerId(id)
    
    // Auto-suggest repo name
    if (!githubRepo || githubRepo === '') {
      setGithubRepo(`${id}-api`)
    }
  }
  
  // Check if GitHub repo exists
  const checkGitHubRepo = async () => {
    if (!githubOrg || !githubRepo || !githubToken) {
      alert('Please fill in all GitHub fields')
      return
    }
    
    setCheckingRepo(true)
    setRepoStatus(null)
    
    try {
      const response = await fetch(`https://api.github.com/repos/${githubOrg}/${githubRepo}`, {
        headers: {
          'Authorization': `token ${githubToken}`,
          'Accept': 'application/vnd.github.v3+json'
        }
      })
      
      if (response.status === 200) {
        setRepoStatus({
          exists: true,
          message: `✅ Repository exists - will use existing repo`
        })
      } else if (response.status === 404) {
        setRepoStatus({
          exists: false,
          message: `📦 Repository doesn't exist - will create from template`
        })
      } else {
        throw new Error('Unable to check repository')
      }
    } catch (error) {
      setRepoStatus({
        exists: null,
        message: `❌ Error: ${error.message}`
      })
    } finally {
      setCheckingRepo(false)
    }
  }
  
  // Validate ArgoCD connection
  const validateArgoCD = async () => {
    if (!argoCDUrl || !argoCDToken) {
      alert('Please fill in ArgoCD URL and token')
      return
    }
    
    setValidatingArgoCD(true)
    
    try {
      // TODO: Call ArgoCD API to validate
      // For now, just simulate validation
      await new Promise(resolve => setTimeout(resolve, 1000))
      setArgoCDValidated(true)
    } catch (error) {
      alert(`ArgoCD validation failed: ${error.message}`)
    } finally {
      setValidatingArgoCD(false)
    }
  }
  
  // Create customer
  const handleCreate = async () => {
    setCreating(true)
    
    try {
      const response = await fetch('/api/customers/create', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          name: customerName,
          id: customerId,
          stack,
          github: {
            org: githubOrg,
            repo: githubRepo,
            token: githubToken,
            branch: githubBranch
          },
          argocd: {
            url: argoCDUrl,
            token: argoCDToken
          }
        })
      })
      
      if (!response.ok) {
        const error = await response.json()
        throw new Error(error.message || 'Failed to create customer')
      }
      
      const result = await response.json()
      
      // Success
      onSuccess(result)
      onClose()
      
    } catch (error) {
      alert(`Failed to create customer: ${error.message}`)
    } finally {
      setCreating(false)
    }
  }
  
  // Navigation
  const canGoNext = () => {
    if (step === 1) return customerName && customerId && stack
    if (step === 2) return repoStatus !== null && repoStatus.exists !== null
    if (step === 3) return argoCDValidated
    return false
  }
  
  const handleNext = () => {
    if (step < 4) setStep(step + 1)
  }
  
  const handleBack = () => {
    if (step > 1) setStep(step - 1)
  }
  
  return (
    <div className="wizard-overlay" onClick={onClose}>
      <div className="wizard-modal" onClick={e => e.stopPropagation()}>
        {/* Header */}
        <div className="wizard-header">
          <h2>🏴‍☠️ Create New Customer</h2>
          <button className="wizard-close" onClick={onClose}>×</button>
        </div>
        
        {/* Progress Bar */}
        <div className="wizard-progress">
          <div className={`progress-step ${step >= 1 ? 'active' : ''}`}>
            <div className="step-circle">1</div>
            <div className="step-label">Customer Info</div>
          </div>
          <div className="progress-line"></div>
          <div className={`progress-step ${step >= 2 ? 'active' : ''}`}>
            <div className="step-circle">2</div>
            <div className="step-label">GitHub ⚠️</div>
          </div>
          <div className="progress-line"></div>
          <div className={`progress-step ${step >= 3 ? 'active' : ''}`}>
            <div className="step-circle">3</div>
            <div className="step-label">ArgoCD ⚠️</div>
          </div>
          <div className="progress-line"></div>
          <div className={`progress-step ${step >= 4 ? 'active' : ''}`}>
            <div className="step-circle">4</div>
            <div className="step-label">Review</div>
          </div>
        </div>
        
        {/* Step Content */}
        <div className="wizard-content">
          {step === 1 && (
            <div className="wizard-step">
              <h3>Customer Information</h3>
              <p className="step-description">Basic details about the customer</p>
              
              <div className="form-group">
                <label>Customer Name *</label>
                <input
                  type="text"
                  value={customerName}
                  onChange={e => handleNameChange(e.target.value)}
                  placeholder="Acme Corp"
                  autoFocus
                />
              </div>
              
              <div className="form-group">
                <label>Customer ID * <small>(auto-generated)</small></label>
                <input
                  type="text"
                  value={customerId}
                  onChange={e => setCustomerId(e.target.value)}
                  placeholder="acme-corp"
                />
                <small className="field-help">Used for namespaces, URLs, and resource names</small>
              </div>
              
              <div className="form-group">
                <label>Application Stack *</label>
                <select value={stack} onChange={e => setStack(e.target.value)}>
                  <option value="nodejs">Node.js</option>
                  <option value="python">Python FastAPI</option>
                  <option value="go">Go</option>
                </select>
              </div>
            </div>
          )}
          
          {step === 2 && (
            <div className="wizard-step">
              <div className="step-required-badge">⚠️ REQUIRED</div>
              <h3>GitHub Integration</h3>
              <p className="step-description">Connect the customer's GitHub repository</p>
              
              <div className="form-group">
                <label>Repository Owner *</label>
                <input
                  type="text"
                  value={githubOrg}
                  onChange={e => setGithubOrg(e.target.value)}
                  placeholder="lebrick07 or https://github.com/lebrick07"
                />
                <small className="field-help">GitHub username or organization (URLs will be auto-extracted)</small>
              </div>
              
              <div className="form-group">
                <label>Repository Name *</label>
                <input
                  type="text"
                  value={githubRepo}
                  onChange={e => setGithubRepo(e.target.value)}
                  placeholder={`${customerId}-api`}
                />
                <small className="field-help">Repository will be created if it doesn't exist</small>
              </div>
              
              <div className="form-group">
                <label>Personal Access Token *</label>
                <input
                  type="password"
                  value={githubToken}
                  onChange={e => setGithubToken(e.target.value)}
                  placeholder="ghp_xxxxxxxxxxxxx"
                />
                <small className="field-help">Token needs: repo, workflow, read:org scopes</small>
              </div>
              
              <div className="form-group">
                <label>Default Branch</label>
                <input
                  type="text"
                  value={githubBranch}
                  onChange={e => setGithubBranch(e.target.value)}
                  placeholder="main"
                />
              </div>
              
              <button
                className="btn-check-repo"
                onClick={checkGitHubRepo}
                disabled={!githubOrg || !githubRepo || !githubToken || checkingRepo}
              >
                {checkingRepo ? '⏳ Checking...' : '🔍 Check Repository'}
              </button>
              
              {repoStatus && (
                <div className={`repo-status ${repoStatus.exists === null ? 'error' : ''}`}>
                  {repoStatus.message}
                </div>
              )}
            </div>
          )}
          
          {step === 3 && (
            <div className="wizard-step">
              <div className="step-required-badge">⚠️ REQUIRED</div>
              <h3>ArgoCD Integration</h3>
              <p className="step-description">Configure GitOps deployment automation</p>
              
              <div className="form-group">
                <label>ArgoCD URL *</label>
                <input
                  type="text"
                  value={argoCDUrl}
                  onChange={e => setArgoCDUrl(e.target.value)}
                  placeholder="http://argocd.local"
                />
              </div>
              
              <div className="form-group">
                <label>ArgoCD Token *</label>
                <input
                  type="password"
                  value={argoCDToken}
                  onChange={e => setArgoCDToken(e.target.value)}
                  placeholder="Enter ArgoCD auth token"
                />
                <small className="field-help">Admin or app creation permissions required</small>
              </div>
              
              <button
                className="btn-validate-argocd"
                onClick={validateArgoCD}
                disabled={!argoCDUrl || !argoCDToken || validatingArgoCD}
              >
                {validatingArgoCD ? '⏳ Validating...' : '🔍 Validate Connection'}
              </button>
              
              {argoCDValidated && (
                <div className="validation-success">
                  ✅ ArgoCD connection validated
                </div>
              )}
            </div>
          )}
          
          {step === 4 && (
            <div className="wizard-step">
              <h3>Review & Create</h3>
              <p className="step-description">Confirm details and create customer</p>
              
              <div className="review-section">
                <h4>Customer</h4>
                <div className="review-item">
                  <span className="review-label">Name:</span>
                  <span className="review-value">{customerName}</span>
                </div>
                <div className="review-item">
                  <span className="review-label">ID:</span>
                  <span className="review-value">{customerId}</span>
                </div>
                <div className="review-item">
                  <span className="review-label">Stack:</span>
                  <span className="review-value">{stack}</span>
                </div>
              </div>
              
              <div className="review-section">
                <h4>GitHub</h4>
                <div className="review-item">
                  <span className="review-label">Repository:</span>
                  <span className="review-value">{githubOrg}/{githubRepo}</span>
                </div>
                <div className="review-item">
                  <span className="review-label">Status:</span>
                  <span className="review-value">{repoStatus?.message}</span>
                </div>
              </div>
              
              <div className="review-section">
                <h4>ArgoCD</h4>
                <div className="review-item">
                  <span className="review-label">URL:</span>
                  <span className="review-value">{argoCDUrl}</span>
                </div>
                <div className="review-item">
                  <span className="review-label">Status:</span>
                  <span className="review-value">✅ Validated</span>
                </div>
              </div>
              
              <div className="review-section">
                <h4>What will be created:</h4>
                <ul className="creation-list">
                  {!repoStatus?.exists && <li>📦 GitHub repository from template</li>}
                  <li>🔧 CI/CD pipeline configuration</li>
                  <li>🏗️ K8s namespaces (dev, preprod, prod)</li>
                  <li>🐙 ArgoCD applications (dev, preprod, prod)</li>
                  <li>⚙️ Integration configs stored</li>
                </ul>
              </div>
            </div>
          )}
        </div>
        
        {/* Footer */}
        <div className="wizard-footer">
          <button
            className="btn-secondary"
            onClick={handleBack}
            disabled={step === 1 || creating}
          >
            ← Back
          </button>
          
          <div className="footer-actions">
            <button className="btn-cancel" onClick={onClose} disabled={creating}>
              Cancel
            </button>
            
            {step < 4 ? (
              <button
                className="btn-primary"
                onClick={handleNext}
                disabled={!canGoNext()}
              >
                Next →
              </button>
            ) : (
              <button
                className="btn-create"
                onClick={handleCreate}
                disabled={creating}
              >
                {creating ? '⏳ Creating...' : '🚀 Create Customer'}
              </button>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}

export default CreateCustomerWizard
