import { useState, useRef } from 'react'
import { useNavigate } from 'react-router-dom'
import { Search, Clock, Tag, Bus, ChevronRight, ArrowLeftRight, Frown } from 'lucide-react'
import { searchTrips } from '../api'
import type { Trip } from '../types'
import LocationPicker from '../components/LocationPicker'
import toast from 'react-hot-toast'
import styles from './Home.module.css'

const fmt = (d: string, t: 'time' | 'date') =>
  new Date(d).toLocaleString('en-BD', t === 'time'
    ? { hour: '2-digit', minute: '2-digit', hour12: true }
    : { day: 'numeric', month: 'short', year: 'numeric' })

export default function Home() {
  const navigate = useNavigate()
  const [from, setFrom]       = useState('')
  const [to, setTo]           = useState('')
  const [trips, setTrips]     = useState<Trip[] | null>(null)
  const [loading, setLoading] = useState(false)
  const [searched, setSearched] = useState(false)
  const resultsRef = useRef<HTMLDivElement>(null)

  const handleSearch = async () => {
    if (!from.trim() || !to.trim()) { toast.error('Pick both From and To locations'); return }
    if (from.trim() === to.trim())  { toast.error('From and To cannot be the same'); return }
    setLoading(true)
    setSearched(true)
    try {
      const res = await searchTrips(from.trim().toLowerCase(), to.trim().toLowerCase())
      setTrips(res.data.data ?? [])
      setTimeout(() => resultsRef.current?.scrollIntoView({ behavior: 'smooth', block: 'start' }), 120)
    } catch {
      toast.error('Could not fetch trips. Is the server running?')
      setTrips([])
    } finally { setLoading(false) }
  }

  const swap = () => { setFrom(to); setTo(from) }

  return (
    <main className={styles.page}>
      {/* ── HERO ── */}
      <section className={styles.hero}>
        <div className={styles.heroInner}>
          <div className={styles.eyebrow}>
            <span>🇧🇩</span>
            <span>Bangladesh Inter-city Travel</span>
          </div>
          <h1 className={styles.heading}>
            Find your next<br />
            <em>journey.</em>
          </h1>
          <p className={styles.sub}>Real-time seats · Instant booking · All major routes</p>

          {/* Search card */}
          <div className={styles.card}>
            <div className={styles.pickers}>
              <LocationPicker
                label="From" value={from} onChange={setFrom}
                placeholder="Departure city…" id="from-loc"
              />
              <button className={styles.swapBtn} onClick={swap} type="button" title="Swap">
                <ArrowLeftRight size={15} />
              </button>
              <LocationPicker
                label="To" value={to} onChange={setTo}
                placeholder="Destination city…" id="to-loc"
              />
            </div>

            <button className={styles.searchBtn} onClick={handleSearch}
              disabled={loading} type="button">
              {loading
                ? <><span className="spinner" /><span>Searching…</span></>
                : <><Search size={17} strokeWidth={2.5} /><span>Search Trips</span></>}
            </button>
          </div>
        </div>
        <div className={styles.heroBg} aria-hidden />
      </section>

      {/* ── RESULTS ── */}
      {(searched || loading) && (
        <section className={styles.results} ref={resultsRef}>
          <div className={styles.resultsInner}>
            {loading ? (
              <>
                <div className={styles.resultsHead}>
                  <div className={`skeleton ${styles.skelTitle}`} />
                </div>
                {[1,2,3].map(i => (
                  <div key={i} className={styles.skelCard} style={{ animationDelay: `${i * 0.05}s` }}>
                    <div className="skeleton" style={{ height: 18, width: '55%', marginBottom: 12 }} />
                    <div className="skeleton" style={{ height: 13, width: '35%' }} />
                  </div>
                ))}
              </>
            ) : trips && trips.length === 0 ? (
              <div className={styles.empty}>
                <Frown size={36} className={styles.emptyIcon} />
                <p>No trips found</p>
                <span>Try a different route or check back later</span>
              </div>
            ) : trips && (
              <>
                <div className={styles.resultsHead}>
                  <h2 className={styles.resultsTitle}>
                    <span className={styles.count}>{trips.length}</span>
                    {' '}trip{trips.length !== 1 ? 's' : ''} found
                    <span className={styles.route}> · {from} → {to}</span>
                  </h2>
                </div>

                <div className={styles.tripList}>
                  {trips.map((trip, i) => (
                    <button
                      key={trip.id}
                      className={styles.tripCard}
                      style={{ animationDelay: `${i * 0.07}s` }}
                      onClick={() => navigate(`/trip/${trip.id}`, { state: { trip } })}
                      type="button"
                    >
                      <div className={styles.punchL} />
                      <div className={styles.punchR} />

                      <div className={styles.tripMain}>
                        <div className={styles.tripRoute}>
                          <span className={styles.city}>{trip.from_location}</span>
                          <div className={styles.routeLine}>
                            <span className={styles.routeDot} />
                            <span className={styles.routeDash} />
                            <Bus size={13} className={styles.routeBus} />
                            <span className={styles.routeDash} />
                            <span className={styles.routeDot} />
                          </div>
                          <span className={styles.city}>{trip.to_location}</span>
                        </div>
                        {trip.title && <p className={styles.tripTitle}>{trip.title}</p>}
                        <div className={styles.tripMeta}>
                          <span><Clock size={12} />{fmt(trip.departure_time, 'time')}</span>
                          <span className={styles.dot}>·</span>
                          <span>{fmt(trip.departure_time, 'date')}</span>
                        </div>
                      </div>

                      <div className={styles.tripRight}>
                        <div className={styles.priceTag}>
                          <Tag size={11} />
                          <span>৳{trip.price}</span>
                        </div>
                        <ChevronRight size={18} className={styles.arrow} />
                      </div>
                    </button>
                  ))}
                </div>
              </>
            )}
          </div>
        </section>
      )}
    </main>
  )
}
