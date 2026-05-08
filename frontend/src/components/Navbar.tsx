import { Bus, LogOut, Settings, Ticket, User } from 'lucide-react'
import { useState } from 'react'
import { Link, useLocation } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'
import LoginModal from './LoginModal'
import styles from './Navbar.module.css'

export default function Navbar() {
  const { user, isAuthenticated, logout } = useAuth()
  const [showLogin, setShowLogin] = useState(false)
  const { pathname } = useLocation()

  return (
    <>
      <nav className={styles.nav}>
        <div className={styles.inner}>
          <Link to='/' className={styles.logo}>
            <div className={styles.logoIcon}>
              <Bus size={16} strokeWidth={2.5} />
            </div>
            <span>
              Yatra<em>BD</em>
            </span>
          </Link>

          <div className={styles.links}>
            <Link
              to='/admin'
              className={`${styles.link} ${pathname === '/admin' ? styles.linkActive : ''}`}
            >
              <Settings size={15} />
              <span>Admin</span>
            </Link>
            {isAuthenticated && (
              <Link
                to='/bookings'
                className={`${styles.link} ${pathname === '/bookings' ? styles.linkActive : ''}`}
              >
                <Ticket size={15} />
                <span>Bookings</span>
              </Link>
            )}

            {isAuthenticated ? (
              <div className={styles.userRow}>
                <div className={styles.userBadge}>
                  <Ticket size={13} />
                  <span>···{user?.phone?.slice(-4)}</span>
                </div>
                <button className={styles.logoutBtn} onClick={logout} title='Sign out'>
                  <LogOut size={14} />
                </button>
              </div>
            ) : (
              <button className={styles.signInBtn} onClick={() => setShowLogin(true)}>
                <User size={14} />
                <span>Sign In</span>
              </button>
            )}
          </div>
        </div>
      </nav>

      {showLogin && <LoginModal onClose={() => setShowLogin(false)} />}
    </>
  )
}
