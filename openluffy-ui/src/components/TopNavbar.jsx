import { useState, useEffect } from 'react'
import { useCustomer } from '../contexts/CustomerContext'
import './TopNavbar.css'

function TopNavbar({ onCreateNew, selectedEnvironment, onEnvironmentChange, onToggleSidebar }) {
  const { customers, selectedCustomer, selectCustomer } = useCustomer()
  const [systemStatus, setSystemStatus] = useState({ healthy: true, loading: true })
  const [notifications, setNotifications] = useState([])
  const [showNotifications, setShowNotifications] = useState(false)
  const [showCreateMenu, setShowCreateMenu] = useState(false)
  const [showUserMenu, setShowUserMenu] = useState(false)
  const [searchQuery, setSearchQuery] = useState('')

  useEffect(() => {
    // Check system health
    fetch('http://localhost:8000/health')
      .then(res => res.json())
      .then(data => {
        setSystemStatus({ healthy: data.status === 'healthy', loading: false })
      })
      .catch(() => {
        setSystemStatus({ healthy: false, loading: false })
      })

    // Fetch notifications (pending approvals count)
    fetch('http://localhost:8000/pending-approvals')
      .then(res => res.json())
      .then(data => {
        if (data.approvals && data.approvals.length > 0) {
          setNotifications(data.approvals)
        }
      })
      .catch(err => console.error('Failed to fetch notifications:', err))
  }, [])

  const notificationCount = notifications.length

  return (
    <nav className="top-navbar">
      {/* Hamburger Menu (Mobile Only) */}
      <button className="hamburger-btn" onClick={onToggleSidebar} title="Toggle menu">
        <span className="hamburger-line"></span>
        <span className="hamburger-line"></span>
        <span className="hamburger-line"></span>
      </button>

      {/* Left Section: Filters */}
      <div className="navbar-left">
        <div className="navbar-filters">
          <select 
            className="filter-select"
            value={selectedCustomer || 'all'}
            onChange={(e) => selectCustomer(e.target.value === 'all' ? null : e.target.value)}
          >
            <option value="all">All Customers</option>
            {customers.map(c => (
              <option key={c.id} value={c.id}>{c.name}</option>
            ))}
          </select>

          <select
            className="filter-select"
            value={selectedEnvironment || 'all'}
            onChange={(e) => onEnvironmentChange(e.target.value)}
          >
            <option value="all">All Environments</option>
            <option value="dev">DEV</option>
            <option value="preprod">PREPROD</option>
            <option value="prod">PROD</option>
          </select>
        </div>
      </div>

      {/* Center Section: Global Search (Priority) */}
      <div className="navbar-center">
        <input 
          type="text"
          placeholder="Search customers, apps, pipelines, logs..."
          className="navbar-search"
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
        />
      </div>

      {/* Right Section: Create | Notifications | Links | User */}
      <div className="navbar-right">
        {/* Create Button - Next to Search */}
        <div className="create-menu-container">
          <button 
            className="create-btn"
            onClick={() => setShowCreateMenu(!showCreateMenu)}
          >
            + Create
          </button>

          {showCreateMenu && (
            <div className="create-menu">
              <button 
                className="create-menu-item"
                onClick={() => {
                  setShowCreateMenu(false)
                  onCreateNew('customer')
                }}
              >
                <span className="menu-icon">🏢</span>
                New Customer
              </button>
              <button 
                className="create-menu-item"
                onClick={() => {
                  setShowCreateMenu(false)
                  onCreateNew('application')
                }}
              >
                <span className="menu-icon">📦</span>
                New Application
              </button>
              <button 
                className="create-menu-item"
                onClick={() => {
                  setShowCreateMenu(false)
                  onCreateNew('pipeline')
                }}
              >
                <span className="menu-icon">🚀</span>
                New Pipeline
              </button>
              <button 
                className="create-menu-item"
                onClick={() => {
                  setShowCreateMenu(false)
                  onCreateNew('integration')
                }}
              >
                <span className="menu-icon">🔌</span>
                New Integration
              </button>
            </div>
          )}
        </div>

        {/* Notifications */}
        <div className="navbar-notifications">
          <button 
            className="icon-btn"
            onClick={() => setShowNotifications(!showNotifications)}
            title="Notifications"
          >
            🔔
            {notificationCount > 0 && (
              <span className="notification-badge">{notificationCount}</span>
            )}
          </button>
          
          {showNotifications && (
            <div className="notification-dropdown">
              <div className="notification-header">
                <span>Notifications</span>
                {notificationCount > 0 && (
                  <span className="count">{notificationCount} pending</span>
                )}
              </div>
              <div className="notification-list">
                {notificationCount === 0 ? (
                  <div className="notification-empty">
                    All caught up
                  </div>
                ) : (
                  notifications.map((approval, idx) => (
                    <div key={idx} className="notification-item">
                      <span className="notification-icon">🚀</span>
                      <div className="notification-content">
                        <div className="notification-title">
                          Production Approval Required
                        </div>
                        <div className="notification-detail">
                          {approval.customer} - {approval.deployment}
                        </div>
                      </div>
                    </div>
                  ))
                )}
              </div>
            </div>
          )}
        </div>

        {/* User Profile with Login/Logout */}
        <div className="navbar-user-container">
          <div 
            className="navbar-user"
            onClick={() => setShowUserMenu(!showUserMenu)}
          >
            <div className="user-avatar">⚔️</div>
            <div className="user-info">
              <span className="user-name">Captain LeBrick</span>
              <span className="user-role">Straw Hat Crew</span>
            </div>
          </div>

          {showUserMenu && (
            <div className="user-menu">
              <div className="user-menu-header">
                <div className="user-avatar-large">⚔️</div>
                <div>
                  <div className="user-menu-name">Captain LeBrick</div>
                  <div className="user-menu-role">Straw Hat Crew</div>
                </div>
              </div>
              <div className="user-menu-items">
                <button className="user-menu-item">
                  <span className="menu-icon">👤</span>
                  Profile Settings
                </button>
                <button className="user-menu-item">
                  <span className="menu-icon">🔑</span>
                  Change Password
                </button>
                <button className="user-menu-item">
                  <span className="menu-icon">⚙️</span>
                  Preferences
                </button>
                <div className="user-menu-divider"></div>
                <button className="user-menu-item logout-item">
                  <span className="menu-icon">🚪</span>
                  Logout
                </button>
              </div>
            </div>
          )}
        </div>
      </div>
    </nav>
  )
}

export default TopNavbar
