import { Navigate, Route, Routes } from 'react-router-dom';
import ErrorBoundary from './components/ErrorBoundary';
import MonitorPage from './pages/MonitorPage';
import SetupWizard from './pages/SetupWizard';

/**
 * Shell da aplicação.
 *
 * Duas páginas apenas:
 *   - "/"                    → SetupWizard (usuário → URL → valor)
 *   - "/monitor/:sessionId"  → MonitorPage  (preview + histórico ao vivo)
 *
 * O ErrorBoundary protege a árvore inteira.
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
        <ErrorBoundary>
          <Routes>
            <Route path="/" element={<SetupWizard />} />
            <Route path="/monitor/:sessionId" element={<MonitorPage />} />
            <Route path="*" element={<Navigate to="/" replace />} />
          </Routes>
        </ErrorBoundary>
      </main>
    </div>
  );
}
