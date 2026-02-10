import { useState } from 'react'
import './App.css'
import TopNavbar from './components/TopNavbar'
import Sidebar from './components/Sidebar'
import CustomerSelector from './components/CustomerSelector'
import CompactDashboard from './components/CompactDashboard'
import CustomerDeploymentsView from './components/CustomerDeploymentsView'
import PendingApprovals from './components/PendingApprovals'
import IntegrationsDashboard from './components/IntegrationsDashboard'
import K8sInsights from './components/K8sInsights'
import PipelinesView from './components/PipelinesView'
import PipelineConfig from './components/PipelineConfig'

function App() {
  const [activeView, setActiveView] = useState('dashboard')
  const [selectedCustomer, setSelectedCustomer] = useState(null)

  const renderView = () => {
    switch (activeView) {
      case 'dashboard':
        return <CompactDashboard selectedCustomer={selectedCustomer} />
      case 'k8s':
        return <K8sInsights selectedCustomer={selectedCustomer} />
      case 'pipelines':
        return <PipelinesView />
      case 'pipeline-config':
        return <PipelineConfig />
      case 'approvals':
        return (
          <div className="view-container">
            <div className="view-header">
              <h1>✅ Production Approvals</h1>
              <p className="view-subtitle">Preprod → Prod promotion workflow</p>
            </div>
            <PendingApprovals />
          </div>
        )
      case 'integrations':
        return <IntegrationsDashboard />
      case 'monitoring':
        return (
          <div className="view-container">
            <div className="view-header">
              <h1>📈 Monitoring</h1>
              <p className="view-subtitle">Metrics, logs, and alerts</p>
            </div>
            <div className="coming-soon">
              <p>🚧 Under Construction</p>
              <p className="coming-soon-detail">Prometheus, Grafana, and log aggregation coming soon...</p>
            </div>
          </div>
        )
      case 'settings':
        return (
          <div className="view-container">
            <div className="view-header">
              <h1>⚙️ Settings</h1>
              <p className="view-subtitle">Configuration and preferences</p>
            </div>
            <div className="coming-soon">
              <p>🚧 Under Construction</p>
              <p className="coming-soon-detail">Configuration options coming soon...</p>
            </div>
          </div>
        )
      default:
        return <CustomerDeploymentsView />
    }
  }

  return (
    <div className="app">
      <TopNavbar 
        selectedCustomer={selectedCustomer}
        onCustomerChange={setSelectedCustomer}
      />
      <div className="app-body">
        <Sidebar activeView={activeView} onViewChange={setActiveView} />
        <main className="app-main">
          <div className="app-content">
            {renderView()}
          </div>
        </main>
      </div>
    </div>
  )
}

export default App
