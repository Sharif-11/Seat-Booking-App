import type { Seat } from '../types'
import styles from './SeatMap.module.css'

interface Props {
  seats: Seat[]
  selected: number[]
  onSeatClick: (seat: Seat) => void
}

const LEGEND = [
  { key: 'AVAILABLE', label: 'Available', cls: 'avail'  },
  { key: 'SELECTED',  label: 'Selected',  cls: 'sel'    },
  { key: 'BOOKED',    label: 'Booked',    cls: 'booked' },
  { key: 'RESERVED',  label: 'Reserved',  cls: 'rsvd'   },
]

export default function SeatMap({ seats, selected, onSeatClick }: Props) {
  const rows = seats.reduce<Record<string, Seat[]>>((acc, s) => {
    const row = s.seat_label[0]
    if (!acc[row]) acc[row] = []
    acc[row].push(s)
    return acc
  }, {})

  const getSeatState = (seat: Seat): string => {
    if (selected.includes(seat.id))  return 'sel'
    if (seat.status === 'BOOKED')    return 'booked'
    if (seat.status === 'RESERVED')  return 'rsvd'
    return 'avail'
  }

  return (
    <div className={styles.wrap}>
      <div className={styles.bus}>
        {/* Front / windshield */}
        <div className={styles.front}>
          <div className={styles.windshield}>
            <div className={styles.wiper} />
            <div className={styles.wiperR} />
          </div>
          <div className={styles.frontBar}>
            <div className={styles.headlight} />
            <span className={styles.busName}>BD Express</span>
            <div className={styles.headlight} />
          </div>
        </div>

        {/* Cabin */}
        <div className={styles.cabin}>
          {/* Driver row */}
          <div className={styles.driverRow}>
            <div className={styles.driverSeat}>
              <span>🎛</span>
              <span className={styles.tiny}>Driver</span>
            </div>
            <div className={styles.doorBox}>
              <div className={styles.door} />
              <span className={styles.tiny}>Door</span>
            </div>
          </div>

          {/* Seat rows */}
          <div className={styles.seatsWrap}>
            {Object.entries(rows).map(([rowLetter, rowSeats]) => {
              const left  = rowSeats.filter(s => parseInt(s.seat_label.slice(1)) <= 2)
              const right = rowSeats.filter(s => parseInt(s.seat_label.slice(1)) > 2)
              return (
                <div key={rowLetter} className={styles.row}>
                  <div className={styles.group}>
                    {left.map(seat => {
                      const st       = getSeatState(seat)
                      const disabled = seat.status !== 'AVAILABLE' && !selected.includes(seat.id)
                      return (
                        <button
                          key={seat.id}
                          className={`${styles.seat} ${styles[st]}`}
                          onClick={() => onSeatClick(seat)}
                          disabled={disabled}
                          title={`${seat.seat_label} — ${seat.status}`}
                          type="button"
                        >
                          <span className={styles.seatLbl}>{seat.seat_label}</span>
                        </button>
                      )
                    })}
                  </div>
                  <div className={styles.aisle}>
                    <span className={styles.aisleLabel}>{rowLetter}</span>
                  </div>
                  <div className={styles.group}>
                    {right.map(seat => {
                      const st       = getSeatState(seat)
                      const disabled = seat.status !== 'AVAILABLE' && !selected.includes(seat.id)
                      return (
                        <button
                          key={seat.id}
                          className={`${styles.seat} ${styles[st]}`}
                          onClick={() => onSeatClick(seat)}
                          disabled={disabled}
                          title={`${seat.seat_label} — ${seat.status}`}
                          type="button"
                        >
                          <span className={styles.seatLbl}>{seat.seat_label}</span>
                        </button>
                      )
                    })}
                  </div>
                </div>
              )
            })}
          </div>
        </div>

        {/* Rear */}
        <div className={styles.rear}>
          <div className={styles.rearLights}>
            <div className={styles.tailLight} />
            <div className={styles.tailLight} />
          </div>
        </div>
      </div>

      {/* Legend */}
      <div className={styles.legend}>
        {LEGEND.map(l => (
          <div key={l.key} className={styles.legendItem}>
            <div className={`${styles.legendDot} ${styles[l.cls]}`} />
            <span>{l.label}</span>
          </div>
        ))}
      </div>
    </div>
  )
}
