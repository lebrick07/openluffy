import { useState, useEffect } from 'react'
import './K8sInsights.css'
import DeploymentDetails from './DeploymentDetails'

function K8sInsights() {
  const [deployments, setDeployments] = useState([])
  const [customers, setCustomers] = useState([])
  const [loading, setLoading] = useState(true)
  const [selectedDeployment, setSelectedDeployment] = useState(null)
  const [filterCustomer, setFilterCustomer] = useState('all')
  const [filterEnvironment, setFilterEnvironment] = useState('all')
  const [filterStatus, setFilterStatus] = useState('all')

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

  const filteredDeployments = deployments.filter(d => {
    if (filterCustomer !== 'all' && d.customer !== filterCustomer) return false
    if (filterEnvironment !== 'all' && d.environment !== filterEnvironment) return false
    if (filterStatus !== 'all' && d.status !== filterStatus) return false
    return true
  })

  const getStatusColor = (status) => {
    if (status === 'running') return 'status-running'
    if (status === 'degraded') return 'status-degraded'
    return 'status-error'
  }

  const getEnvBadgeClass = (env) => {
    if (env === 'dev') return 'env-badge-dev'
    if (env === 'preprod') return 'env-badge-preprod'
    return 'env-badge-prod'
  }

  if (loading) {
    return <div className="k8s-insights loading">Loading Kubernetes data...</div>
  }

  return (
    <div className="k8s-insights">
      <div className="insights-header">
        <div className="header-content">
          <h1>☸️ Kubernetes Insights</h1>
          <p className="header-subtitle">
            Deep cluster visibility · {filteredDeployments.length} deployments
          </p>
        </div>
      </div>

      <div className="insights-filters">
        <div className="filter-group">
          <label>Customer</label>
          <select 
            value={filterCustomer}
            onChange={(e) => setFilterCustomer(e.target.value)}
          >
            <option value="all">All Customers</option>
            {customers.map(c => (
              <option key={c.id} value={c.id}>{c.name}</option>
            ))}
          </select>
        </div>

        <div className="filter-group">
          <label>Environment</label>
          <select 
            value={filterEnvironment}
            onChange={(e) => setFilterEnvironment(e.target.value)}
          >
            <option value="all">All Environments</option>
            <option value="dev">Development</option>
            <option value="preprod">Pre-Production</option>
            <option value="prod">Production</option>
          </select>
        </div>

        <div className="filter-group">
          <label>Status</label>
          <select 
            value={filterStatus}
            onChange={(e) => setFilterStatus(e.target.value)}
          >
            <option value="all">All Statuses</option>
            <option value="running">Running</option>
            <option value="degraded">Degraded</option>
            <option value="error">Error</option>
          </select>
        </div>

        <div className="filter-actions">
          <button 
            className="btn-reset"
            onClick={() => {
              setFilterCustomer('all')
              setFilterEnvironment('all')
              setFilterStatus('all')
            }}
          >
            Reset Filters
          </button>
        </div>
      </div>

      <div className="deployments-grid">
        {filteredDeployments.length === 0 ? (
          <div className="no-results">
            No deployments match the current filters
          </div>
        ) : (
          filteredDeployments.map(deployment => (
            <div 
              key={deployment.id}
              className={`deployment-card ${getStatusColor(deployment.status)}`}
              onClick={() => setSelectedDeployment(deployment.id)}
            >
              <div className="card-header">
                <div className="deployment-name">
                  {deployment.name}
                </div>
                <span className={`env-badge ${getEnvBadgeClass(deployment.environment)}`}>
                  {deployment.environment.toUpperCase()}
                </span>
              </div>

              <div className="card-body">
                <div className="deployment-customer">
                  {customers.find(c => c.id === deployment.customer)?.name || deployment.customer}
                </div>

                <div className="deployment-stats">
                  <div className="stat-item">
                    <span className="stat-label">Pods</span>
                    <span className="stat-value">
                      {deployment.ready}/{deployment.replicas}
                    </span>
                  </div>
                  <div className="stat-item">
                    <span className="stat-label">Status</span>
                    <span className={`stat-badge ${getStatusColor(deployment.status)}`}>
                      {deployment.status}
                    </span>
                  </div>
                </div>

                <div className="deployment-meta">
                  <div className="meta-item">
                    <span className="meta-label">Namespace:</span>
                    <span className="meta-value">{deployment.namespace}</span>
                  </div>
                  <div className="meta-item">
                    <span className="meta-label">Image:</span>
                    <span className="meta-value meta-code">
                      {deployment.image?.split(':')[1] || 'latest'}
                    </span>
                  </div>
                </div>
              </div>

              <div className="card-footer">
                <button className="btn-details">
                  View Details →
                </button>
              </div>
            </div>
          ))
        )}
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

export default K8sInsights
