# Exemplos de Uso

## Interface de Linha de Comando (CLI)

### 1. Registrando Gastos

#### Formato Básico
```bash
> gastei 50 reais com almoço
✅ Gasto registrado: R$ 50,00 - Almoço (Categoria: Alimentação)
```

#### Com Valor e Descrição
```bash
> gastei R$ 30,50 no mercado
✅ Gasto registrado: R$ 30,50 - Mercado (Categoria: Alimentação)

> paguei 150 de conta de luz
✅ Gasto registrado: R$ 150,00 - Conta de luz (Categoria: Moradia)
```

#### Com Categoria Específica
```bash
> gastei 25 em transporte
✅ Gasto registrado: R$ 25,00 - Transporte (Categoria: Transporte)

> despesa de 100 em lazer
✅ Gasto registrado: R$ 100,00 - Lazer (Categoria: Lazer)
```

### 2. Consultando Gastos

#### Resumo Geral
```bash
> resumo
📊 Resumo de Gastos:
- Alimentação: R$ 500,00 (40%)
- Transporte: R$ 200,00 (16%)
- Moradia: R$ 300,00 (24%)
- Lazer: R$ 100,00 (8%)
- Outros: R$ 150,00 (12%)
Total: R$ 1.250,00
```

#### Por Período
```bash
> resumo semana
📊 Resumo Semanal:
- Alimentação: R$ 200,00
- Transporte: R$ 80,00
- Lazer: R$ 50,00
Total da Semana: R$ 330,00
```

#### Por Categoria
```bash
> gastos alimentação
🍽️ Gastos com Alimentação:
1. R$ 50,00 - Almoço (05/03)
2. R$ 30,50 - Mercado (04/03)
3. R$ 25,00 - Lanche (03/03)
Total: R$ 105,50
```

### 3. Interagindo com a IA

#### Perguntas sobre Finanças
```bash
> como economizar em alimentação?
🤖 IA: Aqui estão algumas dicas para economizar em alimentação:
1. Planeje suas refeições semanalmente
2. Faça compras em atacado
3. Aproveite promoções
4. Cozinhe em casa
5. Evite desperdícios

> qual é a melhor forma de investir 1000 reais?
🤖 IA: Para investir R$ 1.000,00, considere:
1. Tesouro Direto (segurança)
2. CDB (liquidez)
3. Fundos de Investimento (diversificação)
4. Ações (risco maior)
```

## Bot Telegram

### 1. Comandos Básicos

#### Iniciando o Bot
```
/start
👋 Olá! Sou seu assistente financeiro.
Use /help para ver os comandos disponíveis.
```

#### Ajuda
```
/help
📚 Comandos Disponíveis:
/start - Iniciar o bot
/help - Ver esta mensagem
/resumo - Ver resumo de gastos
/categorias - Listar categorias
/limpar - Limpar histórico
```

### 2. Registrando Gastos

#### Mensagens Diretas
```
Usuário: gastei 50 reais com almoço
Bot: ✅ Gasto registrado: R$ 50,00 - Almoço (Categoria: Alimentação)

Usuário: paguei 150 de conta de luz
Bot: ✅ Gasto registrado: R$ 150,00 - Conta de luz (Categoria: Moradia)
```

#### Com Emojis
```
Usuário: 🍕 30 reais em pizza
Bot: ✅ Gasto registrado: R$ 30,00 - Pizza (Categoria: Alimentação)

Usuário: 🚕 25 de táxi
Bot: ✅ Gasto registrado: R$ 25,00 - Táxi (Categoria: Transporte)
```

### 3. Consultas e Relatórios

#### Resumo de Gastos
```
/resumo
📊 Seu Resumo de Gastos:
- Alimentação: R$ 500,00 (40%)
- Transporte: R$ 200,00 (16%)
- Moradia: R$ 300,00 (24%)
- Lazer: R$ 100,00 (8%)
- Outros: R$ 150,00 (12%)
Total: R$ 1.250,00
```

#### Categorias
```
/categorias
📋 Categorias Disponíveis:
1. Alimentação
2. Transporte
3. Moradia
4. Lazer
5. Saúde
6. Educação
7. Vestuário
8. Outros
```

### 4. Interação com IA

#### Perguntas Financeiras
```
Usuário: como economizar em transporte?
Bot: 🤖 Aqui estão dicas para economizar em transporte:
1. Use transporte público
2. Carona solidária
3. Bicicleta para trajetos curtos
4. Aplicativos de carona
5. Planeje rotas eficientes

Usuário: qual cartão de crédito é melhor?
Bot: 🤖 Para escolher o melhor cartão, considere:
1. Sua renda mensal
2. Seu perfil de gastos
3. Benefícios oferecidos
4. Taxas e anuidade
5. Programa de pontos
```

## Dicas de Uso Avançado

### 1. Categorização Automática
- O sistema aprende com o tempo
- Use descrições consistentes
- Adicione contexto quando necessário

### 2. Otimizando Consultas à IA
- Seja específico nas perguntas
- Forneça contexto relevante
- Use palavras-chave claras

### 3. Backup e Segurança
- Faça backup regular dos dados
- Mantenha suas chaves de API seguras
- Use senhas fortes para o bot

### 4. Personalização
- Configure categorias personalizadas
- Ajuste limites de gastos
- Defina alertas personalizados 