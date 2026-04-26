import { BrowserRouter, Routes, Route } from 'react-router-dom'
import { Toaster } from 'react-hot-toast'
import { AuthProvider } from './context/AuthContext'
import Navbar from './components/Navbar'
import Home from './pages/Home'
import TripDetail from './pages/TripDetail'
import Payment from './pages/Payment'
import Admin from './pages/Admin'

export default function App() {
  return (
    <AuthProvider>
      <BrowserRouter>
        <Toaster
          position="top-center"
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
          <Route path="/"                      element={<Home />} />
          <Route path="/trip/:id"              element={<TripDetail />} />
          <Route path="/payment/:bookingId"    element={<Payment />} />
          <Route path="/admin"                 element={<Admin />} />
        </Routes>
      </BrowserRouter>
    </AuthProvider>
  )
}
