import { useState, useRef, useEffect, type KeyboardEvent } from 'react'
import { X, Phone, ShieldCheck, RefreshCw, ArrowRight } from 'lucide-react'
import { requestOtp, verifyOtp } from '../api'
import { useAuth } from '../context/AuthContext'
import toast from 'react-hot-toast'
import styles from './LoginModal.module.css'

interface Props {
  onClose: () => void
  onSuccess?: () => void
}

export default function LoginModal({ onClose, onSuccess }: Props) {
  const { login } = useAuth()
  const [phone, setPhone]     = useState('')
  const [otp, setOtp]         = useState<string[]>(['','','','','',''])
  const [otpSent, setOtpSent] = useState(false)
  const [loading, setLoading] = useState(false)
  const [cooldown, setCooldown] = useState(0)
  const otpRefs  = useRef<(HTMLInputElement | null)[]>([])
  const timerRef = useRef<ReturnType<typeof setInterval> | null>(null)

  useEffect(() => () => { if (timerRef.current) clearInterval(timerRef.current) }, [])

  const startCooldown = (secs: number) => {
    setCooldown(secs)
    if (timerRef.current) clearInterval(timerRef.current)
    timerRef.current = setInterval(() => {
      setCooldown(p => {
        if (p <= 1) { clearInterval(timerRef.current!); return 0 }
        return p - 1
      })
    }, 1000)
  }

  const handleSendOtp = async () => {
    if (phone.length !== 11) { toast.error('Enter a valid 11-digit number'); return }
    setLoading(true)
    try {
      const res  = await requestOtp(phone)
      const data = res.data

      // Already verified — token comes back immediately
      if (data.data?.token) {
        login({ user_id: data.data.user_id!, phone: data.data.phone! }, data.data.token)
        toast.success('Welcome back! 👋')
        onSuccess?.(); onClose(); return
      }
      // OTP already in-flight — use remaining_seconds for cooldown
      if (data.data?.remaining_seconds) {
        startCooldown(data.data.remaining_seconds)
        toast.success('OTP already sent — check your phone')
        setOtpSent(true)
        setTimeout(() => otpRefs.current[0]?.focus(), 80)
        return
      }
      // Fresh OTP sent
      setOtpSent(true)
      startCooldown(60)
      toast.success('OTP sent! Check your phone 📱')
      setTimeout(() => otpRefs.current[0]?.focus(), 80)
    } catch (e: unknown) {
      const err = e as { response?: { data?: { message?: string } } }
      toast.error(err?.response?.data?.message || 'Failed to send OTP')
    } finally { setLoading(false) }
  }

  const handleOtpChange = (i: number, val: string) => {
    if (!/^\d*$/.test(val)) return
    const next = [...otp]; next[i] = val.slice(-1); setOtp(next)
    if (val && i < 5) otpRefs.current[i + 1]?.focus()
    if (next.every(d => d)) handleVerify(next.join(''))
  }

  const handleOtpKeyDown = (i: number, e: KeyboardEvent<HTMLInputElement>) => {
    if (e.key === 'Backspace' && !otp[i] && i > 0) otpRefs.current[i - 1]?.focus()
  }

  const handleVerify = async (code: string) => {
    if (code.length !== 6) { toast.error('Enter all 6 digits'); return }
    setLoading(true)
    try {
      const res  = await verifyOtp(phone, code)
      const data = res.data

      if (data.status === 'error' || (data.status_code && data.status_code >= 400)) {
        toast.error(data.message || 'Verification failed')
        setOtp(['','','','','',''])
        otpRefs.current[0]?.focus()
        return
      }
      if (data.data?.token) {
        login({ user_id: data.data.user_id!, phone: data.data.phone! }, data.data.token)
        toast.success('Verified! Welcome 🎉')
        onSuccess?.(); onClose()
      }
    } catch (e: unknown) {
      const err = e as { response?: { data?: { message?: string } } }
      toast.error(err?.response?.data?.message || 'Verification failed')
      setOtp(['','','','','',''])
      otpRefs.current[0]?.focus()
    } finally { setLoading(false) }
  }

  const handleResend = async () => {
    if (cooldown > 0) return
    setLoading(true)
    try {
      const res = await requestOtp(phone)
      const remaining = res.data.data?.remaining_seconds
      startCooldown(remaining ?? 60)
      setOtp(['','','','','',''])
      toast.success('OTP resent!')
      setTimeout(() => otpRefs.current[0]?.focus(), 80)
    } catch { toast.error('Could not resend OTP') }
    finally   { setLoading(false) }
  }

  return (
    <div className="modal-overlay" onClick={e => e.target === e.currentTarget && onClose()}>
      <div className={styles.modal}>
        <button className={styles.closeBtn} onClick={onClose} type="button"><X size={16} /></button>

        <div className={styles.header}>
          <div className={styles.headerIcon}><ShieldCheck size={22} /></div>
          <h2>Sign In</h2>
          <p>Enter your mobile number to continue</p>
        </div>

        <div className={styles.body}>
          {/* Phone — always visible */}
          <div className={styles.field}>
            <label htmlFor="lm-phone">Mobile Number</label>
            <div className={`${styles.phoneWrap} ${otpSent ? styles.phoneWrapFilled : ''}`}>
              <Phone size={14} className={styles.phoneIcon} />
              <span className={styles.prefix}>+880</span>
              <input
                id="lm-phone" type="tel"
                placeholder="01XXXXXXXXX"
                value={phone}
                onChange={e => setPhone(e.target.value.replace(/\D/g,'').slice(0,11))}
                onKeyDown={e => e.key === 'Enter' && !otpSent && handleSendOtp()}
                disabled={otpSent}
                maxLength={11}
                className={styles.phoneInput}
              />
              {otpSent && (
                <button className={styles.changeBtn} type="button"
                  onClick={() => { setOtpSent(false); setOtp(['','','','','','']); setCooldown(0) }}>
                  Change
                </button>
              )}
            </div>
          </div>

          {/* OTP — slides in */}
          {otpSent && (
            <div className={styles.otpBlock}>
              <label>6-Digit OTP</label>
              <p className={styles.otpHint}>Sent to <strong>{phone}</strong></p>
              <div className={styles.otpRow}>
                {otp.map((d, i) => (
                  <input
                    key={i}
                    ref={el => { otpRefs.current[i] = el }}
                    className={`${styles.otpBox} ${d ? styles.otpBoxFilled : ''}`}
                    type="tel" inputMode="numeric"
                    maxLength={1} value={d}
                    onChange={e => handleOtpChange(i, e.target.value)}
                    onKeyDown={e => handleOtpKeyDown(i, e)}
                    aria-label={`OTP digit ${i + 1}`}
                  />
                ))}
              </div>
              <button
                className={styles.resendBtn}
                onClick={handleResend}
                disabled={cooldown > 0 || loading}
                type="button"
              >
                <RefreshCw size={12} />
                {cooldown > 0 ? `Resend in ${cooldown}s` : 'Resend OTP'}
              </button>
            </div>
          )}

          {/* CTA */}
          {!otpSent ? (
            <button className={styles.cta} onClick={handleSendOtp}
              disabled={loading || phone.length !== 11} type="button">
              {loading
                ? <span className="spinner" />
                : <><span>Send OTP</span><ArrowRight size={16} /></>}
            </button>
          ) : (
            <button className={styles.cta} onClick={() => handleVerify(otp.join(''))}
              disabled={loading || otp.some(d => !d)} type="button">
              {loading
                ? <span className="spinner" />
                : <><span>Verify &amp; Continue</span><ArrowRight size={16} /></>}
            </button>
          )}
        </div>
      </div>
    </div>
  )
}
