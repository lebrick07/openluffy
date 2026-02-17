import { useState, useEffect } from 'react'
import { useCustomer } from '../contexts/CustomerContext'
import './IntegrationsDashboard.css'

// Available integrations that can be added
const availableIntegrations = [
  {
    id: 'prometheus',
    name: 'Prometheus',
    icon: '🔥',
    description: 'Metrics collection and monitoring',
    configFields: [
      { name: 'url', label: 'Prometheus URL', type: 'text', placeholder: 'http://prometheus:9090', required: true },
      { name: 'basicAuth', label: 'Basic Auth (optional)', type: 'text', placeholder: 'username:password' }
    ]
  },
  {
    id: 'grafana',
    name: 'Grafana',
    icon: '📊',
    description: 'Visualization and dashboards for metrics',
    configFields: [
      { name: 'url', label: 'Grafana URL', type: 'text', placeholder: 'http://grafana:3000', required: true },
      { name: 'apiKey', label: 'API Key', type: 'password', required: true }
    ]
  },
  {
    id: 'alertmanager',
    name: 'AlertManager',
    icon: '🚨',
    description: 'Alert routing and notifications',
    configFields: [
      { name: 'url', label: 'AlertManager URL', type: 'text', placeholder: 'http://alertmanager:9093', required: true }
    ]
  },
  {
    id: 'splunk',
    name: 'Splunk',
    icon: '🔍',
    description: 'Log aggregation and analysis',
    configFields: [
      { name: 'url', label: 'Splunk URL', type: 'text', placeholder: 'https://splunk.example.com:8089', required: true },
      { name: 'token', label: 'HEC Token', type: 'password', required: true },
      { name: 'index', label: 'Index Name', type: 'text', placeholder: 'main' }
    ]
  },
  {
    id: 'github',
    name: 'GitHub',
    icon: '⚙️',
    description: 'Connect this customer\'s GitHub repository',
    helpText: 'Configure the GitHub repo where this customer\'s application code lives. Used for CI/CD pipeline integration and automated deployments.',
    configFields: [
      { 
        name: 'org', 
        label: 'Repository Owner', 
        type: 'text', 
        placeholder: 'lebrick07 or https://github.com/lebrick07',
        required: true,
        helpText: 'GitHub username or organization (URLs will be auto-extracted)'
      },
      { 
        name: 'repo', 
        label: 'Repository Name', 
        type: 'text', 
        placeholder: 'acme-corp-api',
        required: true,
        helpText: 'Name of the repository (without owner)'
      },
      { 
        name: 'token', 
        label: 'Personal Access Token', 
        type: 'password', 
        required: true,
        helpText: 'GitHub token with repo, workflow, read:org scopes. Used to access this customer\'s repository for CI/CD automation.'
      },
      {
        name: 'branch',
        label: 'Default Branch',
        type: 'text',
        placeholder: 'main',
        required: false,
        helpText: 'Main branch to track (default: main)'
      }
    ],
    instructions: {
      title: 'How to Generate a GitHub Token',
      steps: [
        'Click "Generate Token" below to open GitHub',
        'Confirm the required scopes are selected: repo, workflow, read:org',
        'Set an expiration date (recommend 90 days or No expiration)',
        'Click "Generate token" at the bottom of the page',
        'Copy the token immediately (you won\'t be able to see it again)',
        'Paste the token in the "Personal Access Token" field above',
        'Fill in the Repository Owner and Repository Name',
        'Click "Test Connection" to verify access'
      ],
      tokenUrl: 'https://github.com/settings/tokens/new?scopes=repo,workflow,read:org&description=OpenLuffy+Customer+Integration'
    }
  },
  {
    id: 'ghcr',
    name: 'GitHub Container Registry',
    icon: '📦',
    description: 'GitHub Container Registry (ghcr.io) for Docker images',
    configFields: [
      { name: 'username', label: 'GitHub Username', type: 'text', required: true },
      { name: 'token', label: 'Personal Access Token', type: 'password', required: true }
    ]
  },
  {
    id: 'dockerhub',
    name: 'Docker Hub',
    icon: '🐋',
    description: 'Docker Hub registry for container images',
    configFields: [
      { name: 'username', label: 'Docker Hub Username', type: 'text', required: true },
      { name: 'password', label: 'Password or Access Token', type: 'password', required: true }
    ]
  },
  {
    id: 'ecr',
    name: 'Amazon ECR',
    icon: '📦',
    description: 'Amazon Elastic Container Registry',
    configFields: [
      { name: 'region', label: 'AWS Region', type: 'text', placeholder: 'us-east-1', required: true },
      { name: 'accessKeyId', label: 'Access Key ID', type: 'text', required: true },
      { name: 'secretAccessKey', label: 'Secret Access Key', type: 'password', required: true },
      { name: 'registryId', label: 'Registry ID (Account ID)', type: 'text', required: true }
    ]
  },
  {
    id: 'gcr',
    name: 'Google Container Registry',
    icon: '📦',
    description: 'Google Container Registry (GCR)',
    configFields: [
      { name: 'projectId', label: 'GCP Project ID', type: 'text', required: true },
      { name: 'serviceAccountKey', label: 'Service Account Key (JSON)', type: 'textarea', required: true }
    ]
  },
  {
    id: 'aws',
    name: 'AWS',
    icon: '☁️',
    description: 'Connect your AWS account for resource management',
    configFields: [
      { name: 'accessKeyId', label: 'Access Key ID', type: 'text', required: true },
      { name: 'secretAccessKey', label: 'Secret Access Key', type: 'password', required: true },
      { name: 'region', label: 'Default Region', type: 'text', placeholder: 'us-east-1' }
    ]
  },
  {
    id: 'terraform',
    name: 'Terraform Cloud',
    icon: '🏗️',
    description: 'Integrate Terraform Cloud workspaces',
    configFields: [
      { name: 'apiToken', label: 'API Token', type: 'password', required: true },
      { name: 'organization', label: 'Organization', type: 'text', required: true }
    ]
  },
  {
    id: 'jfrog',
    name: 'JFrog Artifactory',
    icon: '🐸',
    description: 'Connect to JFrog Artifactory for artifact management',
    configFields: [
      { name: 'url', label: 'Artifactory URL', type: 'text', placeholder: 'https://example.jfrog.io', required: true },
      { name: 'apiKey', label: 'API Key', type: 'password', required: true }
    ]
  },
  {
    id: 'datadog',
    name: 'DataDog',
    icon: '🐕',
    description: 'Integrate DataDog monitoring and alerts',
    configFields: [
      { name: 'apiKey', label: 'API Key', type: 'password', required: true },
      { name: 'appKey', label: 'Application Key', type: 'password', required: true }
    ]
  },
  {
    id: 'sonarqube',
    name: 'SonarQube',
    icon: '🔍',
    description: 'Connect SonarQube for code quality analysis',
    configFields: [
      { name: 'url', label: 'SonarQube URL', type: 'text', placeholder: 'https://sonarqube.example.com', required: true },
      { name: 'token', label: 'Access Token', type: 'password', required: true }
    ]
  },
  {
    id: 'vault',
    name: 'HashiCorp Vault',
    icon: '🔐',
    description: 'Integrate Vault for secrets management',
    configFields: [
      { name: 'url', label: 'Vault URL', type: 'text', placeholder: 'https://vault.example.com', required: true },
      { name: 'token', label: 'Vault Token', type: 'password', required: true }
    ]
  },
  {
    id: 'slack',
    name: 'Slack',
    icon: '💬',
    description: 'Send notifications to Slack channels',
    configFields: [
      { name: 'webhookUrl', label: 'Webhook URL', type: 'text', required: true },
      { name: 'channel', label: 'Default Channel', type: 'text', placeholder: '#alerts' }
    ]
  },
  {
    id: 'pagerduty',
    name: 'PagerDuty',
    icon: '🚨',
    description: 'Integrate PagerDuty for incident management',
    configFields: [
      { name: 'apiKey', label: 'API Key', type: 'password', required: true },
      { name: 'serviceKey', label: 'Service Key', type: 'password', required: true }
    ]
  }
]

