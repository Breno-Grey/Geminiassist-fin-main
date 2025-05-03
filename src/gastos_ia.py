from gastos_manager import GastosManager
import google.generativeai as genai
import os
from dotenv import load_dotenv

# Carregar variáveis de ambiente
load_dotenv()

# Configurar a API do Gemini
GOOGLE_API_KEY = "AIzaSyAyQyCQPAkR5yjGkLgz-hOWqzpH-WALRVY"
genai.configure(api_key=GOOGLE_API_KEY)

# Configurar o modelo
model = genai.GenerativeModel('gemini-1.5-pro')

def processar_comando_ia(mensagem):
    """Processa a mensagem usando a IA do Gemini"""
    try:
        # Contexto para a IA
        contexto = """
        Você é o FinBot, um assistente financeiro, inteligente e confiável. Seu objetivo é ajudar pessoas a organizarem suas finanças pessoais de maneira prática, clara e personalizada.

Você entende sobre controle de gastos, investimentos, orçamentos, economia doméstica, metas financeiras e dicas de educação financeira.

Ao conversar, seja sempre educado, positivo e motivador. Fale de forma simples e objetiva, adaptando sua linguagem conforme o nível de conhecimento da pessoa (iniciante, intermediário ou avançado).

Seu papel é:

Registrar e organizar despesas e receitas.

Ajudar a planejar orçamentos e controlar dívidas.

Sugerir melhorias e boas práticas financeiras.

Motivar o usuário a atingir suas metas financeiras.

Responder dúvidas financeiras de maneira precisa e fácil de entender.

Além de tudo você é: um assistente inteligente que ajuda os usuários a gerenciar seus gastos. O sistema possui um banco de dados que armazena categorias e registros de despesas. Seu papel é interpretar mensagens dos usuários como "Gastei 50 reais com mercado" e registrar isso automaticamente, associando o valor à categoria correta (como "Alimentação").
Você entende linguagem natural e reconhece variações como "paguei", "foi", "custou", "comprei", entre outras, mesmo que o valor venha antes ou depois da descrição.
Você é capaz de:

Registrar gastos com base nas mensagens dos usuários, identificando o valor, a descrição e sugerindo a categoria correta automaticamente com base em palavras-chave.

Listar os gastos por data ou categoria.

Gerar resumos que mostram quanto foi gasto por categoria e o total no período.

Listar as categorias disponíveis para os usuários.

Limpar todo o histórico de gastos, mantendo apenas as categorias padrão.

Manter uma base de dados organizada, salvando os dados localmente com segurança.

Seu objetivo é interagir de forma natural com os usuários, permitindo que eles controlem suas finanças apenas enviando mensagens. Ao responder, seja claro, amigável e motivador. Nunca mencione que isso é feito por meio de código Python ou banco de dados SQLite — apenas aja como um assistente que entende e executa.

Não envie respostas Muito longas, seja objetivo, mas também não seja muito curto.
        """
        
        # Combinar contexto com a mensagem do usuário
        prompt = f"{contexto}\n\nUsuário: {mensagem}"
        
        # Gerar resposta
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        return f"Desculpe, ocorreu um erro ao processar sua mensagem: {str(e)}"

def main():
    gm = GastosManager()
    
    try:
        print("\nBem-vindo ao Gerenciador de Gastos com IA!")
        print("Digite seus gastos no formato 'gastei X reais com Y'")
        print("Comandos disponíveis:")
        print("- 'resumo': ver resumo dos gastos")
        print("- 'categorias': listar todas as categorias")
        print("- 'limpar': limpar histórico")
        print("- 'sair': encerrar o programa")
        print("- 'ajuda': mostrar esta mensagem novamente")
        print("\nPara outras perguntas, a IA responderá sobre finanças pessoais.")
        
        while True:
            comando = input("\n> ").strip().lower()
            
            if comando == 'sair':
                print("Até logo!")
                break
                
            elif comando == 'ajuda':
                print("\nComo usar:")
                print("- Digite seus gastos normalmente: 'gastei 50 reais com almoço'")
                print("- 'resumo': ver resumo dos gastos")
                print("- 'categorias': listar todas as categorias disponíveis")
                print("- 'limpar': limpar histórico")
                print("- 'sair': encerrar o programa")
                print("- 'ajuda': mostrar esta mensagem")
                print("\nPara outras perguntas, a IA responderá sobre finanças pessoais.")
                
            elif comando == 'resumo':
                resumo, total = gm.get_resumo()
                print(f"\nTotal gasto: R${total:.2f}")
                print("\nResumo por categoria:")
                for categoria, valor, percentual in resumo:
                    print(f"{categoria}: R${valor:.2f} ({percentual:.1f}%)")
                    
            elif comando == 'categorias':
                categorias = gm.get_categorias()
                print("\nCategorias disponíveis:")
                for i, categoria in enumerate(categorias, 1):
                    print(f"{i}. {categoria}")
                    
            elif comando == 'limpar':
                confirmacao = input("\nTem certeza que deseja limpar todo o histórico de gastos? (s/n): ")
                if confirmacao.lower() == 's':
                    if gm.limpar_historico():
                        print("Histórico de gastos limpo com sucesso!")
                    else:
                        print("Erro ao limpar histórico de gastos.")
                else:
                    print("Operação cancelada.")
                    
            else:
                # Primeiro tenta processar como gasto
                sucesso, resposta = gm.processar_mensagem_gasto(comando)
                if sucesso:
                    print(resposta)
                else:
                    # Se não for um gasto, usa a IA
                    resposta_ia = processar_comando_ia(comando)
                    print("\nResposta da IA:")
                    print(resposta_ia)
            
    finally:
        gm.close()

if __name__ == '__main__':
    main() 