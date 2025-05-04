# Telegram Bot for Railway

Este é um bot do Telegram configurado para rodar 24/7 no Railway.app.

## Estrutura do Projeto

```
.
├── src/
│   └── StartBot.py      # Código principal do bot
├── data/                # Dados do bot
├── config/             # Arquivos de configuração
├── requirements.txt    # Dependências Python
├── Procfile           # Configuração do Railway
└── .env.example       # Exemplo de variáveis de ambiente
```

## Configuração

1. Clone este repositório
2. Copie `.env.example` para `.env` e preencha as variáveis:
   - `TELEGRAM_TOKEN`: Token do seu bot do Telegram
   - `GOOGLE_API_KEY`: Chave da API do Google (para Gemini)
   - `PORT`: Porta para o Railway (geralmente 8000)

## Deploy no Railway

1. Crie uma conta no [Railway.app](https://railway.app)
2. Conecte seu repositório GitHub
3. Configure as variáveis de ambiente no painel do Railway
4. O deploy será automático após o push

## Comandos do Bot

- `/start` - Inicia o bot
- `/ajuda` - Mostra ajuda
- `/salario` - Gerencia salário
- `/resumo` - Mostra resumo financeiro
- `/metas` - Gerencia metas financeiras

## Manutenção

O bot é configurado para:
- Reiniciar automaticamente em caso de falhas
- Manter-se online 24/7
- Logar erros para debug
- Gerenciar conexões de forma eficiente 