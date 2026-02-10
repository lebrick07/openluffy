import { useState } from 'react'
import './Sidebar.css'

function Sidebar({ activeView, onViewChange, isOpen = false }) {
  const [collapsed, setCollapsed] = useState(false)

  const menuItems = [
    {
      id: 'applications',
      icon: '📦',
      label: 'Applications',
      description: 'All deployments & environments'
    },
    {
      id: 'k8s',
      icon: '☸️',
      label: 'Kubernetes',
      description: 'Deep cluster & pod insights'
    },
    {
      id: 'pipelines',
      icon: '🚀',
      label: 'CI/CD Pipelines',
      description: 'GitHub Actions & workflow runs'
    },
    {
      id: 'pipeline-config',
      icon: '⚙️',
      label: 'Pipeline Config',
      description: 'Customize tests & scans'
    },
    {
      id: 'approvals',
      icon: '✅',
      label: 'Production Approvals',
      description: 'Preprod → Prod promotions'
    },
    {
      id: 'integrations',
      icon: '🔌',
      label: 'Integrations',
      description: 'Observability & DevOps tools'
    },
    {
      id: 'monitoring',
      icon: '📈',
      label: 'Monitoring',
      description: 'Metrics, logs, and alerts'
    },
    {
      id: 'settings',
      icon: '🔧',
      label: 'Settings',
      description: 'Configuration & preferences'
    }
  ]

  return (
    <div className={`sidebar ${collapsed ? 'collapsed' : ''} ${isOpen ? 'open' : ''}`}>
      <div className="sidebar-header">
        {!collapsed ? (
          <span className="sidebar-brand">Luffy DevOps</span>
        ) : (
          <span className="sidebar-brand-icon">⚔️</span>
        )}
        <button 
          className="collapse-btn"
          onClick={() => setCollapsed(!collapsed)}
          title={collapsed ? 'Expand' : 'Collapse'}
        >
          {collapsed ? '→' : '←'}
        </button>
      </div>

      <nav className="sidebar-nav">
        {menuItems.map(item => (
          <button
            key={item.id}
            className={`nav-item ${activeView === item.id ? 'active' : ''}`}
            onClick={() => onViewChange(item.id)}
            title={collapsed ? item.label : ''}
          >
            <span className="nav-icon">{item.icon}</span>
            {!collapsed && (
              <div className="nav-content">
                <span className="nav-label">{item.label}</span>
                <span className="nav-description">{item.description}</span>
              </div>
            )}
          </button>
        ))}
      </nav>

      <div className="sidebar-footer">
        {!collapsed && (
          <>
            <div className="footer-link">
              <a 
                href="http://argocd.local" 
                target="_blank" 
                rel="noopener noreferrer"
              >
                🐙 ArgoCD
              </a>
            </div>
            <div className="footer-link">
              <a 
                href="https://github.com/lebrick07/lebrickbot" 
                target="_blank" 
                rel="noopener noreferrer"
              >
                📦 GitHub
              </a>
            </div>
          </>
        )}
      </div>
    </div>
  )
}

export default Sidebar
