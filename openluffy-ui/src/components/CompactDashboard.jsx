import { useState, useEffect } from 'react'
import './CompactDashboard.css'
import DeploymentDetails from './DeploymentDetails'

function CompactDashboard({ selectedCustomer }) {
  const [deployments, setDeployments] = useState([])
  const [customers, setCustomers] = useState([])
  const [pipelines, setPipelines] = useState([])
  const [loading, setLoading] = useState(true)
  const [selectedDeployment, setSelectedDeployment] = useState(null)

  useEffect(() => {
    fetchData()
    const interval = setInterval(fetchData, 30000)
    return () => clearInterval(interval)
  }, [])

  const fetchData = async () => {
    try {
      const [deploymentsRes, customersRes, pipelinesRes] = await Promise.all([
        fetch('/api/deployments'),
        fetch('/customers'),
        fetch('/api/pipelines/status')
      ])
      
      const deploymentsData = await deploymentsRes.json()
      const customersData = await customersRes.json()
      const pipelinesData = await pipelinesRes.json()
      
      setDeployments(deploymentsData.deployments || [])
      setCustomers(customersData.customers || [])
      setPipelines(pipelinesData.pipelines || [])
    } catch (error) {
      console.error('Error fetching data:', error)
    } finally {
      setLoading(false)
    }
  }

  const filteredDeployments = selectedCustomer
    ? deployments.filter(d => d.customer === selectedCustomer)
    : deployments

  const getCustomerName = (customerId) => {
    const customer = customers.find(c => c.id === customerId)
    return customer ? customer.name : customerId
  }

  const getPipelineStatus = (customerId) => {
    const pipeline = pipelines.find(p => p.customer_id === customerId)
    if (!pipeline) return { icon: '○', color: '#6b7280', status: 'unknown' }
    
    if (pipeline.status === 'completed') {
      if (pipeline.conclusion === 'success') {
        return { icon: '✓', color: '#16a34a', status: 'passing' }
      }
      return { icon: '✗', color: '#dc2626', status: 'failing' }
    }
    if (pipeline.status === 'in_progress') {
      return { icon: '⟳', color: '#f59e0b', status: 'running' }
    }
    return { icon: '○', color: '#6b7280', status: 'unknown' }
  }

  const getStatusBadge = (status) => {
    if (status === 'running') return { bg: '#dcfce7', text: '#16a34a', label: 'Running' }
    if (status === 'degraded') return { bg: '#fef3c7', text: '#d97706', label: 'Degraded' }
    return { bg: '#fee2e2', text: '#dc2626', label: 'Error' }
  }

  const getEnvBadge = (env) => {
    if (env === 'dev') return { bg: '#dbeafe', text: '#1e40af' }
    if (env === 'preprod') return { bg: '#fed7aa', text: '#c2410c' }
    return { bg: '#e9d5ff', text: '#7e22ce' }
  }

  if (loading) {
    return <div className="compact-dashboard loading">Loading...</div>
  }

  return (
    <div className="compact-dashboard">
      <div className="table-container">
        <table className="deployments-table">
          <thead>
            <tr>
              <th>Customer</th>
              <th>Application</th>
              <th>Environment</th>
              <th>Status</th>
              <th>Pods</th>
              <th>Image</th>
              <th>Pipeline</th>
              <th>Actions</th>
            </tr>
          </thead>
          <tbody>
            {filteredDeployments.length === 0 ? (
              <tr>
                <td colSpan="8" className="no-data">No deployments found</td>
              </tr>
            ) : (
              filteredDeployments.map(deployment => {
                const statusBadge = getStatusBadge(deployment.status)
                const envBadge = getEnvBadge(deployment.environment)
                const pipeline = getPipelineStatus(deployment.customer)
                
                return (
                  <tr key={deployment.id} className="deployment-row">
                    <td className="cell-customer">
                      <strong>{getCustomerName(deployment.customer)}</strong>
                    </td>
                    <td className="cell-app">{deployment.name}</td>
                    <td className="cell-env">
                      <span 
                        className="env-badge"
                        style={{ 
                          background: envBadge.bg, 
                          color: envBadge.text 
                        }}
                      >
                        {deployment.environment.toUpperCase()}
                      </span>
                    </td>
                    <td className="cell-status">
                      <span 
                        className="status-badge"
                        style={{ 
                          background: statusBadge.bg, 
                          color: statusBadge.text 
                        }}
                      >
                        {statusBadge.label}
                      </span>
                    </td>
                    <td className="cell-pods">
                      <span className={deployment.ready === deployment.replicas ? 'pods-healthy' : 'pods-warning'}>
                        {deployment.ready ?? 0}/{deployment.replicas ?? 0}
                      </span>
                    </td>
                    <td className="cell-image">
                      <code>{deployment.image?.split(':')[1] || 'latest'}</code>
                    </td>
                    <td className="cell-pipeline">
                      <span 
                        className="pipeline-status"
                        style={{ color: pipeline.color }}
                        title={pipeline.status}
                      >
                        {pipeline.icon}
                      </span>
                    </td>
                    <td className="cell-actions">
                      <button 
                        className="btn-action"
                        onClick={() => setSelectedDeployment(deployment.id)}
                      >
                        Details
                      </button>
                    </td>
                  </tr>
                )
              })
            )}
          </tbody>
        </table>
      </div>

      {selectedDeployment && (
        <DeploymentDetails 
          deploymentId={selectedDeployment}
          onClose={() => setSelectedDeployment(null)}
        />
      )}
    </div>
  )
}

export default CompactDashboard
