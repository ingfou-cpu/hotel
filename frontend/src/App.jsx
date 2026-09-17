// App.jsx — Routes principales avec React Router v7 + lazy loading
import React, { Suspense, lazy } from 'react'
import { Routes, Route, Outlet } from 'react-router-dom'
import Layout from './components/Layout'
import PrivateRoute from './components/PrivateRoute'
import ManagerRoute from './components/ManagerRoute'
import Spinner from './components/Spinner'

// Pages publiques
const HomePage = lazy(() => import('./pages/HomePage'))
const NewsPage = lazy(() => import('./pages/NewsPage'))
const HotelDetailPage = lazy(() => import('./pages/HotelDetailPage'))
const LoginPage = lazy(() => import('./pages/LoginPage'))
const RegisterPage = lazy(() => import('./pages/RegisterPage'))
const PaymentSuccessPage = lazy(() => import('./pages/PaymentSuccessPage'))
const PaymentCancelPage = lazy(() => import('./pages/PaymentCancelPage'))

// Pages privées (auth requise)
const BookingPage = lazy(() => import('./pages/BookingPage'))
const BookingDetailPage = lazy(() => import('./pages/BookingDetailPage'))
const MyBookingsPage = lazy(() => import('./pages/MyBookingsPage'))
const ProfilePage = lazy(() => import('./pages/ProfilePage'))
const FavoritesPage = lazy(() => import('./pages/FavoritesPage'))
const NotificationsPage = lazy(() => import('./pages/NotificationsPage'))

// Pages manager (rôle hotel_manager/admin/staff requis)
const DashboardPage = lazy(() => import('./pages/manager/DashboardPage'))
const ManagerHotelsPage = lazy(() => import('./pages/manager/ManagerHotelsPage'))
const HotelFormPage = lazy(() => import('./pages/manager/HotelFormPage'))
const ManagerRoomsPage = lazy(() => import('./pages/manager/ManagerRoomsPage'))
const RoomFormPage = lazy(() => import('./pages/manager/RoomFormPage'))
const ManagerBookingsPage = lazy(() => import('./pages/manager/ManagerBookingsPage'))
const ManagerPaymentsPage = lazy(() => import('./pages/manager/ManagerPaymentsPage'))

// 404
const NotFoundPage = lazy(() => import('./pages/NotFoundPage'))

const LoadingFallback = () => (
  <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', minHeight: '50vh' }}>
    <Spinner size="lg" ariaLabel="Chargement de la page" />
  </div>
)

export default function App() {
  return (
    <Suspense fallback={<LoadingFallback />}>
      <Routes>
        {/* Layout partagé pour toutes les routes */}
        <Route element={<Layout />}>
          {/* Routes publiques */}
          <Route path="/" element={<HomePage />} />
          <Route path="/actualites" element={<NewsPage />} />
          <Route path="/hotels/:id" element={<HotelDetailPage />} />
          <Route path="/connexion" element={<LoginPage />} />
          <Route path="/inscription" element={<RegisterPage />} />
          <Route path="/reservation/success" element={<PaymentSuccessPage />} />
          <Route path="/reservation/annulation" element={<PaymentCancelPage />} />

          {/* Routes privées (utilisateur connecté) */}
          <Route element={<PrivateRoute><Outlet /></PrivateRoute>}>
            <Route path="/reservation" element={<BookingPage />} />
            <Route path="/reservation/:bookingCode" element={<BookingDetailPage />} />
            <Route path="/mes-reservations" element={<MyBookingsPage />} />
            <Route path="/profil" element={<ProfilePage />} />
            <Route path="/favoris" element={<FavoritesPage />} />
            <Route path="/notifications" element={<NotificationsPage />} />
          </Route>

          {/* Routes manager (gestionnaire/admin) */}
          <Route element={<ManagerRoute><Outlet /></ManagerRoute>}>
            <Route path="/back-office" element={<DashboardPage />} />
            <Route path="/back-office/hotels" element={<ManagerHotelsPage />} />
            <Route path="/back-office/hotels/nouveau" element={<HotelFormPage />} />
            <Route path="/back-office/hotels/:id/modifier" element={<HotelFormPage />} />
            <Route path="/back-office/hotels/:id/chambres" element={<ManagerRoomsPage />} />
            <Route path="/back-office/hotels/:id/chambres/nouveau" element={<RoomFormPage />} />
            <Route path="/back-office/chambres/:roomId/modifier" element={<RoomFormPage />} />
            <Route path="/back-office/reservations" element={<ManagerBookingsPage />} />
            <Route path="/back-office/paiements" element={<ManagerPaymentsPage />} />
          </Route>

          {/* 404 - doit être en dernier */}
          <Route path="*" element={<NotFoundPage />} />
        </Route>
      </Routes>
    </Suspense>
  )
}