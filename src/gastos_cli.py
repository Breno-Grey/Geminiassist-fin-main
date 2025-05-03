from gastos_manager import GastosManager
import sys

def main():
    gm = GastosManager()
    
    try:
        print("\nBem-vindo ao Gerenciador de Gastos!")
        print("Digite seus gastos no formato 'gastei X reais com Y'")
        print("Comandos disponíveis:")
        print("- 'resumo': ver resumo dos gastos")
        print("- 'categorias': listar todas as categorias")
        print("- 'limpar': limpar histórico")
        print("- 'sair': encerrar o programa")
        print("- 'ajuda': mostrar esta mensagem novamente")
        
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
                sucesso, resposta = gm.processar_mensagem_gasto(comando)
                print(resposta)
            
    finally:
        gm.close()

if __name__ == '__main__':
    main() 