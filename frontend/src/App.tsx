import { Toaster } from 'react-hot-toast'
import { BrowserRouter, Route, Routes } from 'react-router-dom'
import Navbar from './components/Navbar'
import { AuthProvider } from './context/AuthContext'
import Admin from './pages/Admin'
import Home from './pages/Home'
import Payment from './pages/Payment'
import TripDetail from './pages/TripDetail'
import MyBookings from './pages/MyBookings'

export default function App() {
  return (
    <AuthProvider>
      <BrowserRouter>
        <Toaster
          position='top-center'
          toastOptions={{
            duration: 3500,
            style: {
              fontFamily: "'Plus Jakarta Sans', sans-serif",
              fontSize: '0.875rem',
              fontWeight: 600,
              borderRadius: '10px',
              background: '#2a2319',
              color: '#f0e4d0',
              border: '1px solid #4d4033',
            },
            success: {
              iconTheme: { primary: '#4caf82', secondary: '#2a2319' },
            },
            error: {
              iconTheme: { primary: '#e05252', secondary: '#2a2319' },
            },
          }}
        />
        <Navbar />
        <Routes>
          <Route path='/' element={<Home />} />
          <Route path='/trip/:id' element={<TripDetail />} />
          <Route path='/payment/:bookingId' element={<Payment />} />
          <Route path='/admin' element={<Admin />} />
          <Route path='/bookings' element={<MyBookings />} />
        </Routes>
      </BrowserRouter>
    </AuthProvider>
  )
}
