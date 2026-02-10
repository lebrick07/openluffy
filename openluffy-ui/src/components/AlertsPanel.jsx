import './AlertsPanel.css'

function AlertsPanel({ alerts }) {
  const activeAlerts = alerts || [
    { id: 1, severity: 'critical', service: 'api-gateway', message: 'High error rate (5.2%)', time: '2m ago' },
    { id: 2, severity: 'warning', service: 'database', message: 'CPU usage at 78%', time: '5m ago' },
    { id: 3, severity: 'info', service: 'auth-service', message: 'Deployment completed', time: '10m ago' }
  ]

  const criticalCount = activeAlerts.filter(a => a.severity === 'critical').length
  const warningCount = activeAlerts.filter(a => a.severity === 'warning').length

  return (
    <div className="alerts-panel">
      <div className="alerts-header">
        <h4>🚨 Active Alerts</h4>
        <div className="alerts-summary">
          {criticalCount > 0 && <span className="alert-badge critical">{criticalCount}</span>}
          {warningCount > 0 && <span className="alert-badge warning">{warningCount}</span>}
        </div>
      </div>

      <div className="alerts-list">
        {activeAlerts.map(alert => (
          <div key={alert.id} className={`alert-item alert-${alert.severity}`}>
            <div className="alert-icon">
              {alert.severity === 'critical' ? '🔴' : alert.severity === 'warning' ? '⚠️' : 'ℹ️'}
            </div>
            <div className="alert-content">
              <div className="alert-service">{alert.service}</div>
              <div className="alert-message">{alert.message}</div>
              <div className="alert-time">{alert.time}</div>
            </div>
            <button className="alert-dismiss">✕</button>
          </div>
        ))}
      </div>

      {activeAlerts.length === 0 && (
        <div className="alerts-empty">
          <span className="empty-icon">✅</span>
          <p>All systems operational</p>
        </div>
      )}
    </div>
  )
}

export default AlertsPanel
