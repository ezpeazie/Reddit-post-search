import { useCallback, useEffect, useState } from 'react'
import { api } from './api.js'
import ProjectForm from './ProjectForm.jsx'
import PostCard from './PostCard.jsx'

const FILTERS = [
  { key: 'alle', label: 'Alle' },
  { key: 'karma', label: 'Karma' },
  { key: 'marketing', label: 'Marketing' },
  { key: 'research', label: 'Research' },
]

export default function App() {
  const [projects, setProjects] = useState([])
  const [activeId, setActiveId] = useState(null)
  const [posts, setPosts] = useState([])
  const [filter, setFilter] = useState('alle')
  const [editing, setEditing] = useState(null) // null | 'new' | project-object
  const [scanning, setScanning] = useState(false)
  const [status, setStatus] = useState('')
  const [error, setError] = useState('')

  const active = projects.find((p) => p.id === activeId) || null

  const loadProjects = useCallback(async () => {
    const list = await api.listProjects()
    setProjects(list)
    return list
  }, [])

  useEffect(() => {
    loadProjects().then((list) => {
      if (list.length > 0) setActiveId((id) => id ?? list[0].id)
    }).catch((e) => setError(e.message))
  }, [loadProjects])

  useEffect(() => {
    if (activeId == null) { setPosts([]); return }
    api.listPosts(activeId).then(setPosts).catch((e) => setError(e.message))
  }, [activeId])

  async function handleScan() {
    if (!active) return
    setScanning(true)
    setError('')
    setStatus('Bezig met scannen en scoren…')
    try {
      const result = await api.scan(active.id)
      setStatus(`${result.found} posts gevonden, ${result.new} nieuw gescoord.`)
      setPosts(await api.listPosts(active.id))
    } catch (e) {
      setError(e.message)
      setStatus('')
    } finally {
      setScanning(false)
    }
  }

  async function handleSaveProject(data) {
    setError('')
    try {
      if (editing === 'new') {
        const created = await api.createProject(data)
        await loadProjects()
        setActiveId(created.id)
      } else {
        await api.updateProject(editing.id, data)
        await loadProjects()
      }
      setEditing(null)
    } catch (e) {
      setError(e.message)
    }
  }

  async function handleDeleteProject(id) {
    if (!window.confirm('Project en alle bijbehorende geschiedenis verwijderen?')) return
    await api.deleteProject(id)
    const list = await loadProjects()
    setActiveId(list.length > 0 ? list[0].id : null)
    setEditing(null)
  }

  function updatePost(updated) {
    setPosts((prev) => prev.map((p) => (p.id === updated.id ? updated : p)))
  }

  const visible = filter === 'alle' ? posts : posts.filter((p) => p.label === filter)

  return (
    <div className="layout">
      <aside className="sidebar">
        <h1>Reddit Scanner</h1>
        <nav>
          {projects.map((p) => (
            <button
              key={p.id}
              className={p.id === activeId ? 'project active' : 'project'}
              onClick={() => { setActiveId(p.id); setEditing(null); setStatus(''); setFilter('alle') }}
            >
              {p.name}
            </button>
          ))}
        </nav>
        <button className="new-project" onClick={() => setEditing('new')}>+ Nieuw project</button>
      </aside>

      <main className="main">
        {error && <div className="error">{error}</div>}

        {editing ? (
          <ProjectForm
            project={editing === 'new' ? null : editing}
            onSave={handleSaveProject}
            onCancel={() => setEditing(null)}
            onDelete={editing !== 'new' ? () => handleDeleteProject(editing.id) : null}
          />
        ) : active ? (
          <>
            <header className="project-header">
              <div>
                <h2>{active.name}</h2>
                <p className="muted">
                  {active.subreddits.length > 0
                    ? active.subreddits
                        .map((s) => `r/${s.name}${s.selfpromo ? ' ✓promo' : ''}`)
                        .join(', ')
                    : '—'}
                  {' · keywords: '}
                  {active.keywords.join(', ') || '—'}
                </p>
              </div>
              <div className="header-actions">
                <button onClick={() => setEditing(active)}>Bewerken</button>
                <button className="primary" onClick={handleScan} disabled={scanning}>
                  {scanning ? 'Bezig…' : 'Generate'}
                </button>
              </div>
            </header>

            {status && <p className="status">{status}</p>}

            <div className="filters">
              {FILTERS.map((f) => (
                <button
                  key={f.key}
                  className={filter === f.key ? 'filter active' : 'filter'}
                  onClick={() => setFilter(f.key)}
                >
                  {f.label}
                  {f.key !== 'alle' && ` (${posts.filter((p) => p.label === f.key).length})`}
                </button>
              ))}
            </div>

            {visible.length === 0 ? (
              <p className="muted empty">
                Nog geen posts{filter !== 'alle' ? ' met dit label' : ''}. Klik op Generate om te scannen.
              </p>
            ) : (
              visible.map((post) => (
                <PostCard key={post.id} post={post} onUpdate={updatePost} onError={setError} />
              ))
            )}
          </>
        ) : (
          <p className="muted empty">Maak links een project aan om te beginnen.</p>
        )}
      </main>
    </div>
  )
}
