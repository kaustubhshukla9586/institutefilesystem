import { Link, useNavigate } from 'react-router-dom'
import RoleBadge from './RoleBadge'
import './Navbar.css'

function getUser() {
  try { return JSON.parse(localStorage.getItem('user')) } catch { return null }
}

export default function Navbar() {
  const navigate = useNavigate()
  const user = getUser()

  function logout() {
    localStorage.removeItem('token')
    localStorage.removeItem('user')
    navigate('/login')
  }

  return (
    <nav className="navbar">
      <div className="navbar-brand">
        <Link to="/chat">UniRAG</Link>
        <span className="navbar-subtitle">University Document Assistant</span>
      </div>
      <div className="navbar-right">
        {user ? (
          <>
            <div className="navbar-user">
              <span className="navbar-email">{user.email}</span>
              <RoleBadge role={user.role} />
            </div>
            {user.role === 'admin' && (
              <Link to="/admin" className="btn btn-outline" style={{ padding: '5px 12px', fontSize: '13px' }}>
                Admin
              </Link>
            )}
            <button className="btn btn-outline" onClick={logout} style={{ padding: '5px 12px', fontSize: '13px' }}>
              Log out
            </button>
          </>
        ) : (
          <div style={{ display: 'flex', gap: '8px' }}>
            <Link to="/login" className="btn btn-outline" style={{ padding: '5px 12px', fontSize: '13px' }}>Log in</Link>
            <Link to="/signup" className="btn btn-primary" style={{ padding: '5px 12px', fontSize: '13px' }}>Sign up</Link>
          </div>
        )}
      </div>
    </nav>
  )
}
