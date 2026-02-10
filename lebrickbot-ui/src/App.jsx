import { useState } from 'react'
import './App.css'
import { CustomerProvider } from './contexts/CustomerContext'
import TopNavbar from './components/TopNavbar'
import Sidebar from './components/Sidebar'
import ApplicationsTable from './components/ApplicationsTable'
import PendingApprovals from './components/PendingApprovals'
import IntegrationsDashboard from './components/IntegrationsDashboard'
import K8sInsights from './components/K8sInsights'
import PipelinesView from './components/PipelinesView'
import PipelineConfig from './components/PipelineConfig'
import CreateCustomerModal from './components/CreateCustomerModal'
import AIChatPanel from './components/AIChatPanel'

function App() {
  const [activeView, setActiveView] = useState('applications')
  const [selectedEnvironment, setSelectedEnvironment] = useState('all')
  const [showCreateModal, setShowCreateModal] = useState(null) // null | 'customer' | 'application' | 'pipeline' | 'integration'
  const [aiChatOpen, setAIChatOpen] = useState(false)
  const [sidebarOpen, setSidebarOpen] = useState(false) // Mobile sidebar state

  const handleCreateNew = (type) => {
    setShowCreateModal(type)
  }

  const handleCreated = () => {
    setShowCreateModal(null)
  }

  const toggleSidebar = () => {
    setSidebarOpen(!sidebarOpen)
  }

  const closeSidebar = () => {
    setSidebarOpen(false)
  }

  const renderView = () => {
    switch (activeView) {
      case 'applications':
        return (
          <ApplicationsTable 
            selectedEnvironment={selectedEnvironment}
          />
        )
      case 'k8s':
        return <K8sInsights />
      case 'pipelines':
        return <PipelinesView />
      case 'pipeline-config':
        return <PipelineConfig />
      case 'approvals':
        return (
          <div className="view-container">
            <div className="view-header">
              <h1>Production Approvals</h1>
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
              <h1>Monitoring</h1>
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
              <h1>Settings</h1>
              <p className="view-subtitle">Configuration and preferences</p>
            </div>
            <div className="coming-soon">
              <p>🚧 Under Construction</p>
              <p className="coming-soon-detail">Configuration options coming soon...</p>
            </div>
          </div>
        )
      default:
        return (
          <ApplicationsTable 
            selectedEnvironment={selectedEnvironment}
          />
        )
    }
  }

  return (
    <CustomerProvider>
      <div className="app operator-grade">
        <TopNavbar 
          onCreateNew={handleCreateNew}
          selectedEnvironment={selectedEnvironment}
          onEnvironmentChange={setSelectedEnvironment}
          onToggleSidebar={toggleSidebar}
        />
        <div className="app-body">
          <Sidebar 
            activeView={activeView} 
            onViewChange={(view) => {
              setActiveView(view)
              closeSidebar() // Close sidebar on mobile when selecting a view
            }}
            isOpen={sidebarOpen}
          />
          {sidebarOpen && <div className="sidebar-overlay" onClick={closeSidebar}></div>}
          <main className="app-main">
            <div className="app-content">
              {renderView()}
            </div>
          </main>
        </div>

        {/* Create Modals */}
        {showCreateModal === 'customer' && (
          <CreateCustomerModal
            onClose={() => setShowCreateModal(null)}
            onCustomerCreated={handleCreated}
          />
        )}

        {showCreateModal === 'application' && (
          <div className="modal-overlay" onClick={() => setShowCreateModal(null)}>
            <div className="modal-content" onClick={(e) => e.stopPropagation()}>
              <div className="modal-header">
                <h2>📦 Create New Application</h2>
                <button className="modal-close" onClick={() => setShowCreateModal(null)}>×</button>
              </div>
              <div className="modal-body">
                <p>Application creation wizard coming soon...</p>
              </div>
            </div>
          </div>
        )}

        {showCreateModal === 'pipeline' && (
          <div className="modal-overlay" onClick={() => setShowCreateModal(null)}>
            <div className="modal-content" onClick={(e) => e.stopPropagation()}>
              <div className="modal-header">
                <h2>🚀 Create New Pipeline</h2>
                <button className="modal-close" onClick={() => setShowCreateModal(null)}>×</button>
              </div>
              <div className="modal-body">
                <p>Pipeline creation wizard coming soon...</p>
              </div>
            </div>
          </div>
        )}

        {showCreateModal === 'integration' && (
          <div className="modal-overlay" onClick={() => setShowCreateModal(null)}>
            <div className="modal-content" onClick={(e) => e.stopPropagation()}>
              <div className="modal-header">
                <h2>🔌 Create New Integration</h2>
                <button className="modal-close" onClick={() => setShowCreateModal(null)}>×</button>
              </div>
              <div className="modal-body">
                <p>Integration creation wizard coming soon...</p>
              </div>
            </div>
          </div>
        )}

        {/* AI Chat Panel - Always Available */}
        <AIChatPanel 
          isOpen={aiChatOpen}
          onToggle={() => setAIChatOpen(!aiChatOpen)}
        />
      </div>
    </CustomerProvider>
  )
}

export default App
