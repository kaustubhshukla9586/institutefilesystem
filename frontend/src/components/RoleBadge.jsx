export default function RoleBadge({ role }) {
  const cls = `badge badge-${role || 'student'}`
  return <span className={cls}>{role || 'student'}</span>
}
