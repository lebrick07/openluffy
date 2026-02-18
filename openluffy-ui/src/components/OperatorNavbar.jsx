import { useState, useEffect } from 'react'
import './OperatorNavbar.css'

function OperatorNavbar({ 
  selectedCustomer, 
  onCustomerChange,
  selectedEnvironment,
  onEnvironmentChange,
  onCreateNew
}) {
  const [customers, setCustomers] = useState([])
  const [notifications, setNotifications] = useState([])
  const [showNotifications, setShowNotifications] = useState(false)
  const [showCreateMenu, setShowCreateMenu] = useState(false)
  const [searchQuery, setSearchQuery] = useState('')

  useEffect(() => {
    fetchCustomers()
    fetchNotifications()
  }, [])

  const fetchCustomers = async () => {
    try {
      const res = await fetch('/api/customers')
      const data = await res.json()
      setCustomers(data.customers || [])
    } catch (err) {
      console.error('Failed to fetch customers:', err)
    }
  }

  const fetchNotifications = async () => {
    try {
      const res = await fetch('/api/pending-approvals')
      const data = await res.json()
      setNotifications(data.approvals || [])
    } catch (err) {
      console.error('Failed to fetch notifications:', err)
    }
  }

  const notificationCount = notifications.length

  return (
    <nav className="operator-navbar">
      {/* Left: Filters */}
      <div className="navbar-filters">
        <select 
          className="filter-select"
          value={selectedCustomer || 'all'}
          onChange={(e) => onCustomerChange(e.target.value === 'all' ? null : e.target.value)}
        >
          <option value="all">All Customers</option>
          {customers.map(c => (
            <option key={c.id} value={c.id}>{c.name}</option>
          ))}
        </select>

        <select
          className="filter-select"
          value={selectedEnvironment}
          onChange={(e) => onEnvironmentChange(e.target.value)}
        >
          <option value="all">All Environments</option>
          <option value="dev">DEV</option>
          <option value="preprod">PREPROD</option>
          <option value="prod">PROD</option>
        </select>
      </div>

      {/* Center: Search */}
      <div className="navbar-search-container">
        <input 
          type="text"
          placeholder="Search customers, apps, pipelines, images..."
          className="navbar-search"
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
        />
      </div>

      {/* Right: Actions */}
      <div className="navbar-actions">
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

        {/* Create Button */}
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

        {/* Quick Links */}
        <a 
          href="http://argocd.local" 
          target="_blank" 
          rel="noopener noreferrer"
          className="icon-btn"
          title="ArgoCD"
        >
          🐙
        </a>
        <a 
          href="https://github.com/lebrick07/openluffy" 
          target="_blank" 
          rel="noopener noreferrer"
          className="icon-btn"
          title="GitHub"
        >
          📦
        </a>
      </div>
    </nav>
  )
}

export default OperatorNavbar
