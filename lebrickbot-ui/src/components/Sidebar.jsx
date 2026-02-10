import './Sidebar.css'

function Sidebar({ currentView, setCurrentView, collapsed, setCollapsed }) {
  const menuItems = [
    { id: 'overview', icon: '📊', label: 'Overview' },
    { id: 'deployments', icon: '🚀', label: 'Deployments' },
    { id: 'monitoring', icon: '📈', label: 'Monitoring' },
    { id: 'integrations', icon: '🔗', label: 'Integrations' },
    { id: 'logs', icon: '📋', label: 'Activity Logs' },
    { id: 'costs', icon: '💰', label: 'Cost Management' },
    { id: 'settings', icon: '⚙️', label: 'Settings' }
  ]

  return (
    <aside className={`sidebar ${collapsed ? 'collapsed' : ''}`}>
      <div className="sidebar-header">
        <div className="sidebar-logo">
          {!collapsed ? (
            <div className="logo-text-block">
              <div className="logo-line">LUFFY</div>
              <div className="logo-line sub">DEVOPS</div>
            </div>
          ) : (
            <div className="logo-icon-text">L</div>
          )}
        </div>
        <button className="collapse-btn" onClick={() => setCollapsed(!collapsed)}>
          {collapsed ? '→' : '←'}
        </button>
      </div>

      <nav className="sidebar-nav">
        {menuItems.map(item => (
          <button
            key={item.id}
            className={`nav-item ${currentView === item.id ? 'active' : ''}`}
            onClick={() => setCurrentView(item.id)}
            title={collapsed ? item.label : ''}
          >
            <span className="nav-icon">{item.icon}</span>
            {!collapsed && <span className="nav-label">{item.label}</span>}
          </button>
        ))}
      </nav>

      <div className="sidebar-footer">
        {!collapsed && (
          <div className="version-info">
            <div className="version-text">v0.1.0</div>
            <div className="version-label">Freelance DevOps Platform</div>
          </div>
        )}
      </div>
    </aside>
  )
}

export default Sidebar