function IntegrationsDashboard() {
  const { activeCustomer } = useCustomer()
  const [connectedIntegrations, setConnectedIntegrations] = useState([])
  const [showAddModal, setShowAddModal] = useState(false)
  const [selectedToAdd, setSelectedToAdd] = useState(null)
  const [configData, setConfigData] = useState({})
  const [loading, setLoading] = useState(true)
  const [testingConnection, setTestingConnection] = useState(false)
  const [testResult, setTestResult] = useState(null)

  // Fetch real connected integrations (per customer)
  useEffect(() => {
    if (activeCustomer) {
      fetchConnectedIntegrations()
    } else {
      setConnectedIntegrations([])
      setLoading(false)
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [activeCustomer])

  const fetchConnectedIntegrations = async () => {
    setLoading(true)
    try {
      // Fetch real data for connected integrations
      const [argoCDStatus, githubStatus, k8sStatus] = await Promise.all([
        fetchArgoCDStatus(),
        fetchGitHubStatus(),
        fetchK8sStatus()
      ])

      const connected = []
      
      if (argoCDStatus) connected.push(argoCDStatus)
      if (githubStatus) connected.push(githubStatus)
      if (k8sStatus) connected.push(k8sStatus)

      setConnectedIntegrations(connected)
    } catch (error) {
      console.error('Error fetching integrations:', error)
    } finally {
      setLoading(false)
    }
  }

  const fetchArgoCDStatus = async () => {
    try {
      // TODO: Call ArgoCD API to get real status
      // For now, return structure with placeholder
      return {
        id: 'argocd',
        name: 'ArgoCD',
        icon: '🐙',
        status: 'connected',
        statusText: 'Connected',
        metrics: {
          'Status': 'Ready to query',
          'URL': 'http://argocd.local'
        },
        actions: ['Open UI', 'Sync Apps', 'Configure'],
        url: 'http://argocd.local'
      }
    } catch {
      return null
    }
  }

  const fetchGitHubStatus = async () => {
    if (!activeCustomer) return null
    
    try {
      // Fetch customer's GitHub config from backend API
      const response = await fetch(`/customers/${activeCustomer.id}/integrations/github`)
      
      if (!response.ok) {
        // Not configured yet
        return null
      }
      
      const data = await response.json()
      // Backend returns { id, customer_id, type, config: { org, repo, token, branch } }
      // Extract the actual config
      const config = data.config || data
      const repoUrl = `https://github.com/${config.org}/${config.repo}`
      
      return {
        id: 'github',
        name: 'GitHub',
        icon: '⚙️',
        status: 'connected',
        statusText: 'Connected',
        metrics: {
          'Repository': `${config.org}/${config.repo}`,
          'Branch': config.branch || 'main',
          'Customer': activeCustomer.name
        },
        actions: ['View Repo', 'Workflows', 'Reinitialize', 'Configure', 'Remove'],
        url: repoUrl,
        config: config
      }
    } catch {
      return null
    }
  }

  const fetchK8sStatus = async () => {
    try {
      const response = await fetch('/api/deployments')
      if (!response.ok) throw new Error('Failed to fetch')
      
      const deployments = await response.json()
      const totalPods = deployments.reduce((sum, d) => sum + (d.replicas || 0), 0)
      
      return {
        id: 'kubernetes',
        name: 'Kubernetes',
        icon: '☸️',
        status: 'healthy',
        statusText: 'Cluster healthy',
        metrics: {
          'Deployments': deployments.length,
          'Pods': `${totalPods} running`,
          'Cluster': 'K3s on Pi5'
        },
        actions: ['View Pods', 'Deployments', 'Configure']
      }
    } catch {
      return null
    }
  }

  const handleAddIntegration = (integration) => {
    setSelectedToAdd(integration)
    setConfigData({})
    setTestResult(null)
    setShowAddModal(true)
  }

  const handleTestConnection = async () => {
    if (selectedToAdd.id !== 'github') return
    
    setTestingConnection(true)
    setTestResult(null)

    try {
      // Validate token by checking user
      const userResponse = await fetch('https://api.github.com/user', {
        headers: {
          'Authorization': `token ${configData.token}`,
          'Accept': 'application/vnd.github.v3+json'
        }
      })

      if (!userResponse.ok) {
        throw new Error('Invalid token or insufficient permissions')
      }

      const userData = await userResponse.json()

      // Check if the repository exists
      if (!configData.org || !configData.repo) {
        throw new Error('Repository owner and name are required')
      }

      const repoResponse = await fetch(`https://api.github.com/repos/${configData.org}/${configData.repo}`, {
        headers: {
          'Authorization': `token ${configData.token}`,
          'Accept': 'application/vnd.github.v3+json'
        }
      })

      if (!repoResponse.ok) {
        if (repoResponse.status === 404) {
          throw new Error(`Repository "${configData.org}/${configData.repo}" not found or no access`)
        }
        throw new Error('Unable to access repository')
      }

      const repoData = await repoResponse.json()

      setTestResult({ 
        success: true, 
        message: `✅ Connected as ${userData.login}. Repository "${repoData.full_name}" accessible!` 
      })
    } catch (error) {
      setTestResult({ 
        success: false, 
        message: `❌ Connection failed: ${error.message}` 
      })
    } finally {
      setTestingConnection(false)
    }
  }

  const handleConfigChange = (field, value) => {
    // Auto-extract username from GitHub URLs for org field
    if (field === 'org' && selectedToAdd?.id === 'github' && value) {
      // Match patterns like:
      // https://github.com/username
      // http://github.com/username
      // github.com/username
      const urlMatch = value.match(/(?:https?:\/\/)?(?:www\.)?github\.com\/([^\/\s]+)/i)
      if (urlMatch) {
        value = urlMatch[1]
      }
    }
    
    setConfigData({ ...configData, [field]: value })
  }

  const handleSaveIntegration = async () => {
    if (!activeCustomer) {
      alert('No customer selected')
      return
    }
    
    try {
      const response = await fetch(`/customers/${activeCustomer.id}/integrations/${selectedToAdd.id}`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(configData)
      })
      
      if (!response.ok) {
        const error = await response.json()
        throw new Error(error.message || 'Failed to save integration')
      }
      
      // Success - close modal and refresh
      setShowAddModal(false)
      setTestResult(null)
      fetchConnectedIntegrations()
      
    } catch (error) {
      alert(`Failed to save integration: ${error.message}`)
    }
  }

  const handleAction = (integration, action) => {
    if (action === 'Open UI' && integration.url) {
      window.open(integration.url, '_blank')
    } else if (action === 'View Repo' && integration.url) {
      window.open(integration.url, '_blank')
    } else if (action === 'Reinitialize') {
      handleReinitialize(integration)
    } else if (action === 'Configure') {
      handleConfigure(integration)
    } else if (action === 'Remove') {
      handleRemove(integration)
    } else {
      console.log(`Action: ${action} on ${integration.name}`)
    }
  }

  const handleConfigure = (integration) => {
    // Find the integration definition from availableIntegrations
    const integrationDef = availableIntegrations.find(a => a.id === integration.id)
    if (!integrationDef) return
    
    setSelectedToAdd(integrationDef)
    setConfigData(integration.config || {})
    setTestResult(null)
    setShowAddModal(true)
  }

  const handleRemove = async (integration) => {
    if (!activeCustomer) return
    
    if (!confirm(`Remove ${integration.name} integration for ${activeCustomer.name}?`)) {
      return
    }
    
    try {
      const response = await fetch(`/customers/${activeCustomer.id}/integrations/${integration.id}`, {
        method: 'DELETE'
      })
      
      if (!response.ok) {
        throw new Error('Failed to remove integration')
      }
      
      // Refresh integrations list
      fetchConnectedIntegrations()
    } catch (error) {
      alert(`Failed to remove integration: ${error.message}`)
    }
  }

  const handleReinitialize = async (integration) => {
    if (!activeCustomer || integration.id !== 'github') return
    
    if (!confirm(`Reinitialize GitHub repository for ${activeCustomer.name}?\n\nThis will push 8 template files (workflow, Dockerfile, app code, K8s manifests) to the repository. Existing files will be updated.`)) {
      return
    }
    
    try {
      const response = await fetch(`/customers/${activeCustomer.id}/reinitialize`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({})
      })
      
      if (!response.ok) {
        const errorData = await response.json()
        throw new Error(errorData.error || 'Failed to reinitialize repository')
      }
      
      const result = await response.json()
      
      if (result.success) {
        alert(`✅ Repository reinitialized successfully!\n\n${result.templates_pushed.length} files pushed:\n${result.templates_pushed.map(f => `  • ${f}`).join('\n')}\n\nStack: ${result.stack}`)
      } else {
        alert(`⚠️ Reinitialize completed with errors:\n\n✅ Pushed: ${result.templates_pushed.length} files\n❌ Errors: ${result.errors.length}\n\n${result.errors.join('\n')}`)
      }
      
      // Refresh integrations list
      fetchConnectedIntegrations()
    } catch (error) {
      alert(`Failed to reinitialize repository: ${error.message}`)
    }
  }

  // Filter out already connected integrations from available list
  const connectedIds = connectedIntegrations.map(i => i.id)
  const notConnected = availableIntegrations.filter(a => !connectedIds.includes(a.id))

  if (loading) {
    return (
      <div className="integrations-dashboard">
        <div className="integrations-header">
          <h2>🔗 DevOps Integrations</h2>
          <p>Loading...</p>
        </div>
      </div>
    )
  }

  // Show message if no customer selected
  if (!activeCustomer) {
    return (
      <div className="integrations-dashboard">
        <div className="integrations-header">
          <div className="header-content">
            <h2>🔗 DevOps Integrations</h2>
            <p>Select a customer to view their integrations</p>
          </div>
        </div>
        <div className="empty-state">
          <div className="empty-icon">🏢</div>
          <h3>No Customer Selected</h3>
          <p>Select a customer from the dropdown to view and manage their integrations.</p>
        </div>
      </div>
    )
  }

  return (
    <div className="integrations-dashboard">
      <div className="integrations-header">
        <div className="header-content">
          <h2>🔗 DevOps Integrations</h2>
          <p>Connect {activeCustomer.name}'s DevOps tools</p>
        </div>
        
        <div className="status-summary">
          <div className="summary-item summary-healthy">
            <span className="summary-count">{connectedIntegrations.length}</span>
            <span className="summary-label">Connected</span>
          </div>
          <div className="summary-item summary-warning">
            <span className="summary-count">{notConnected.length}</span>
            <span className="summary-label">Available</span>
          </div>
        </div>
      </div>

      {/* Connected Integrations */}
      {connectedIntegrations.length > 0 && (
        <>
          <h3 className="section-title">✅ Connected</h3>
          <div className="integrations-grid">
            {connectedIntegrations.map(integration => (
              <div 
                key={integration.id} 
                className={`integration-card integration-${integration.status}`}
              >
                <div className="integration-header">
                  <div className="integration-title">
                    <span className="integration-icon">{integration.icon}</span>
                    <div>
                      <h3>{integration.name}</h3>
                      <span className={`integration-status status-${integration.status}`}>
                        {integration.statusText}
                      </span>
                    </div>
                  </div>
                  <span className={`status-indicator status-${integration.status}`}></span>
                </div>

                <div className="integration-metrics">
                  {Object.entries(integration.metrics).map(([key, value]) => (
                    <div key={key} className="metric">
                      <span className="metric-label">{key}</span>
                      <span className="metric-value">{value}</span>
                    </div>
                  ))}
                </div>

                <div className="integration-actions">
                  {integration.actions.map(action => (
                    <button 
                      key={action}
                      className="integration-action-btn"
                      onClick={() => handleAction(integration, action)}
                    >
                      {action}
                    </button>
                  ))}
                </div>
              </div>
            ))}
          </div>
        </>
      )}

      {/* Available Integrations */}
      {notConnected.length > 0 && (
        <>
          <h3 className="section-title">➕ Available Integrations</h3>
          <div className="integrations-grid">
            {notConnected.map(integration => (
              <div 
                key={integration.id} 
                className="integration-card integration-available"
              >
                <div className="integration-header">
                  <div className="integration-title">
                    <span className="integration-icon">{integration.icon}</span>
                    <div>
                      <h3>{integration.name}</h3>
                      <p className="integration-description">{integration.description}</p>
                    </div>
                  </div>
                </div>

                <button 
                  className="btn-add-integration"
                  onClick={() => handleAddIntegration(integration)}
                >
                  ➕ Connect
                </button>
              </div>
            ))}
          </div>
        </>
      )}

      {/* Add Integration Modal */}
      {showAddModal && selectedToAdd && (
        <div className="modal-overlay" onClick={() => setShowAddModal(false)}>
          <div className="modal-content integration-modal" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <h2>
                <span className="integration-icon">{selectedToAdd.icon}</span>
                Connect {selectedToAdd.name}
              </h2>
              <button className="modal-close" onClick={() => setShowAddModal(false)}>×</button>
            </div>

            <div className="modal-body">
              <p className="integration-description">{selectedToAdd.description}</p>
              
              {selectedToAdd.helpText && (
                <div className="integration-help-box">
                  <span className="help-icon">💡</span>
                  <p>{selectedToAdd.helpText}</p>
                </div>
              )}

              {selectedToAdd.instructions && (
                <div className="integration-instructions">
                  <h4>{selectedToAdd.instructions.title}</h4>
                  <ol>
                    {selectedToAdd.instructions.steps.map((step, idx) => (
                      <li key={idx}>{step}</li>
                    ))}
                  </ol>
                  <button 
                    type="button"
                    className="btn-generate-token"
                    onClick={() => window.open(selectedToAdd.instructions.tokenUrl, '_blank')}
                  >
                    🔗 Generate Token on GitHub
                  </button>
                </div>
              )}
              
              <form className="integration-form">
                {selectedToAdd.configFields.map(field => (
                  <div key={field.name} className="form-group">
                    <label>
                      {field.label}
                      {field.required && <span className="required">*</span>}
                    </label>
                    {field.helpText && (
                      <small className="field-help">{field.helpText}</small>
                    )}
                    {field.type === 'textarea' ? (
                      <textarea
                        placeholder={field.placeholder || ''}
                        value={configData[field.name] || ''}
                        onChange={(e) => handleConfigChange(field.name, e.target.value)}
                        required={field.required}
                        rows={4}
                      />
                    ) : (
                      <input
                        type={field.type}
                        placeholder={field.placeholder || ''}
                        value={configData[field.name] || ''}
                        onChange={(e) => handleConfigChange(field.name, e.target.value)}
                        required={field.required}
                      />
                    )}
                  </div>
                ))}
              </form>
            </div>

            <div className="modal-footer">
              {testResult && (
                <div className={`test-result ${testResult.success ? 'test-success' : 'test-error'}`}>
                  {testResult.message}
                </div>
              )}
              
              <div className="modal-footer-actions">
                <button className="btn-secondary" onClick={() => setShowAddModal(false)}>
                  Cancel
                </button>
                
                {selectedToAdd.id === 'github' && (
                  <button 
                    className="btn-test" 
                    onClick={handleTestConnection}
                    disabled={!configData.token || !configData.org || !configData.repo || testingConnection}
                  >
                    {testingConnection ? '⏳ Testing...' : '🔍 Test Connection'}
                  </button>
                )}
                
                <button 
                  className="btn-primary" 
                  onClick={handleSaveIntegration}
                  disabled={selectedToAdd.id === 'github' && !testResult?.success}
                >
                  Save & Connect
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

export default IntegrationsDashboard
