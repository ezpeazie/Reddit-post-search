async function request(url, options = {}) {
  const res = await fetch(url, {
    headers: { 'Content-Type': 'application/json' },
    ...options,
  })
  if (!res.ok) {
    let detail = res.statusText
    try {
      detail = (await res.json()).detail || detail
    } catch { /* geen JSON-body */ }
    throw new Error(detail)
  }
  return res.json()
}

export const api = {
  listProjects: () => request('/api/projects'),
  createProject: (p) => request('/api/projects', { method: 'POST', body: JSON.stringify(p) }),
  updateProject: (id, p) => request(`/api/projects/${id}`, { method: 'PUT', body: JSON.stringify(p) }),
  deleteProject: (id) => request(`/api/projects/${id}`, { method: 'DELETE' }),
  scan: (id) => request(`/api/projects/${id}/scan`, { method: 'POST' }),
  listPosts: (id) => request(`/api/projects/${id}/posts`),
  createDraft: (postId, mode) =>
    request(`/api/posts/${postId}/draft`, { method: 'POST', body: JSON.stringify({ mode }) }),
  suggest: (instruction) =>
    request('/api/suggest', { method: 'POST', body: JSON.stringify({ instruction }) }),
  getRules: (name) => request(`/api/subreddits/${encodeURIComponent(name)}/rules`),
}
