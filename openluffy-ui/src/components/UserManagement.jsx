import { useState, useEffect } from 'react'
import { API_BASE_URL } from '../config/api'
import './UserManagement.css'

function UserManagement() {
  const [users, setUsers] = useState([])
  const [loading, setLoading] = useState(true)
  const [showAddModal, setShowAddModal] = useState(false)
  const [showEditModal, setShowEditModal] = useState(false)
  const [selectedUser, setSelectedUser] = useState(null)
  
  const [newUser, setNewUser] = useState({
    email: '',
    password: '',
    first_name: '',
    last_name: '',
    role: 'viewer'
  })

  useEffect(() => {
    fetchUsers()
  }, [])

  const fetchUsers = async () => {
    try {
      const token = localStorage.getItem('authToken')
      const response = await fetch(`${API_BASE_URL}/v1/auth/users`, {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      })
      
      if (!response.ok) throw new Error('Failed to fetch users')
      
      const data = await response.json()
      setUsers(data.users || [])
    } catch (err) {
      console.error('Failed to fetch users:', err)
    } finally {
      setLoading(false)
    }
  }

  const handleAddUser = async () => {
    try {
      const token = localStorage.getItem('authToken')
      const response = await fetch(`${API_BASE_URL}/v1/auth/users`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(newUser)
      })
      
      if (!response.ok) {
        const error = await response.json()
        throw new Error(error.detail || 'Failed to create user')
      }
      
      setShowAddModal(false)
      setNewUser({ email: '', password: '', first_name: '', last_name: '', role: 'viewer' })
      fetchUsers()
    } catch (err) {
      alert(err.message)
    }
  }

  const handleUpdateUser = async () => {
    try {
      const token = localStorage.getItem('authToken')
      const response = await fetch(`${API_BASE_URL}/v1/auth/users/${selectedUser.id}`, {
        method: 'PATCH',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          first_name: selectedUser.first_name,
          last_name: selectedUser.last_name,
          role: selectedUser.role,
          is_active: selectedUser.is_active
        })
      })
      
      if (!response.ok) throw new Error('Failed to update user')
      
      setShowEditModal(false)
      setSelectedUser(null)
      fetchUsers()
    } catch (err) {
      alert(err.message)
    }
  }

  const handleDeleteUser = async (userId, email) => {
    if (!confirm(`Are you sure you want to delete user ${email}?`)) return
    
    try {
      const token = localStorage.getItem('authToken')
      const response = await fetch(`${API_BASE_URL}/v1/auth/users/${userId}`, {
        method: 'DELETE',
        headers: {
          'Authorization': `Bearer ${token}`
        }
      })
      
      if (!response.ok) throw new Error('Failed to delete user')
      
      fetchUsers()
    } catch (err) {
      alert(err.message)
    }
  }

  if (loading) {
    return <div className="loading">Loading users...</div>
  }

  return (
    <div className="user-management">
      <div className="section-header">
        <div>
          <h3>👥 User Management</h3>
          <p>Manage user accounts and permissions</p>
        </div>
        <button className="btn-primary" onClick={() => setShowAddModal(true)}>
          + Add User
        </button>
      </div>

      <div className="users-table">
        <table>
          <thead>
            <tr>
              <th>User</th>
              <th>Email</th>
              <th>Role</th>
              <th>Status</th>
              <th>Last Login</th>
              <th>Actions</th>
            </tr>
          </thead>
          <tbody>
            {users.map(user => (
              <tr key={user.id}>
                <td>
                  <div className="user-cell">
                    <div className="user-avatar">{user.first_name?.[0] || user.username?.[0] || 'U'}</div>
                    <div>
                      <div className="user-name">{user.first_name} {user.last_name}</div>
                      <div className="user-username">@{user.username}</div>
                    </div>
                  </div>
                </td>
                <td>{user.email}</td>
                <td>
                  <span className={`role-badge role-${user.role}`}>
                    {user.role}
                  </span>
                </td>
                <td>
                  <span className={`status-badge status-${user.is_active ? 'active' : 'inactive'}`}>
                    {user.is_active ? 'Active' : 'Disabled'}
                  </span>
                </td>
                <td>
                  {user.last_login ? new Date(user.last_login).toLocaleDateString() : 'Never'}
                </td>
                <td>
                  <div className="action-buttons">
                    <button 
                      className="btn-icon" 
                      onClick={() => {
                        setSelectedUser(user)
                        setShowEditModal(true)
                      }}
                      title="Edit user"
                    >
                      ✏️
                    </button>
                    <button 
                      className="btn-icon btn-danger" 
                      onClick={() => handleDeleteUser(user.id, user.email)}
                      title="Delete user"
                    >
                      🗑️
                    </button>
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* Add User Modal */}
      {showAddModal && (
        <div className="modal-overlay" onClick={() => setShowAddModal(false)}>
          <div className="modal-content" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <h3>Add New User</h3>
              <button className="modal-close" onClick={() => setShowAddModal(false)}>×</button>
            </div>
            <div className="modal-body">
              <div className="form-group">
                <label>Email *</label>
                <input 
                  type="email" 
                  value={newUser.email}
                  onChange={(e) => setNewUser({ ...newUser, email: e.target.value })}
                  placeholder="user@example.com"
                />
              </div>
              <div className="form-group">
                <label>Password *</label>
                <input 
                  type="password" 
                  value={newUser.password}
                  onChange={(e) => setNewUser({ ...newUser, password: e.target.value })}
                  placeholder="Minimum 8 characters"
                />
              </div>
              <div className="form-row">
                <div className="form-group">
                  <label>First Name *</label>
                  <input 
                    type="text" 
                    value={newUser.first_name}
                    onChange={(e) => setNewUser({ ...newUser, first_name: e.target.value })}
                  />
                </div>
                <div className="form-group">
                  <label>Last Name *</label>
                  <input 
                    type="text" 
                    value={newUser.last_name}
                    onChange={(e) => setNewUser({ ...newUser, last_name: e.target.value })}
                  />
                </div>
              </div>
              <div className="form-group">
                <label>Role *</label>
                <select 
                  value={newUser.role}
                  onChange={(e) => setNewUser({ ...newUser, role: e.target.value })}
                >
                  <option value="viewer">Viewer</option>
                  <option value="admin">Admin</option>
                </select>
              </div>
            </div>
            <div className="modal-footer">
              <button className="btn-secondary" onClick={() => setShowAddModal(false)}>
                Cancel
              </button>
              <button className="btn-primary" onClick={handleAddUser}>
                Create User
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Edit User Modal */}
      {showEditModal && selectedUser && (
        <div className="modal-overlay" onClick={() => setShowEditModal(false)}>
          <div className="modal-content" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <h3>Edit User</h3>
              <button className="modal-close" onClick={() => setShowEditModal(false)}>×</button>
            </div>
            <div className="modal-body">
              <div className="form-row">
                <div className="form-group">
                  <label>First Name</label>
                  <input 
                    type="text" 
                    value={selectedUser.first_name}
                    onChange={(e) => setSelectedUser({ ...selectedUser, first_name: e.target.value })}
                  />
                </div>
                <div className="form-group">
                  <label>Last Name</label>
                  <input 
                    type="text" 
                    value={selectedUser.last_name}
                    onChange={(e) => setSelectedUser({ ...selectedUser, last_name: e.target.value })}
                  />
                </div>
              </div>
              <div className="form-group">
                <label>Role</label>
                <select 
                  value={selectedUser.role}
                  onChange={(e) => setSelectedUser({ ...selectedUser, role: e.target.value })}
                >
                  <option value="viewer">Viewer</option>
                  <option value="admin">Admin</option>
                </select>
              </div>
              <div className="form-group">
                <label className="checkbox-label">
                  <input 
                    type="checkbox" 
                    checked={selectedUser.is_active}
                    onChange={(e) => setSelectedUser({ ...selectedUser, is_active: e.target.checked })}
                  />
                  <span>Active</span>
                </label>
              </div>
            </div>
            <div className="modal-footer">
              <button className="btn-secondary" onClick={() => setShowEditModal(false)}>
                Cancel
              </button>
              <button className="btn-primary" onClick={handleUpdateUser}>
                Save Changes
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

export default UserManagement
