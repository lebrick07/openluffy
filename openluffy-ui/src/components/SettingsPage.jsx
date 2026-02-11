import { useState } from 'react'
import { useCustomer } from '../contexts/CustomerContext'
import './SettingsPage.css'

function SettingsPage() {
  const { activeCustomer } = useCustomer()
  const [settings, setSettings] = useState({
    awsAccessKey: '••••••••••••',
    awsSecretKey: '••••••••••••',
    githubToken: 'ghp_••••••••••••',
    slackWebhook: 'https://hooks.slack.com/••••',
    notifyOnDeploy: true,
    notifyOnFailure: true,
    costAlertThreshold: 80,
    theme: 'dark'
  })

  const [showDeleteModal, setShowDeleteModal] = useState(false)
  const [deleteConfirmation, setDeleteConfirmation] = useState('')
  const [deleteInProgress, setDeleteInProgress] = useState(false)
  const [deleteResult, setDeleteResult] = useState(null)

  const handleChange = (key, value) => {
    setSettings({ ...settings, [key]: value })
  }

  const handleDeleteCustomer = async () => {
    if (!activeCustomer) {
      alert('No customer selected')
      return
    }

    if (deleteConfirmation !== activeCustomer.id) {
      alert(`Please type "${activeCustomer.id}" to confirm deletion`)
      return
    }

    setDeleteInProgress(true)
    setDeleteResult(null)

    try {
      const response = await fetch(
        `/customers/${activeCustomer.id}?confirm=${activeCustomer.id}&delete_repo=false`,
        {
          method: 'DELETE'
        }
      )

      const result = await response.json()

      if (result.success) {
        setDeleteResult({
          success: true,
          message: 'Customer deleted successfully',
          details: result.deleted
        })

        // Wait 2 seconds then reload to refresh customer list
        setTimeout(() => {
          window.location.reload()
        }, 2000)
      } else {
        setDeleteResult({
          success: false,
          message: 'Delete failed with errors',
          errors: result.errors
        })
      }
    } catch (error) {
      setDeleteResult({
        success: false,
        message: error.message
      })
    } finally {
      setDeleteInProgress(false)
    }
  }

  return (
    <div className="settings-page">
      <div className="settings-header">
        <h2>⚙️ Settings</h2>
        <p>Configure integrations and preferences</p>
      </div>

      <div className="settings-sections">
        {/* API Keys */}
        <section className="settings-section">
          <h3>🔑 API Keys</h3>
          <div className="settings-grid">
            <div className="setting-item">
              <label>AWS Access Key</label>
              <input type="password" value={settings.awsAccessKey} onChange={(e) => handleChange('awsAccessKey', e.target.value)} />
            </div>
            <div className="setting-item">
              <label>AWS Secret Key</label>
              <input type="password" value={settings.awsSecretKey} onChange={(e) => handleChange('awsSecretKey', e.target.value)} />
            </div>
            <div className="setting-item">
              <label>GitHub Token</label>
              <input type="password" value={settings.githubToken} onChange={(e) => handleChange('githubToken', e.target.value)} />
            </div>
            <div className="setting-item">
              <label>Slack Webhook URL</label>
              <input type="password" value={settings.slackWebhook} onChange={(e) => handleChange('slackWebhook', e.target.value)} />
            </div>
          </div>
        </section>

        {/* Notifications */}
        <section className="settings-section">
          <h3>🔔 Notifications</h3>
          <div className="settings-list">
            <div className="setting-toggle">
              <div className="toggle-info">
                <strong>Deployment notifications</strong>
                <span>Get notified when deployments complete</span>
              </div>
              <label className="toggle-switch">
                <input type="checkbox" checked={settings.notifyOnDeploy} onChange={(e) => handleChange('notifyOnDeploy', e.target.checked)} />
                <span className="toggle-slider"></span>
              </label>
            </div>
            <div className="setting-toggle">
              <div className="toggle-info">
                <strong>Failure alerts</strong>
                <span>Immediate alerts for deployment failures</span>
              </div>
              <label className="toggle-switch">
                <input type="checkbox" checked={settings.notifyOnFailure} onChange={(e) => handleChange('notifyOnFailure', e.target.checked)} />
                <span className="toggle-slider"></span>
              </label>
            </div>
          </div>
        </section>

        {/* Cost Alerts */}
        <section className="settings-section">
          <h3>💰 Cost Management</h3>
          <div className="setting-item">
            <label>Alert threshold ({settings.costAlertThreshold}%)</label>
            <input 
              type="range" 
              min="50" 
              max="100" 
              value={settings.costAlertThreshold} 
              onChange={(e) => handleChange('costAlertThreshold', e.target.value)}
              className="range-slider"
            />
            <div className="range-labels">
              <span>50%</span>
              <span>100%</span>
            </div>
          </div>
        </section>

        {/* Team */}
        <section className="settings-section">
          <h3>👥 Team Members</h3>
          <div className="team-list">
            <div className="team-member">
              <div className="member-avatar">LB</div>
              <div className="member-info">
                <strong>LeBrick</strong>
                <span>Admin</span>
              </div>
              <span className="member-badge">Owner</span>
            </div>
          </div>
          <button className="btn-secondary">+ Invite Member</button>
        </section>

        {/* Actions */}
        <div className="settings-actions">
          <button className="btn-secondary">Cancel</button>
          <button className="btn-primary">Save Changes</button>
        </div>

        {/* Danger Zone */}
        {activeCustomer && (
          <section className="settings-section danger-zone">
            <h3 className="section-title danger-title">⚠️ Danger Zone</h3>
            <div className="danger-zone-content">
              <div className="danger-zone-info">
                <h4>Delete Customer</h4>
                <p>
                  Permanently delete {activeCustomer.name} and destroy all environments. 
                  This will:
                </p>
                <ul>
                  <li>Delete all K8s namespaces (dev, preprod, prod)</li>
                  <li>Remove all ArgoCD applications</li>
                  <li>Archive the GitHub repository (repo won't be deleted)</li>
                  <li>Remove all integrations</li>
                </ul>
                <p className="danger-warning">
                  <strong>This action cannot be undone.</strong>
                </p>
              </div>
              <button 
                className="btn-danger" 
                onClick={() => setShowDeleteModal(true)}
              >
                🗑️ Delete Customer
              </button>
            </div>
          </section>
        )}
      </div>

      {/* Delete Confirmation Modal */}
      {showDeleteModal && activeCustomer && (
        <div className="modal-overlay" onClick={() => setShowDeleteModal(false)}>
          <div className="modal-content" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <h2>⚠️ Confirm Deletion</h2>
              <button className="modal-close" onClick={() => setShowDeleteModal(false)}>×</button>
            </div>

            <div className="modal-body">
              <div className="delete-confirmation-warning">
                <p><strong>You are about to permanently delete:</strong></p>
                <div className="customer-to-delete">
                  <h3>{activeCustomer.name}</h3>
                  <code>{activeCustomer.id}</code>
                </div>

                <p>This will destroy:</p>
                <ul>
                  <li>✗ 3 Kubernetes namespaces ({activeCustomer.id}-dev, -preprod, -prod)</li>
                  <li>✗ 3 ArgoCD applications</li>
                  <li>📦 GitHub repository (archived, not deleted)</li>
                  <li>✗ All integrations and configurations</li>
                </ul>

                <div className="confirmation-input-group">
                  <label>
                    Type <code>{activeCustomer.id}</code> to confirm:
                  </label>
                  <input
                    type="text"
                    value={deleteConfirmation}
                    onChange={(e) => setDeleteConfirmation(e.target.value)}
                    placeholder={activeCustomer.id}
                    className="delete-confirmation-input"
                  />
                </div>

                {deleteResult && (
                  <div className={`delete-result ${deleteResult.success ? 'success' : 'error'}`}>
                    <p><strong>{deleteResult.message}</strong></p>
                    {deleteResult.errors && (
                      <ul>
                        {deleteResult.errors.map((err, idx) => (
                          <li key={idx}>{err}</li>
                        ))}
                      </ul>
                    )}
                    {deleteResult.details && (
                      <details>
                        <summary>Deletion details</summary>
                        <pre>{JSON.stringify(deleteResult.details, null, 2)}</pre>
                      </details>
                    )}
                  </div>
                )}
              </div>
            </div>

            <div className="modal-footer">
              <button 
                className="btn-secondary" 
                onClick={() => {
                  setShowDeleteModal(false)
                  setDeleteConfirmation('')
                  setDeleteResult(null)
                }}
                disabled={deleteInProgress}
              >
                Cancel
              </button>
              <button 
                className="btn-danger" 
                onClick={handleDeleteCustomer}
                disabled={deleteConfirmation !== activeCustomer.id || deleteInProgress}
              >
                {deleteInProgress ? '🗑️ Deleting...' : '🗑️ Delete Customer'}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

export default SettingsPage
