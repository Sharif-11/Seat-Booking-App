import { useState } from 'react'
import { useParams, useLocation, useNavigate } from 'react-router-dom'
import {
  ArrowLeft, CheckCircle2, XCircle, CreditCard,
  Phone, Clock, MapPin, AlertTriangle, PartyPopper
} from 'lucide-react'
import { confirmPaymentSuccess, confirmPaymentFailed } from '../api'
import type { BookingResult, Trip } from '../types'
import toast from 'react-hot-toast'
import styles from './Payment.module.css'

const GATEWAYS = [
  { id: 'BKASH',  name: 'bKash',  color: '#e91e8c', bg: 'rgba(233,30,140,0.12)', emoji: '💳' },
  { id: 'NAGAD',  name: 'Nagad',  color: '#f26522', bg: 'rgba(242,101,34,0.12)', emoji: '🔶' },
  { id: 'ROCKET', name: 'Rocket', color: '#8b1fa9', bg: 'rgba(139,31,169,0.12)', emoji: '🚀' },
  { id: 'UPAY',   name: 'Upay',   color: '#00a651', bg: 'rgba(0,166,81,0.12)',   emoji: '💚' },
]

const fmt = (d: string, t: 'time' | 'date') =>
  new Date(d).toLocaleString('en-BD', t === 'time'
    ? { hour: '2-digit', minute: '2-digit', hour12: true }
    : { day: 'numeric', month: 'short', year: 'numeric' })

