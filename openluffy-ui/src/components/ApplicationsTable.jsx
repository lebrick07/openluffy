import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { useCustomer } from '../contexts/CustomerContext'
import './ApplicationsTable.css'

function ApplicationsTable({ selectedEnvironment }) {
  const { activeCustomer } = useCustomer()
  const navigate = useNavigate()
  const [deployments, setDeployments] = useState([])
  const [customers, setCustomers] = useState([])
  const [loading, setLoading] = useState(true)
  const [viewMode, setViewMode] = useState('customers') // 'customers' or 'control_plane'

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
      
      // New response structure: { control_plane: [...], customers: [...] }
      const allDeployments = {
        control_plane: deploymentsData.control_plane || [],
        customers: deploymentsData.customers || []
      }
      setDeployments(allDeployments)
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

  const handleDeploy = async (deployment, e) => {
    e.stopPropagation()
    
    if (!confirm(`Deploy latest version of ${deployment.name}?`)) return
    
    setLoading(true)
    try {
      const response = await fetch(
        `/api/v1/deployments/${deployment.id}/deploy`,
        { 
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ revision: 'HEAD' })
        }
      )
      
      if (!response.ok) {
        const error = await response.json()
        throw new Error(error.detail || 'Deploy failed')
      }
      
      const result = await response.json()
      alert(`✓ ${result.message}`)
      fetchData() // Refresh table
    } catch (error) {
      alert(`✗ Deploy failed: ${error.message}`)
    } finally {
      setLoading(false)
    }
  }

  const handleRollback = async (deployment, e) => {
    e.stopPropagation()
    
    if (!confirm(`Rollback ${deployment.name} to previous version?`)) return
    
    setLoading(true)
    try {
      const response = await fetch(
        `/api/v1/deployments/${deployment.id}/rollback`,
        { 
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ to_revision: 'previous' })
        }
      )
      
      if (!response.ok) {
        const error = await response.json()
        throw new Error(error.detail || 'Rollback failed')
      }
      
      const result = await response.json()
      alert(`✓ ${result.message}`)
      fetchData()
    } catch (error) {
      alert(`✗ Rollback failed: ${error.message}`)
    } finally {
      setLoading(false)
    }
  }

  const handleScale = async (deployment, e) => {
    e.stopPropagation()
    
    const replicas = prompt('How many replicas? (0-20)', deployment.replicas || 1)
    if (!replicas || isNaN(replicas)) return
    
    const replicasNum = parseInt(replicas)
    if (replicasNum < 0 || replicasNum > 20) {
      alert('Replicas must be between 0 and 20')
      return
    }
    
    setLoading(true)
    try {
      const response = await fetch(
        `/api/v1/deployments/${deployment.id}/scale`,
        { 
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ replicas: replicasNum })
        }
      )
      
      if (!response.ok) {
        const error = await response.json()
        throw new Error(error.detail || 'Scale failed')
      }
      
      const result = await response.json()
      alert(`✓ ${result.message}`)
      fetchData()
    } catch (error) {
      alert(`✗ Scale failed: ${error.message}`)
    } finally {
      setLoading(false)
    }
  }

  const handleRestart = async (deployment, e) => {
    e.stopPropagation()
    
    if (!confirm(`Restart all pods for ${deployment.name}?`)) return
    
    setLoading(true)
    try {
      const response = await fetch(
        `/api/v1/deployments/${deployment.id}/restart`,
        { 
          method: 'POST',
          headers: { 'Content-Type': 'application/json' }
        }
      )
      
      if (!response.ok) {
        const error = await response.json()
        throw new Error(error.detail || 'Restart failed')
      }
      
      const result = await response.json()
      alert(`✓ ${result.message}`)
      fetchData()
    } catch (error) {
      alert(`✗ Restart failed: ${error.message}`)
    } finally {
      setLoading(false)
    }
  }

  // Get deployments based on view mode
  const currentDeployments = viewMode === 'control_plane' 
    ? (deployments.control_plane || [])
    : (deployments.customers || [])

  // Filter deployments
  const filtered = currentDeployments.filter(d => {
    // In control plane view, don't filter by customer
    if (viewMode === 'customers' && activeCustomer && d.customer !== activeCustomer.id) return false
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
        <div className="table-controls">
          <select 
            className="view-mode-selector"
            value={viewMode}
            onChange={(e) => setViewMode(e.target.value)}
          >
            <option value="customers">View: Customers</option>
            <option value="control_plane">View: Control Plane</option>
          </select>
          <span className="table-count">{filtered.length} deployments</span>
        </div>
      </div>

      <table className="applications-table">
        <thead>
          <tr>
            {viewMode === 'customers' && <th>Customer</th>}
            <th>{viewMode === 'control_plane' ? 'Component' : 'Application'}</th>
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
              <td colSpan={viewMode === 'customers' ? 9 : 8} className="no-data">
                {viewMode === 'control_plane' 
                  ? 'No control plane deployments found'
                  : !activeCustomer 
                    ? '👤 Select a customer from the dropdown to view their applications'
                    : `No applications found for ${activeCustomer.name}${selectedEnvironment !== 'all' ? ` in ${selectedEnvironment} environment` : ''}`
                }
              </td>
            </tr>
          ) : (
            filtered.map(deployment => (
              <tr 
                key={deployment.id}
                onClick={() => navigate(`/customers/${deployment.customer}/${deployment.environment}`)}
                className="table-row"
                style={{ cursor: 'pointer' }}
              >
                {viewMode === 'customers' && (
                  <td className="cell-customer">
                    <span className="customer-name">{getCustomerName(deployment.customer)}</span>
                  </td>
                )}
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
                    onClick={() => navigate(`/customers/${deployment.customer}/${deployment.environment}`)}
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
                      const action = prompt('Choose action:\n1. Scale\n2. Restart\n3. Cancel', '1')
                      if (action === '1') handleScale(deployment, e)
                      else if (action === '2') handleRestart(deployment, e)
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
    </div>
  )
}

export default ApplicationsTable
