import { render, screen, fireEvent } from '@testing-library/react';
import { describe, it, expect, vi } from 'vitest';
import ToastContainer from '../components/ToastContainer';
import { useToastStore } from '../store/toastStore';

vi.mock('../store/toastStore');

type ToastState = ReturnType<typeof useToastStore.getState>;

describe('ToastContainer', () => {
  /**
   * Cenário: o store não possui nenhum toast na fila
   * Esperado:
   * - O componente não deve renderizar nenhum elemento no DOM,
   *   ou seja, `container.firstChild` deve ser null
   */
  it('não renderiza nada se não houver toasts', () => {
    vi.mocked(useToastStore).mockImplementation((selector) => {
      const state = { toasts: [], remover: vi.fn() } as unknown as ToastState;
      return selector(state);
    });

    const { container } = render(<ToastContainer />);
    expect(container.firstChild).toBeNull();
  });

  /**
   * Cenário: o store possui um toast do tipo 'sucesso' com a mensagem 'Tudo certo!'
   * Esperado:
   * - O texto 'Tudo certo!' deve estar visível na tela
   * - Deve existir um botão acessível com nome que corresponda a /dispensar/i
   * - Ao clicar no botão, a função `remover` do store deve ser chamada
   *   com o id do toast ('1'), removendo-o da fila
   */
  it('renderiza os toasts e permite dispensá-los', () => {
    const mockRemover = vi.fn();
    vi.mocked(useToastStore).mockImplementation((selector) => {
      const state = {
        toasts: [{ id: '1', tipo: 'sucesso', mensagem: 'Tudo certo!' }],
        remover: mockRemover,
      } as unknown as ToastState;
      return selector(state);
    });

    render(<ToastContainer />);
    
    expect(screen.getByText('Tudo certo!')).toBeInTheDocument();

    const btnFechar = screen.getByRole('button', { name: /dispensar/i });
    fireEvent.click(btnFechar);

    expect(mockRemover).toHaveBeenCalledWith('1');
  });
});