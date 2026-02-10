import { useState, useEffect } from 'react'
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
  const [connectedIntegrations, setConnectedIntegrations] = useState([])
  const [showAddModal, setShowAddModal] = useState(false)
  const [selectedToAdd, setSelectedToAdd] = useState(null)
  const [configData, setConfigData] = useState({})
  const [loading, setLoading] = useState(true)

  // Fetch real connected integrations
  useEffect(() => {
    fetchConnectedIntegrations()
  }, [])

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
    } catch (error) {
      return null
    }
  }

  const fetchGitHubStatus = async () => {
    try {
      // TODO: Call GitHub API to get real status
      return {
        id: 'github',
        name: 'GitHub',
        icon: '⚙️',
        status: 'connected',
        statusText: 'Connected',
        metrics: {
          'Repository': 'lebrick07/openluffy',
          'Status': 'Ready to query'
        },
        actions: ['View Repo', 'Workflows', 'Configure'],
        url: 'https://github.com/lebrick07/openluffy'
      }
    } catch (error) {
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
    } catch (error) {
      return null
    }
  }

  const handleAddIntegration = (integration) => {
    setSelectedToAdd(integration)
    setConfigData({})
    setShowAddModal(true)
  }

  const handleConfigChange = (field, value) => {
    setConfigData({ ...configData, [field]: value })
  }

  const handleSaveIntegration = async () => {
    // TODO: Send config to backend to store credentials
    console.log('Saving integration:', selectedToAdd.id, configData)
    
    // For now, just close modal
    // In production, this would save to backend and re-fetch integrations
    setShowAddModal(false)
    alert(`Integration configuration saved! (Backend API coming soon)`)
  }

  const handleAction = (integration, action) => {
    if (action === 'Open UI' && integration.url) {
      window.open(integration.url, '_blank')
    } else if (action === 'View Repo' && integration.url) {
      window.open(integration.url, '_blank')
    } else {
      console.log(`Action: ${action} on ${integration.name}`)
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

  return (
    <div className="integrations-dashboard">
      <div className="integrations-header">
        <div className="header-content">
          <h2>🔗 DevOps Integrations</h2>
          <p>Connect your DevOps tools</p>
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
              
              <form className="integration-form">
                {selectedToAdd.configFields.map(field => (
                  <div key={field.name} className="form-group">
                    <label>
                      {field.label}
                      {field.required && <span className="required">*</span>}
                    </label>
                    <input
                      type={field.type}
                      placeholder={field.placeholder || ''}
                      value={configData[field.name] || ''}
                      onChange={(e) => handleConfigChange(field.name, e.target.value)}
                      required={field.required}
                    />
                  </div>
                ))}
              </form>
            </div>

            <div className="modal-footer">
              <button className="btn-secondary" onClick={() => setShowAddModal(false)}>
                Cancel
              </button>
              <button className="btn-primary" onClick={handleSaveIntegration}>
                Save & Connect
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

export default IntegrationsDashboard
