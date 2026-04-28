import {
  ArrowRight,
  ChevronRight,
  Clock,
  CreditCard,
  Download,
  MapPin,
  PackageOpen,
  RefreshCw,
  Ticket,
} from 'lucide-react'
import { useEffect, useState } from 'react'
import toast from 'react-hot-toast'
import { useNavigate } from 'react-router-dom'
import { downloadTicketSlip, getMyBookings } from '../api'
import { useAuth } from '../context/AuthContext'
import type { BookingStatus, MyBooking } from '../types'
import styles from './MyBookings.module.css'
import { generateTicketPDF } from './TicketTemplate'

/* ── helpers ── */
const fmtTime = (s: string) =>
  new Date(s).toLocaleTimeString('en-BD', { hour: '2-digit', minute: '2-digit', hour12: true })

const fmtDate = (s: string) =>
  new Date(s).toLocaleDateString('en-BD', { day: 'numeric', month: 'short', year: 'numeric' })

const fmtDateShort = (s: string) =>
  new Date(s).toLocaleDateString('en-BD', { day: 'numeric', month: 'short' })

const STATUS_META: Record<BookingStatus, { label: string; cls: string }> = {
  PENDING: { label: 'Pending Payment', cls: 'pending' },
  CONFIRMED: { label: 'Confirmed', cls: 'confirmed' },
  EXPIRED: { label: 'Expired', cls: 'expired' },
  FAILED: { label: 'Failed', cls: 'failed' },
  CANCELLED: { label: 'Cancelled', cls: 'cancelled' },
}

// Function to generate and download PDF ticket
// Helper function to generate and download PDF ticket

// Updated handler

