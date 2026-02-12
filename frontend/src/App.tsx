import { useEffect, useState, lazy, Suspense } from 'react';
import { BrowserRouter, Routes, Route, Navigate, useNavigate } from 'react-router-dom';
import { useAppStore } from './stores/appStore';
import { RequireAuth } from './components/RequireAuth/RequireAuth';
import { RequireAdmin } from './components/RequireAdmin/RequireAdmin';
import { ErrorBoundary } from './components/ErrorBoundary/ErrorBoundary';
import { Login } from './pages/Login/Login';
import { apiService } from './services/api';
import './styles/global.css';

// Route-based code splitting: load pages on demand
const AuthCallback = lazy(() => import('./pages/AuthCallback/AuthCallback').then(m => ({ default: m.AuthCallback })));
const AuthCallbackFacebook = lazy(() => import('./pages/AuthCallback/AuthCallbackFacebook').then(m => ({ default: m.AuthCallbackFacebook })));
const DashboardLayout = lazy(() => import('./pages/DashboardLayout').then(m => ({ default: m.DashboardLayout })));
const Dashboard = lazy(() => import('./pages/Dashboard/Dashboard').then(m => ({ default: m.Dashboard })));
const Convert = lazy(() => import('./pages/Convert/Convert').then(m => ({ default: m.Convert })));
const History = lazy(() => import('./pages/History/History').then(m => ({ default: m.History })));
const FormatManuscript = lazy(() => import('./pages/FormatManuscript/FormatManuscript').then(m => ({ default: m.FormatManuscript })));
const PdfTools = lazy(() => import('./pages/PdfTools/PdfTools').then(m => ({ default: m.PdfTools })));
const TermsOfUse = lazy(() => import('./pages/TermsOfUse/TermsOfUse').then(m => ({ default: m.TermsOfUse })));
const PrivacyPolicy = lazy(() => import('./pages/PrivacyPolicy/PrivacyPolicy').then(m => ({ default: m.PrivacyPolicy })));
const Pricing = lazy(() => import('./pages/Pricing/Pricing').then(m => ({ default: m.Pricing })));
const Security = lazy(() => import('./pages/Security/Security').then(m => ({ default: m.Security })));
const Features = lazy(() => import('./pages/Features/Features').then(m => ({ default: m.Features })));
const About = lazy(() => import('./pages/About/About').then(m => ({ default: m.About })));
const EditProfile = lazy(() => import('./pages/EditProfile/EditProfile').then(m => ({ default: m.EditProfile })));
const Admin = lazy(() => import('./pages/Admin/Admin').then(m => ({ default: m.Admin })));
const AdminUserDetail = lazy(() => import('./pages/Admin/AdminUserDetail').then(m => ({ default: m.AdminUserDetail })));
const AdminConversions = lazy(() => import('./pages/Admin/AdminConversions').then(m => ({ default: m.AdminConversions })));
const AdminActivity = lazy(() => import('./pages/Admin/AdminActivity').then(m => ({ default: m.AdminActivity })));
const Collaboration = lazy(() => import('./pages/Collaboration/Collaboration').then(m => ({ default: m.Collaboration })));
const MyDocuments = lazy(() => import('./pages/MyDocuments/MyDocuments').then(m => ({ default: m.MyDocuments })));

const PageFallback = () => (
  <div className="page-fallback" role="status" aria-live="polite" style={{ padding: '2rem', textAlign: 'center' }}>
    Cargando…
  </div>
);

/** Valida el token con el backend antes de redirigir al dashboard; si es inválido (401) se limpia la sesión y se muestra el login. */
function LoginRoute() {
  const { token } = useAppStore();
  const navigate = useNavigate();
  const [validating, setValidating] = useState(!!token);

  useEffect(() => {
    if (!token) {
      setValidating(false);
      return;
    }
    let cancelled = false;
    setValidating(true);
    apiService
      .getProfile()
      .then(() => {
        if (!cancelled) navigate('/dashboard', { replace: true });
      })
      .catch(() => {
        if (!cancelled) setValidating(false);
      })
      .finally(() => {
        if (!cancelled) setValidating(false);
      });
    return () => {
      cancelled = true;
    };
  }, [token, navigate]);

  if (!token) return <Login />;
  if (validating) {
    return (
      <div className="login-validating" role="status" aria-live="polite">
        Comprobando sesión…
      </div>
    );
  }
  return null;
}

function App() {
  const { theme } = useAppStore();

  useEffect(() => {
    if (typeof document !== 'undefined') {
      document.documentElement.setAttribute('data-theme', theme);
    }
  }, [theme]);

  return (
    <ErrorBoundary>
      <BrowserRouter>
        <Suspense fallback={<PageFallback />}>
          <Routes>
          <Route path="/login" element={<LoginRoute />} />
          <Route path="/auth/callback" element={<AuthCallback />} />
          <Route path="/auth/callback/facebook" element={<AuthCallbackFacebook />} />
          <Route path="/admin" element={<RequireAdmin><Admin /></RequireAdmin>} />
          <Route path="/admin/users/:id" element={<RequireAdmin><AdminUserDetail /></RequireAdmin>} />
          <Route path="/admin/conversions" element={<RequireAdmin><AdminConversions /></RequireAdmin>} />
          <Route path="/admin/activity" element={<RequireAdmin><AdminActivity /></RequireAdmin>} />
          <Route path="/" element={<DashboardLayout />}>
            <Route index element={<Navigate to="/dashboard" />} />
            <Route path="dashboard" element={<Dashboard />} />
            <Route path="convert" element={<Convert />} />
            <Route path="pdf-tools" element={<PdfTools />} />
            <Route path="history" element={<RequireAuth><History /></RequireAuth>} />
            <Route path="format-manuscript" element={<FormatManuscript />} />
            <Route path="terms-of-use" element={<TermsOfUse />} />
            <Route path="privacy-policy" element={<PrivacyPolicy />} />
            <Route path="pricing" element={<Pricing />} />
            <Route path="security" element={<Security />} />
            <Route path="features" element={<Features />} />
            <Route path="about" element={<About />} />
            <Route path="settings" element={<RequireAuth><EditProfile /></RequireAuth>} />
            <Route path="documents" element={<RequireAuth><MyDocuments /></RequireAuth>} />
            <Route path="collab/:id" element={<RequireAuth><Collaboration /></RequireAuth>} />
          </Route>
          </Routes>
        </Suspense>
      </BrowserRouter>
    </ErrorBoundary>
  );
}

export default App;
