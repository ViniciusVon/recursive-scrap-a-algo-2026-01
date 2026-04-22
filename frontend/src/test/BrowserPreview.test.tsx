import { render, screen } from '@testing-library/react';
import { describe, it, expect, vi } from 'vitest';
import BrowserPreview from '../components/BrowserPreview';
import { useSessionStore } from '../store/sessionStore';

vi.mock('../store/sessionStore');

type SessionState = ReturnType<typeof useSessionStore.getState>;

describe('BrowserPreview', () => {
  /**
   * Cenário: o campo `screenshot` é null (nenhuma captura recebida ainda)
   * Esperado:
   * - Deve exibir o texto "Aguardando primeiro screenshot..." na tela
   * - Deve exibir o texto "conectado" (status da conexão)
   */
  it('mostra mensagem de aguardar quando não há screenshot', () => {
    vi.mocked(useSessionStore).mockImplementation((selector) => {
      const state = { screenshot: null, conn: 'conectado' } as unknown as SessionState;
      return selector(state);
    });

    render(<BrowserPreview />);
    expect(screen.getByText('Aguardando primeiro screenshot...')).toBeInTheDocument();
    expect(screen.getByText('conectado')).toBeInTheDocument();
  });

  /**
   * Cenário: o campo `screenshot` contém uma string base64 válida
   * Esperado:
   * - Deve renderizar uma tag <img> com alt="Navegador monitorado"
   * - O atributo `src` da imagem deve ser "data:image/png;base64,base64falsa123",
   *   ou seja, o componente deve montar a URL de dados corretamente a partir da string base64
   */
  it('mostra a imagem quando o screenshot está disponível', () => {
    vi.mocked(useSessionStore).mockImplementation((selector) => {
      const state = { screenshot: 'base64falsa123', conn: 'conectado' } as unknown as SessionState;
      return selector(state);
    });

    render(<BrowserPreview />);
    
    const img = screen.getByAltText('Navegador monitorado');
    expect(img).toBeInTheDocument();
    expect(img).toHaveAttribute('src', 'data:image/png;base64,base64falsa123');
  });

  /**
   * Cenário: a conexão está no estado "conectando" (ainda não estabelecida)
   * Esperado:
   * - Deve exibir o texto "Conectando ao navegador..." na tela
   * - Deve existir um badge/elemento com o texto "conectando"
   * - Esse badge deve ter a classe CSS "bg-gray-500", indicando
   *   que o estado de conexão pendente é representado visualmente em cinza
   */
  it('mostra status de conectando com a cor correta', () => {
    vi.mocked(useSessionStore).mockImplementation((selector) => {
      const state = { screenshot: null, conn: 'conectando' } as unknown as SessionState;
      return selector(state);
    });

    render(<BrowserPreview />);
    expect(screen.getByText('Conectando ao navegador...')).toBeInTheDocument();
    const badge = screen.getByText('conectando');
    expect(badge.className).toContain('bg-gray-500'); 
  });
});