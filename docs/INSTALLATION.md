# Guia de Instalação e Configuração

## Requisitos do Sistema

### Requisitos Mínimos
- Python 3.8 ou superior
- 2GB de RAM
- 500MB de espaço em disco
- Conexão com internet (para uso da IA)

### Requisitos Recomendados
- Python 3.10 ou superior
- 4GB de RAM
- 1GB de espaço em disco
- Conexão estável com internet

## Instalação

### 1. Clonando o Repositório
```bash
git clone https://github.com/seu-usuario/geminiassist-fin.git
cd geminiassist-fin
```

### 2. Configurando o Ambiente Virtual
```bash
# Criando ambiente virtual
python -m venv venv

# Ativando ambiente virtual
# No Windows:
venv\Scripts\activate
# No Linux/Mac:
source venv/bin/activate
```

### 3. Instalando Dependências
```bash
pip install -r requirements.txt
```

### 4. Configuração do Ambiente

#### Criando Arquivo .env
Crie um arquivo `.env` na raiz do projeto com as seguintes variáveis:

```env
# Chave da API do Google Gemini
GEMINI_API_KEY=sua_chave_aqui

# Configurações do Bot Telegram (opcional)
TELEGRAM_BOT_TOKEN=seu_token_aqui
TELEGRAM_BOT_USERNAME=seu_bot_username

# Configurações do Banco de Dados
DB_PATH=./data/gastos.db
DB_BACKUP_PATH=./data/backups/

# Configurações de Cache
CACHE_SIZE=1000
CACHE_TTL=3600
```

### 5. Inicialização do Banco de Dados
```bash
python src/init_db.py
```

## Configuração do Bot Telegram (Opcional)

### 1. Criando um Bot no Telegram
1. Abra o Telegram e procure por @BotFather
2. Use o comando `/newbot`
3. Siga as instruções para criar seu bot
4. Copie o token fornecido para o arquivo `.env`

### 2. Configurando o Bot
1. Edite o arquivo `config/bot_config.py` com suas preferências
2. Configure os comandos do bot usando o BotFather:
   ```
   /start - Iniciar o bot
   /help - Ver ajuda
   /resumo - Ver resumo de gastos
   /categorias - Listar categorias
   /limpar - Limpar histórico
   ```

## Executando o Sistema

### Modo CLI
```bash
python src/main.py
```

### Modo Bot Telegram
```bash
python src/telegram_bot.py
```

## Verificação da Instalação

### Testes Automáticos
```bash
python -m pytest tests/
```

### Testes Manuais
1. Execute o sistema em modo CLI
2. Tente registrar um gasto
3. Verifique se o banco de dados foi criado
4. Confirme se a IA está respondendo

## Solução de Problemas

### Problemas Comuns

1. **Erro de Conexão com a API**
   - Verifique sua chave da API
   - Confirme sua conexão com a internet
   - Verifique as quotas da API

2. **Problemas com o Banco de Dados**
   - Verifique as permissões do diretório
   - Confirme o caminho do banco de dados
   - Tente reinicializar o banco

3. **Erros do Bot Telegram**
   - Verifique o token do bot
   - Confirme se o bot está ativo
   - Verifique as configurações de privacidade

### Logs
- Os logs são armazenados em `logs/`
- Níveis de log configuráveis no arquivo `.env`

## Atualização

### Atualizando o Sistema
```bash
git pull
pip install -r requirements.txt --upgrade
python src/init_db.py --update
```

### Backup
```bash
python src/backup.py
```

## Suporte

Para suporte adicional:
- Consulte a documentação em `docs/`
- Abra uma issue no GitHub
- Entre em contato com a equipe de suporte 