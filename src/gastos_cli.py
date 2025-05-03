from gastos_manager import GastosManager
from validadores import ValidadorEntrada

def main():
    gm = GastosManager()
    validador = ValidadorEntrada()
    
    try:
        while True:
            comando = input("\nDigite um comando ou um gasto (ex: gastei 50 reais com almoço): ").strip()
            
            if comando.lower() in ['sair', 'exit', 'quit']:
                print("Até logo! 👋")
                break
                
            elif comando.lower() in ['ajuda', 'help', '?']:
                print("\nComandos disponíveis:")
                print("- resumo: ver resumo dos gastos")
                print("- categorias: listar todas as categorias")
                print("- limpar: limpar histórico de gastos")
                print("- sair: encerrar o programa")
                print("\nPara registrar um gasto, use:")
                print("- gastei X reais com Y")
                print("- paguei X em Y")
                print("- comprei X por Y")
                print("\nExemplos:")
                print("- gastei 50 reais com almoço")
                print("- paguei 150 de conta de luz")
                print("- comprei 30 de mercado")
                
            elif comando.lower() == 'resumo':
                resumo = gm.get_resumo()
                print("\n📊 Resumo de Gastos:")
                for categoria, valor, percentual in resumo:
                    print(f"- {categoria}: R${valor:.2f} ({percentual:.1f}%)")
                    
            elif comando.lower() == 'categorias':
                categorias = gm.get_categorias()
                print("\n📋 Categorias Disponíveis:")
                for i, categoria in enumerate(categorias, 1):
                    print(f"{i}. {categoria}")
                    
            elif comando.lower() == 'limpar':
                confirmacao = input("\nTem certeza que deseja limpar todo o histórico de gastos? (s/n): ")
                if confirmacao.lower() == 's':
                    if gm.limpar_historico():
                        print("✅ Histórico de gastos limpo com sucesso!")
                    else:
                        print("❌ Erro ao limpar histórico de gastos.")
                else:
                    print("Operação cancelada.")
                    
            else:
                sucesso, resposta = gm.processar_mensagem_gasto(comando)
                print(resposta)
            
    finally:
        gm.close()

if __name__ == "__main__":
    main() 