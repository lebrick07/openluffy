import { createContext, useContext, useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { API_BASE_URL } from '../config/api'

const ProjectContext = createContext()

export const useProject = () => {
  const context = useContext(ProjectContext)
  if (!context) {
    throw new Error('useProject must be used within ProjectProvider')
  }
  return context
}

export const ProjectProvider = ({ children }) => {
  const navigate = useNavigate()
  const [projects, setProjects] = useState([])
  const [controlPlane, setControlPlane] = useState(null)
  const [selectedProject, setSelectedProject] = useState('control-plane') // Default to control plane
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    fetchProjects()
  }, [])

  const fetchProjects = async () => {
    try {
      const res = await fetch(`${API_BASE_URL}/api/v1/projects`)
      const data = await res.json()
      
      setControlPlane(data.control_plane)
      setProjects(data.customer_projects || [])
    } catch (err) {
      console.error('Failed to fetch projects:', err)
    } finally {
      setLoading(false)
    }
  }

  const selectProject = (projectId) => {
    setSelectedProject(projectId)
    // Navigate to project's applications page
    navigate(`/projects/${projectId}/applications`)
  }

  const refreshProjects = () => {
    fetchCustomers()
  }

  const value = {
    // Projects data
    projects,
    controlPlane,
    allProjects: controlPlane ? [controlPlane, ...projects] : projects,
    
    // Selection state
    selectedProject,
    selectProject,
    
    // Computed values
    activeProject: selectedProject === 'control-plane' 
      ? controlPlane 
      : projects.find(p => p.id === selectedProject) || null,
    isControlPlane: selectedProject === 'control-plane',
    
    // Actions
    refreshProjects,
    loading
  }

  return (
    <ProjectContext.Provider value={value}>
      {children}
    </ProjectContext.Provider>
  )
}
