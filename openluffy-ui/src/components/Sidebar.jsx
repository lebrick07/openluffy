import './Sidebar.css'

function Sidebar({ activeView, onViewChange, isOpen = false }) {
  const menuItems = [
    {
      id: 'applications',
      icon: '📦',
      label: 'Applications',
      description: 'All deployments & environments'
    },
    {
      id: 'secrets',
      icon: '🔐',
      label: 'Secrets & Variables',
      description: 'Environment secrets & config'
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
    <div className={`sidebar ${isOpen ? 'open' : ''}`}>
      <div className="sidebar-header">
        <span className="sidebar-brand">Luffy DevOps</span>
      </div>

      <nav className="sidebar-nav">
        {menuItems.map(item => (
          <button
            key={item.id}
            className={`nav-item ${activeView === item.id ? 'active' : ''}`}
            onClick={() => onViewChange(item.id)}
          >
            <span className="nav-icon">{item.icon}</span>
            <div className="nav-content">
              <span className="nav-label">{item.label}</span>
              <span className="nav-description">{item.description}</span>
            </div>
          </button>
        ))}
      </nav>

    </div>
  )
}

export default Sidebar
