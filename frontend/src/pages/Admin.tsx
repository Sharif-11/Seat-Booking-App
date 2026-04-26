import { useState } from 'react'
import { Plus, Edit3, CheckCircle2, AlertTriangle, Settings } from 'lucide-react'
import { createTrip, updateTrip } from '../api'
import type { CreateTripPayload, UpdateTripPayload } from '../api'
import LocationPicker from '../components/LocationPicker'
import toast from 'react-hot-toast'
import styles from './Admin.module.css'

type Mode = 'create' | 'update'

const defaultCreate = { title: '', from_location: '', to_location: '', departure_time: '', price: '', seat_count: '28' }
const defaultUpdate  = { id: '', title: '', from_location: '', to_location: '', departure_time: '', price: '' }

export default function Admin() {
  const [mode, setMode]   = useState<Mode>('create')
  const [cf, setCf]       = useState(defaultCreate)
  const [uf, setUf]       = useState(defaultUpdate)
  const [loading, setLoading] = useState(false)

  const setC = (k: keyof typeof defaultCreate, v: string) => setCf(p => ({ ...p, [k]: v }))
  const setU = (k: keyof typeof defaultUpdate, v: string) => setUf(p => ({ ...p, [k]: v }))

  const handleCreate = async () => {
    if (!cf.title || !cf.from_location || !cf.to_location || !cf.departure_time || !cf.price) {
      toast.error('Fill all required fields'); return
    }
    setLoading(true)
    try {
      const payload: CreateTripPayload = {
        title: cf.title.trim(),
        from_location:  cf.from_location.toLowerCase().trim(),
        to_location:    cf.to_location.toLowerCase().trim(),
        departure_time: new Date(cf.departure_time).toISOString(),
        price:      parseFloat(cf.price),
        seat_count: parseInt(cf.seat_count) || 28,
      }
      await createTrip(payload)
      toast.success('Trip created! 🚌')
      setCf(defaultCreate)
    } catch (e: unknown) {
      const err = e as { response?: { data?: { message?: string } } }
      toast.error(err?.response?.data?.message || 'Failed to create trip')
    } finally { setLoading(false) }
  }

  const handleUpdate = async () => {
    if (!uf.id || !uf.title || !uf.from_location || !uf.to_location || !uf.departure_time || !uf.price) {
      toast.error('Fill all required fields'); return
    }
    setLoading(true)
    try {
      const payload: UpdateTripPayload = {
        title: uf.title.trim(),
        from_location:  uf.from_location.toLowerCase().trim(),
        to_location:    uf.to_location.toLowerCase().trim(),
        departure_time: new Date(uf.departure_time).toISOString(),
        price: parseFloat(uf.price),
      }
      await updateTrip(parseInt(uf.id), payload)
      toast.success(`Trip #${uf.id} updated!`)
    } catch (e: unknown) {
      const err = e as { response?: { data?: { message?: string } } }
      toast.error(err?.response?.data?.message || 'Failed to update trip')
    } finally { setLoading(false) }
  }

  const isCreate = mode === 'create'

  return (
    <main className={styles.page}>
      <div className={styles.inner}>
        <div className={styles.header}>
          <div className={styles.headerLeft}>
            <div className={styles.icon}><Settings size={20} /></div>
            <div>
              <h1 className={styles.title}>Admin Panel</h1>
              <p className={styles.sub}>Manage trips &amp; schedules</p>
            </div>
          </div>
          <div className={styles.demoTag}><AlertTriangle size={12} />Demo</div>
        </div>

        {/* Tabs */}
        <div className={styles.tabs}>
          <button className={`${styles.tab} ${isCreate ? styles.tabActive : ''}`}
            onClick={() => setMode('create')} type="button">
            <Plus size={15} />Create Trip
          </button>
          <button className={`${styles.tab} ${!isCreate ? styles.tabActive : ''}`}
            onClick={() => setMode('update')} type="button">
            <Edit3 size={15} />Update Trip
          </button>
        </div>

        {/* Form */}
        <div className={styles.form}>
          {!isCreate && (
            <div className={styles.field}>
              <label>Trip ID *</label>
              <input className={styles.input} type="number" placeholder="e.g. 5"
                value={uf.id} onChange={e => setU('id', e.target.value)} />
            </div>
          )}

          <div className={styles.field}>
            <label>Bus / Service Name *</label>
            <input className={styles.input} type="text" placeholder="e.g. Ena Paribahan"
              value={isCreate ? cf.title : uf.title}
              onChange={e => isCreate ? setC('title', e.target.value) : setU('title', e.target.value)} />
          </div>

          <div className={styles.rowGrid}>
            <LocationPicker
              label="From *" placeholder="Departure…"
              value={isCreate ? cf.from_location : uf.from_location}
              onChange={v => isCreate ? setC('from_location', v) : setU('from_location', v)}
            />
            <LocationPicker
              label="To *" placeholder="Destination…"
              value={isCreate ? cf.to_location : uf.to_location}
              onChange={v => isCreate ? setC('to_location', v) : setU('to_location', v)}
            />
          </div>

          <div className={styles.rowGrid}>
            <div className={styles.field}>
              <label>Departure Time *</label>
              <input className={styles.input} type="datetime-local"
                value={isCreate ? cf.departure_time : uf.departure_time}
                onChange={e => isCreate ? setC('departure_time', e.target.value) : setU('departure_time', e.target.value)} />
            </div>
            <div className={styles.field}>
              <label>Price (৳) *</label>
              <input className={styles.input} type="number" placeholder="e.g. 650" min={1}
                value={isCreate ? cf.price : uf.price}
                onChange={e => isCreate ? setC('price', e.target.value) : setU('price', e.target.value)} />
            </div>
          </div>

          {isCreate && (
            <div className={styles.field}>
              <label>Seat Count</label>
              <input className={styles.input} type="number" placeholder="Default: 28" min={1} max={60}
                value={cf.seat_count} onChange={e => setC('seat_count', e.target.value)} />
              <p className={styles.hint}>Standard coaches: 28–44 seats</p>
            </div>
          )}

          <button className={styles.submitBtn} type="button"
            onClick={isCreate ? handleCreate : handleUpdate} disabled={loading}>
            {loading ? <span className="spinner" /> : <CheckCircle2 size={17} />}
            {isCreate ? 'Create Trip' : 'Update Trip'}
          </button>
        </div>
      </div>
    </main>
  )
}