export default function Payment() {
  const { bookingId } = useParams<{ bookingId: string }>()
  const { state }     = useLocation()
  const navigate      = useNavigate()

  const booking: BookingResult | undefined = state?.booking
  const trip: Trip | undefined             = state?.trip

  const [gateway, setGateway]         = useState('')
  const [walletPhone, setWalletPhone] = useState('')
  const [processing, setProcessing]   = useState(false)
  const [result, setResult]           = useState<'success' | 'fail' | null>(null)
  const [txId, setTxId]               = useState('')

  const buildPayload = () => ({
    status: 'SUCCESS' as const,
    wallet_name:  gateway,
    wallet_phone: walletPhone,
    idempotency_key: `pay_${bookingId}_${Date.now()}`.slice(0, 32),
  })

  const handlePay = async (success: boolean) => {
    if (!gateway)                  { toast.error('Choose a payment method'); return }
    if (walletPhone.length !== 11) { toast.error('Enter valid 11-digit wallet number'); return }
    setProcessing(true)
    try {
      if (success) {
        const res = await confirmPaymentSuccess(Number(bookingId), buildPayload())
        setTxId(res.data.data?.transaction_id ?? '')
        setResult('success')
        toast.success('Payment successful! 🎉')
      } else {
        await confirmPaymentFailed(Number(bookingId), buildPayload())
        setResult('fail')
        toast.error('Payment failed — seats released')
      }
    } catch (e: unknown) {
      const err = e as { response?: { data?: { message?: string } } }
      toast.error(err?.response?.data?.message || 'Something went wrong')
    } finally { setProcessing(false) }
  }

  /* ── Success screen ── */
  if (result === 'success') return (
    <div className={styles.resultPage}>
      <div className={styles.resultCard}>
        <div className={`${styles.resultIcon} ${styles.successIcon}`}>
          <PartyPopper size={44} />
        </div>
        <h2>Booking Confirmed!</h2>
        <p>Your seats are booked. Have a great journey! 🚌</p>
        <div className={styles.txBox}>
          <span>Booking ID</span><strong>#{bookingId}</strong>
          {txId && <><span>Transaction</span><strong className={styles.txId}>{txId.slice(0,18)}…</strong></>}
          <span>Gateway</span><strong>{GATEWAYS.find(g => g.id === gateway)?.name}</strong>
          <span>Amount</span><strong>৳{booking?.total_amount}</strong>
        </div>
        <button className={styles.homeBtn} onClick={() => navigate('/')} type="button">
          Back to Home
        </button>
      </div>
    </div>
  )

  /* ── Fail screen ── */
  if (result === 'fail') return (
    <div className={styles.resultPage}>
      <div className={styles.resultCard}>
        <div className={`${styles.resultIcon} ${styles.failIcon}`}>
          <XCircle size={44} />
        </div>
        <h2>Payment Failed</h2>
        <p>Your payment was not processed. Seats have been released.</p>
        <button className={styles.homeBtn} onClick={() => navigate('/')} type="button">Back to Home</button>
        <button className={styles.retryBtn} onClick={() => navigate(-1)} type="button">Try Again</button>
      </div>
    </div>
  )

  /* ── Payment form ── */
  return (
    <main className={styles.page}>
      <div className={styles.inner}>
        <div className={styles.header}>
          <button className={styles.backBtn} onClick={() => navigate(-1)} type="button">
            <ArrowLeft size={17} />
          </button>
          <h1 className={styles.title}>Complete Payment</h1>
        </div>

        <div className={styles.layout}>
          {/* Order summary */}
          <div className={styles.summary}>
            <div className={styles.summaryHead}>
              <CreditCard size={16} /><h3>Order Summary</h3>
            </div>
            <div className={styles.summaryBody}>
              {trip && (
                <>
                  <div className={styles.sRow}>
                    <span><MapPin size={12} />Route</span>
                    <span>{trip.from_location} → {trip.to_location}</span>
                  </div>
                  {trip.title && (
                    <div className={styles.sRow}>
                      <span>Bus</span>
                      <span className={styles.italic}>{trip.title}</span>
                    </div>
                  )}
                  <div className={styles.sRow}>
                    <span><Clock size={12} />Departs</span>
                    <span>{fmt(trip.departure_time,'time')}, {fmt(trip.departure_time,'date')}</span>
                  </div>
                </>
              )}
              {booking && (
                <>
                  <div className={styles.sRow}>
                    <span>Booking #</span><span>#{booking.booking_id}</span>
                  </div>
                  <div className={styles.sRow}>
                    <span>Seats</span><span>{booking.seat_ids.length} seat(s)</span>
                  </div>
                  <div className={styles.sRow}>
                    <span><Clock size={12} />Expires</span>
                    <span className={styles.expires}>{fmt(booking.expires_at,'time')}</span>
                  </div>
                  <div className={`${styles.sRow} ${styles.sTotal}`}>
                    <span>Total</span>
                    <span className={styles.totalAmt}>৳{booking.total_amount}</span>
                  </div>
                </>
              )}
            </div>
          </div>

          {/* Payment form */}
          <div className={styles.payForm}>
            <h3 className={styles.payTitle}>Payment Method</h3>

            <div className={styles.gateways}>
              {GATEWAYS.map(gw => (
                <button key={gw.id} type="button"
                  className={`${styles.gw} ${gateway === gw.id ? styles.gwActive : ''}`}
                  style={gateway === gw.id ? { borderColor: gw.color, background: gw.bg } : {}}
                  onClick={() => setGateway(gw.id)}>
                  <span className={styles.gwEmoji}>{gw.emoji}</span>
                  <span className={styles.gwName}>{gw.name}</span>
                </button>
              ))}
            </div>

            <div className={styles.phoneField}>
              <label><Phone size={13} /> Wallet Number</label>
              <div className={styles.phoneWrap}>
                <span className={styles.prefix}>+880</span>
                <input
                  type="tel" placeholder="01XXXXXXXXX" maxLength={11}
                  value={walletPhone}
                  onChange={e => setWalletPhone(e.target.value.replace(/\D/g,'').slice(0,11))}
                  className={styles.phoneInput}
                />
              </div>
            </div>

            <div className={styles.demoNote}>
              <AlertTriangle size={13} /> Demo mode — no real transaction occurs
            </div>

            <div className={styles.actions}>
              <button className={`${styles.actBtn} ${styles.successBtn}`}
                onClick={() => handlePay(true)} disabled={processing} type="button">
                {processing ? <span className="spinner" /> : <CheckCircle2 size={17} />}
                Simulate Success
              </button>
              <button className={`${styles.actBtn} ${styles.failBtn}`}
                onClick={() => handlePay(false)} disabled={processing} type="button">
                {processing ? <span className="spinner spinner--terra" /> : <XCircle size={17} />}
                Simulate Failure
              </button>
            </div>
          </div>
        </div>
      </div>
    </main>
  )
}
