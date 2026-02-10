import { useState } from 'react'
import './SettingsPage.css'

function SettingsPage() {
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

  const handleChange = (key, value) => {
    setSettings({ ...settings, [key]: value })
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
      </div>
    </div>
  )
}

export default SettingsPage
