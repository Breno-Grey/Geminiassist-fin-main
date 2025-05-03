from gastos_manager import GastosManager
import google.generativeai as genai
import os
from dotenv import load_dotenv
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes, CallbackQueryHandler
from collections import defaultdict
from datetime import datetime, timedelta
import logging
from validadores import ValidadorEntrada
from resumo_manager import ResumoManager
import telegram
import time

# Configurar logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Criar pasta data se não existir
if not os.path.exists('data'):
    os.makedirs('data')

# Configurar a API do Gemini
GOOGLE_API_KEY = "AIzaSyAyQyCQPAkR5yjGkLgz-hOWqzpH-WALRVY"
TELEGRAM_TOKEN = "7806097135:AAFb40DQgSGiu7uIk6trkdFWISW-j37Keyg"
genai.configure(api_key=GOOGLE_API_KEY)

# Configurar o modelo
model = genai.GenerativeModel('gemini-1.5-pro')

# Dicionário para armazenar instâncias do GastosManager por usuário
gastos_managers = {}

# Dicionário para armazenar histórico de conversas por usuário
historico_conversas = defaultdict(list)

# Dicionário para armazenar estado de espera por salário
aguardando_salario = set()

# Dicionário para armazenar estado de espera por nome
aguardando_nome = set()

# Dicionário para armazenar estado de espera por meta
aguardando_meta = {}

# Adicione um controle de estado para saber se o usuário está no fluxo de envio de comprovante
aguardando_comprovante = set()

# Adicione um dicionário para rastrear o último tipo de mensagem enviada para cada usuário
ultimo_estado_usuario = {}

# Configuração do histórico
MAX_HISTORICO = 10  # Número máximo de mensagens no histórico
TEMPO_EXPIRACAO = timedelta(hours=12)  # Tempo para expirar o histórico

# Inicializa o gerenciador de resumos
resumo_manager = ResumoManager()

def get_gastos_manager(user_id):
    """Obtém ou cria uma instância do GastosManager para um usuário"""
    if user_id not in gastos_managers:
        # Cria um banco de dados específico para o usuário na pasta data
        db_name = f'data/gastos_{user_id}.db'
        gastos_managers[user_id] = GastosManager(db_name)
    return gastos_managers[user_id]

def limpar_historico_antigo():
    """Limpa o histórico antigo de todos os usuários"""
    agora = datetime.now()
    for user_id in list(historico_conversas.keys()):
        historico_conversas[user_id] = [
            msg for msg in historico_conversas[user_id]
            if agora - msg['timestamp'] <= TEMPO_EXPIRACAO
        ]
        if not historico_conversas[user_id]:
            del historico_conversas[user_id]

def adicionar_mensagem_historico(user_id, role, content):
    """Adiciona uma mensagem ao histórico do usuário"""
    limpar_historico_antigo()
    
    if user_id not in historico_conversas:
        historico_conversas[user_id] = []
    
    historico_conversas[user_id].append({
        'role': role,
        'content': content,
        'timestamp': datetime.now()
    })
    
    # Mantém apenas as últimas MAX_HISTORICO mensagens
    if len(historico_conversas[user_id]) > MAX_HISTORICO:
        historico_conversas[user_id] = historico_conversas[user_id][-MAX_HISTORICO:]

