import { useState } from 'react'
import { api } from './api.js'

// Subreddit-item: { name, selfpromo, checked }
// Keyword-item:   { value, checked }

export default function ProjectForm({ project, onSave, onCancel, onDelete }) {
  const [name, setName] = useState(project?.name || '')
  const [instruction, setInstruction] = useState(project?.instruction || '')
  const [subs, setSubs] = useState(
    project?.subreddits.map((s) => ({ ...s, checked: true })) || []
  )
  const [keywords, setKeywords] = useState(
    project?.keywords.map((k) => ({ value: k, checked: true })) || []
  )
  const [newSub, setNewSub] = useState('')
  const [newKeyword, setNewKeyword] = useState('')
  const [suggesting, setSuggesting] = useState(false)
  const [suggestInfo, setSuggestInfo] = useState('')
  const [error, setError] = useState('')
  const [rules, setRules] = useState({}) // naam -> 'loading' | [{short_name, description}] | null (verborgen)

  async function handleSuggest() {
    if (!instruction.trim()) {
      setError('Vul eerst een instructie in — die stuurt het voorstel.')
      return
    }
    setSuggesting(true)
    setError('')
    setSuggestInfo('')
    try {
      const result = await api.suggest(instruction)
      const existing = new Set(subs.map((s) => s.name.toLowerCase()))
      const addedSubs = result.subreddits
        .filter((n) => !existing.has(n.toLowerCase()))
        // Self-promo staat voor elke nieuwe subreddit standaard UIT (karma-only).
        .map((n) => ({ name: n, selfpromo: false, checked: true }))
      const existingKw = new Set(keywords.map((k) => k.value.toLowerCase()))
      const addedKw = result.keywords
        .filter((k) => !existingKw.has(k.toLowerCase()))
        .map((k) => ({ value: k, checked: true }))
      setSubs((prev) => [...prev, ...addedSubs])
      setKeywords((prev) => [...prev, ...addedKw])
      const parts = [`${addedSubs.length} geverifieerde subreddits en ${addedKw.length} keywords toegevoegd.`]
      if (result.rejected.length > 0) {
        parts.push(`Afgevallen (bestaan niet of niet toegankelijk): ${result.rejected.join(', ')}.`)
      }
      setSuggestInfo(parts.join(' '))
    } catch (e) {
      setError(e.message)
    } finally {
      setSuggesting(false)
    }
  }

  function addSub() {
    const clean = newSub.trim().replace(/^r\//, '')
    if (!clean) return
    if (subs.some((s) => s.name.toLowerCase() === clean.toLowerCase())) { setNewSub(''); return }
    setSubs((prev) => [...prev, { name: clean, selfpromo: false, checked: true }])
    setNewSub('')
  }

  function addKeyword() {
    const clean = newKeyword.trim()
    if (!clean) return
    if (keywords.some((k) => k.value.toLowerCase() === clean.toLowerCase())) { setNewKeyword(''); return }
    setKeywords((prev) => [...prev, { value: clean, checked: true }])
    setNewKeyword('')
  }

  function patchSub(idx, patch) {
    setSubs((prev) => prev.map((s, i) => (i === idx ? { ...s, ...patch } : s)))
  }

  async function toggleRules(subName) {
    if (rules[subName] && rules[subName] !== 'loading') {
      setRules((prev) => ({ ...prev, [subName]: null }))
      return
    }
    setRules((prev) => ({ ...prev, [subName]: 'loading' }))
    try {
      const result = await api.getRules(subName)
      setRules((prev) => ({ ...prev, [subName]: result.rules }))
    } catch (e) {
      setError(e.message)
      setRules((prev) => ({ ...prev, [subName]: null }))
    }
  }

  function submit(e) {
    e.preventDefault()
    // Opslaan gebeurt alleen hier, na expliciete bevestiging van de gebruiker.
    onSave({
      name: name.trim(),
      instruction: instruction.trim(),
      subreddits: subs.filter((s) => s.checked).map(({ name, selfpromo }) => ({ name, selfpromo })),
      keywords: keywords.filter((k) => k.checked).map((k) => k.value),
    })
  }

  return (
    <form className="project-form" onSubmit={submit}>
      <h2>{project ? `Project bewerken: ${project.name}` : 'Nieuw project'}</h2>
      {error && <div className="error">{error}</div>}

      <label>
        Naam
        <input value={name} onChange={(e) => setName(e.target.value)} required placeholder="bijv. Codex" />
      </label>

      <label>
        Instructie / beschrijving
        <textarea
          value={instruction}
          onChange={(e) => setInstruction(e.target.value)}
          rows={4}
          placeholder='bijv. "focus timer voor developers, studenten, ADHD" — dit stuurt het voorstel én de relevantiescore.'
        />
      </label>

      <div className="suggest-row">
        <button type="button" onClick={handleSuggest} disabled={suggesting}>
          {suggesting ? 'Voorstel wordt gemaakt en geverifieerd…' : 'Stel subreddits & keywords voor'}
        </button>
        {suggestInfo && <span className="status">{suggestInfo}</span>}
      </div>

      <fieldset>
        <legend>Subreddits</legend>
        {subs.length === 0 && <p className="muted">Nog geen subreddits — gebruik het voorstel of voeg handmatig toe.</p>}
        {subs.map((s, idx) => (
          <div key={s.name} className="sub-row-wrap">
            <div className="sub-row">
              <label className="check">
                <input
                  type="checkbox"
                  checked={s.checked}
                  onChange={(e) => patchSub(idx, { checked: e.target.checked })}
                />
                r/{s.name}
              </label>
              <label className="check promo" title="Alleen aanzetten als de subreddit-regels zelfpromotie toestaan — kijk ze eerst na.">
                <input
                  type="checkbox"
                  checked={s.selfpromo}
                  onChange={(e) => patchSub(idx, { selfpromo: e.target.checked })}
                />
                zelfpromotie toegestaan
              </label>
              <button type="button" className="link" onClick={() => toggleRules(s.name)}>
                {rules[s.name] === 'loading' ? 'regels laden…' : rules[s.name] ? 'verberg regels' : 'bekijk regels'}
              </button>
            </div>
            {Array.isArray(rules[s.name]) && (
              <div className="rules">
                {rules[s.name].length === 0 ? (
                  <p className="muted">Geen regels gepubliceerd.</p>
                ) : (
                  rules[s.name].map((r, i) => (
                    <p key={i}><strong>{r.short_name}</strong>{r.description ? ` — ${r.description}` : ''}</p>
                  ))
                )}
              </div>
            )}
          </div>
        ))}
        <div className="add-row">
          <input
            value={newSub}
            onChange={(e) => setNewSub(e.target.value)}
            onKeyDown={(e) => { if (e.key === 'Enter') { e.preventDefault(); addSub() } }}
            placeholder="subreddit handmatig toevoegen"
          />
          <button type="button" onClick={addSub}>Toevoegen</button>
        </div>
      </fieldset>

      <fieldset>
        <legend>Keywords</legend>
        {keywords.length === 0 && <p className="muted">Nog geen keywords.</p>}
        <div className="chips">
          {keywords.map((k, idx) => (
            <label key={k.value} className={k.checked ? 'chip checked' : 'chip'}>
              <input
                type="checkbox"
                checked={k.checked}
                onChange={(e) =>
                  setKeywords((prev) => prev.map((kw, i) => (i === idx ? { ...kw, checked: e.target.checked } : kw)))
                }
              />
              {k.value}
            </label>
          ))}
        </div>
        <div className="add-row">
          <input
            value={newKeyword}
            onChange={(e) => setNewKeyword(e.target.value)}
            onKeyDown={(e) => { if (e.key === 'Enter') { e.preventDefault(); addKeyword() } }}
            placeholder="keyword handmatig toevoegen"
          />
          <button type="button" onClick={addKeyword}>Toevoegen</button>
        </div>
      </fieldset>

      <div className="form-actions">
        <button type="submit" className="primary">Bevestigen & opslaan</button>
        <button type="button" onClick={onCancel}>Annuleren</button>
        {onDelete && (
          <button type="button" className="danger" onClick={onDelete}>Verwijderen</button>
        )}
      </div>
    </form>
  )
}
