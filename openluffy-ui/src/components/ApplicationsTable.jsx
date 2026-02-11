import { useState, useEffect } from 'react'
import { useCustomer } from '../contexts/CustomerContext'
import './ApplicationsTable.css'
import DeploymentDetails from './DeploymentDetails'

function ApplicationsTable({ selectedEnvironment }) {
  const { activeCustomer } = useCustomer()
  const [deployments, setDeployments] = useState([])
  const [customers, setCustomers] = useState([])
  const [loading, setLoading] = useState(true)
  const [selectedDeployment, setSelectedDeployment] = useState(null)

  useEffect(() => {
    fetchData()
    const interval = setInterval(fetchData, 10000)
    return () => clearInterval(interval)
  }, [])

  const fetchData = async () => {
    try {
      const [deploymentsRes, customersRes] = await Promise.all([
        fetch('/api/deployments'),
        fetch('/api/customers')
      ])
      
      const deploymentsData = await deploymentsRes.json()
      const customersData = await customersRes.json()
      
      setDeployments(deploymentsData.deployments || [])
      setCustomers(customersData.customers || [])
    } catch (error) {
      console.error('Error fetching data:', error)
    } finally {
      setLoading(false)
    }
  }

  const getCustomerName = (customerId) => {
    const customer = customers.find(c => c.id === customerId)
    return customer ? customer.name : customerId
  }

  const getStatusColor = (status) => {
    if (status === 'running') return 'status-ok'
    if (status === 'degraded') return 'status-warning'
    return 'status-error'
  }

  const getPipelineStatus = () => {
    // TODO: Get real pipeline status from API
    return '✓'
  }

  const formatTimestamp = (timestamp) => {
    if (!timestamp) return '—'
    const date = new Date(timestamp)
    const now = new Date()
    const diff = now - date
    const minutes = Math.floor(diff / 60000)
    
    if (minutes < 60) return `${minutes}m ago`
    if (minutes < 1440) return `${Math.floor(minutes / 60)}h ago`
    return `${Math.floor(minutes / 1440)}d ago`
  }

  const handleDeploy = (deployment, e) => {
    e.stopPropagation()
    console.log('Deploy:', deployment)
    alert(`Deploy ${deployment.name} - Backend API coming soon`)
  }

  const handleRollback = (deployment, e) => {
    e.stopPropagation()
    if (confirm(`Rollback ${deployment.name}?`)) {
      console.log('Rollback:', deployment)
      alert('Rollback - Backend API coming soon')
    }
  }

  // Filter deployments
  const filtered = deployments.filter(d => {
    if (activeCustomer && d.customer !== activeCustomer.id) return false
    if (selectedEnvironment !== 'all' && d.environment !== selectedEnvironment) return false
    return true
  })

  if (loading) {
    return <div className="applications-table-loading">Loading applications...</div>
  }

  return (
    <div className="applications-table-container">
      <div className="table-header-bar">
        <h2>Applications</h2>
        <span className="table-count">{filtered.length} deployments</span>
      </div>

      <table className="applications-table">
        <thead>
          <tr>
            <th>Customer</th>
            <th>Application</th>
            <th>Environment</th>
            <th>Status</th>
            <th>Pods</th>
            <th>Image</th>
            <th>Pipeline</th>
            <th>Last Deploy</th>
            <th>Actions</th>
          </tr>
        </thead>
        <tbody>
          {filtered.length === 0 ? (
            <tr>
              <td colSpan="9" className="no-data">
                {!activeCustomer 
                  ? '👤 Select a customer from the dropdown to view their applications'
                  : `No applications found for ${activeCustomer.name}${selectedEnvironment !== 'all' ? ` in ${selectedEnvironment} environment` : ''}`
                }
              </td>
            </tr>
          ) : (
            filtered.map(deployment => (
              <tr 
                key={deployment.id}
                onClick={() => setSelectedDeployment(deployment.id)}
                className="table-row"
              >
                <td className="cell-customer">
                  <span className="customer-name">{getCustomerName(deployment.customer)}</span>
                </td>
                <td className="cell-app">
                  <span className="app-name">{deployment.name}</span>
                </td>
                <td className="cell-env">
                  <span className={`env-badge env-${deployment.environment}`}>
                    {deployment.environment.toUpperCase()}
                  </span>
                </td>
                <td className="cell-status">
                  <span className={`status-badge ${getStatusColor(deployment.status)}`}>
                    {deployment.status}
                  </span>
                </td>
                <td className="cell-pods">
                  <span className={deployment.ready === deployment.replicas ? 'pods-ok' : 'pods-warning'}>
                    {deployment.ready}/{deployment.replicas}
                  </span>
                </td>
                <td className="cell-image">
                  <code className="image-tag">
                    {deployment.image?.split(':')[1] || 'latest'}
                  </code>
                </td>
                <td className="cell-pipeline">
                  <span className="pipeline-icon" title="Pipeline passing">
                    {getPipelineStatus()}
                  </span>
                </td>
                <td className="cell-time">
                  <span className="time-ago">
                    {formatTimestamp(deployment.lastDeploy)}
                  </span>
                </td>
                <td className="cell-actions" onClick={(e) => e.stopPropagation()}>
                  <button 
                    className="action-btn action-view" 
                    onClick={() => setSelectedDeployment(deployment.id)}
                    title="View Details"
                  >
                    View
                  </button>
                  <button 
                    className="action-btn action-deploy"
                    onClick={(e) => handleDeploy(deployment, e)}
                    title="Deploy Latest"
                  >
                    Deploy
                  </button>
                  <button 
                    className="action-btn action-rollback"
                    onClick={(e) => handleRollback(deployment, e)}
                    title="Rollback"
                  >
                    Rollback
                  </button>
                  <button 
                    className="action-btn action-more"
                    onClick={(e) => {
                      e.stopPropagation()
                      alert('More actions - Backend API coming soon')
                    }}
                    title="More Actions"
                  >
                    ⋯
                  </button>
                </td>
              </tr>
            ))
          )}
        </tbody>
      </table>

      {selectedDeployment && (
        <DeploymentDetails 
          deploymentId={selectedDeployment}
          onClose={() => setSelectedDeployment(null)}
        />
      )}
    </div>
  )
}

export default ApplicationsTable
