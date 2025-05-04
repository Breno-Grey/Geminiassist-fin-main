# Telegram Bot

Um bot do Telegram simples que pode ser hospedado no Railway.app.

## Funcionalidades

- Comando `/start` - Inicia o bot
- Comando `/help` - Mostra ajuda
- Comando `/ping` - Verifica se o bot está online
- Ecoa mensagens de texto

## Configuração

1. Clone este repositório
2. Crie um arquivo `.env` baseado no `.env.example`:
   ```
   TELEGRAM_TOKEN=seu_token_aqui
   ```
3. Obtenha um token do BotFather no Telegram
4. Substitua `seu_token_aqui` pelo token real

## Deploy no Railway.app

1. Crie uma conta no [Railway.app](https://railway.app)
2. Conecte seu repositório GitHub
3. Adicione as variáveis de ambiente:
   - `TELEGRAM_TOKEN`: Seu token do BotFather
4. O deploy será automático

## Estrutura do Projeto

```
.
├── Procfile          # Configuração do Railway
├── requirements.txt  # Dependências Python
├── src/
│   └── bot.py       # Código principal do bot
└── .env             # Variáveis de ambiente (não versionado)
```

## Desenvolvimento Local

1. Instale as dependências:
   ```bash
   pip install -r requirements.txt
   ```
2. Execute o bot:
   ```bash
   python src/bot.py
   ``` 