import { useState, useEffect } from 'react'
import './CustomerDeploymentsView.css'
import DeploymentDetails from './DeploymentDetails'

function CustomerDeploymentsView() {
  const [customers, setCustomers] = useState([])
  const [deployments, setDeployments] = useState([])
  const [loading, setLoading] = useState(true)
  const [selectedDeployment, setSelectedDeployment] = useState(null)

  useEffect(() => {
    fetchData()
    const interval = setInterval(fetchData, 10000)
    return () => clearInterval(interval)
  }, [])

  const fetchData = async () => {
    try {
      const [customersRes, deploymentsRes] = await Promise.all([
        fetch('/api/customers'),
        fetch('/api/deployments')
      ])
      
      const customersData = await customersRes.json()
      const deploymentsData = await deploymentsRes.json()
      
      setCustomers(customersData.customers || [])
      setDeployments(deploymentsData.deployments || [])
    } catch (error) {
      console.error('Error fetching data:', error)
    } finally {
      setLoading(false)
    }
  }

  const getDeploymentsByCustomerAndEnv = (customerId, environment) => {
    return deployments.filter(d => 
      d.customer === customerId && d.environment === environment
    )
  }

  const getStatusColor = (status) => {
    if (status === 'running') return 'status-running'
    if (status === 'degraded') return 'status-degraded'
    return 'status-error'
  }

  const openDeploymentDetails = (deployment) => {
    setSelectedDeployment(deployment.id)
  }

  if (loading) {
    return <div className="customer-deployments-loading">Loading deployments...</div>
  }

  return (
    <div className="customer-deployments-view">
      <div className="view-header">
        <h2>Customer Deployments</h2>
        <p className="view-subtitle">
          {customers.length} customers · {deployments.length} total deployments
        </p>
      </div>

      <div className="customers-grid">
        {customers.map(customer => {
          const devDeploys = getDeploymentsByCustomerAndEnv(customer.id, 'dev')
          const preprodDeploys = getDeploymentsByCustomerAndEnv(customer.id, 'preprod')
          const prodDeploys = getDeploymentsByCustomerAndEnv(customer.id, 'prod')

          return (
            <div key={customer.id} className="customer-card">
              <div className="customer-header">
                <div className="customer-info">
                  <h3>{customer.name}</h3>
                  <span className="customer-stack">{customer.stack}</span>
                </div>
                <div className="customer-overall-status">
                  <span className={`status-indicator ${getStatusColor(customer.overallStatus)}`}>
                    {customer.overallStatus}
                  </span>
                </div>
              </div>

              <div className="environments-row">
                {/* DEV Environment */}
                <div className="environment-column env-dev">
                  <div className="env-header">
                    <span className="env-badge badge-dev">DEV</span>
                    <span className="env-count">{devDeploys.length}</span>
                  </div>
                  <div className="env-deployments">
                    {devDeploys.length === 0 ? (
                      <div className="no-deployments">No deployments</div>
                    ) : (
                      devDeploys.map(deploy => (
                        <div 
                          key={deploy.id} 
                          className={`deployment-item ${getStatusColor(deploy.status)}`}
                          onClick={() => openDeploymentDetails(deploy)}
                        >
                          <div className="deploy-name">{deploy.name}</div>
                          <div className="deploy-stats">
                            <span className="stat-replicas">
                              {deploy.ready}/{deploy.replicas} pods
                            </span>
                            <span className={`stat-status ${getStatusColor(deploy.status)}`}>
                              {deploy.status}
                            </span>
                          </div>
                          <div className="deploy-image">{deploy.image?.split(':')[1] || 'latest'}</div>
                        </div>
                      ))
                    )}
                  </div>
                </div>

                {/* PREPROD Environment */}
                <div className="environment-column env-preprod">
                  <div className="env-header">
                    <span className="env-badge badge-preprod">PREPROD</span>
                    <span className="env-count">{preprodDeploys.length}</span>
                  </div>
                  <div className="env-deployments">
                    {preprodDeploys.length === 0 ? (
                      <div className="no-deployments">No deployments</div>
                    ) : (
                      preprodDeploys.map(deploy => (
                        <div 
                          key={deploy.id} 
                          className={`deployment-item ${getStatusColor(deploy.status)}`}
                          onClick={() => openDeploymentDetails(deploy)}
                        >
                          <div className="deploy-name">{deploy.name}</div>
                          <div className="deploy-stats">
                            <span className="stat-replicas">
                              {deploy.ready}/{deploy.replicas} pods
                            </span>
                            <span className={`stat-status ${getStatusColor(deploy.status)}`}>
                              {deploy.status}
                            </span>
                          </div>
                          <div className="deploy-image">{deploy.image?.split(':')[1] || 'latest'}</div>
                        </div>
                      ))
                    )}
                  </div>
                </div>

                {/* PROD Environment */}
                <div className="environment-column env-prod">
                  <div className="env-header">
                    <span className="env-badge badge-prod">PROD</span>
                    <span className="env-count">{prodDeploys.length}</span>
                  </div>
                  <div className="env-deployments">
                    {prodDeploys.length === 0 ? (
                      <div className="no-deployments">No deployments</div>
                    ) : (
                      prodDeploys.map(deploy => (
                        <div 
                          key={deploy.id} 
                          className={`deployment-item ${getStatusColor(deploy.status)}`}
                          onClick={() => openDeploymentDetails(deploy)}
                        >
                          <div className="deploy-name">{deploy.name}</div>
                          <div className="deploy-stats">
                            <span className="stat-replicas">
                              {deploy.ready}/{deploy.replicas} pods
                            </span>
                            <span className={`stat-status ${getStatusColor(deploy.status)}`}>
                              {deploy.status}
                            </span>
                          </div>
                          <div className="deploy-image">{deploy.image?.split(':')[1] || 'latest'}</div>
                        </div>
                      ))
                    )}
                  </div>
                </div>
              </div>

              <div className="customer-footer">
                <a 
                  href={`https://github.com/lebrick07/${customer.app}`}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="link-github"
                >
                  📁 View Repository
                </a>
                <a 
                  href={`http://argocd.local/applications?search=${customer.id}`}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="link-argocd"
                >
                  🐙 ArgoCD Apps
                </a>
              </div>
            </div>
          )
        })}
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

export default CustomerDeploymentsView
