import { describe, it, expect, beforeEach } from 'vitest';
import { useSessionStore } from '../store/sessionStore';
import type { RegistroHistorico, Sessao } from '../api/client';

describe('useSessionStore', () => {
  /**
   * Antes de cada teste, o store é resetado para o estado inicial,
   * garantindo que nenhum teste seja contaminado pelo estado deixado pelo anterior.
   */
  beforeEach(() => {
    useSessionStore.getState().reset();
  });

  /**
   * Cenário: a função `setConn` é chamada com status 'conectando' e uma mensagem
   * Esperado:
   * - `conn` deve ser atualizado para 'conectando'
   * - `mensagem` deve ser atualizada para 'A aguardar backend...'
   */
  it('deve atualizar o estado de conexão e a mensagem', () => {
    useSessionStore.getState().setConn('conectando', 'A aguardar backend...');
    const estado = useSessionStore.getState();
    
    expect(estado.conn).toBe('conectando');
    expect(estado.mensagem).toBe('A aguardar backend...');
  });

  /**
   * Cenário: chega um evento do tipo 'inicial' com dados de sessão e histórico
   * Esperado:
   * - `sessao` deve conter os dados da sessão recebida (sem o campo `ciclo`, que é separado)
   * - `ultimoCiclo` deve ser atualizado para 5
   * - `historico` deve conter exatamente 1 registro, igual ao mock enviado
   */
  it('deve processar o evento "inicial"', () => {
    const sessaoMock = { id: 1, url: 'https://exemplo.com', xpath_monitorado: '.preco', status: 'ativa', valor_atual: '0' } as unknown as Sessao;
    const historicoMock = [{ id: 1, sessao_id: 1, valor_antigo: '0', valor_novo: '1', data_hora: '2026-01-01T12:00:00Z' }] as unknown as RegistroHistorico[];
    
    useSessionStore.getState().aplicarEvento({
      type: 'inicial',
      sessao: { ...sessaoMock, ciclo: 5 },
      historico: historicoMock
    });

    const estado = useSessionStore.getState();
    expect(estado.sessao).toMatchObject(sessaoMock);
    expect(estado.ultimoCiclo).toBe(5);
    expect(estado.historico).toHaveLength(1);
    expect(estado.historico[0]).toEqual(historicoMock[0]);
  });

  /**
   * Cenário: já existe uma sessão no store e chega um evento do tipo 'ciclo'
   * Esperado:
   * - `ultimoCiclo` deve ser atualizado para 12
   * - `sessao.valor_atual` deve ser sobrescrito com '150.00',
   *   refletindo o novo valor monitorado capturado neste ciclo
   */
  it('deve processar o evento "ciclo" e atualizar o valor atual', () => {
    useSessionStore.setState({ sessao: { id: 1, valor_atual: '0' } as unknown as Sessao });
    
    useSessionStore.getState().aplicarEvento({
      type: 'ciclo',
      ciclo: 12,
      valor_atual: '150.00'
    });

    const estado = useSessionStore.getState();
    expect(estado.ultimoCiclo).toBe(12);
    expect(estado.sessao?.valor_atual).toBe('150.00');
  });

  /**
   * Cenário: chega um evento do tipo 'alteracao' com um novo registro de mudança de valor
   * Esperado:
   * - O registro deve ser anexado ao array `historico`
   * - `historico` deve ter exatamente 1 entrada (store estava vazio antes)
   * - O registro inserido deve ser idêntico ao mock enviado
   */
  it('deve processar o evento "alteracao" e anexar ao histórico', () => {
    const novoReg = { id: 2, sessao_id: 1, valor_antigo: '100', valor_novo: '200', data_hora: '2026-01-01T12:00:00Z' } as unknown as RegistroHistorico;
    
    useSessionStore.getState().aplicarEvento({
      type: 'alteracao',
      registro: novoReg
    });

    const estado = useSessionStore.getState();
    expect(estado.historico).toHaveLength(1);
    expect(estado.historico[0]).toEqual(novoReg);
  });

  /**
   * Cenário: chega um evento do tipo 'screenshot' com uma string base64
   * Esperado:
   * - `screenshot` no store deve ser atualizado para a string recebida,
   *   que será usada pelo componente BrowserPreview para renderizar a imagem
   */
  it('deve processar o evento "screenshot" atualizando o ecrã', () => {
    useSessionStore.getState().aplicarEvento({ type: 'screenshot', data: 'base64image123' });
    expect(useSessionStore.getState().screenshot).toBe('base64image123');
  });

  /**
   * Cenário: já existe uma sessão ativa no store e chega um evento do tipo 'encerrada'
   * Esperado:
   * - `sessao.status` deve ser atualizado de 'ativa' para 'encerrada',
   *   sinalizando que o monitoramento desta sessão foi finalizado
   */
  it('deve processar o evento "encerrada" marcando o status da sessão', () => {
    useSessionStore.setState({ sessao: { id: 1, status: 'ativa' } as unknown as Sessao });
    
    useSessionStore.getState().aplicarEvento({ type: 'encerrada' });
    
    expect(useSessionStore.getState().sessao?.status).toBe('encerrada');
  });

  /**
   * Cenário: chega um evento do tipo 'erro' com uma mensagem descritiva
   * Esperado:
   * - `mensagem` no store deve ser atualizada para o texto do erro recebido,
   *   permitindo que a UI exiba o feedback de falha ao utilizador
   */
  it('deve processar o evento "erro"', () => {
    useSessionStore.getState().aplicarEvento({ type: 'erro', mensagem: 'Falha ao aceder à página' });
    expect(useSessionStore.getState().mensagem).toBe('Falha ao aceder à página');
  });
});