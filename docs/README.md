# Manual do Sistema de Gerenciamento de Gastos com IA

## 📋 Visão Geral
Este é um sistema inteligente que combina gerenciamento de gastos com assistência de IA. Além de registrar e organizar seus gastos, o sistema pode responder perguntas sobre finanças pessoais usando a IA do Google Gemini.

## 🚀 Como Usar

### Versão Telegram
1. Adicione o bot @SeuBotName no Telegram
2. Inicie uma conversa com o comando `/start`
3. Use os comandos ou digite suas mensagens normalmente

#### Comandos do Telegram
- `/start` - Iniciar o bot e ver instruções
- `/help` - Ver todos os comandos disponíveis
- `/resumo` - Ver resumo dos gastos
- `/categorias` - Listar todas as categorias
- `/limpar` - Limpar histórico de gastos

#### Registro de Gastos no Telegram
Digite normalmente suas mensagens:
- "gastei 50 reais com almoço"
- "gastei 30 com transporte"
- "gastei R$100 no mercado"

#### Perguntas para a IA
Qualquer outra mensagem será respondida pela IA sobre:
- Investimentos
- Dívidas
- Orçamento
- Planejamento financeiro
- Dicas de economia

### Versão CLI (Linha de Comando)
1. Execute o arquivo `gastos_ia.py` para iniciar o programa
2. O sistema criará automaticamente um banco de dados (`gastos.db`) na primeira execução
3. Certifique-se de ter configurado sua chave da API do Google Gemini no arquivo `.env`

#### Comandos CLI
- `resumo` - ver resumo dos gastos
- `categorias` - listar todas as categorias
- `limpar` - limpar histórico
- `sair` - encerrar o programa
- `ajuda` - mostrar esta mensagem novamente

## 🗂️ Categorias Padrão
O sistema inclui as seguintes categorias:
- Alimentação
- Transporte
- Moradia
- Lazer
- Saúde
- Educação
- Vestuário
- Outros

## 🔧 Funcionalidades Técnicas

### Banco de Dados
- Usa SQLite para armazenamento
- Tabelas:
  - `categorias`: armazena as categorias de gastos
  - `gastos`: registra cada despesa com valor, descrição e categoria

### Processamento de Linguagem Natural
- Reconhece diferentes formatos de entrada
- Identifica valores monetários
- Categoriza automaticamente as despesas

### Inteligência Artificial
- Integração com Google Gemini
- Respostas especializadas em finanças
- Contexto personalizado para cada pergunta

### Relatórios
- Gera resumos por categoria
- Calcula percentuais de gastos
- Ordena categorias por valor gasto

## 💡 Dicas de Uso
1. Seja específico nas descrições para melhor categorização
2. Use o resumo regularmente para acompanhar seus gastos
3. Mantenha o hábito de registrar gastos imediatamente após realizá-los
4. Use o comando `categorias` para verificar como seus gastos estão sendo classificados
5. Faça perguntas específicas para a IA para obter respostas mais úteis

## ⚠️ Observações Importantes
- O banco de dados é local e não requer conexão com internet
- O histórico de gastos é mantido até você optar por limpar
- A categorização automática pode ser melhorada com o tempo de uso
- A IA requer conexão com a internet para funcionar
- As respostas da IA são gerais e não substituem consultoria financeira profissional
- No Telegram, cada usuário tem seu próprio banco de dados

## 🔄 Atualizações Futuras
- Adição de novas categorias
- Exportação de relatórios
- Análise de tendências de gastos
- Suporte a múltiplas moedas
- Melhorias na integração com IA
- Análise de padrões de gastos
- Gráficos e visualizações no Telegram 