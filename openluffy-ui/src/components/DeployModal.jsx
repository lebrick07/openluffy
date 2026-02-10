import { useState } from 'react'
import './Modal.css'

function DeployModal({ onClose, onDeploy, loading }) {
  const [formData, setFormData] = useState({
    name: '',
    image: '',
    replicas: 1,
    port: 8080,
    envVars: ''
  })

  const handleSubmit = (e) => {
    e.preventDefault()
    onDeploy(formData)
  }

  const handleChange = (e) => {
    setFormData({
      ...formData,
      [e.target.name]: e.target.value
    })
  }

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal-content" onClick={(e) => e.stopPropagation()}>
        <div className="modal-header">
          <h2>🚀 Deploy New Service</h2>
          <button className="modal-close" onClick={onClose}>✕</button>
        </div>
        
        <form onSubmit={handleSubmit} className="modal-form">
          <div className="form-group">
            <label htmlFor="name">Service Name *</label>
            <input
              type="text"
              id="name"
              name="name"
              placeholder="my-awesome-app"
              value={formData.name}
              onChange={handleChange}
              required
              disabled={loading}
            />
          </div>

          <div className="form-group">
            <label htmlFor="image">Container Image *</label>
            <input
              type="text"
              id="image"
              name="image"
              placeholder="nginx:latest or ghcr.io/user/app:v1.0"
              value={formData.image}
              onChange={handleChange}
              required
              disabled={loading}
            />
          </div>

          <div className="form-row">
            <div className="form-group">
              <label htmlFor="replicas">Replicas</label>
              <input
                type="number"
                id="replicas"
                name="replicas"
                min="1"
                max="10"
                value={formData.replicas}
                onChange={handleChange}
                disabled={loading}
              />
            </div>

            <div className="form-group">
              <label htmlFor="port">Port</label>
              <input
                type="number"
                id="port"
                name="port"
                min="1"
                max="65535"
                value={formData.port}
                onChange={handleChange}
                disabled={loading}
              />
            </div>
          </div>

          <div className="form-group">
            <label htmlFor="envVars">Environment Variables (optional)</label>
            <textarea
              id="envVars"
              name="envVars"
              placeholder="KEY1=value1&#10;KEY2=value2"
              rows="3"
              value={formData.envVars}
              onChange={handleChange}
              disabled={loading}
            />
          </div>

          <div className="modal-actions">
            <button type="button" className="btn-secondary" onClick={onClose} disabled={loading}>
              Cancel
            </button>
            <button type="submit" className="btn-primary" disabled={loading}>
              {loading ? '⏳ Deploying...' : '🚀 Deploy'}
            </button>
          </div>
        </form>
      </div>
    </div>
  )
}

export default DeployModal
