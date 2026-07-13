import { useState } from 'react'
import { api } from './api.js'

const FACTORS = [
  { key: 'relevance', label: 'Relevantie' },
  { key: 'age_score', label: 'Recentheid' },
  { key: 'comments_score', label: 'Ruimte (weinig reacties)' },
  { key: 'upvotes_score', label: 'Upvotes' },
]

const LABEL_INFO = {
  karma: { text: 'Karma', hint: 'Geen zelfpromotie — reactie zonder productvermelding' },
  marketing: { text: 'Marketing', hint: 'Zelfpromotie toegestaan — project noemen mag (met disclosure)' },
  research: { text: 'Research', hint: 'Pijnpunt/klacht over concurrent — bewaren als inspiratie' },
}

function scoreColor(total) {
  if (total >= 65) return 'var(--good)'
  if (total >= 40) return 'var(--mid)'
  return 'var(--bad)'
}

function ageText(createdUtc) {
  const hours = (Date.now() / 1000 - createdUtc) / 3600
  if (hours < 24) return `${Math.max(1, Math.round(hours))}u geleden`
  return `${Math.round(hours / 24)}d geleden`
}

export default function PostCard({ post, onUpdate, onError }) {
  const [busy, setBusy] = useState(false)
  const [expanded, setExpanded] = useState(false)
  const label = LABEL_INFO[post.label] || LABEL_INFO.karma

  async function draft(mode) {
    setBusy(true)
    onError('')
    try {
      const d = await api.createDraft(post.id, mode)
      onUpdate({ ...post, drafts: [...post.drafts, d] })
      setExpanded(true)
    } catch (e) {
      onError(e.message)
    } finally {
      setBusy(false)
    }
  }

  return (
    <article className="post-card">
      <div className="post-top">
        <div className="score-badge" style={{ background: scoreColor(post.total) }}>
          {Math.round(post.total)}
        </div>
        <div className="post-info">
          <div className="post-meta">
            <span className={`label label-${post.label}`} title={label.hint}>{label.text}</span>
            <span className="muted">r/{post.subreddit} · {ageText(post.created_utc)} · ▲{post.upvotes} · 💬{post.num_comments}</span>
          </div>
          <a className="post-title" href={post.url} target="_blank" rel="noreferrer">{post.title}</a>
          {post.rationale && <p className="rationale">{post.rationale}</p>}
        </div>
      </div>

      <div className="factors">
        {FACTORS.map((f) => (
          <div key={f.key} className="factor">
            <span className="factor-label">{f.label}</span>
            <div className="bar-track">
              <div className="bar-fill" style={{ width: `${Math.min(100, post[f.key])}%` }} />
            </div>
            <span className="factor-value">{Math.round(post[f.key])}</span>
          </div>
        ))}
      </div>

      <div className="post-actions">
        {post.label !== 'research' && (
          <>
            <button disabled={busy} onClick={() => draft('karma')}>
              {busy ? 'Bezig…' : 'Genereer reactie (karma)'}
            </button>
            {post.label === 'marketing' && (
              <button disabled={busy} onClick={() => draft('marketing')}>
                {busy ? 'Bezig…' : 'Genereer reactie (marketing)'}
              </button>
            )}
          </>
        )}
        {post.drafts.length > 0 && (
          <button className="link" onClick={() => setExpanded(!expanded)}>
            {expanded ? 'Verberg concepten' : `Toon ${post.drafts.length} concept${post.drafts.length > 1 ? 'en' : ''}`}
          </button>
        )}
      </div>

      {expanded && post.drafts.map((d) => (
        <div key={d.id} className="draft">
          <div className="draft-head">
            <span className="muted">Concept ({d.mode}) · {d.created_at}</span>
            <button className="link" onClick={() => navigator.clipboard.writeText(d.content)}>
              Kopieer
            </button>
          </div>
          <pre>{d.content}</pre>
        </div>
      ))}
    </article>
  )
}
