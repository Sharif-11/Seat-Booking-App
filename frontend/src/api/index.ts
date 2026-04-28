import axios from 'axios'
import type { OtpRequestResponse } from '../types'

const BASE = 'http://localhost:8000'

const api = axios.create({ baseURL: BASE, headers: { 'Content-Type': 'application/json' } })

api.interceptors.request.use(cfg => {
  const t = localStorage.getItem('token')
  if (t) cfg.headers.Authorization = `Bearer ${t}`
  return cfg
})

// ── Auth ──────────────────────────────────────────────────────────────────────
export const requestOtp = (phone: string) =>
  api.post<OtpRequestResponse>('/auth/request-otp', { phone })

export const verifyOtp = (phone: string, otp: string) =>
  api.post<OtpRequestResponse>('/auth/verify-otp', { phone, otp })

export const getMyBookings = () => api.get('/booking')
// ── Shows / Trips
export const downloadTicketSlip = (bookingId: number) => api.get(`/booking/${bookingId}/ticket`)
export const searchTrips = (from_location: string, to_location: string) =>
  api.get('/shows/list', { params: { from_location, to_location } })

export const getSeats = (showId: number) => api.get(`/shows/${showId}/seats`)

export interface CreateTripPayload {
  title: string
  from_location: string
  to_location: string
  departure_time: string
  price: number
  seat_count: number
}
export const createTrip = (data: CreateTripPayload) => api.post('/shows/create', data)

export interface UpdateTripPayload {
  title: string
  from_location: string
  to_location: string
  departure_time: string
  price: number
}
export const updateTrip = (id: number, data: UpdateTripPayload) =>
  api.put(`/shows/update/${id}`, data)

// ── Booking ───────────────────────────────────────────────────────────────────
export const createBooking = (show_id: number, seat_ids: number[]) =>
  api.post('/booking/', {
    show_id,
    seat_ids,
    idempotency_key: `bk_${show_id}_${Date.now()}_${Math.random().toString(36).slice(2, 10)}`,
  })

export interface PaymentPayload {
  status: 'SUCCESS'
  wallet_name: string
  wallet_phone: string
  idempotency_key: string
}

export const confirmPaymentSuccess = (bookingId: number, payload: PaymentPayload) =>
  api.post(`/booking/${bookingId}/success`, payload)

export const confirmPaymentFailed = (bookingId: number, payload: PaymentPayload) =>
  api.post(`/booking/${bookingId}/failed`, payload)

export default api
