import { Routes, Route, Navigate } from 'react-router-dom'
import { useAuthStore } from './store/auth'
import Welcome from './pages/Welcome'
import Login from './pages/Login'
import Register from './pages/Register'
import ZipStep from './pages/onboarding/ZipStep'
import TransportStep from './pages/onboarding/TransportStep'
import CommuteStep from './pages/onboarding/CommuteStep'
import DietStep from './pages/onboarding/DietStep'
import HomeStep from './pages/onboarding/HomeStep'
import PetStep from './pages/onboarding/PetStep'
import Dashboard from './pages/Dashboard'
import Community from './pages/Community'
import Progress from './pages/Progress'
import Profile from './pages/Profile'
import BottomNav from './components/layout/BottomNav'
import TopBar from './components/layout/TopBar'
import OnboardingShell from './components/onboarding/OnboardingShell'

function ProtectedRoute({ children }) {
  const token = useAuthStore((s) => s.token)
  if (!token) return <Navigate to="/login" replace />
  return children
}

function AppLayout({ children }) {
  return (
    <div className="min-h-screen bg-surface flex flex-col max-w-md mx-auto">
      <TopBar />
      <main className="flex-1 pb-20 overflow-y-auto">{children}</main>
      <BottomNav />
    </div>
  )
}

export default function App() {
  const token = useAuthStore((s) => s.token)

  return (
    <Routes>
      <Route path="/" element={<Navigate to={token ? '/home' : '/welcome'} replace />} />
      <Route path="/welcome" element={<Welcome />} />
      <Route path="/login" element={<Login />} />
      <Route path="/register" element={<Register />} />
      <Route path="/onboarding" element={<OnboardingShell />}>
        <Route path="zip" element={<ZipStep />} />
        <Route path="transport" element={<TransportStep />} />
        <Route path="commute" element={<CommuteStep />} />
        <Route path="diet" element={<DietStep />} />
        <Route path="home" element={<HomeStep />} />
        <Route path="pet" element={<PetStep />} />
      </Route>
      <Route
        path="/home"
        element={
          <ProtectedRoute>
            <AppLayout><Dashboard /></AppLayout>
          </ProtectedRoute>
        }
      />
      <Route
        path="/community"
        element={
          <ProtectedRoute>
            <AppLayout><Community /></AppLayout>
          </ProtectedRoute>
        }
      />
      <Route
        path="/progress"
        element={
          <ProtectedRoute>
            <AppLayout><Progress /></AppLayout>
          </ProtectedRoute>
        }
      />
      <Route
        path="/profile"
        element={
          <ProtectedRoute>
            <AppLayout><Profile /></AppLayout>
          </ProtectedRoute>
        }
      />
    </Routes>
  )
}
