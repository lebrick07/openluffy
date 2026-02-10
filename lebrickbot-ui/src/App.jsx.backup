import { useState, useEffect } from 'react'
import './App.css'
import Sidebar from './components/Sidebar'
import ClientSelector from './components/ClientSelector'
import DeployModal from './components/DeployModal'
import ActionModal from './components/ActionModal'
import Toast from './components/Toast'
import CostWidget from './components/CostWidget'
import AlertsPanel from './components/AlertsPanel'
import SettingsPage from './components/SettingsPage'
import IntegrationsDashboard from './components/IntegrationsDashboard'

function App() {
  const [deployments, setDeployments] = useState([])
  const [customers, setCustomers] = useState([])
  const [selectedClient, setSelectedClient] = useState(null)
  const [logs, setLogs] = useState([])
  const [stats, setStats] = useState({ deploymentsToday: 3, activeServices: 0, costThisMonth: '$142.35', uptime: '99.98%' })
  const [showDeployModal, setShowDeployModal] = useState(false)
  const [showActionModal, setShowActionModal] = useState(false)
  const [selectedDeployment, setSelectedDeployment] = useState(null)
  const [selectedAction, setSelectedAction] = useState(null)
  const [toast, setToast] = useState(null)
  const [loading, setLoading] = useState(false)
  const [currentView, setCurrentView] = useState('overview')
  const [theme, setTheme] = useState('dark')
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false)
  const [searchQuery, setSearchQuery] = useState('')

  useEffect(() => {
    fetchCustomers()
    fetchDeployments()
    const interval = setInterval(() => { fetchCustomers(); fetchDeployments() }, 10000)
    return () => clearInterval(interval)
  }, [])

  const fetchCustomers = async () => {
    try {
      const res = await fetch('/api/customers')
      const data = await res.json()
      setCustomers(data.customers || [])
      setStats(prev => ({ ...prev, activeServices: data.customers?.filter(c => c.status === 'running').length || 0 }))
    } catch (err) {
      console.error('Failed to fetch customers:', err)
    }
  }

  const fetchDeployments = async () => {
    try {
      const res = await fetch('/api/deployments')
      const data = await res.json()
      setDeployments(data.deployments?.map(d => ({
        id: d.id, name: d.name, status: d.status, replicas: d.replicas,
        time: 'live', cost: '$0.05/hr', customer: d.customer, namespace: d.namespace
      })) || [])
    } catch (err) {
      console.error('Failed to fetch deployments:', err)
    }
  }

  useEffect(() => { document.documentElement.setAttribute('data-theme', theme) }, [theme])

  const showToast = (message, type = 'info') => {
    setToast({ message, type })
    setTimeout(() => setToast(null), 4000)
  }

  const addLog = (message, level = 'info') => {
    const time = new Date().toLocaleTimeString('en-US', { hour12: false })
    setLogs(prev => [{ time, level, message }, ...prev].slice(0, 20))
  }

  const handleAction = (deployment, action) => {
    setSelectedDeployment(deployment)
    setSelectedAction(action)
    setShowActionModal(true)
  }

  const executeAction = async () => {
    setLoading(true)
    addLog(`Executing ${selectedAction} on ${selectedDeployment.name}`, 'info')
    setTimeout(() => {
      showToast(`${selectedAction} completed on ${selectedDeployment.name}`, 'success')
      setShowActionModal(false)
      setLoading(false)
      fetchDeployments()
    }, 1500)
  }

  const filteredCustomers = selectedClient ? customers.filter(c => c.id === selectedClient) : customers
  const filteredDeployments = deployments.filter(d =>
    (!selectedClient || d.namespace === selectedClient) &&
    (d.name.toLowerCase().includes(searchQuery.toLowerCase()) || d.customer?.toLowerCase().includes(searchQuery.toLowerCase()))
  )

  const selectedCustomerData = selectedClient ? customers.find(c => c.id === selectedClient) : null

  return (
    <div className={`app-container ${theme}`}>
      {toast && <Toast message={toast.message} type={toast.type} />}
      
      <Sidebar currentView={currentView} setCurrentView={setCurrentView} collapsed={sidebarCollapsed} setCollapsed={setSidebarCollapsed} />
      
      <div className={`main-content ${sidebarCollapsed ? 'sidebar-collapsed' : ''}`}>
        <header className="top-bar">
          <div className="top-bar-left">
            <ClientSelector customers={customers} selectedClient={selectedClient} setSelectedClient={setSelectedClient} />
          </div>
          <div className="top-bar-right">
            <button className="theme-toggle-btn" onClick={() => setTheme(theme === 'dark' ? 'light' : 'dark')}>
              {theme === 'dark' ? '☀️' : '🌙'}
            </button>
          </div>
        </header>

        <div className="content-area">
          {currentView === 'settings' ? (
            <SettingsPage />
          ) : currentView === 'integrations' ? (
            <IntegrationsDashboard />
          ) : currentView === 'costs' ? (
            <div className="view-container">
              <h2>💰 Cost Management</h2>
              <div className="grid-2">
                <CostWidget />
                <div className="section">
                  <h3>Cost Breakdown by Customer</h3>
                  {filteredCustomers.map(c => (
                    <div key={c.id} className="cost-row">
                      <span>{c.name}</span>
                      <span>$47.45/mo</span>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          ) : currentView === 'monitoring' ? (
            <div className="view-container">
              <h2>📈 Monitoring</h2>
              <div className="grid-2">
                <CostWidget />
                <AlertsPanel />
              </div>
            </div>
          ) : currentView === 'logs' ? (
            <div className="view-container">
              <h2>📋 Activity Logs</h2>
              <div className="logs-list">
                {logs.map((log, idx) => (
                  <div key={idx} className={`log-entry log-${log.level}`}>
                    <span className="log-time">{log.time}</span>
                    <span className="log-level">[{log.level.toUpperCase()}]</span>
                    <span className="log-message">{log.message}</span>
                  </div>
                ))}
              </div>
            </div>
          ) : currentView === 'overview' ? (
            <div className="view-container">
              {selectedCustomerData ? (
                <>
                  <div className="customer-header-banner">
                    <h1>{selectedCustomerData.name}</h1>
                    <span className={`status-badge status-${selectedCustomerData.status}`}>{selectedCustomerData.status}</span>
                  </div>
                  <div className="stats-grid-4">
                    <div className="stat-card">
                      <div className="stat-value">{selectedCustomerData.replicas}</div>
                      <div className="stat-label">Replicas</div>
                    </div>
                    <div className="stat-card">
                      <div className="stat-value">{selectedCustomerData.stack}</div>
                      <div className="stat-label">Stack</div>
                    </div>
                    <div className="stat-card">
                      <div className="stat-value">{selectedCustomerData.endpoints.length}</div>
                      <div className="stat-label">Endpoints</div>
                    </div>
                    <div className="stat-card">
                      <div className="stat-value">99.9%</div>
                      <div className="stat-label">Uptime</div>
                    </div>
                  </div>
                </>
              ) : (
                <>
                  <h2>Dashboard Overview</h2>
                  <div className="stats-grid-4">
                    <div className="stat-card">
                      <div className="stat-value">{customers.length}</div>
                      <div className="stat-label">Total Customers</div>
                    </div>
                    <div className="stat-card">
                      <div className="stat-value">{stats.activeServices}</div>
                      <div className="stat-label">Active Services</div>
                    </div>
                    <div className="stat-card">
                      <div className="stat-value">{stats.costThisMonth}</div>
                      <div className="stat-label">Monthly Cost</div>
                    </div>
                    <div className="stat-card">
                      <div className="stat-value">{stats.uptime}</div>
                      <div className="stat-label">Uptime</div>
                    </div>
                  </div>
                  <div className="customers-grid-compact">
                    {customers.map(c => (
                      <div key={c.id} className="customer-card-compact" onClick={() => setSelectedClient(c.id)}>
                        <h3>{c.name}</h3>
                        <p>{c.stack} • {c.replicas} replicas</p>
                        <span className={`badge badge-${c.status}`}>{c.status}</span>
                      </div>
                    ))}
                  </div>
                </>
              )}
            </div>
          ) : currentView === 'deployments' ? (
            <div className="view-container">
              <div className="view-header">
                <h2>🚀 Deployments</h2>
                <input type="text" placeholder="🔍 Search..." className="search-input" value={searchQuery} onChange={(e) => setSearchQuery(e.target.value)} />
              </div>
              {filteredDeployments.length === 0 ? (
                <div className="empty-state">
                  <span className="empty-icon">📦</span>
                  <h4>No deployments found</h4>
                </div>
              ) : (
                <div className="deployments-list">
                  {filteredDeployments.map(dep => (
                    <div key={dep.id} className="deployment-card">
                      <div className="deployment-header">
                        <div>
                          <span className="deployment-name">{dep.name}</span>
                          {!selectedClient && <span className="deployment-customer">({dep.customer})</span>}
                        </div>
                        <span className={`deployment-status status-${dep.status}`}>{dep.status}</span>
                      </div>
                      <div className="deployment-meta">
                        <span>⏱ {dep.time}</span>
                        <span>📦 {dep.replicas}</span>
                        <span>💰 {dep.cost}</span>
                      </div>
                      <div className="deployment-actions">
                        <button className="action-btn" onClick={() => handleAction(dep, 'scale')}>⬆️</button>
                        <button className="action-btn" onClick={() => handleAction(dep, 'restart')}>🔄</button>
                        <button className="action-btn" onClick={() => handleAction(dep, 'logs')}>📋</button>
                        <button className="action-btn" onClick={() => handleAction(dep, 'delete')}>🗑️</button>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          ) : null}
        </div>
      </div>

      {showDeployModal && <DeployModal onClose={() => setShowDeployModal(false)} onDeploy={() => {}} loading={loading} />}
      {showActionModal && selectedDeployment && (
        <ActionModal deployment={selectedDeployment} action={selectedAction} onClose={() => setShowActionModal(false)} onConfirm={executeAction} loading={loading} />
      )}
    </div>
  )
}

export default App
