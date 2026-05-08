import { ArrowLeft, Clock, RefreshCw, ShoppingBag, Tag, Ticket, X } from 'lucide-react'
import { useEffect, useRef, useState } from 'react'
import toast from 'react-hot-toast'
import { useLocation, useNavigate, useParams } from 'react-router-dom'
import { createBooking, getSeats } from '../api'
import { getSocket } from '../api/socket'
import LoginModal from '../components/LoginModal'
import SeatMap from '../components/SeatMap'
import { useAuth } from '../context/AuthContext'
import type { BookingResult, Seat, Trip } from '../types'
import styles from './TripDetail.module.css'

const fmt = (d: string, t: 'time' | 'date') =>
  new Date(d).toLocaleString(
    'en-BD',
    t === 'time'
      ? { hour: '2-digit', minute: '2-digit', hour12: true }
      : { day: 'numeric', month: 'short', year: 'numeric' }
  )

export default function TripDetail() {
  const { id } = useParams<{ id: string }>()
  const { state } = useLocation()
  const navigate = useNavigate()
  const { isAuthenticated } = useAuth()

  const trip: Trip | undefined = state?.trip
  const [seats, setSeats] = useState<Seat[]>([])
  const [selected, setSelected] = useState<number[]>([])
  const [loadingSeats, setLoadingSeats] = useState(true)
  const [booking, setBooking] = useState(false)
  const [showLogin, setShowLogin] = useState(false)
  const [pendingCheckout, setPendingCheckout] = useState(false)
  const socketRef = useRef<any>(null)

  const load = async () => {
    setLoadingSeats(true)
    try {
      const res = await getSeats(Number(id))
      setSeats(res.data.data ?? [])
    } catch {
      toast.error('Failed to load seat map')
    } finally {
      setLoadingSeats(false)
    }
  }

  useEffect(() => {
    load()
  }, [id])
  useEffect(() => {
    if (!id) return

    const socket = getSocket()
    socketRef.current = socket

    // Wait for connection before joining room
    const onConnect = () => {
      console.log('✅ Connected:', socket.id)
      socket.emit('join_show', { show_id: id })
    }

    // Handler for when socket is already connected
    if (socket.connected) {
      onConnect()
    } else {
      socket.on('connect', onConnect)
    }

    // Listen for seat updates
    const onSeatUpdate = (data: Seat[]) => {
      console.log('📡 Seat update:', data)
      setSeats(data)
    }
    socket.on('seat_update', onSeatUpdate)

    // Cleanup function
    return () => {
      console.log('❌ Leaving room and cleaning up:', id)

      // Remove event listeners
      socket.off('connect', onConnect)
      socket.off('seat_update', onSeatUpdate)

      // Leave the room if socket is still connected
      if (socket.connected) {
        socket.emit('leave_show', { show_id: id })
      }
    }
  }, [id]) // Only re-run if id changes

  const handleSeatClick = (seat: Seat) => {
    if (seat.status !== 'AVAILABLE') return
    setSelected(p => (p.includes(seat.id) ? p.filter(x => x !== seat.id) : [...p, seat.id]))
  }

  const doBooking = async () => {
    if (!selected.length) return
    setBooking(true)
    try {
      const res = await createBooking(Number(id), selected)
      const bk: BookingResult = res.data.data
      toast.success('Seats reserved! Complete payment →')
      navigate(`/payment/${bk.booking_id}`, { state: { booking: bk, trip } })
    } catch (e: unknown) {
      const err = e as { response?: { data?: { message?: string } } }
      toast.error(err?.response?.data?.message || 'Booking failed')
    } finally {
      setBooking(false)
    }
  }

  const handleCheckout = () => {
    if (!selected.length) {
      toast.error('Select at least one seat')
      return
    }
    if (!isAuthenticated) {
      setPendingCheckout(true)
      setShowLogin(true)
      return
    }
    doBooking()
  }

  const handleLoginSuccess = () => {
    if (pendingCheckout) {
      setPendingCheckout(false)
      doBooking()
    }
  }

  const selectedSeats = seats.filter(s => selected.includes(s.id))
  const total = selected.length * (trip?.price ?? 0)
  const available = seats.filter(s => s.status === 'AVAILABLE').length

  return (
    <main className={styles.page}>
      {/* Header */}
      <div className={styles.header}>
        <div className={styles.headerInner}>
          <button className={styles.backBtn} onClick={() => navigate(-1)} type='button'>
            <ArrowLeft size={17} />
          </button>
          <div className={styles.tripInfo}>
            <h1 className={styles.routeHead}>
              <span className={styles.loc}>{trip?.from_location ?? '—'}</span>
              <span className={styles.arrow}>→</span>
              <span className={styles.loc}>{trip?.to_location ?? '—'}</span>
            </h1>
            {trip?.title && <p className={styles.tripName}>{trip.title}</p>}
            <div className={styles.tripMeta}>
              {trip && (
                <>
                  <span>
                    <Clock size={12} />
                    {fmt(trip.departure_time, 'time')}
                  </span>
                  <span className={styles.sep}>·</span>
                  <span>{fmt(trip.departure_time, 'date')}</span>
                  <span className={styles.sep}>·</span>
                  <span>
                    <Tag size={12} />৳{trip.price}/seat
                  </span>
                </>
              )}
            </div>
          </div>
          <button
            className={`${styles.refreshBtn} ${loadingSeats ? styles.spinning : ''}`}
            onClick={load}
            disabled={loadingSeats}
            type='button'
            title='Refresh seat map'
          >
            <RefreshCw size={15} />
          </button>
        </div>
      </div>

      <div className={styles.body}>
        {/* Seat section */}
        <section className={styles.seatSection}>
          <div className={styles.seatHead}>
            <h2>Select Seats</h2>
            {!loadingSeats && <span className={styles.availBadge}>{available} available</span>}
          </div>

          {loadingSeats ? (
            <div className={styles.seatLoading}>
              <span className='spinner spinner--terra' style={{ width: 30, height: 30 }} />
              <p>Loading seat map…</p>
            </div>
          ) : (
            <SeatMap seats={seats} selected={selected} onSeatClick={handleSeatClick} />
          )}
        </section>

        {/* Checkout panel */}
        {selected.length > 0 && (
          <aside className={styles.checkout}>
            <div className={styles.checkoutCard}>
              <div className={styles.checkoutHead}>
                <ShoppingBag size={16} />
                <h3>Booking Summary</h3>
                <button className={styles.clearBtn} onClick={() => setSelected([])} type='button'>
                  <X size={13} /> Clear
                </button>
              </div>

              <div className={styles.checkoutBody}>
                <div className={styles.row}>
                  <span>Route</span>
                  <span className={styles.val}>
                    {trip?.from_location} → {trip?.to_location}
                  </span>
                </div>
                {trip?.title && (
                  <div className={styles.row}>
                    <span>Bus</span>
                    <span className={`${styles.val} ${styles.valItalic}`}>{trip.title}</span>
                  </div>
                )}
                <div className={styles.row}>
                  <span>Departs</span>
                  <span className={styles.val}>
                    {trip
                      ? `${fmt(trip.departure_time, 'time')}, ${fmt(trip.departure_time, 'date')}`
                      : '—'}
                  </span>
                </div>
                <div className={styles.row}>
                  <span>Seats ({selected.length})</span>
                  <div className={styles.chips}>
                    {selectedSeats.map(s => (
                      <span key={s.id} className={styles.chip}>
                        {s.seat_label}
                      </span>
                    ))}
                  </div>
                </div>
                <div className={styles.row}>
                  <span>Per seat</span>
                  <span className={styles.val}>৳{trip?.price}</span>
                </div>
                <div className={`${styles.row} ${styles.totalRow}`}>
                  <span>Total</span>
                  <span className={styles.total}>৳{total}</span>
                </div>
              </div>

              <button
                className={styles.checkoutBtn}
                onClick={handleCheckout}
                disabled={booking}
                type='button'
              >
                {booking ? (
                  <>
                    <span className='spinner' />
                    Reserving…
                  </>
                ) : (
                  <>
                    <Ticket size={16} />
                    Proceed to Pay
                  </>
                )}
              </button>

              {!isAuthenticated && (
                <p className={styles.authHint}>🔐 Sign in required to complete booking</p>
              )}
            </div>
          </aside>
        )}
      </div>

      {showLogin && (
        <LoginModal
          onClose={() => {
            setShowLogin(false)
            setPendingCheckout(false)
          }}
          onSuccess={handleLoginSuccess}
        />
      )}
    </main>
  )
}
