# Trabalho 01 - Análise de Algoritmos

## Desenvolver um assistente de lances para sites de leilão

### O objetivo é monitorar um preço que está dentro de uma página WEB, a qual você não sabe previamente a estrutura (o usuário vai passar a URL na hora de informar detro da página qual é o cammpmo a ser analisado).

### Ao identificar a mudança de preços, você deverá interagir com outra página (Qualquer uma que serja pública - você não controla o código fonte dela.) e inserir um textoinfromando o valor antigo e o novo e clicar em um botão.

### Outro sistema público - Gmail, por exemplo, e clicar no botão de send.

## Calcular

### Calcule o Big O do seu código.
### Pode usar qualquer biblioteca.
### Qualquer linguagem, arquitetura e cliente - WEB, app mobile ou desktop.

## *Critérios*

### **0 pontos** -> O sistema que não encontrar a variável OU travar durante a execução do código, seja por bug ou por não validação de entrada de usuário.

### **2 pontos** -> Se encontrar o número na página (o sistema deve logar no console sua posição na página - Xpath, Regex)

### **2 pontos** -> Monitorar adequadamente (O sistema deve logar no console todas as alterações identificadas do número).

### **2 pontos** -> Se identificar alteração, registar em outra página e acionar um botão da tela

### **1 ponto** -> Documentação do código
#### O resultado deve ser apresentado utilizando Sphinx, pydoc ou MkDocs, ou outra ferramenta.

### **1 ponto** -> Se o sistema tiver um log de ações do usuário (todas).
#### Nesse caso deve pedir o nome do usuário como entrada (Nesse caso não precisa ter crítica, exceto se é um nome composto APENAS por caracteres com ao menos 3 caracteres, Os nomes podem ser duplicados).

### **1 ponto** -> Se os testes unitários estiverem automatizados.

### **1 ponto** -> Se o big O estiver correto.

### *Ponto Extra*
#### **1 ponto** -> Se o git do projeto "contar" a história da evolução. Com commits de todos alunos, evoluções, controles de bugs, etc...
#### **1 ponto** -> Se a interface for amigável e intuitiva

## *Regras*

### No dia da apresentação todos devem estar presentes.
### A nota é do grupo. Perguntas serão feitas para os membros do grupo durante a apresentação sobre o código apresentado.

# **Proposta de Ferramentas**

## Utilizar RegEx para busca de valores nas páginas (De acordo com a página que o usuário informar).
## Utilizar Selenium para descobrir o Xpath daquele elemento que buscamos com o RegEx
## Utilizar python para a implementação do web scrapping

# **Organização do Repositório**

## Utilizaremos cada ponto a ser alcançado como uma milestone, com isso conseguiremos ter um controle melhor sobre o que precisa ser feito.
## Faremos uma pipeline de verificação de testes e build do projeto para um possível deploy em ambiente de homologação / produção
## Seguiremos o padrão de gitflow para a criação de branchs bem como a criação de Pull Requests.
### Nomes de branchs seguirão o modelo:
- **feature/nome-da-feature** -> para o desenvolvimento de novas funcionalidades que serão atribuídas a um milestone.

- **fix/nome-do-fix** -> para o desenvolvimento de ajustes de funcionalidades existentes dentro de um milestone.

- **release/version** -> Utilizaremos essa nomenclatura de branch para subir a versão para a branch principal. Version será o nome da versão que subiremos (Ex: 0.1.0).

- **hotfix/nome-do-hotfix** -> Se, porventura, subirmos o projeto para hospedagem, essa nomenclatura seria interessante caso for preciso realizar uma alteração urgente no projeto.

## *Lembrando que os commits precisam ter uma issue relacionada.*

## Cada Pull Request deverá ter 2 reviewers para que o código que vá para a branch principal tenha menos probabilidade de dar erro.


---

# **Documentação**

Toda a documentação do projeto está em [`documentation/`](./documentation/):

| Camada | Overview | Complexidade (Big O) |
|--------|----------|----------------------|
| Backend | [`documentation/backend.md`](./documentation/backend.md) | [`documentation/complexidade_backend.md`](./documentation/complexidade_backend.md) |
| Frontend | [`documentation/frontend.md`](./documentation/frontend.md) | [`documentation/complexidade_frontend.md`](./documentation/complexidade_frontend.md) |

As análises de complexidade são validadas contra o código em `main` e batem com
os docstrings das funções. Resumo do algoritmo principal (monitoramento):

> **T(n, d, u, k, s, C) = O(n · d + C · (d + s) + k)**
>
> Setup **linear no DOM** (`n · d`), ciclo **constante** após a seleção (`d + s`,
> com `s = 1` na prática), e **O(k)** no encerramento pra persistir o histórico.
