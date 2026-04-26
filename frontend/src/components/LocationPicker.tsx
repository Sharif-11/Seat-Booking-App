import { useState, useRef, useEffect, type KeyboardEvent } from 'react'
import { MapPin, ChevronDown, X } from 'lucide-react'
import { BD_DIVISIONS, POPULAR_CITIES } from '../data/locations'
import type { LocationOption } from '../data/locations'
import styles from './LocationPicker.module.css'

interface Props {
  value: string
  onChange: (val: string) => void
  placeholder?: string
  label: string
  id?: string
}

export default function LocationPicker({ value, onChange, placeholder = 'Type or pick…', label, id }: Props) {
  const [open, setOpen]   = useState(false)
  const [query, setQuery] = useState('')
  const inputRef = useRef<HTMLInputElement>(null)
  const dropRef  = useRef<HTMLDivElement>(null)

  useEffect(() => {
    const handle = (e: MouseEvent) => {
      if (dropRef.current && !dropRef.current.contains(e.target as Node)) setOpen(false)
    }
    document.addEventListener('mousedown', handle)
    return () => document.removeEventListener('mousedown', handle)
  }, [])

  const all: LocationOption[] = [...BD_DIVISIONS, ...POPULAR_CITIES]
  const filtered = query.trim()
    ? all.filter(l => l.label.toLowerCase().includes(query.toLowerCase()) || l.id.includes(query.toLowerCase()))
    : all
  const divisions = filtered.filter(l => BD_DIVISIONS.some(d => d.id === l.id))
  const cities    = filtered.filter(l => POPULAR_CITIES.some(c => c.id === l.id))

  const select = (opt: LocationOption) => {
    onChange(opt.id); setQuery(''); setOpen(false)
  }

  const clear = (e: React.MouseEvent) => {
    e.stopPropagation(); onChange(''); setQuery('')
    inputRef.current?.focus()
  }

  const handleInput = (e: React.ChangeEvent<HTMLInputElement>) => {
    const v = e.target.value
    setQuery(v)
    onChange(v.toLowerCase())
    if (!open) setOpen(true)
  }

  const handleKeyDown = (e: KeyboardEvent<HTMLInputElement>) => {
    if (e.key === 'Enter' && query.trim()) {
      onChange(query.trim().toLowerCase()); setOpen(false)
    }
    if (e.key === 'Escape') setOpen(false)
  }

  const displayValue = (() => {
    const found = all.find(l => l.id === value)
    return found ? found.label : value
  })()

  return (
    <div className={styles.root} ref={dropRef}>
      <label className={styles.label} htmlFor={id}>{label}</label>
      <div
        className={`${styles.field} ${open ? styles.fieldOpen : ''}`}
        onClick={() => { setOpen(true); setTimeout(() => inputRef.current?.focus(), 40) }}
      >
        <MapPin size={15} className={styles.icon} />
        <input
          ref={inputRef}
          id={id}
          className={styles.input}
          placeholder={placeholder}
          value={open ? query : displayValue}
          onChange={handleInput}
          onFocus={() => { setOpen(true); setQuery('') }}
          onKeyDown={handleKeyDown}
          autoComplete="off"
          aria-autocomplete="list"
          aria-expanded={open}
        />
        {value ? (
          <button className={styles.clearBtn} onClick={clear} type="button" aria-label="Clear">
            <X size={13} />
          </button>
        ) : (
          <ChevronDown size={14} className={`${styles.chevron} ${open ? styles.chevronUp : ''}`} />
        )}
      </div>

      {open && (
        <div className={styles.dropdown} role="listbox">
          {divisions.length > 0 && (
            <div className={styles.section}>
              <span className={styles.sectionLabel}>Divisions</span>
              <div className={styles.chips}>
                {divisions.map(loc => (
                  <button
                    key={loc.id}
                    className={`${styles.chip} ${value === loc.id ? styles.chipActive : ''}`}
                    onClick={() => select(loc)}
                    type="button"
                    role="option"
                    aria-selected={value === loc.id}
                  >
                    <span className={styles.chipEmoji}>{loc.emoji}</span>
                    {loc.label}
                  </button>
                ))}
              </div>
            </div>
          )}

          {cities.length > 0 && (
            <div className={styles.section}>
              <span className={styles.sectionLabel}>Popular Cities</span>
              <div className={styles.list}>
                {cities.map(loc => (
                  <button
                    key={loc.id}
                    className={`${styles.listItem} ${value === loc.id ? styles.listItemActive : ''}`}
                    onClick={() => select(loc)}
                    type="button"
                    role="option"
                    aria-selected={value === loc.id}
                  >
                    <span>{loc.emoji}</span>
                    <span>{loc.label}</span>
                  </button>
                ))}
              </div>
            </div>
          )}

          {filtered.length === 0 && query && (
            <div className={styles.noResults}>
              Press <kbd>Enter</kbd> to search "<strong>{query}</strong>"
            </div>
          )}
        </div>
      )}
    </div>
  )
}
