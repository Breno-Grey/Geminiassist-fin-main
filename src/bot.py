import os
import logging
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from dotenv import load_dotenv

# Configurar logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Carregar variáveis de ambiente
load_dotenv()
TOKEN = os.getenv('TELEGRAM_TOKEN')

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Manipula o comando /start"""
    user = update.effective_user
    await update.message.reply_text(
        f'Olá {user.first_name}! 👋\n\n'
        'Bem-vindo ao seu bot! Estou aqui para ajudar.\n\n'
        'Comandos disponíveis:\n'
        '/start - Iniciar o bot\n'
        '/help - Ver ajuda\n'
        '/ping - Verificar se o bot está online'
    )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Manipula o comando /help"""
    await update.message.reply_text(
        '🤖 Comandos disponíveis:\n\n'
        '/start - Iniciar o bot\n'
        '/help - Ver esta mensagem de ajuda\n'
        '/ping - Verificar se o bot está online'
    )

async def ping(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Manipula o comando /ping"""
    await update.message.reply_text('🏓 Pong! O bot está online!')

async def echo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Ecoa a mensagem do usuário"""
    await update.message.reply_text(update.message.text)

def main():
    """Inicia o bot"""
    # Criar a aplicação
    application = Application.builder().token(TOKEN).build()

    # Adicionar handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("ping", ping))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, echo))

    # Iniciar o bot
    application.run_polling()

# Criar a aplicação para o Railway
app = Application.builder().token(TOKEN).build()

# Adicionar handlers para a aplicação
app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("help", help_command))
app.add_handler(CommandHandler("ping", ping))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, echo))

if __name__ == '__main__':
    main() 