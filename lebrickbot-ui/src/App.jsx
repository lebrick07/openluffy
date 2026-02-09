import { useState, useEffect } from 'react'
import './App.css'
import DeployModal from './components/DeployModal'
import ActionModal from './components/ActionModal'
import Toast from './components/Toast'
import IntegrationsDashboard from './components/IntegrationsDashboard'

function App() {
  const [deployments, setDeployments] = useState([
    { id: 1, name: 'api-gateway', status: 'running', replicas: 3, time: '2m ago', cost: '$0.12/hr' },
    { id: 2, name: 'auth-service', status: 'running', replicas: 2, time: '5m ago', cost: '$0.08/hr' },
    { id: 3, name: 'database-cluster', status: 'healthy', replicas: 1, time: '1h ago', cost: '$0.45/hr' }
  ])
  
  const [logs, setLogs] = useState([
    { time: '11:32:15', level: 'info', message: 'ArgoCD sync completed successfully' },
    { time: '11:31:42', level: 'success', message: 'Deployment api-gateway scaled to 3 replicas' },
    { time: '11:30:08', level: 'info', message: 'Image pull completed: backend:latest' },
    { time: '11:29:33', level: 'warning', message: 'Resolved ghcr.io authentication issue' },
    { time: '11:28:45', level: 'info', message: 'Triage agent detected ImagePullBackOff' }
  ])

  const [stats, setStats] = useState({
    deploymentsToday: 12,
    activeServices: 8,
    costThisMonth: '$142.35',
    uptime: '99.98%'
  })

  const [showDeployModal, setShowDeployModal] = useState(false)
  const [showActionModal, setShowActionModal] = useState(false)
  const [selectedDeployment, setSelectedDeployment] = useState(null)
  const [selectedAction, setSelectedAction] = useState(null)
  const [toast, setToast] = useState(null)
  const [loading, setLoading] = useState(false)
  const [currentView, setCurrentView] = useState('deployments') // 'deployments' or 'integrations'

  useEffect(() => {
    // Test API connectivity
    fetch('/api/')
      .then(res => res.json())
      .then(data => {
        console.log('Backend connected:', data)
        showToast('Backend connected', 'success')
      })
      .catch(err => {
        console.log('Backend offline:', err)
        showToast('Backend offline - using demo data', 'warning')
      })
  }, [])

  const showToast = (message, type = 'info') => {
    setToast({ message, type })
    setTimeout(() => setToast(null), 4000)
  }

  const addLog = (message, level = 'info') => {
    const now = new Date()
    const time = now.toLocaleTimeString('en-US', { hour12: false })
    setLogs(prev => [{ time, level, message }, ...prev].slice(0, 20))
  }

  const handleDeploy = async (service) => {
    setLoading(true)
    addLog(`Initiating deployment: ${service.name}`, 'info')
    
    // Simulate API call
    setTimeout(() => {
      const newDeployment = {
        id: Date.now(),
        name: service.name,
        status: 'running',
        replicas: service.replicas || 1,
        time: 'just now',
        cost: '$0.05/hr'
      }
      
      setDeployments(prev => [newDeployment, ...prev])
      setStats(prev => ({
        ...prev,
        deploymentsToday: prev.deploymentsToday + 1,
        activeServices: prev.activeServices + 1
      }))
      
      addLog(`Deployment ${service.name} created successfully`, 'success')
      showToast(`${service.name} deployed successfully!`, 'success')
      setShowDeployModal(false)
      setLoading(false)
    }, 2000)
  }

  const handleAction = (deployment, action) => {
    setSelectedDeployment(deployment)
    setSelectedAction(action)
    setShowActionModal(true)
  }

  const executeAction = async () => {
    setLoading(true)
    const { name } = selectedDeployment
    
    addLog(`Executing ${selectedAction} on ${name}`, 'info')
    
    // Simulate API call
    setTimeout(() => {
      switch(selectedAction) {
        case 'scale':
          setDeployments(prev => prev.map(d => 
            d.id === selectedDeployment.id 
              ? { ...d, replicas: d.replicas + 1 }
              : d
          ))
          addLog(`Scaled ${name} to ${selectedDeployment.replicas + 1} replicas`, 'success')
          showToast(`${name} scaled up!`, 'success')
          break
          
        case 'restart':
          addLog(`Restarted ${name}`, 'success')
          showToast(`${name} restarted!`, 'success')
          break
          
        case 'logs':
          addLog(`Fetching logs for ${name}`, 'info')
          showToast('Log viewer coming soon!', 'info')
          break
          
        case 'delete':
          setDeployments(prev => prev.filter(d => d.id !== selectedDeployment.id))
          setStats(prev => ({
            ...prev,
            activeServices: prev.activeServices - 1
          }))
          addLog(`Deleted ${name}`, 'warning')
          showToast(`${name} deleted`, 'warning')
          break
      }
      
      setShowActionModal(false)
      setLoading(false)
    }, 1500)
  }

  return (
    <div className="dashboard">
      {/* Toast Notifications */}
      {toast && <Toast message={toast.message} type={toast.type} />}

      {/* Header */}
      <header className="header">
        <div className="logo">
          <span className="logo-icon">🤖</span>
          <h1>LeBrickBot</h1>
        </div>
        <nav className="nav">
          <a 
            href="#deployments" 
            className={currentView === 'deployments' ? 'active' : ''}
            onClick={(e) => { e.preventDefault(); setCurrentView('deployments'); }}
          >
            Deployments
          </a>
          <a 
            href="#integrations" 
            className={currentView === 'integrations' ? 'active' : ''}
            onClick={(e) => { e.preventDefault(); setCurrentView('integrations'); }}
          >
            Integrations
          </a>
          <a href="#monitoring">Monitoring</a>
          <a href="#costs">Costs</a>
          <a href="#settings">Settings</a>
        </nav>
      </header>

      {/* Hero Section */}
      <section className="hero">
        <h2>Autonomous DevOps Platform</h2>
        <p>Replace your entire DevOps team with AI-powered infrastructure management</p>
        <div className="hero-features">
          <div className="feature">
            <span className="feature-icon">🚀</span>
            <span>Auto-Deploy</span>
          </div>
          <div className="feature">
            <span className="feature-icon">🔧</span>
            <span>Self-Heal</span>
          </div>
          <div className="feature">
            <span className="feature-icon">💰</span>
            <span>Cost Optimize</span>
          </div>
          <div className="feature">
            <span className="feature-icon">📊</span>
            <span>Real-time Monitor</span>
          </div>
        </div>
      </section>

      {/* Stats Grid */}
      <section className="stats">
        <div className="stat-card">
          <div className="stat-value">{stats.deploymentsToday}</div>
          <div className="stat-label">Deployments Today</div>
        </div>
        <div className="stat-card">
          <div className="stat-value">{stats.activeServices}</div>
          <div className="stat-label">Active Services</div>
        </div>
        <div className="stat-card">
          <div className="stat-value">{stats.costThisMonth}</div>
          <div className="stat-label">Cost This Month</div>
        </div>
        <div className="stat-card">
          <div className="stat-value">{stats.uptime}</div>
          <div className="stat-label">Uptime</div>
        </div>
      </section>

      {/* Main Content */}
      {currentView === 'deployments' ? (
        <div className="content">
          {/* Deployments */}
          <section className="section deployments-section">
            <h3>Active Deployments</h3>
            <div className="deployments-list">
              {deployments.map(dep => (
                <div key={dep.id} className="deployment-card">
                  <div className="deployment-header">
                    <span className="deployment-name">{dep.name}</span>
                    <span className={`deployment-status status-${dep.status}`}>{dep.status}</span>
                  </div>
                  <div className="deployment-meta">
                    <span className="deployment-time">⏱ {dep.time}</span>
                    <span className="deployment-replicas">📦 {dep.replicas} replica{dep.replicas > 1 ? 's' : ''}</span>
                    <span className="deployment-cost">💰 {dep.cost}</span>
                  </div>
                  <div className="deployment-actions">
                    <button className="action-btn action-scale" onClick={() => handleAction(dep, 'scale')} title="Scale Up">
                      ⬆️
                    </button>
                    <button className="action-btn action-restart" onClick={() => handleAction(dep, 'restart')} title="Restart">
                      🔄
                    </button>
                    <button className="action-btn action-logs" onClick={() => handleAction(dep, 'logs')} title="View Logs">
                      📋
                    </button>
                    <button className="action-btn action-delete" onClick={() => handleAction(dep, 'delete')} title="Delete">
                      🗑️
                    </button>
                  </div>
                </div>
              ))}
            </div>
            <button className="btn-primary" onClick={() => setShowDeployModal(true)}>
              🚀 Deploy New Service
            </button>
          </section>

          {/* Activity Logs */}
          <section className="section logs-section">
            <h3>Activity Logs</h3>
            <div className="logs-list">
              {logs.map((log, idx) => (
                <div key={idx} className={`log-entry log-${log.level}`}>
                  <span className="log-time">{log.time}</span>
                  <span className="log-level">[{log.level.toUpperCase()}]</span>
                  <span className="log-message">{log.message}</span>
                </div>
              ))}
            </div>
          </section>
        </div>
      ) : (
        <IntegrationsDashboard />
      )}

      {/* Footer */}
      <footer className="footer">
        <p>LeBrickBot v0.1.0 - Autonomous DevOps Platform</p>
        <p>Powered by GitOps • K3s • ArgoCD • FastAPI</p>
      </footer>

      {/* Modals */}
      {showDeployModal && (
        <DeployModal 
          onClose={() => setShowDeployModal(false)}
          onDeploy={handleDeploy}
          loading={loading}
        />
      )}

      {showActionModal && selectedDeployment && (
        <ActionModal
          deployment={selectedDeployment}
          action={selectedAction}
          onClose={() => setShowActionModal(false)}
          onConfirm={executeAction}
          loading={loading}
        />
      )}
    </div>
  )
}

export default App
