import { useState, useEffect } from 'react'
import api from '../api/client'
import RoleBadge from '../components/RoleBadge'
import './AdminDashboard.css'

function formatDate(ts) {
  return new Date(ts).toLocaleString('en-IN', { dateStyle: 'medium', timeStyle: 'short' })
}

export default function AdminDashboard() {
  const [tab, setTab] = useState('audit')
  const [auditLog, setAuditLog] = useState([])
  const [documents, setDocuments] = useState([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [expandedRow, setExpandedRow] = useState(null)

  useEffect(() => {
    loadData()
  }, [tab])

  async function loadData() {
    setLoading(true)
    setError('')
    try {
      if (tab === 'audit') {
        const res = await api.get('/admin/audit-log')
        setAuditLog(res.data)
      } else {
        const res = await api.get('/admin/documents')
        setDocuments(res.data)
      }
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to load data')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="admin-page">
      <div className="admin-container">
        <div className="admin-header">
          <h1>Admin Dashboard</h1>
          <RoleBadge role="admin" />
        </div>

        <div className="tab-bar">
          <button
            className={`tab-btn ${tab === 'audit' ? 'active' : ''}`}
            onClick={() => setTab('audit')}
          >
            Audit Log {auditLog.length > 0 && <span className="tab-count">{auditLog.length}</span>}
          </button>
          <button
            className={`tab-btn ${tab === 'docs' ? 'active' : ''}`}
            onClick={() => setTab('docs')}
          >
            Documents {documents.length > 0 && <span className="tab-count">{documents.length}</span>}
          </button>
          <button className="btn btn-outline refresh-btn" onClick={loadData} disabled={loading}>
            {loading ? '…' : 'Refresh'}
          </button>
        </div>

        {error && <div className="error-msg" style={{ marginBottom: 16 }}>{error}</div>}

        {loading && <div className="admin-loading">Loading…</div>}

        {!loading && tab === 'audit' && (
          <div className="table-wrap">
            {auditLog.length === 0 ? (
              <p className="empty-state">No queries logged yet.</p>
            ) : (
              <table className="admin-table">
                <thead>
                  <tr>
                    <th>#</th>
                    <th>User</th>
                    <th>Role</th>
                    <th>Question</th>
                    <th>Docs retrieved</th>
                    <th>Timestamp</th>
                  </tr>
                </thead>
                <tbody>
                  {auditLog.map(log => (
                    <>
                      <tr
                        key={log.id}
                        className={`log-row ${expandedRow === log.id ? 'expanded' : ''}`}
                        onClick={() => setExpandedRow(expandedRow === log.id ? null : log.id)}
                      >
                        <td className="col-id">{log.id}</td>
                        <td className="col-email">{log.user_email}</td>
                        <td><RoleBadge role={log.user_role} /></td>
                        <td className="col-question">{log.question}</td>
                        <td className="col-docs">{log.retrieved_doc_ids.length}</td>
                        <td className="col-time">{formatDate(log.timestamp)}</td>
                      </tr>
                      {expandedRow === log.id && (
                        <tr key={`exp-${log.id}`} className="expanded-row">
                          <td colSpan={6}>
                            <div className="expanded-content">
                              <div>
                                <strong>Doc IDs:</strong> {log.retrieved_doc_ids.join(', ') || '(none)'}
                              </div>
                              <div>
                                <strong>Answer:</strong>
                                <p className="expanded-answer">{log.answer}</p>
                              </div>
                            </div>
                          </td>
                        </tr>
                      )}
                    </>
                  ))}
                </tbody>
              </table>
            )}
          </div>
        )}

        {!loading && tab === 'docs' && (
          <div className="table-wrap">
            {documents.length === 0 ? (
              <p className="empty-state">No documents found. Run the ingestion pipeline first.</p>
            ) : (
              <table className="admin-table">
                <thead>
                  <tr>
                    <th>Doc ID</th>
                    <th>Title</th>
                    <th>Category</th>
                    <th>Access Level</th>
                  </tr>
                </thead>
                <tbody>
                  {documents.map(doc => (
                    <tr key={doc.doc_id}>
                      <td className="col-id">{doc.doc_id}</td>
                      <td className="col-title">{doc.title}</td>
                      <td className="col-category">{doc.category}</td>
                      <td><RoleBadge role={doc.access_level} /></td>
                    </tr>
                  ))}
                </tbody>
              </table>
            )}
          </div>
        )}
      </div>
    </div>
  )
}