async def processar_comando_ia(mensagem, user_id, nome):
    """Processa a mensagem usando a IA do Gemini com contexto"""
    try:
        gm = get_gastos_manager(user_id)
        
        # Obtém dados financeiros do usuário
        salario = gm.get_salario()
        resumo_gastos, total_gastos, _ = gm.get_resumo()
        resumo_receitas, total_receitas = gm.get_resumo_receitas()
        metas = gm.get_metas()
        
        # Prepara o contexto financeiro
        contexto_financeiro = ""
        if salario:
            contexto_financeiro += f"\n💰 Salário: R${salario:.2f}"
        
        if total_gastos > 0:
            contexto_financeiro += "\n\n📊 Gastos:"
            for categoria, valor, percentual in resumo_gastos:
                contexto_financeiro += f"\n• {categoria}: R${valor:.2f} ({percentual:.1f}%)"
            contexto_financeiro += f"\n💵 Total: R${total_gastos:.2f}"
            
            if salario:
                percentual_salario = (total_gastos / salario) * 100
                contexto_financeiro += f"\n📈 {percentual_salario:.1f}% do salário"
        
        if total_receitas > 0:
            contexto_financeiro += "\n\n💵 Receitas:"
            for categoria, valor, percentual in resumo_receitas:
                contexto_financeiro += f"\n• {categoria}: R${valor:.2f} ({percentual:.1f}%)"
            contexto_financeiro += f"\n💰 Total: R${total_receitas:.2f}"
        
        if metas:
            contexto_financeiro += "\n\n🎯 Metas Financeiras:"
            for meta in metas:
                id_meta, nome_meta, valor_meta, valor_atual, data_limite, descricao, status = meta
                percentual = (valor_atual / valor_meta) * 100 if valor_meta > 0 else 0
                emoji = "✅" if status == "concluída" else "⏳" if status == "ativa" else "❌"
                contexto_financeiro += f"\n{emoji} {nome_meta}: R${valor_atual:.2f} / R${valor_meta:.2f} ({percentual:.1f}%)"
        
        # Contexto base para a IA
        contexto_base = f"""
        Você é o FinBot, um assistente financeiro amigável e atencioso. Seu objetivo é ajudar {nome} a organizar suas finanças de forma simples e prática, sempre com um toque pessoal.

Dados financeiros de {nome}:
{contexto_financeiro}

Use esses dados para dar conselhos práticos e personalizados. Seja conciso, mas mantenha um tom amigável e acolhedor.

Regras de comunicação:
1. Use emojis para destacar pontos importantes
2. Seja breve e objetivo, mas não muito direto
3. Divida respostas longas em mensagens curtas
4. Use formatação simples
5. Evite jargões financeiros
6. Dê exemplos práticos
7. Mantenha um tom amigável e acolhedor

Exemplo de resposta:
"Olá {nome}! 👋

💰 Analisando seus gastos:
• Alimentação: R$500 (25%)
• Transporte: R$300 (15%)

💡 Sugestão: Que tal tentar reduzir os gastos com alimentação em 10%? Cozinhar em casa pode ser uma boa opção! 

Se precisar de ajuda com receitas econômicas, é só me avisar! 😊"

Nunca use:
- Asteriscos (*)
- Texto em negrito
- Respostas muito longas
- Jargões técnicos
- Caracteres especiais

Mantenha as respostas:
- Curtas e diretas, mas amigáveis
- Com emojis relevantes
- Focadas em ações práticas
- Baseadas nos dados do usuário
- Com um toque pessoal
        """
        
        # Adiciona a mensagem do usuário ao histórico
        adicionar_mensagem_historico(user_id, 'user', mensagem)
        
        # Prepara o histórico para o modelo
        historico_formatado = [{'role': 'user', 'parts': [contexto_base]}]
        for msg in historico_conversas[user_id]:
            historico_formatado.append({
                'role': msg['role'],
                'parts': [msg['content']]
            })
        
        try:
            # Gera resposta com contexto
            response = model.generate_content(historico_formatado)
            resposta = response.text
            
            # Adiciona a resposta ao histórico
            adicionar_mensagem_historico(user_id, 'model', resposta)
            
            return resposta
            
        except Exception as e:
            logger.error(f"Erro ao gerar resposta do Gemini: {str(e)}")
            if "quota" in str(e).lower():
                return "Desculpe, estou tendo dificuldades temporárias para processar sua pergunta devido a limitações de uso. Por favor, tente novamente em alguns minutos. 😊"
            return "Desculpe, estou tendo dificuldades para processar sua pergunta. Por favor, tente novamente em alguns instantes. 😊"
        
    except Exception as e:
        logger.error(f"Erro ao processar comando IA: {str(e)}")
        return "Desculpe, ocorreu um erro ao processar sua mensagem. Por favor, tente novamente mais tarde. 😊"

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Manipula o comando /start"""
    user_id = update.effective_user.id
    gm = get_gastos_manager(user_id)
    
    # Verifica se já tem nome registrado
    nome = gm.get_nome_usuario()
    
    if nome is None:
        # Adiciona usuário à lista de espera por nome
        aguardando_nome.add(user_id)
        
        welcome_message = """
        🎉 Bem-vindo ao FinBot! 🤖

        Qual é o seu nome?
        """
        await update.message.reply_text(welcome_message)
    else:
        # Verifica se já tem salário registrado
        salario = gm.get_salario()
        
        if salario is None:
            # Adiciona usuário à lista de espera por salário
            aguardando_salario.add(user_id)
            
            welcome_message = f"""
            Olá {nome}! 👋

            Qual é seu salário mensal?
            (apenas números, exemplo: 3000)
            """
            await update.message.reply_text(welcome_message)
        else:
            # Verifica se já tem metas registradas
            metas = gm.get_metas()
            
            if not metas:
                # Adiciona usuário à lista de espera por meta
                aguardando_meta[user_id] = {
                    'etapa': 'nome_meta',
                    'dados': {}
                }
                
                welcome_message = f"""
                Olá {nome}! 👋

                Vamos criar sua primeira meta?
                Qual é o nome da meta?
                (exemplo: "Viagem para a praia")
                """
                await update.message.reply_text(welcome_message)
            else:
                # Cria botões inline para ações comuns
                keyboard = [
                    [
                        InlineKeyboardButton("💰 Registrar Gasto", callback_data="registrar_gasto"),
                        InlineKeyboardButton("💵 Registrar Receita", callback_data="registrar_receita")
                    ],
                    [
                        InlineKeyboardButton("📊 Ver Resumo", callback_data="ver_resumo"),
                        InlineKeyboardButton("🎯 Ver Metas", callback_data="ver_metas")
                    ],
                    [
                        InlineKeyboardButton("📝 Ajuda", callback_data="ajuda"),
                        InlineKeyboardButton("⚙️ Configurações", callback_data="configuracoes")
                    ]
                ]
                reply_markup = InlineKeyboardMarkup(keyboard)
                
                welcome_message = f"""
                Olá {nome}! 👋

                Como posso te ajudar hoje?
                """
                await update.message.reply_text(welcome_message, parse_mode='Markdown', reply_markup=reply_markup)

async def ajuda(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Manipula o comando /ajuda"""
    # Cria botões inline para seções de ajuda
    keyboard = [
        [
            InlineKeyboardButton("💰 Gastos", callback_data="ajuda_gastos"),
            InlineKeyboardButton("💵 Receitas", callback_data="ajuda_receitas")
        ],
        [
            InlineKeyboardButton("🎯 Metas", callback_data="ajuda_metas"),
            InlineKeyboardButton("📊 Resumos", callback_data="ajuda_resumos")
        ],
        [
            InlineKeyboardButton("⚙️ Configurações", callback_data="ajuda_config"),
            InlineKeyboardButton("❓ Outros", callback_data="ajuda_outros")
        ],
        [
            InlineKeyboardButton("🎉 Acesso Ilimitado", callback_data="acesso_ilimitado")
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    help_message = """
    *📋 Comandos Disponíveis*

    *💰 Gastos*
    • "gastei 50 com almoço"
    • "paguei 100 no mercado"
    • "comprei um presente por 80"

    *💵 Receitas*
    • "ganhei 100 com freela"
    • "recebi 50 de presente"
    • "consegui 200 com vendas"

    *📊 Comandos*
    /salario - Salário
    /resumo - Resumo básico
    /resumodetalhado - Análise completa
    /categorias - Lista de categorias
    /metas - Gerenciar metas
    /limpar - Limpar histórico

    *🎯 Metas*
    • Crie metas com nome e valor
    • Acompanhe seu progresso
    • Defina data limite

    *🤖 IA Financeira*
    • Pergunte sobre investimentos
    • Peça dicas de economia
    • Consulte sobre orçamento

    Clique nos botões para mais detalhes!
    """
    await update.message.reply_text(help_message, parse_mode='Markdown', reply_markup=reply_markup)

async def salario(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Manipula o comando /salario"""
    gm = get_gastos_manager(update.effective_user.id)
    
    # Se não tiver argumentos, mostra o salário atual
    if not context.args:
        salario = gm.get_salario()
        if salario is None:
            await update.message.reply_text(
                "❌ Você ainda não definiu seu salário.\n\n"
                "Para definir, use: /salario [valor]\n"
                "Exemplo: /salario 3000"
            )
        else:
            await update.message.reply_text(
                f"💰 Seu salário atual é: R${salario:.2f}\n\n"
                "Para alterar, use: /salario [novo valor]\n"
                "Exemplo: /salario 3500"
            )
        return
    
    # Se tiver argumentos, tenta alterar o salário
    try:
        novo_salario = float(context.args[0].replace(',', '.'))
        
        if novo_salario <= 0:
            await update.message.reply_text("❌ O salário deve ser maior que zero. Por favor, digite um valor válido.")
            return
        
        if gm.definir_salario(novo_salario):
            await update.message.reply_text(
                f"✅ Salário atualizado com sucesso!\n"
                f"💰 Novo salário: R${novo_salario:.2f}"
            )
        else:
            await update.message.reply_text("❌ Erro ao atualizar salário. Por favor, tente novamente.")
            
    except ValueError:
        await update.message.reply_text(
            "❌ Formato inválido. Use: /salario [valor]\n"
            "Exemplo: /salario 3000"
        )

async def resumo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Manipula o comando /resumo"""
    try:
        gm = get_gastos_manager(update.effective_user.id)
        resumo, total, resumo_texto = gm.get_resumo()
        await update.message.reply_text(resumo_texto)
    except Exception as e:
        await update.message.reply_text(f"❌ Erro ao gerar resumo: {str(e)}")

async def resumo_detalhado(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Manipula o comando /resumodetalhado"""
    try:
        gm = get_gastos_manager(update.effective_user.id)
        
        # Verifica se foram passados argumentos de data
        data_inicio = None
        data_fim = None
        
        if context.args:
            if len(context.args) >= 2:
                data_inicio = context.args[0]
                data_fim = context.args[1]
            else:
                await update.message.reply_text(
                    "⚠️ Por favor, forneça as datas no formato: /resumodetalhado DD/MM/YYYY DD/MM/YYYY"
                )
                return
        
        # Gera o resumo detalhado
        resumo_texto, grafico_bytes = gm.get_resumo_detalhado(data_inicio, data_fim)
        
        # Envia o texto do resumo
        await update.message.reply_text(resumo_texto)
        
        # Se houver gráfico, envia como foto
        if grafico_bytes:
            await update.message.reply_photo(photo=grafico_bytes)
            
    except Exception as e:
        await update.message.reply_text(f"❌ Erro ao gerar resumo detalhado: {str(e)}")

async def categorias(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Manipula o comando /categorias"""
    gm = get_gastos_manager(update.effective_user.id)
    categorias = gm.get_categorias()
    
    message = "📑 Categorias disponíveis:\n"
    for i, categoria in enumerate(categorias, 1):
        message += f"{i}. {categoria}\n"
    
    await update.message.reply_text(message)

async def metas(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Manipula o comando /metas e suas variações"""
    user_id = update.effective_user.id
    gm = get_gastos_manager(user_id)
    
    # Se não tiver argumentos, mostra as metas atuais
    if not context.args:
        metas = gm.get_metas()
        
        if not metas:
            await update.message.reply_text(
                "🎯 Você ainda não tem metas definidas.\n\n"
                "Para criar uma nova meta, você pode:\n"
                "1. Usar o comando: /metas criar [nome] [valor] [data_limite]\n"
                "   Exemplo: /metas criar Viagem 5000 31/12/2024\n\n"
                "2. Ou digitar frases como:\n"
                "   • 'Quero criar uma meta de Viagem com 5000 reais'\n"
                "   • 'Nova meta chamada Carro com 30000 reais'\n"
                "   • 'Vou guardar 1000 reais para a meta Casa'"
            )
            return
        
        message = "🎯 Suas Metas Financeiras:\n\n"
        for meta in metas:
            id_meta, nome, valor_meta, valor_atual, data_limite, descricao, status = meta
            percentual = (valor_atual / valor_meta) * 100 if valor_meta > 0 else 0
            emoji = "✅" if status == "concluída" else "⏳" if status == "ativa" else "❌"
            message += f"{emoji} {nome} (ID: {id_meta}):\n"
            message += f"💰 Meta: R${valor_meta:.2f}\n"
            message += f"💵 Atual: R${valor_atual:.2f} ({percentual:.1f}%)\n"
            if data_limite:
                message += f"📅 Data limite: {data_limite}\n"
            if descricao:
                message += f"📝 {descricao}\n"
            message += "\n"
        
        message += "\n📌 Comandos disponíveis:\n"
        message += "/meta [nome da meta] [valor] - Adicionar valor a uma meta\n"
        message += "/metas editar [id] [campo] [valor] - Editar uma meta\n"
        message += "/metas remover [id] - Remover uma meta\n"
        message += "Exemplos:\n"
        message += "• /meta Viagem 1000\n"
        message += "• /metas editar 1 nome Nova Viagem\n"
        message += "• /metas editar 1 valor 6000\n"
        message += "• /metas editar 1 data 31/12/2024\n"
        message += "• /metas remover 1\n"
        
        await update.message.reply_text(message)
        return
    
    # Comandos de gerenciamento de metas
    comando = context.args[0].lower()
    
    if comando in ["criar", "nova", "adicionar", "estabelecer", "definir"]:
        if len(context.args) < 3:
            await update.message.reply_text(
                "⚠️ Formato incorreto. Use: /metas criar [nome] [valor] [data_limite]\n"
                "Exemplo: /metas criar Viagem 5000 31/12/2024\n\n"
                "💡 Você também pode digitar frases como:\n"
                "• 'Quero criar uma meta de Viagem com 5000 reais'\n"
                "• 'Nova meta chamada Carro com 30000 reais'\n"
                "• 'Vou guardar 1000 reais para a meta Casa'"
            )
            return
        
        nome = context.args[1]
        try:
            valor = float(context.args[2].replace(',', '.'))
            data_limite = context.args[3] if len(context.args) > 3 else None
            
            if gm.definir_meta(nome, valor, data_limite):
                await update.message.reply_text(
                    f"✅ Meta '{nome}' criada com sucesso!\n\n"
                    f"💰 Valor: R${valor:.2f}\n"
                    f"📅 Data limite: {data_limite if data_limite else 'Não definida'}\n\n"
                    "💡 Para adicionar valores a esta meta, use o comando:\n"
                    "/meta [nome da meta] [valor a adicionar]\n"
                    "Exemplo: /meta Viagem 1000"
                )
            else:
                await update.message.reply_text("❌ Erro ao criar meta. Tente novamente.")
        except ValueError:
            await update.message.reply_text("❌ Valor inválido. Use apenas números.")
    
    elif comando in ["atualizar", "atualiza", "atualize", "mudar", "alterar", "modificar"]:
        if len(context.args) < 3:
            await update.message.reply_text(
                "⚠️ Formato incorreto. Use: /metas atualizar [id] [valor_atual]\n"
                "Exemplo: /metas atualizar 1 1000\n\n"
                "💡 Dica: Você também pode usar o comando /meta [nome da meta] [valor a adicionar]"
            )
            return
        
        try:
            meta_id = int(context.args[1])
            valor_atual = float(context.args[2].replace(',', '.'))
            
            if gm.atualizar_meta(meta_id, valor_atual):
                await update.message.reply_text(
                    f"✅ Meta atualizada com sucesso!\n"
                    f"💰 Novo valor: R${valor_atual:.2f}\n\n"
                    "💡 Dica: Use o comando /meta [nome da meta] [valor a adicionar] para adicionar valores"
                )
            else:
                await update.message.reply_text("❌ Erro ao atualizar meta. Verifique o ID.")
        except ValueError:
            await update.message.reply_text("❌ Valores inválidos. Use números.")
    
    elif comando in ["ver", "mostrar", "listar", "exibir", "consultar"]:
        metas = gm.get_metas()
        if not metas:
            await update.message.reply_text("🎯 Você ainda não tem metas definidas.")
            return
        
        message = "🎯 Suas Metas Financeiras:\n\n"
        for meta in metas:
            id_meta, nome, valor_meta, valor_atual, data_limite, descricao, status = meta
            percentual = (valor_atual / valor_meta) * 100 if valor_meta > 0 else 0
            emoji = "✅" if status == "concluída" else "⏳" if status == "ativa" else "❌"
            message += f"{emoji} {nome}:\n"
            message += f"💰 Meta: R${valor_meta:.2f}\n"
            message += f"💵 Atual: R${valor_atual:.2f} ({percentual:.1f}%)\n"
            if data_limite:
                message += f"📅 Data limite: {data_limite}\n"
            if descricao:
                message += f"📝 {descricao}\n"
            message += "\n"
        
        await update.message.reply_text(message)
    
    elif comando in ["remover", "deletar", "excluir", "apagar"]:
        if len(context.args) < 2:
            await update.message.reply_text(
                "⚠️ Formato incorreto. Use: /metas remover [id]\n"
                "Exemplo: /metas remover 1\n\n"
                "💡 Dica: Use /metas para ver a lista de metas e seus IDs"
            )
            return
        
        try:
            meta_id = int(context.args[1])
            if gm.remover_meta(meta_id):
                await update.message.reply_text(
                    f"✅ Meta removida com sucesso!\n\n"
                    "💡 Use /metas para ver a lista atualizada de metas"
                )
            else:
                await update.message.reply_text(
                    "❌ Erro ao remover meta. Verifique se o ID está correto.\n"
                    "Use /metas para ver a lista de metas e seus IDs"
                )
        except ValueError:
            await update.message.reply_text("❌ ID inválido. Use apenas números.")
    
    elif comando in ["editar", "alterar", "modificar", "mudar"]:
        if len(context.args) < 4:
            await update.message.reply_text(
                "⚠️ Formato incorreto. Use: /metas editar [id] [campo] [valor]\n\n"
                "📝 Campos disponíveis:\n"
                "• nome - Nome da meta\n"
                "• valor - Valor da meta\n"
                "• data - Data limite (formato: DD/MM/AAAA)\n"
                "• descricao - Descrição da meta\n\n"
                "Exemplos:\n"
                "• /metas editar 1 nome Nova Viagem\n"
                "• /metas editar 1 valor 6000\n"
                "• /metas editar 1 data 31/12/2024\n"
                "• /metas editar 1 descricao Viagem para o Caribe"
            )
            return
        
        try:
            meta_id = int(context.args[1])
            campo = context.args[2].lower()
            valor = " ".join(context.args[3:])
            
            # Converte o valor conforme o campo
            if campo == "valor":
                valor = float(valor.replace(',', '.'))
            elif campo == "data":
                # Valida o formato da data
                try:
                    datetime.strptime(valor, '%d/%m/%Y')
                except ValueError:
                    await update.message.reply_text(
                        "❌ Data inválida. Use o formato DD/MM/AAAA\n"
                        "Exemplo: 31/12/2024"
                    )
                    return
            
            # Mapeia o campo para o parâmetro correto
            campos = {
                "nome": "nome",
                "valor": "valor_meta",
                "data": "data_limite",
                "descricao": "descricao"
            }
            
            if campo not in campos:
                await update.message.reply_text(
                    "❌ Campo inválido. Campos disponíveis:\n"
                    "• nome - Nome da meta\n"
                    "• valor - Valor da meta\n"
                    "• data - Data limite\n"
                    "• descricao - Descrição da meta"
                )
                return
            
            # Prepara os parâmetros para a função editar_meta
            parametros = {campos[campo]: valor}
            
            if gm.editar_meta(meta_id, **parametros):
                await update.message.reply_text(
                    f"✅ Meta editada com sucesso!\n\n"
                    "💡 Use /metas para ver a lista atualizada de metas"
                )
            else:
                await update.message.reply_text(
                    "❌ Erro ao editar meta. Verifique se o ID e os valores estão corretos.\n"
                    "Use /metas para ver a lista de metas e seus IDs"
                )
                
        except ValueError as e:
            if "could not convert string to float" in str(e):
                await update.message.reply_text("❌ Valor inválido. Use apenas números para o campo 'valor'.")
            else:
                await update.message.reply_text("❌ ID inválido. Use apenas números para o ID da meta.")
    
    else:
        await update.message.reply_text(
            "⚠️ Comando inválido. Use:\n"
            "/metas - Ver todas as metas\n"
            "/metas criar [nome] [valor] [data_limite] - Criar nova meta\n"
            "/meta [nome da meta] [valor a adicionar] - Adicionar valor a uma meta\n\n"
            "💡 Dica: Você também pode gerenciar metas digitando frases como:\n"
            "• 'Quero criar uma meta de Viagem com 5000 reais'\n"
            "• 'Mostre minhas metas'"
        )

async def meta(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Manipula o comando /meta para atualizar o valor de uma meta"""
    if len(context.args) < 2:
        await update.message.reply_text(
            "⚠️ Formato incorreto. Use: /meta [nome da meta] [valor a adicionar]\n"
            "Exemplo: /meta Viagem 1000"
        )
        return
    
    try:
        nome_meta = " ".join(context.args[:-1])  # Pega todos os argumentos exceto o último como nome da meta
        valor = float(context.args[-1].replace(',', '.'))
        
        if valor <= 0:
            await update.message.reply_text("❌ O valor deve ser maior que zero.")
            return
        
        gm = get_gastos_manager(update.effective_user.id)
        metas = gm.get_metas()
        
        # Procura a meta pelo nome
        meta_encontrada = None
        for meta in metas:
            if meta[1].lower() == nome_meta.lower():
                meta_encontrada = meta
                break
        
        if not meta_encontrada:
            await update.message.reply_text(f"❌ Meta '{nome_meta}' não encontrada.")
            return
        
        # Atualiza a meta
        if gm.registrar_contribuicao_meta(meta_encontrada[0], valor)[0]:
            await update.message.reply_text(
                f"✅ Valor adicionado à meta '{nome_meta}' com sucesso!\n"
                f"💰 Valor adicionado: R${valor:.2f}"
            )
        else:
            await update.message.reply_text("❌ Erro ao atualizar meta. Tente novamente.")
            
    except ValueError:
        await update.message.reply_text(
            "❌ Valor inválido. Use: /meta [nome da meta] [valor a adicionar]\n"
            "Exemplo: /meta Viagem 1000"
        )

async def limpar(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Manipula o comando /limpar"""
    gm = get_gastos_manager(update.effective_user.id)
    
    # Criar botões de confirmação
    keyboard = [
        [
            InlineKeyboardButton("Sim", callback_data="limpar_sim"),
            InlineKeyboardButton("Não", callback_data="limpar_nao")
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        "⚠️ Tem certeza que deseja limpar todo o histórico de gastos?",
        reply_markup=reply_markup
    )

async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Manipula os callbacks dos botões inline"""
    query = update.callback_query
    await query.answer()
    
    user_id = query.from_user.id
    gm = get_gastos_manager(user_id)
    
    if query.data == "registrar_gasto":
        await query.edit_message_text(
            "*💰 Registro de Gastos*\n\n"
            "Digite seu gasto no formato:\n"
            "• \"gastei 50 reais com almoço\"\n"
            "• \"paguei 100 no mercado\"\n"
            "• \"comprei um presente por 80\"\n\n"
            "💡 Você pode especificar a data:\n"
            "• \"gastei 50 com almoço ontem\"\n"
            "• \"paguei 100 no mercado semana passada\"",
            parse_mode='Markdown'
        )
        
    elif query.data == "registrar_receita":
        await query.edit_message_text(
            "*💵 Registro de Receitas*\n\n"
            "Digite sua receita no formato:\n"
            "• \"ganhei 100 reais com freela\"\n"
            "• \"recebi 50 de presente\"\n"
            "• \"consegui 200 com vendas\"\n\n"
            "💡 Você pode especificar a data:\n"
            "• \"ganhei 100 com freela ontem\"\n"
            "• \"recebi 50 de presente semana passada\"",
            parse_mode='Markdown'
        )
        
    elif query.data == "ver_resumo":
        resumo, total, resumo_texto = gm.get_resumo()
        await query.edit_message_text(
            f"*📊 Resumo Financeiro*\n\n"
            f"{resumo_texto}\n\n"
            "💡 Use /resumodetalhado para ver uma análise mais completa",
            parse_mode='Markdown'
        )
        
    elif query.data == "ver_metas":
        metas = gm.get_metas()
        if not metas:
            await query.edit_message_text(
                "*🎯 Metas Financeiras*\n\n"
                "Você ainda não tem metas definidas.\n\n"
                "Para criar uma nova meta, use o comando /metas ou clique em Ajuda para mais informações.",
                parse_mode='Markdown'
            )
        else:
            message = "*🎯 Suas Metas Financeiras*\n\n"
            for meta in metas:
                id_meta, nome, valor_meta, valor_atual, data_limite, descricao, status = meta
                percentual = (valor_atual / valor_meta) * 100 if valor_meta > 0 else 0
                emoji = "✅" if status == "concluída" else "⏳" if status == "ativa" else "❌"
                message += f"{emoji} *{nome}*\n"
                message += f"💰 Meta: R${valor_meta:.2f}\n"
                message += f"💵 Atual: R${valor_atual:.2f} ({percentual:.1f}%)\n"
                if data_limite:
                    message += f"📅 Data limite: {data_limite}\n"
                if descricao:
                    message += f"📝 {descricao}\n"
                message += "\n"
            await query.edit_message_text(message, parse_mode='Markdown')
            
    elif query.data == "ajuda":
        # Cria botões inline para seções de ajuda
        keyboard = [
            [
                InlineKeyboardButton("💰 Gastos", callback_data="ajuda_gastos"),
                InlineKeyboardButton("💵 Receitas", callback_data="ajuda_receitas")
            ],
            [
                InlineKeyboardButton("🎯 Metas", callback_data="ajuda_metas"),
                InlineKeyboardButton("📊 Resumos", callback_data="ajuda_resumos")
            ],
            [
                InlineKeyboardButton("⚙️ Configurações", callback_data="ajuda_config"),
                InlineKeyboardButton("❓ Outros", callback_data="ajuda_outros")
            ],
            [
                InlineKeyboardButton("🎉 Acesso Ilimitado", callback_data="acesso_ilimitado")
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        help_message = """
        *📋 Comandos Disponíveis*

        *💰 Gastos*
        • "gastei 50 com almoço"
        • "paguei 100 no mercado"
        • "comprei um presente por 80"

        *💵 Receitas*
        • "ganhei 100 com freela"
        • "recebi 50 de presente"
        • "consegui 200 com vendas"

        *📊 Comandos*
        /salario - Salário
        /resumo - Resumo básico
        /resumodetalhado - Análise completa
        /categorias - Lista de categorias
        /metas - Gerenciar metas
        /limpar - Limpar histórico

        *🎯 Metas*
        • Crie metas com nome e valor
        • Acompanhe seu progresso
        • Defina data limite

        *🤖 IA Financeira*
        • Pergunte sobre investimentos
        • Peça dicas de economia
        • Consulte sobre orçamento

        Clique nos botões para mais detalhes!
        """
        await query.edit_message_text(help_message, parse_mode='Markdown', reply_markup=reply_markup)
        
    elif query.data == "configuracoes":
        await query.edit_message_text(
            "*⚙️ Configurações*\n\n"
            "📝 *Comandos disponíveis:*\n"
            "/salario - Ver ou alterar seu salário\n"
            "/categorias - Listar categorias\n"
            "/limpar - Limpar histórico\n\n"
            "💡 Use /ajuda para ver todas as opções disponíveis",
            parse_mode='Markdown'
        )
        
    elif query.data == "ajuda_gastos":
        await query.edit_message_text(
            "*💰 Ajuda: Registro de Gastos*\n\n"
            "📝 *Formato:*\n"
            "• \"gastei 50 reais com almoço\"\n"
            "• \"paguei 100 no mercado\"\n"
            "• \"comprei um presente por 80\"\n\n"
            "📅 *Datas:*\n"
            "• \"gastei 50 com almoço ontem\"\n"
            "• \"paguei 100 no mercado semana passada\"\n"
            "• \"comprei um presente por 80 em 15/03\"\n\n"
            "💡 *Dicas:*\n"
            "• O bot identifica automaticamente a categoria\n"
            "• Use emojis para facilitar a leitura\n"
            "• Mantenha suas descrições claras",
            parse_mode='Markdown'
        )
        
    elif query.data == "ajuda_receitas":
        await query.edit_message_text(
            "*💵 Ajuda: Registro de Receitas*\n\n"
            "📝 *Formato:*\n"
            "• \"ganhei 100 reais com freela\"\n"
            "• \"recebi 50 de presente\"\n"
            "• \"consegui 200 com vendas\"\n\n"
            "📅 *Datas:*\n"
            "• \"ganhei 100 com freela ontem\"\n"
            "• \"recebi 50 de presente semana passada\"\n"
            "• \"consegui 200 com vendas em 15/03\"\n\n"
            "💡 *Dicas:*\n"
            "• Registre todas as suas receitas\n"
            "• Inclua renda extra e bônus\n"
            "• Mantenha um histórico organizado",
            parse_mode='Markdown'
        )
        
    elif query.data == "ajuda_metas":
        await query.edit_message_text(
            "*🎯 Ajuda: Metas Financeiras*\n\n"
            "📝 *Como criar uma meta:*\n"
            "1. Use o comando /metas\n"
            "2. Digite o nome da meta\n"
            "3. Defina o valor alvo\n"
            "4. (Opcional) Defina uma data limite\n\n"
            "💡 *Dicas:*\n"
            "• Defina metas realistas\n"
            "• Acompanhe seu progresso\n"
            "• Celebre suas conquistas\n\n"
            "📊 *Comandos:*\n"
            "/metas - Ver todas as metas\n"
            "/metas criar [nome] [valor] [data] - Criar nova meta\n"
            "/metas editar [id] [campo] [valor] - Editar uma meta\n"
            "/metas remover [id] - Remover uma meta\n"
            "/meta [nome] [valor] - Adicionar valor a uma meta\n\n"
            "📝 *Campos para edição:*\n"
            "• nome - Nome da meta\n"
            "• valor - Valor da meta\n"
            "• data - Data limite (DD/MM/AAAA)\n"
            "• descricao - Descrição da meta\n\n"
            "💡 *Exemplos:*\n"
            "• /metas criar Viagem 5000 31/12/2024\n"
            "• /metas editar 1 nome Nova Viagem\n"
            "• /metas editar 1 valor 6000\n"
            "• /metas editar 1 data 31/12/2024\n"
            "• /metas remover 1\n"
            "• /meta Viagem 1000",
            parse_mode='Markdown'
        )
        
    elif query.data == "ajuda_resumos":
        await query.edit_message_text(
            "*📊 Ajuda: Resumos Financeiros*\n\n"
            "📝 *Comandos disponíveis:*\n"
            "/resumo - Ver resumo básico\n"
            "/resumodetalhado - Ver análise completa\n\n"
            "💡 *O que você verá:*\n"
            "• Total de gastos e receitas\n"
            "• Distribuição por categoria\n"
            "• Percentuais e tendências\n"
            "• Gráficos e visualizações\n\n"
            "📅 *Dicas:*\n"
            "• Revise seu resumo semanalmente\n"
            "• Compare períodos diferentes\n"
            "• Identifique oportunidades de economia",
            parse_mode='Markdown'
        )
        
    elif query.data == "ajuda_config":
        await query.edit_message_text(
            "*⚙️ Ajuda: Configurações*\n\n"
            "📝 *Comandos disponíveis:*\n"
            "/salario - Ver ou alterar seu salário\n"
            "/categorias - Listar categorias\n"
            "/limpar - Limpar histórico\n\n"
            "💡 *Dicas:*\n"
            "• Mantenha seu salário atualizado\n"
            "• Organize suas categorias\n"
            "• Faça backup regularmente",
            parse_mode='Markdown'
        )
        
    elif query.data == "ajuda_outros":
        await query.edit_message_text(
            "*❓ Ajuda: Outros Tópicos*\n\n"
            "🤖 *IA Financeira:*\n"
            "• Pergunte sobre investimentos\n"
            "• Peça dicas de economia\n"
            "• Consulte sobre orçamento\n"
            "• Tire dúvidas financeiras\n\n"
            "💡 *Dicas Gerais:*\n"
            "• Use emojis para facilitar a leitura\n"
            "• Mantenha suas descrições claras\n"
            "• Revise seus dados regularmente\n"
            "• Defina metas realistas\n\n"
            "📱 *Suporte:*\n"
            "Use /ajuda para ver esta mensagem novamente",
            parse_mode='Markdown'
        )
        
    elif query.data == "acesso_ilimitado":
        # Cria botões para o menu de acesso ilimitado
        keyboard = [
            [
                InlineKeyboardButton("📱 Enviar Comprovante", callback_data="enviar_comprovante"),
                InlineKeyboardButton("❓ Dúvidas", callback_data="duvidas_pagamento")
            ],
            [
                InlineKeyboardButton("🔙 Voltar", callback_data="ajuda")
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            "*🎉 Acesso Ilimitado ao FinBot*\n\n"
            "💰 *Valor:* R$19,99 (apenas uma vez)\n\n"
            "✨ *Benefícios:*\n"
            "• Acesso vitalício ao bot\n"
            "• Todas as atualizações futuras\n"
            "• Suporte prioritário\n"
            "• Recursos exclusivos\n\n"
            "🔑 *Chave PIX:*\n"
            "`123.456.789-00`\n\n"
            "📝 *Após o pagamento:*\n"
            "1. Clique em 'Enviar Comprovante'\n"
            "2. Envie o comprovante de pagamento\n"
            "3. Aguarde a confirmação\n\n"
            "💡 *Dúvidas?* Clique no botão abaixo",
            parse_mode='Markdown',
            reply_markup=reply_markup
        )
        
    elif query.data == "enviar_comprovante":
        aguardando_comprovante.add(user_id)
        ultimo_estado_usuario[user_id] = 'aguardando_comprovante'
        await query.edit_message_text(
            "*📱 Envio de Comprovante*\n\n"
            "Por favor, envie o comprovante de pagamento PIX.\n\n"
            "⚠️ *Importante:*\n"
            "• Envie apenas imagens ou PDF\n"
            "• Aguarde nossa confirmação\n"
            "• O processamento pode levar até 24h\n\n"
            "🔙 Use /ajuda para voltar ao menu",
            parse_mode='Markdown'
        )
        return
        
    elif query.data == "duvidas_pagamento":
        await query.edit_message_text(
            "*❓ Dúvidas sobre Pagamento*\n\n"
            "📝 *Perguntas Frequentes:*\n\n"
            "1. *O pagamento é único?*\n"
            "Sim! Apenas R$19,99 e você terá acesso vitalício.\n\n"
            "2. *Quais as formas de pagamento?*\n"
            "Aceitamos apenas PIX no momento.\n\n"
            "3. *Como recebo o acesso?*\n"
            "Após confirmarmos seu pagamento, seu acesso será liberado automaticamente.\n\n"
            "4. *E as atualizações futuras?*\n"
            "Todas as atualizações serão gratuitas para você.\n\n"
            "5. *Posso transferir meu acesso?*\n"
            "Não, o acesso é pessoal e intransferível.\n\n"
            "🔙 Use /ajuda para voltar ao menu",
            parse_mode='Markdown'
        )

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Manipula mensagens de texto"""
    message = update.message.text
    user_id = update.effective_user.id
    nome = update.effective_user.first_name
    
    # Verifica se a mensagem contém um documento (comprovante)
    if (user_id in aguardando_comprovante or ultimo_estado_usuario.get(user_id) == 'aguardando_comprovante') and update.message.document:
        if update.message.document.mime_type == 'application/pdf':
            comprovantes_dir = os.path.join('data', 'comprovantes')
            if not os.path.exists(comprovantes_dir):
                os.makedirs(comprovantes_dir)
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            nome_limpo = ''.join(c for c in nome if c.isalnum() or c in (' ', '_')).replace(' ', '_')
            filename = f'comprovante_{user_id}_{nome_limpo}_{timestamp}.pdf'
            file_path = os.path.join(comprovantes_dir, filename)
            try:
                file = await context.bot.get_file(update.message.document.file_id)
                await file.download_to_drive(file_path)
                log_file = os.path.join(comprovantes_dir, 'comprovantes_log.txt')
                with open(log_file, 'a', encoding='utf-8') as f:
                    log_entry = f"{timestamp} - Usuário: {user_id} - Nome: {nome} - Arquivo: {filename}\n"
                    f.write(log_entry)
                    logger.info(f"Log atualizado: {log_entry}")
                aguardando_comprovante.discard(user_id)
                ultimo_estado_usuario[user_id] = None
                await update.message.reply_text(
                    "✅ Comprovante recebido e salvo!\n\n"
                    "📝 *Status:* Em análise\n"
                    "⏳ *Prazo:* Até 24 horas\n\n"
                    "🔔 Você receberá uma mensagem quando seu acesso for liberado.\n"
                    "Obrigado pela preferência! 😊",
                    parse_mode='Markdown'
                )
            except Exception as e:
                logger.error(f"Erro ao salvar comprovante: {str(e)}")
                await update.message.reply_text(
                    "❌ Desculpe, ocorreu um erro ao salvar seu comprovante.\n"
                    "Por favor, tente novamente ou entre em contato com o suporte.",
                    parse_mode='Markdown'
                )
            return
            
    # Obtém o gerenciador de gastos para o usuário
    gm = get_gastos_manager(user_id)
    validador = ValidadorEntrada()
    
    # Verifica se está aguardando salário
    if user_id in aguardando_salario:
        try:
            # Usa o validador para normalizar o valor
            sucesso, valor, mensagem = validador.normalizar_valor(message)
            
            if not sucesso:
                await update.message.reply_text(f"❌ {mensagem}. Por favor, digite um valor válido.")
                return
            
            # Define o salário
            if gm.definir_salario(float(valor)):
                aguardando_salario.remove(user_id)
                # Adiciona usuário à lista de espera por meta
                aguardando_meta[user_id] = {
                    'etapa': 'nome_meta',
                    'dados': {}
                }
                # Atualiza o resumo
                resumo_manager.atualizar_resumo(user_id, nome)
                await update.message.reply_text(
                    f"✅ Salário registrado com sucesso: R${valor:.2f}\n\n"
                    f"Agora vamos definir suas metas financeiras!\n\n"
                    "🎯 Qual é o nome da sua primeira meta? (exemplo: 'Viagem para a praia')"
                )
            else:
                await update.message.reply_text("❌ Erro ao registrar salário. Por favor, tente novamente.")
        except Exception as e:
            await update.message.reply_text("❌ Erro ao processar o salário. Por favor, tente novamente.")
        return
    
    # Verifica se está aguardando definição de meta
    if user_id in aguardando_meta:
        etapa = aguardando_meta[user_id]['etapa']
        dados = aguardando_meta[user_id]['dados']
        
        if etapa == 'nome_meta':
            dados['nome'] = message
            aguardando_meta[user_id]['etapa'] = 'valor_meta'
            await update.message.reply_text(
                f"Ótimo! Agora, qual é o valor que você quer juntar para '{message}'?\n"
                "Digite apenas o número (exemplo: 5000)"
            )
            return
            
        elif etapa == 'valor_meta':
            try:
                valor = float(message.replace(',', '.'))
                if valor <= 0:
                    await update.message.reply_text("❌ O valor deve ser maior que zero. Por favor, digite um valor válido.")
                    return
                    
                dados['valor'] = valor
                aguardando_meta[user_id]['etapa'] = 'data_limite'
                await update.message.reply_text(
                    "Ótimo! Agora, qual é a data limite para atingir esta meta?\n"
                    "Digite no formato DD/MM/AAAA (exemplo: 31/12/2024)\n"
                    "Ou digite 'sem data' se não quiser definir uma data limite."
                )
                return
                
            except ValueError:
                await update.message.reply_text("❌ Por favor, digite apenas números para o valor (exemplo: 5000)")
                return
                
        elif etapa == 'data_limite':
            if message.lower() == 'sem data':
                data_limite = None
            else:
                try:
                    # Verifica se a data está no formato correto
                    datetime.strptime(message, '%d/%m/%Y')
                    data_limite = message
                except ValueError:
                    await update.message.reply_text("❌ Data inválida. Use o formato DD/MM/AAAA (exemplo: 31/12/2024)")
                    return
            
            # Cria a meta
            if gm.definir_meta(dados['nome'], dados['valor'], data_limite):
                del aguardando_meta[user_id]
                # Atualiza o resumo
                resumo_manager.atualizar_resumo(user_id, nome)
                await update.message.reply_text(
                    f"✅ Meta '{dados['nome']}' criada com sucesso!\n\n"
                    f"💰 Valor: R${dados['valor']:.2f}\n"
                    f"📅 Data limite: {data_limite if data_limite else 'Não definida'}\n\n"
                    "💡 Para adicionar valores a esta meta, você pode:\n"
                    "• Usar o comando /metas atualizar\n"
                    "• Ou digitar 'Juntei X reais para a meta Y'\n\n"
                    "Utilize /ajuda para voltar ao menu."
                )
            else:
                await update.message.reply_text("❌ Erro ao criar meta. Tente novamente.")
            return
    
    # Verifica se está aguardando nome
    if user_id in aguardando_nome:
        # Define o nome do usuário
        if gm.definir_nome_usuario(message):
            aguardando_nome.remove(user_id)
            # Adiciona usuário à lista de espera por salário
            aguardando_salario.add(user_id)
            # Atualiza o resumo
            resumo_manager.atualizar_resumo(user_id, message)
            await update.message.reply_text(
                f"✅ Nome registrado com sucesso: {message}\n\n"
                f"Para podermos começar a organizar suas finanças, preciso saber seu salário mensal.\n\n"
                "💰 Por favor, digite seu salário (apenas números, por exemplo: 3000)"
            )
        else:
            await update.message.reply_text("❌ Erro ao registrar nome. Por favor, tente novamente.")
        return
    
    # Primeiro tenta processar como contribuição para meta
    sucesso, resposta = gm.processar_mensagem_meta(message)
    if sucesso:
        # Atualiza o resumo
        resumo_manager.atualizar_resumo(user_id, nome)
        await update.message.reply_text(resposta + "\n\nUtilize /ajuda para voltar ao menu.")
        return
    
    # Depois tenta processar como receita
    sucesso, resposta = gm.processar_mensagem_receita(message)
    if sucesso:
        # Atualiza o resumo
        resumo_manager.atualizar_resumo(user_id, nome)
        await update.message.reply_text(resposta + "\n\nUtilize /ajuda para voltar ao menu.")
        return
    
    # Depois tenta processar como gasto
    sucesso, resposta = gm.processar_mensagem_gasto(message)
    if sucesso:
        # Atualiza o resumo
        resumo_manager.atualizar_resumo(user_id, nome)
        await update.message.reply_text(resposta + "\n\nUtilize /ajuda para voltar ao menu.")
        return
    
    # Se não for nenhum dos casos acima, envia para a IA
    resposta = await processar_comando_ia(message, user_id, nome)
    await update.message.reply_text(resposta + "\n\nUtilize /ajuda para voltar ao menu.")

def main():
    """Inicia o bot"""
    # Criar a aplicação
    application = Application.builder().token(TELEGRAM_TOKEN).build()

    # Adicionar handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("ajuda", ajuda))
    application.add_handler(CommandHandler("salario", salario))
    application.add_handler(CommandHandler("resumo", resumo))
    application.add_handler(CommandHandler("resumodetalhado", resumo_detalhado))
    application.add_handler(CommandHandler("categorias", categorias))
    application.add_handler(CommandHandler("metas", metas))
    application.add_handler(CommandHandler("meta", meta))
    application.add_handler(CommandHandler("limpar", limpar))
    
    # Adicionar handler para botões inline
    application.add_handler(CallbackQueryHandler(button_callback))
    
    # Adicionar handler para mensagens de texto
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    # Iniciar o bot com retentativas
    max_retries = 3
    retry_delay = 5  # segundos
    
    for attempt in range(max_retries):
        try:
            print(f"🤖 Tentando iniciar o bot (tentativa {attempt + 1}/{max_retries})...")
            application.run_polling()
            break
        except telegram.error.TimedOut:
            if attempt < max_retries - 1:
                print(f"❌ Timeout na conexão. Tentando novamente em {retry_delay} segundos...")
                time.sleep(retry_delay)
            else:
                print("❌ Falha ao conectar após várias tentativas. Verifique sua conexão com a internet.")
        except Exception as e:
            print(f"❌ Erro ao iniciar o bot: {str(e)}")
            if attempt < max_retries - 1:
                print(f"Tentando novamente em {retry_delay} segundos...")
                time.sleep(retry_delay)
            else:
                print("❌ Falha ao iniciar o bot após várias tentativas.")
            break

if __name__ == '__main__':
    main() 