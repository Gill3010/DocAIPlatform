import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { useAppStore } from './stores/appStore';
import { Login } from './pages/Login/Login';
import { DashboardLayout } from './pages/DashboardLayout';
import { Dashboard } from './pages/Dashboard/Dashboard';
import { Convert } from './pages/Convert/Convert';
import { History } from './pages/History/History';
import { FormatManuscript } from './pages/FormatManuscript/FormatManuscript';
import { TerminosDeUso } from './pages/TerminosDeUso/TerminosDeUso';
import { PoliticaPrivacidad } from './pages/PoliticaPrivacidad/PoliticaPrivacidad';
import './styles/global.css';

function App() {
  const { token, theme } = useAppStore();

  // Sync theme to document (mount and when theme changes from SettingsMenu)
  if (typeof document !== 'undefined') {
    document.documentElement.setAttribute('data-theme', theme);
  }

  return (
    <BrowserRouter>
      <Routes>
        <Route path="/login" element={token ? <Navigate to="/dashboard" /> : <Login />} />
        <Route path="/" element={token ? <DashboardLayout /> : <Navigate to="/login" />}>
          <Route index element={<Navigate to="/dashboard" />} />
          <Route path="dashboard" element={<Dashboard />} />
          <Route path="convert" element={<Convert />} />
          <Route path="history" element={<History />} />
          <Route path="format-manuscript" element={<FormatManuscript />} />
          <Route path="terminos-de-uso" element={<TerminosDeUso />} />
          <Route path="politica-privacidad" element={<PoliticaPrivacidad />} />
          <Route path="settings" element={<div style={{ padding: '2rem' }}>Settings page coming soon...</div>} />
        </Route>
      </Routes>
    </BrowserRouter>
  );
}

export default App;
