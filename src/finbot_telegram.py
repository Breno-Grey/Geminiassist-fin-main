import logging
import google.generativeai as genai
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# Configuração do logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Configuração do Gemini
GOOGLE_API_KEY = "AIzaSyAyQyCQPAkR5yjGkLgz-hOWqzpH-WALRVY"
genai.configure(api_key=GOOGLE_API_KEY)

# Configuração do modelo
model = genai.GenerativeModel('gemini-1.5-pro')

# Prompt do FinBot
FINBOT_PROMPT = """
Você é o FinBot, um assistente financeiro, inteligente e confiável. Seu objetivo é ajudar pessoas a organizarem suas finanças pessoais de maneira prática, clara e personalizada.

Você entende sobre controle de gastos, investimentos, orçamentos, economia doméstica, metas financeiras e dicas de educação financeira.

Ao conversar, seja sempre educado, positivo e motivador. Fale de forma simples e objetiva, adaptando sua linguagem conforme o nível de conhecimento da pessoa (iniciante, intermediário ou avançado).

Seu papel é:

Registrar e organizar despesas e receitas.

Ajudar a planejar orçamentos e controlar dívidas.

Sugerir melhorias e boas práticas financeiras.

Motivar o usuário a atingir suas metas financeiras.

Responder dúvidas financeiras de maneira precisa e fácil de entender.

Sempre pergunte de forma respeitosa antes de agir, e encoraje o usuário a manter uma rotina saudável de acompanhamento financeiro.

Quando receber informações financeiras, registre com atenção e, se necessário, faça perguntas para entender melhor.

Você é o parceiro financeiro que as pessoas podem confiar todos os dias.
"""

# Dicionário para armazenar as conversas
user_chats = {}

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler para o comando /start"""
    user_id = update.effective_user.id
    
    # Inicia uma nova conversa para o usuário
    user_chats[user_id] = model.start_chat(history=[])
    user_chats[user_id].send_message(FINBOT_PROMPT)
    
    welcome_message = (
        "👋 Olá! Eu sou o FinBot, seu assistente financeiro pessoal!\n\n"
        "Posso ajudar você com:\n\n"
        "💰 Controle de gastos e receitas\n"
        "📊 Planejamento orçamentário\n"
        "🎯 Definição de metas financeiras\n"
        "💡 Dicas de investimento\n"
        "📝 Gestão de dívidas\n"
        "📚 Educação financeira\n\n"
        "Como posso ajudar você hoje?"
    )
    await update.message.reply_text(welcome_message)

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler para o comando /help"""
    help_text = (
        "Comandos disponíveis:\n\n"
        "/start - Iniciar conversa\n"
        "/help - Mostrar esta mensagem\n"
        "/gastos - Ajudar com controle de gastos\n"
        "/orçamento - Ajudar com planejamento orçamentário\n"
        "/metas - Ajudar a definir metas financeiras\n"
        "/investimentos - Dicas de investimento\n"
        "/dividas - Ajudar com gestão de dívidas\n\n"
        "Você também pode simplesmente conversar comigo sobre qualquer assunto financeiro!"
    )
    await update.message.reply_text(help_text)

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler para mensagens de texto"""
    try:
        user_id = update.effective_user.id
        
        # Se o usuário não tem uma conversa ativa, inicia uma nova
        if user_id not in user_chats:
            user_chats[user_id] = model.start_chat(history=[])
            user_chats[user_id].send_message(FINBOT_PROMPT)
        
        # Envia a mensagem para o Gemini e obtém a resposta
        response = user_chats[user_id].send_message(update.message.text)
        
        # Envia a resposta para o usuário
        await update.message.reply_text(response.text)
        
    except Exception as e:
        logger.error(f"Erro ao processar mensagem: {e}")
        await update.message.reply_text(
            "Desculpe, tive um problema ao processar sua mensagem. "
            "Por favor, tente novamente ou use um dos comandos disponíveis."
        )

def main():
    """Função principal que inicia o bot"""
    # Token do Telegram
    TELEGRAM_TOKEN = "7527630621:AAFVK10miTDtB1ivqZA5HCshQREKaBNs1es"
    
    # Cria a aplicação
    application = Application.builder().token(TELEGRAM_TOKEN).build()

    # Adiciona os handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    # Inicia o bot
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == '__main__':
    main() 