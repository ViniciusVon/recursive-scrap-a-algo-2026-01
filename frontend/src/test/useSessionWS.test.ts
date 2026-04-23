import { renderHook } from '@testing-library/react';
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { useSessionWS } from '../hooks/useSessionWS';
import { useSessionStore } from '../store/sessionStore';

vi.mock('../store/sessionStore');

type SessionState = ReturnType<typeof useSessionStore.getState>;

describe('useSessionWS', () => {
  let mockWebSocket: Partial<WebSocket>;
  let MockWebSocketConstructor: ReturnType<typeof vi.fn> & { OPEN: number };

  /**
   * Antes de cada teste:
   * - Os timers reais são substituídos por timers fake (controlados manualmente),
   *   permitindo simular o delay de conexão sem esperar tempo real
   * - Um objeto WebSocket falso é criado com `close` mockado e `readyState: 1` (OPEN)
   * - O construtor global `WebSocket` é substituído pelo mock,
   *   para interceptar e verificar quando/como a conexão é criada
   */
  beforeEach(() => {
    vi.useFakeTimers(); 
    
    mockWebSocket = {
      close: vi.fn(),
      readyState: 1,
    };
    
    MockWebSocketConstructor = Object.assign(
      vi.fn(function () {
        return mockWebSocket;
      }),
      { OPEN: 1 }
    );
    
    vi.stubGlobal('WebSocket', MockWebSocketConstructor);
  });

  /**
   * Após cada teste, todos os mocks e stubs globais são restaurados,
   * garantindo que o `WebSocket` real não fique substituído entre testes.
   */
  afterEach(() => {
    vi.restoreAllMocks();
    vi.unstubAllGlobals();
  });

  /**
   * Cenário: o hook é chamado sem um `sessionId` (valor `undefined`)
   * Esperado:
   * - Mesmo após avançar todos os timers, o construtor `WebSocket`
   *   não deve ser chamado — o hook deve abortar antes de tentar conectar
   */
  it('não liga se o sessionId estiver indefinido', () => {
    renderHook(() => useSessionWS(undefined));
    vi.runAllTimers();
    
    expect(MockWebSocketConstructor).not.toHaveBeenCalled();
  });

  /**
   * Cenário: o hook recebe um `sessionId` válido ('sessao-123')
   * Esperado (em ordem):
   * 1. `reset` deve ser chamado imediatamente ao montar, limpando o estado anterior
   * 2. Após avançar 150ms, `WebSocket` deve ser instanciado com uma URL contendo '/ws/sessoes/sessao-123'
   * 3. `setConn` deve ser chamado com 'conectando', atualizando o status da ligação no store
   * 4. Ao desmontar o hook, `ws.close` deve ser chamado com código 1000 e motivo 'unmount',
   *    encerrando a ligação de forma limpa
   */
  it('inicia a ligação WS após o delay e encerra ao desmontar', () => {
    const mockReset = vi.fn();
    const mockSetConn = vi.fn();
    
    vi.mocked(useSessionStore).mockImplementation((selector) => {
      const state = { 
        reset: mockReset, 
        setConn: mockSetConn, 
        aplicarEvento: vi.fn() 
      } as unknown as SessionState;
      
      return selector(state);
    });

    const { unmount } = renderHook(() => useSessionWS('sessao-123'));
    
    expect(mockReset).toHaveBeenCalled();
    
    vi.advanceTimersByTime(150);
    
    expect(MockWebSocketConstructor).toHaveBeenCalledWith(expect.stringContaining('/ws/sessoes/sessao-123'));
    expect(mockSetConn).toHaveBeenCalledWith('conectando');

    unmount();
    expect(mockWebSocket.close).toHaveBeenCalledWith(1000, 'unmount');
  });
});