import { Navigate, Route, Routes } from 'react-router-dom';
import ConfigPage from './pages/ConfigPage';
import DashboardPage from './pages/DashboardPage';
import LoginPage from './pages/LoginPage';
import SelectValuePage from './pages/SelectValuePage';

/**
 * Shell da aplicação. Fase 1 usa roteamento por rotas simples; estado
 * compartilhado entre telas vai via navigate(state: ...).
 * Zustand/Context entra na Fase 2.
 */
export default function App() {
  return (
    <div className="min-h-screen">
      <header className="bg-white border-b border-gray-200 px-6 py-3">
        <h1 className="text-lg font-semibold text-gray-800">
          Monitor de Preços — <span className="text-indigo-600">MVP</span>
        </h1>
      </header>

      <main className="max-w-5xl mx-auto px-6 py-8">
        <Routes>
          <Route path="/" element={<Navigate to="/login" replace />} />
          <Route path="/login" element={<LoginPage />} />
          <Route path="/config" element={<ConfigPage />} />
          <Route path="/select/:sessionId" element={<SelectValuePage />} />
          <Route path="/dashboard/:sessionId" element={<DashboardPage />} />
        </Routes>
      </main>
    </div>
  );
}