export default function MyBookings() {
  const { isAuthenticated } = useAuth()
  const navigate = useNavigate()

  const [bookings, setBookings] = useState<MyBooking[]>([])
  const [loading, setLoading] = useState(true)
  const [refreshing, setRefreshing] = useState(false)
  const [filter, setFilter] = useState<BookingStatus | 'ALL'>('ALL')
  const [downloadingId, setDownloadingId] = useState<number | null>(null)

  /* redirect if not logged in */
  useEffect(() => {
    if (!isAuthenticated) navigate('/', { replace: true })
  }, [isAuthenticated, navigate])

  const load = async (silent = false) => {
    if (!silent) setLoading(true)
    else setRefreshing(true)
    try {
      const res = await getMyBookings()
      const list: MyBooking[] = res.data?.data ?? res.data ?? []
      setBookings(list)
    } catch (e: any) {
      if (!silent) toast.error(e?.response?.data?.detail || 'Failed to load bookings')
    } finally {
      setLoading(false)
      setRefreshing(false)
    }
  }

  useEffect(() => {
    load()
  }, [])

  const handleRefresh = () => load(true)

  const handleDownloadTicket = async (bookingId: number) => {
    setDownloadingId(bookingId)
    try {
      const response = await downloadTicketSlip(bookingId)
      const ticketData = response.data?.data ?? response.data

      if (!ticketData) {
        throw new Error('No ticket data received')
      }

      await generateTicketPDF(ticketData)
      toast.success('Ticket downloaded successfully')
    } catch (error: any) {
      console.error('Download error:', error)
      toast.error(error?.response?.data?.detail || 'Failed to download ticket')
    } finally {
      setDownloadingId(null)
    }
  }

  const filtered = filter === 'ALL' ? bookings : bookings.filter(b => b.status === filter)

  const counts = bookings.reduce<Partial<Record<BookingStatus | 'ALL', number>>>(
    (acc, b) => {
      acc['ALL'] = (acc['ALL'] ?? 0) + 1
      acc[b.status] = (acc[b.status] ?? 0) + 1
      return acc
    },
    { ALL: 0 }
  )

  const canPay = (b: MyBooking) =>
    b.status === 'PENDING' && b.expires_at && new Date(b.expires_at) > new Date()

  /* ── render ── */
  if (!isAuthenticated) return null

  return (
    <div className={styles.page}>
      <div className={styles.inner}>
        {/* ── Page header ── */}
        <div className={styles.pageHeader}>
          <div className={styles.pageHeaderLeft}>
            <div className={styles.pageIcon}>
              <Ticket size={20} />
            </div>
            <div>
              <h1 className={styles.pageTitle}>My Bookings</h1>
              <p className={styles.pageSubtitle}>All your trip reservations</p>
            </div>
          </div>
          <button
            className={`${styles.refreshBtn} ${refreshing ? styles.spinning : ''}`}
            onClick={handleRefresh}
            disabled={refreshing}
            title='Refresh'
          >
            <RefreshCw size={15} />
          </button>
        </div>

        {/* ── Summary stats ── */}
        {!loading && bookings.length > 0 && (
          <div className={styles.stats}>
            {(
              [
                { key: 'ALL', label: 'Total' },
                { key: 'CONFIRMED', label: 'Confirmed' },
                { key: 'PENDING', label: 'Pending' },
                { key: 'EXPIRED', label: 'Expired' },
              ] as { key: BookingStatus | 'ALL'; label: string }[]
            ).map(({ key, label }) => (
              <button
                key={key}
                className={`${styles.statCard} ${filter === key ? styles.statActive : ''}`}
                onClick={() => setFilter(key)}
              >
                <span className={styles.statNum}>{counts[key] ?? 0}</span>
                <span className={styles.statLabel}>{label}</span>
              </button>
            ))}
          </div>
        )}

        {/* ── Filter pills (mobile) ── */}
        {!loading && bookings.length > 0 && (
          <div className={styles.filterBar}>
            {(['ALL', 'PENDING', 'CONFIRMED', 'EXPIRED', 'FAILED', 'CANCELLED'] as const).map(f => (
              <button
                key={f}
                className={`${styles.filterPill} ${filter === f ? styles.filterActive : ''}`}
                onClick={() => setFilter(f)}
              >
                {f === 'ALL' ? 'All' : STATUS_META[f]?.label || f}
                {counts[f] ? <span className={styles.filterCount}>{counts[f]}</span> : null}
              </button>
            ))}
          </div>
        )}

        {/* ── List ── */}
        {loading ? (
          <div className={styles.list}>
            {[1, 2, 3].map(i => (
              <div key={i} className={`${styles.card} skeleton`} style={{ height: 130 }} />
            ))}
          </div>
        ) : filtered.length === 0 ? (
          <EmptyState filter={filter} onClear={() => setFilter('ALL')} navigate={navigate} />
        ) : (
          <div className={styles.list}>
            {filtered.map((b, idx) => {
              const meta = STATUS_META[b.status] ?? { label: b.status, cls: 'pending' }
              const payable = canPay(b)
              const expired = b.expires_at ? new Date(b.expires_at) < new Date() : false
              const isDownloading = downloadingId === b.booking_id

              return (
                <div
                  key={b.booking_id}
                  className={styles.card}
                  style={{ animationDelay: `${idx * 0.05}s` }}
                >
                  {/* Ticket notch decoration */}
                  <div className={styles.notchLeft} />
                  <div className={styles.notchRight} />

                  <div className={styles.cardTop}>
                    {/* Route */}
                    <div className={styles.route}>
                      <span className={styles.city}>Show #{b.show_id}</span>
                    </div>

                    {/* Status badge */}
                    <span className={`${styles.statusBadge} ${styles[meta.cls]}`}>
                      {meta.label}
                    </span>
                  </div>

                  <div className={styles.cardMid}>
                    {/* Meta row */}
                    <div className={styles.metaRow}>
                      <span className={styles.metaItem}>
                        <MapPin size={12} />
                        {b.seats?.length || 0} seat{(b.seats?.length || 0) !== 1 ? 's' : ''}
                      </span>
                      <span className={styles.metaItem}>
                        <CreditCard size={12} />৳{b.total_amount}
                      </span>
                    </div>
                  </div>

                  <div className={styles.cardDivider} />

                  <div className={styles.cardBottom}>
                    <div className={styles.bookingId}>
                      <span className={styles.idLabel}>Booking</span>
                      <span className={styles.idVal}>#{b.booking_id}</span>
                    </div>

                    <div className={styles.cardActions}>
                      {b.status === 'PENDING' && b.expires_at && !expired && (
                        <span className={styles.expiresIn}>
                          <Clock size={11} />
                          Expires {fmtTime(b.expires_at)}
                        </span>
                      )}
                      {b.status === 'PENDING' && expired && (
                        <span className={styles.expiredNote}>Reservation expired</span>
                      )}

                      {b.status === 'PENDING' ? (
                        <button
                          className={`${styles.actionBtn} ${styles.payBtn}`}
                          onClick={() => navigate(`/payment/${b.booking_id}`)}
                        >
                          Pay Now
                          <ChevronRight size={14} />
                        </button>
                      ) : b.status === 'CONFIRMED' ? (
                        <button
                          className={`${styles.actionBtn} ${styles.downloadBtn}`}
                          onClick={() => handleDownloadTicket(b.booking_id)}
                          disabled={isDownloading}
                        >
                          {isDownloading ? (
                            'Downloading...'
                          ) : (
                            <>
                              Download Ticket
                              <Download size={14} />
                            </>
                          )}
                        </button>
                      ) : (
                        <button
                          className={`${styles.actionBtn} ${styles.viewBtn}`}
                          onClick={() => navigate(`/payment/${b.booking_id}`)}
                        >
                          View
                          <ChevronRight size={14} />
                        </button>
                      )}
                    </div>
                  </div>
                </div>
              )
            })}
          </div>
        )}
      </div>
    </div>
  )
}

function EmptyState({
  filter,
  onClear,
  navigate,
}: {
  filter: BookingStatus | 'ALL'
  onClear: () => void
  navigate: ReturnType<typeof useNavigate>
}) {
  return (
    <div className={styles.empty}>
      <div className={styles.emptyIcon}>
        <PackageOpen size={40} />
      </div>
      {filter === 'ALL' ? (
        <>
          <h3>No bookings yet</h3>
          <p>You haven't booked any trips. Start exploring routes!</p>
          <button className={styles.emptyBtn} onClick={() => navigate('/')}>
            Browse Trips <ArrowRight size={15} />
          </button>
        </>
      ) : (
        <>
          <h3>No {STATUS_META[filter]?.label.toLowerCase() || filter.toLowerCase()} bookings</h3>
          <p>Nothing to show for this filter.</p>
          <button className={styles.emptyBtn} onClick={onClear}>
            Show all bookings
          </button>
        </>
      )}
    </div>
  )
}
