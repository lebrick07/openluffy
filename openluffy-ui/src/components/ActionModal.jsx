import './Modal.css'

const actionConfig = {
  scale: {
    icon: '⬆️',
    title: 'Scale Up',
    description: 'Increase the number of replicas',
    color: '#3b82f6',
    confirmText: 'Scale Up'
  },
  restart: {
    icon: '🔄',
    title: 'Restart Service',
    description: 'Rolling restart of all pods',
    color: '#8b5cf6',
    confirmText: 'Restart'
  },
  logs: {
    icon: '📋',
    title: 'View Logs',
    description: 'Open log viewer for this service',
    color: '#06b6d4',
    confirmText: 'View Logs'
  },
  delete: {
    icon: '🗑️',
    title: 'Delete Service',
    description: 'Permanently remove this deployment',
    color: '#ef4444',
    confirmText: 'Delete',
    warning: true
  }
}

function ActionModal({ deployment, action, onClose, onConfirm, loading }) {
  const config = actionConfig[action]
  
  if (!config) return null

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal-content modal-small" onClick={(e) => e.stopPropagation()}>
        <div className="modal-header">
          <h2>{config.icon} {config.title}</h2>
          <button className="modal-close" onClick={onClose}>✕</button>
        </div>
        
        <div className="modal-body">
          <div className="action-target">
            <strong>{deployment.name}</strong>
            {deployment.replicas && (
              <span className="target-meta">
                {deployment.replicas} replica{deployment.replicas > 1 ? 's' : ''}
              </span>
            )}
          </div>
          
          <p className={config.warning ? 'action-description warning' : 'action-description'}>
            {config.description}
          </p>

          {config.warning && (
            <div className="warning-box">
              <strong>⚠️ Warning:</strong> This action cannot be undone.
            </div>
          )}
        </div>

        <div className="modal-actions">
          <button 
            className="btn-secondary" 
            onClick={onClose}
            disabled={loading}
          >
            Cancel
          </button>
          <button 
            className={config.warning ? 'btn-danger' : 'btn-primary'}
            onClick={onConfirm}
            disabled={loading}
            style={{ backgroundColor: loading ? '#6b7280' : config.color }}
          >
            {loading ? '⏳ Processing...' : config.confirmText}
          </button>
        </div>
      </div>
    </div>
  )
}

export default ActionModal
