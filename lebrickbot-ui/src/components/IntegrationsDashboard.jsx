import { useState } from 'react'
import './IntegrationsDashboard.css'

const integrations = [
  {
    id: 'github-actions',
    name: 'GitHub Actions',
    icon: '⚙️',
    status: 'healthy',
    statusText: 'All workflows passing',
    metrics: {
      'Workflows': '12 active',
      'Last run': '2m ago',
      'Success rate': '98.5%'
    },
    actions: ['View workflows', 'Trigger build', 'Configure']
  },
  {
    id: 'argocd',
    name: 'ArgoCD',
    icon: '🐙',
    status: 'synced',
    statusText: '8 apps synced',
    metrics: {
      'Applications': '8',
      'Last sync': 'just now',
      'Out of sync': '0'
    },
    actions: ['Open UI', 'Sync all', 'Configure'],
    url: 'http://argocd.local'
  },
  {
    id: 'aws',
    name: 'AWS',
    icon: '☁️',
    status: 'healthy',
    statusText: 'All services operational',
    metrics: {
      'EC2 instances': '4 running',
      'RDS databases': '2 active',
      'Monthly cost': '$142.35'
    },
    actions: ['Open console', 'View costs', 'Configure']
  },
  {
    id: 'terraform',
    name: 'Terraform Cloud',
    icon: '🏗️',
    status: 'healthy',
    statusText: 'No pending runs',
    metrics: {
      'Workspaces': '6',
      'Last apply': '1h ago',
      'Resources': '42 managed'
    },
    actions: ['View workspaces', 'Plan', 'Configure']
  },
  {
    id: 'jfrog',
    name: 'JFrog Artifactory',
    icon: '🐸',
    status: 'healthy',
    statusText: 'Registry operational',
    metrics: {
      'Repositories': '8',
      'Artifacts': '1.2k',
      'Storage': '15.3 GB'
    },
    actions: ['Browse artifacts', 'Upload', 'Configure']
  },
  {
    id: 'datadog',
    name: 'DataDog',
    icon: '🐕',
    status: 'warning',
    statusText: '2 active alerts',
    metrics: {
      'Monitors': '24',
      'Alerts': '2 active',
      'Hosts': '8 reporting'
    },
    actions: ['View alerts', 'Open dashboard', 'Configure']
  },
  {
    id: 'sonarqube',
    name: 'SonarQube',
    icon: '🔍',
    status: 'healthy',
    statusText: 'Code quality: A',
    metrics: {
      'Projects': '12',
      'Bugs': '3',
      'Coverage': '84.2%'
    },
    actions: ['View projects', 'Run scan', 'Configure']
  },
  {
    id: 'vault',
    name: 'HashiCorp Vault',
    icon: '🔐',
    status: 'healthy',
    statusText: 'Sealed: No',
    metrics: {
      'Secrets': '156',
      'Auth methods': '3',
      'Policies': '12'
    },
    actions: ['Manage secrets', 'Open UI', 'Configure']
  },
  {
    id: 'slack',
    name: 'Slack',
    icon: '💬',
    status: 'connected',
    statusText: 'Notifications active',
    metrics: {
      'Channels': '3',
      'Messages today': '47',
      'Alerts sent': '12'
    },
    actions: ['Send test', 'Configure', 'Mute']
  },
  {
    id: 'pagerduty',
    name: 'PagerDuty',
    icon: '🚨',
    status: 'healthy',
    statusText: 'No incidents',
    metrics: {
      'On-call': '2 people',
      'Incidents (24h)': '0',
      'Response time': '3.2m avg'
    },
    actions: ['View incidents', 'Test alert', 'Configure']
  }
]

function IntegrationsDashboard() {
  const [selectedIntegration, setSelectedIntegration] = useState(null)
  const [filter, setFilter] = useState('all')

  const statusCounts = {
    healthy: integrations.filter(i => i.status === 'healthy' || i.status === 'synced' || i.status === 'connected').length,
    warning: integrations.filter(i => i.status === 'warning').length,
    error: integrations.filter(i => i.status === 'error').length
  }

  const filteredIntegrations = filter === 'all' 
    ? integrations 
    : integrations.filter(i => i.status === filter)

  const handleAction = (integration, action) => {
    if (action === 'Open UI' && integration.url) {
      window.open(integration.url, '_blank')
    } else {
      console.log(`Action: ${action} on ${integration.name}`)
      // Here you'd trigger the actual backend action
    }
  }

  return (
    <div className="integrations-dashboard">
      <div className="integrations-header">
        <div className="header-content">
          <h2>🔗 DevOps Integrations</h2>
          <p>One-stop shop for all your DevOps tools</p>
        </div>
        
        <div className="status-summary">
          <div className="summary-item summary-healthy">
            <span className="summary-count">{statusCounts.healthy}</span>
            <span className="summary-label">Healthy</span>
          </div>
          <div className="summary-item summary-warning">
            <span className="summary-count">{statusCounts.warning}</span>
            <span className="summary-label">Warnings</span>
          </div>
          <div className="summary-item summary-error">
            <span className="summary-count">{statusCounts.error}</span>
            <span className="summary-label">Errors</span>
          </div>
        </div>
      </div>

      <div className="integrations-filters">
        <button 
          className={`filter-btn ${filter === 'all' ? 'active' : ''}`}
          onClick={() => setFilter('all')}
        >
          All Tools
        </button>
        <button 
          className={`filter-btn ${filter === 'healthy' ? 'active' : ''}`}
          onClick={() => setFilter('healthy')}
        >
          Healthy
        </button>
        <button 
          className={`filter-btn ${filter === 'warning' ? 'active' : ''}`}
          onClick={() => setFilter('warning')}
        >
          Warnings
        </button>
        <button 
          className={`filter-btn ${filter === 'error' ? 'active' : ''}`}
          onClick={() => setFilter('error')}
        >
          Errors
        </button>
      </div>

      <div className="integrations-grid">
        {filteredIntegrations.map(integration => (
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

      <div className="integration-add">
        <button className="btn-add-integration">
          ➕ Add Integration
        </button>
      </div>
    </div>
  )
}

export default IntegrationsDashboard
