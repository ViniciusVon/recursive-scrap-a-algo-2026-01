/**
 * ErrorBoundary simples para capturar erros de render das páginas.
 * React Router v7 também tem errorElement, mas um boundary explícito
 * pega tudo que não passa por rota.
 */

import { Component, type ErrorInfo, type ReactNode } from 'react';

interface State {
  erro: Error | null;
}

interface Props {
  children: ReactNode;
}

export default class ErrorBoundary extends Component<Props, State> {
  state: State = { erro: null };

  static getDerivedStateFromError(erro: Error): State {
    return { erro };
  }

  componentDidCatch(erro: Error, info: ErrorInfo): void {
    // Em produção mandaria para um serviço de monitoramento (Sentry, etc.)
    console.error('ErrorBoundary capturou:', erro, info);
  }

  render() {
    if (this.state.erro) {
      return (
        <div className="max-w-xl mx-auto mt-12 bg-white rounded-lg border border-red-200 p-6">
          <h2 className="text-lg font-medium text-red-700 mb-2">
            Algo deu errado.
          </h2>
          <pre className="text-sm text-red-600 whitespace-pre-wrap">
            {this.state.erro.message}
          </pre>
          <button
            onClick={() => window.location.assign('/')}
            className="mt-4 px-4 py-2 bg-indigo-600 text-white rounded hover:bg-indigo-700"
          >
            Voltar ao início
          </button>
        </div>
      );
    }
    return this.props.children;
  }
}
