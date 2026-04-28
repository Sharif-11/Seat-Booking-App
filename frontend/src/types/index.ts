export interface Trip {
  id: number
  title: string
  from_location: string
  to_location: string
  departure_time: string
  price: number
  created_at: string
}

export interface Seat {
  id: number
  seat_label: string
  status: 'AVAILABLE' | 'RESERVED' | 'BOOKED'
}

export interface BookingResult {
  booking_id: number
  seat_ids: number[]
  show_id: number
  total_amount: number
  expires_at: string
}

export interface User {
  user_id: number
  phone: string
}

export interface OtpRequestResponse {
  status: string
  status_code: number
  message: string
  data?: {
    user_id?: number
    phone?: string
    token?: string
    remaining_seconds?: number
  }
}
export type BookingStatus = 'PENDING' | 'CONFIRMED' | 'EXPIRED' | 'FAILED' | 'CANCELLED'

export interface MyBooking {
  booking_id: number
  user_id: number
  show_id: number
  status: BookingStatus
  total_amount: number
  expires_at: string
  created_at: string
  seats: [
    {
      id: number
      seat_label: string
    },
  ]
}
