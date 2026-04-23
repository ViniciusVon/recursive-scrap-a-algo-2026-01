# Análise de complexidade — frontend

Notação: `n` = tamanho da coleção relevante, `k` = constantes pequenas
(número de toasts visíveis, retries, etc.), `m` = número de mensagens
WebSocket processadas em uma sessão.

## Renderização de listas

| Componente / hook                       | Operação                       | Complexidade |
| --------------------------------------- | ------------------------------ | ------------ |
| `SetupWizard → StepUsuario`             | render da lista de usuários    | **O(n)**     |
| `SetupWizard → StepValor`               | render da lista de valores     | **O(n)**     |
| `SetupWizard → SessoesAnteriores`       | slice(0,10) + render           | **O(1)**     |
| `MonitorPage` → tabela de histórico     | render                         | **O(m)**     |
| `ToastContainer`                        | render                         | **O(k)**     |

React reconcilia por `key`, portanto inserções no fim (novos toasts,
novos registros de histórico) custam **O(1)** amortizado — o trabalho
extra é proporcional ao item novo, não à lista inteira.

## Estado global (Zustand)

| Ação                               | Complexidade | Observação                                  |
| ---------------------------------- | ------------ | ------------------------------------------- |
| `toast.emitir`                     | O(1)         | append + setTimeout                         |
| `toast.remover`                    | O(k)         | filter sobre a fila (k pequeno)             |
| `sessionStore.aplicarEvento` — `inicial`    | O(m)  | copia histórico recebido do backend         |
| `sessionStore.aplicarEvento` — `ciclo`      | O(1)  | atualiza 2 campos                           |
| `sessionStore.aplicarEvento` — `alteracao`  | O(1)  | append na lista (spread copia O(m), mas foi avaliado aceitável para m < 10⁴) |
| `sessionStore.aplicarEvento` — `screenshot` | O(1)  | troca referência base64                     |

O spread em `alteracao` é **O(m)** em cada mensagem recebida —
aceitável porque o monitor compara a cada 15s e `m` cresce devagar.
Se esse fluxo precisar de milhões de eventos, trocaríamos para
estrutura persistente ou buffer circular.

## Hooks de ciclo de vida

| Hook                         | Por mount                                | Complexidade |
| ---------------------------- | ---------------------------------------- | ------------ |
| `useSessionWS`               | 1 WS + handlers + reconnect exponencial | O(1) setup, O(m) processing total |
| `useNotificarAlteracoes`     | diff por contagem de histórico           | O(alterações novas por render) |

A comparação via `contagemAnterior.current` evita varrer o histórico
inteiro: só fatiamos os registros **novos**, então o custo por tick é
proporcional ao delta, não ao total.

## Rede (cliente HTTP)

- `request<T>`: custo dominado pelo round-trip; em falha de rede em
  verbos idempotentes, até **3 tentativas** com backoff [250, 750]ms.
  Custo extra: **O(1)** chamadas adicionais no pior caso.
- `JSON.parse` do corpo: **O(L)** no tamanho da resposta.

## Validação (Zod)

Cada `safeParse` faz uma passada em profundidade pelo schema. Para os
modelos usados (`usuarioInSchema`, `sessaoInSchema`, `selecaoInSchema`),
a profundidade é constante (<5 campos), logo **O(1)** por chamada.

## Resumo

O frontend é **linear** no tamanho das coleções exibidas e **constante**
por evento individual recebido do backend. Os únicos pontos potenciais
de gargalo são:

1. O spread em `alteracao` (O(m) por mensagem) — ver nota acima.
2. Re-renderização completa da tabela de histórico quando um registro
   novo chega; mitigável com `React.memo` caso `m` vire problema.

Para o escopo atual (sessões de até algumas horas, dezenas de
alterações), a performance é folgada.
