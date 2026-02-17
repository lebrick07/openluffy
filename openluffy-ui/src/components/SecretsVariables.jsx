import { useState } from 'react'
import { useCustomer } from '../contexts/CustomerContext'
import './SecretsVariables.css'

function SecretsVariables() {
  const { activeCustomer, customers } = useCustomer()
  const [selectedCustomer, setSelectedCustomer] = useState(null)
  
  const [secrets, setSecrets] = useState([
    { id: 1, key: 'AWS_ACCESS_KEY', value: '••••••••••••', type: 'secret', scope: 'all', customer: null },
    { id: 2, key: 'AWS_SECRET_KEY', value: '••••••••••••', type: 'secret', scope: 'all', customer: null },
    { id: 3, key: 'GITHUB_TOKEN', value: 'ghp_••••••••••••', type: 'secret', scope: 'all', customer: null },
    { id: 4, key: 'SLACK_WEBHOOK_URL', value: 'https://hooks.slack.com/••••', type: 'secret', scope: 'prod', customer: 'openluffy' },
    { id: 5, key: 'DATABASE_URL', value: 'postgres://user:••••@host/db', type: 'secret', scope: 'all', customer: 'openluffy' },
    { id: 6, key: 'API_BASE_URL', value: 'https://api.example.com', type: 'variable', scope: 'all', customer: 'global-movers' },
    { id: 7, key: 'LOG_LEVEL', value: 'info', type: 'variable', scope: 'all', customer: 'global-movers' },
    { id: 8, key: 'MAX_RETRIES', value: '3', type: 'variable', scope: 'dev', customer: null }
  ])

  const [showAddModal, setShowAddModal] = useState(false)
  const [showEditModal, setShowEditModal] = useState(false)
  const [selectedItem, setSelectedItem] = useState(null)
  const [filterType, setFilterType] = useState('all')
  
  const [newItem, setNewItem] = useState({
    key: '',
    value: '',
    type: 'secret',
    scope: 'all',
    customer: null
  })

  // Filter by selected customer (or show global if no customer selected)
  const customerFilteredSecrets = selectedCustomer === 'global'
    ? secrets.filter(s => s.customer === null)
    : selectedCustomer
      ? secrets.filter(s => s.customer === selectedCustomer || s.customer === null)
      : secrets.filter(s => s.customer === null)

  const filteredSecrets = filterType === 'all' 
    ? customerFilteredSecrets 
    : customerFilteredSecrets.filter(s => s.type === filterType)

  const handleAdd = () => {
    const newEntry = {
      id: Date.now(),
      ...newItem,
      customer: selectedCustomer === 'global' ? null : selectedCustomer
    }
    setSecrets([...secrets, newEntry])
    setShowAddModal(false)
    setNewItem({ key: '', value: '', type: 'secret', scope: 'all', customer: null })
  }

  const handleEdit = () => {
    setSecrets(secrets.map(s => s.id === selectedItem.id ? selectedItem : s))
    setShowEditModal(false)
    setSelectedItem(null)
  }

  const handleDelete = (id) => {
    if (!confirm('Are you sure you want to delete this item?')) return
    setSecrets(secrets.filter(s => s.id !== id))
  }

  return (
    <div className="secrets-variables">
      <div className="section-header">
        <div>
          <h3>🔐 Secrets & Variables</h3>
          <p>Manage environment secrets and configuration variables per customer</p>
        </div>
        <button className="btn-primary" onClick={() => setShowAddModal(true)}>
          + Add Secret/Variable
        </button>
      </div>

      <div className="customer-selector">
        <label>Customer:</label>
        <select 
          value={selectedCustomer || 'global'}
          onChange={(e) => setSelectedCustomer(e.target.value === 'global' ? 'global' : e.target.value)}
        >
          <option value="global">🌍 Global (Platform-wide)</option>
          {customers.map(c => (
            <option key={c.id} value={c.id}>{c.name}</option>
          ))}
        </select>
      </div>

      <div className="filter-tabs">
        <button 
          className={`tab ${filterType === 'all' ? 'active' : ''}`}
          onClick={() => setFilterType('all')}
        >
          All ({secrets.length})
        </button>
        <button 
          className={`tab ${filterType === 'secret' ? 'active' : ''}`}
          onClick={() => setFilterType('secret')}
        >
          Secrets ({secrets.filter(s => s.type === 'secret').length})
        </button>
        <button 
          className={`tab ${filterType === 'variable' ? 'active' : ''}`}
          onClick={() => setFilterType('variable')}
        >
          Variables ({secrets.filter(s => s.type === 'variable').length})
        </button>
      </div>

      <div className="secrets-list">
        {filteredSecrets.map(item => (
          <div key={item.id} className="secret-item">
            <div className="secret-info">
              <div className="secret-header">
                <span className="secret-key">{item.key}</span>
                <div className="secret-badges">
                  <span className={`type-badge type-${item.type}`}>
                    {item.type === 'secret' ? '🔒' : '📝'} {item.type}
                  </span>
                  <span className={`scope-badge scope-${item.scope}`}>
                    {item.scope}
                  </span>
                </div>
              </div>
              <div className="secret-value">{item.value}</div>
            </div>
            <div className="secret-actions">
              <button 
                className="btn-icon" 
                onClick={() => {
                  setSelectedItem(item)
                  setShowEditModal(true)
                }}
                title="Edit"
              >
                ✏️
              </button>
              <button 
                className="btn-icon btn-danger" 
                onClick={() => handleDelete(item.id)}
                title="Delete"
              >
                🗑️
              </button>
            </div>
          </div>
        ))}
        
        {filteredSecrets.length === 0 && (
          <div className="empty-state">
            <div className="empty-icon">🔐</div>
            <p>No {filterType === 'all' ? 'items' : filterType + 's'} yet</p>
            <button className="btn-secondary" onClick={() => setShowAddModal(true)}>
              Add {filterType === 'all' ? 'Secret or Variable' : filterType}
            </button>
          </div>
        )}
      </div>

      {/* Add Modal */}
      {showAddModal && (
        <div className="modal-overlay" onClick={() => setShowAddModal(false)}>
          <div className="modal-content" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <h3>Add Secret/Variable</h3>
              <button className="modal-close" onClick={() => setShowAddModal(false)}>×</button>
            </div>
            <div className="modal-body">
              <div className="form-group">
                <label>Type *</label>
                <select 
                  value={newItem.type}
                  onChange={(e) => setNewItem({ ...newItem, type: e.target.value })}
                >
                  <option value="secret">Secret (encrypted)</option>
                  <option value="variable">Variable (plain text)</option>
                </select>
              </div>
              <div className="form-group">
                <label>Key Name *</label>
                <input 
                  type="text" 
                  value={newItem.key}
                  onChange={(e) => setNewItem({ ...newItem, key: e.target.value.toUpperCase().replace(/[^A-Z0-9_]/g, '_') })}
                  placeholder="AWS_ACCESS_KEY"
                />
                <small>Use UPPER_SNAKE_CASE for environment variables</small>
              </div>
              <div className="form-group">
                <label>Value *</label>
                <textarea 
                  value={newItem.value}
                  onChange={(e) => setNewItem({ ...newItem, value: e.target.value })}
                  placeholder={newItem.type === 'secret' ? 'Enter secret value' : 'Enter variable value'}
                  rows="3"
                />
              </div>
              <div className="form-group">
                <label>Scope *</label>
                <select 
                  value={newItem.scope}
                  onChange={(e) => setNewItem({ ...newItem, scope: e.target.value })}
                >
                  <option value="all">All Environments</option>
                  <option value="dev">Development Only</option>
                  <option value="preprod">Pre-Production Only</option>
                  <option value="prod">Production Only</option>
                </select>
              </div>
            </div>
            <div className="modal-footer">
              <button className="btn-secondary" onClick={() => setShowAddModal(false)}>
                Cancel
              </button>
              <button className="btn-primary" onClick={handleAdd}>
                Add {newItem.type === 'secret' ? 'Secret' : 'Variable'}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Edit Modal */}
      {showEditModal && selectedItem && (
        <div className="modal-overlay" onClick={() => setShowEditModal(false)}>
          <div className="modal-content" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <h3>Edit {selectedItem.type === 'secret' ? 'Secret' : 'Variable'}</h3>
              <button className="modal-close" onClick={() => setShowEditModal(false)}>×</button>
            </div>
            <div className="modal-body">
              <div className="form-group">
                <label>Key Name</label>
                <input 
                  type="text" 
                  value={selectedItem.key}
                  onChange={(e) => setSelectedItem({ ...selectedItem, key: e.target.value })}
                  disabled
                />
                <small>Key names cannot be changed</small>
              </div>
              <div className="form-group">
                <label>Value</label>
                <textarea 
                  value={selectedItem.value}
                  onChange={(e) => setSelectedItem({ ...selectedItem, value: e.target.value })}
                  rows="3"
                />
              </div>
              <div className="form-group">
                <label>Scope</label>
                <select 
                  value={selectedItem.scope}
                  onChange={(e) => setSelectedItem({ ...selectedItem, scope: e.target.value })}
                >
                  <option value="all">All Environments</option>
                  <option value="dev">Development Only</option>
                  <option value="preprod">Pre-Production Only</option>
                  <option value="prod">Production Only</option>
                </select>
              </div>
            </div>
            <div className="modal-footer">
              <button className="btn-secondary" onClick={() => setShowEditModal(false)}>
                Cancel
              </button>
              <button className="btn-primary" onClick={handleEdit}>
                Save Changes
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

export default SecretsVariables
