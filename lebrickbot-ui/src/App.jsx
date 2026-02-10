import { useState } from 'react'
import './App.css'
import CustomerDeploymentsView from './components/CustomerDeploymentsView'
import PendingApprovals from './components/PendingApprovals'
import IntegrationsDashboard from './components/IntegrationsDashboard'

function App() {
  const [currentView, setCurrentView] = useState('deployments')

  return (
    <div className="app-container">
      <div className="app-header">
        <div className="header-content">
          <h1>🏴‍☠️ LeBrickBot</h1>
          <p className="header-subtitle">DevOps Automation Platform</p>
        </div>
        <div className="header-nav">
          <button 
            className={`nav-btn ${currentView === 'deployments' ? 'active' : ''}`}
            onClick={() => setCurrentView('deployments')}
          >
            🚀 Deployments
          </button>
          <button 
            className={`nav-btn ${currentView === 'integrations' ? 'active' : ''}`}
            onClick={() => setCurrentView('integrations')}
          >
            🔗 Integrations
          </button>
        </div>
      </div>

      <div className="app-body">
        {currentView === 'deployments' && (
          <>
            <PendingApprovals />
            <CustomerDeploymentsView />
          </>
        )}

        {currentView === 'integrations' && (
          <IntegrationsDashboard />
        )}
      </div>
    </div>
  )
}

export default App
