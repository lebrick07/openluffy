import { useState, useEffect } from 'react'
import './App.css'
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import { CustomerProvider, useCustomer } from './contexts/CustomerContext'
import TopNavbar from './components/TopNavbar'
import Sidebar from './components/Sidebar'
import ApplicationsTable from './components/ApplicationsTable'
import PendingApprovals from './components/PendingApprovals'
import IntegrationsDashboard from './components/IntegrationsDashboard'
import PipelinesView from './components/PipelinesView'
import PipelineConfig from './components/PipelineConfig'
import SecretsVariables from './components/SecretsVariables'
import CreateCustomerWizard from './components/CreateCustomerWizard'
import AIChatPanel from './components/AIChatPanel'
import SettingsPage from './components/SettingsPage'
import ErrorBoundary from './components/ErrorBoundary'
import Login from './components/Login'
import CustomerApplicationDetail from './components/CustomerApplicationDetail'
import { isAuthenticated, getCurrentUser } from './utils/auth'

function AppContent() {
  const { refreshCustomers } = useCustomer()
  const [activeView, setActiveView] = useState('applications')
  const [selectedEnvironment, setSelectedEnvironment] = useState('all')
  const [showCreateModal, setShowCreateModal] = useState(null) // null | 'customer' | 'application' | 'pipeline' | 'integration'
  const [sidebarOpen, setSidebarOpen] = useState(false) // Mobile sidebar state
  const [splitPosition, setSplitPosition] = useState(50) // Split position percentage
  const [isDragging, setIsDragging] = useState(false)
  const [chatCollapsed, setChatCollapsed] = useState(false)

  const handleCreateNew = (type) => {
    setShowCreateModal(type)
  }

  const handleCreated = () => {
    setShowCreateModal(null)
    // Refresh customer list after creation
    refreshCustomers()
  }

  const toggleSidebar = () => {
    setSidebarOpen(!sidebarOpen)
  }

  const closeSidebar = () => {
    setSidebarOpen(false)
  }

  const handleMouseDown = () => {
    setIsDragging(true)
  }

  const handleMouseMove = (e) => {
    if (!isDragging) return
    const windowHeight = window.innerHeight - 52 // Subtract navbar height
    const newPosition = ((e.clientY - 52) / windowHeight) * 100
    if (newPosition >= 20 && newPosition <= 80) {
      setSplitPosition(newPosition)
    }
  }

  const handleMouseUp = () => {
    setIsDragging(false)
  }

  const renderView = () => {
    switch (activeView) {
      case 'applications':
        return (
          <ApplicationsTable 
            selectedEnvironment={selectedEnvironment}
          />
        )
      case 'pipelines':
        return <PipelinesView />
      case 'secrets':
        return <SecretsVariables />
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
        return <SettingsPage />
      default:
        return (
          <ApplicationsTable 
            selectedEnvironment={selectedEnvironment}
          />
        )
    }
  }

  return (
      <div 
        className="app operator-grade" 
        onMouseMove={handleMouseMove}
        onMouseUp={handleMouseUp}
        onMouseLeave={handleMouseUp}
      >
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
          
          {/* Split Screen Layout */}
          <div className="split-container">
            {/* Top: Dashboard */}
            <main className="app-main split-top" style={{ height: chatCollapsed ? 'calc(100% - 40px)' : `${splitPosition}%` }}>
              <div className="app-content">
                {renderView()}
              </div>
            </main>

            {/* Draggable Divider */}
            {!chatCollapsed && (
              <div 
                className={`split-divider ${isDragging ? 'dragging' : ''}`}
                onMouseDown={handleMouseDown}
              >
                <div className="split-divider-handle">
                  <span>⋮⋮⋮</span>
                </div>
              </div>
            )}

            {/* Bottom: Luffy Chat (Collapsible) */}
            <div className="split-bottom" style={{ height: chatCollapsed ? 'auto' : `${100 - splitPosition}%` }}>
              {chatCollapsed ? (
                <div className="chat-collapsed-bar" onClick={() => setChatCollapsed(false)}>
                  <div className="chat-collapsed-left">
                    <span className="chat-collapsed-icon">⚔️</span>
                    <span className="chat-collapsed-text">Luffy – Captain's Deck</span>
                  </div>
                  <button className="chat-expand-btn">▲ Expand</button>
                </div>
              ) : (
                <AIChatPanel onCollapse={() => setChatCollapsed(true)} />
              )}
            </div>
          </div>
        </div>

        {/* Create Modals */}
        {showCreateModal === 'customer' && (
          <CreateCustomerWizard
            onClose={() => setShowCreateModal(null)}
            onSuccess={handleCreated}
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
      </div>
  )
}

function App() {
  const [authenticated, setAuthenticated] = useState(false)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    // Check if user is authenticated on mount
    const checkAuth = () => {
      const isAuth = isAuthenticated()
      setAuthenticated(isAuth)
      setLoading(false)
    }

    checkAuth()
  }, [])

  const handleLoginSuccess = (user) => {
    console.log('Login successful:', user)
    setAuthenticated(true)
  }

  if (loading) {
    return (
      <div style={{
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        height: '100vh',
        background: '#0d1117',
        color: '#c9d1d9'
      }}>
        <div>Loading...</div>
      </div>
    )
  }

  if (!authenticated) {
    return <Login onLoginSuccess={handleLoginSuccess} />
  }

  return (
    <ErrorBoundary>
      <CustomerProvider>
        <BrowserRouter>
          <Routes>
            {/* Main app route */}
            <Route path="/" element={<AppContent />} />
            
            {/* Application detail page route */}
            <Route 
              path="/customers/:customerId/:environment" 
              element={
                <div className="app-container">
                  <TopNavbar currentUser={authenticated ? getCurrentUser() : null} />
                  <CustomerApplicationDetail />
                </div>
              } 
            />
            
            {/* Catch-all redirect */}
            <Route path="*" element={<Navigate to="/" replace />} />
          </Routes>
        </BrowserRouter>
      </CustomerProvider>
    </ErrorBoundary>
  )
}

export default App
