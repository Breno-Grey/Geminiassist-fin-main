import os
from datetime import datetime
from gastos_manager import GastosManager

class ResumoManager:
    def __init__(self):
        self.pasta_data = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data')
        self.arquivo_resumo = os.path.join(self.pasta_data, 'resumo_usuarios.txt')
        
        # Garante que a pasta data existe
        if not os.path.exists(self.pasta_data):
            os.makedirs(self.pasta_data)
    
    def atualizar_resumo(self, user_id: int, nome_usuario: str):
        """Atualiza o resumo do usuário no arquivo"""
        try:
            # Obtém o gerenciador de gastos do usuário
            gm = GastosManager(f'data/gastos_{user_id}.db')
            
            # Obtém os dados do usuário
            salario = gm.get_salario()
            resumo_gastos, total_gastos, _ = gm.get_resumo()
            resumo_receitas, total_receitas = gm.get_resumo_receitas()
            metas = gm.get_metas()
            
            # Prepara o texto do resumo
            texto_resumo = f"\n{'='*50}\n"
            texto_resumo += f"Resumo de {nome_usuario} (ID: {user_id})\n"
            texto_resumo += f"Atualizado em: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}\n"
            texto_resumo += f"{'='*50}\n\n"
            
            # Adiciona salário
            if salario:
                texto_resumo += f"💰 Salário: R${salario:.2f}\n\n"
            
            # Adiciona gastos
            if total_gastos > 0:
                texto_resumo += "📊 Gastos:\n"
                for categoria, valor, percentual in resumo_gastos:
                    texto_resumo += f"• {categoria}: R${valor:.2f} ({percentual:.1f}%)\n"
                texto_resumo += f"💵 Total: R${total_gastos:.2f}\n\n"
            
            # Adiciona receitas
            if total_receitas > 0:
                texto_resumo += "💵 Receitas:\n"
                for categoria, valor, percentual in resumo_receitas:
                    texto_resumo += f"• {categoria}: R${valor:.2f} ({percentual:.1f}%)\n"
                texto_resumo += f"💰 Total: R${total_receitas:.2f}\n\n"
            
            # Adiciona metas
            if metas:
                texto_resumo += "🎯 Metas Financeiras:\n"
                for meta in metas:
                    id_meta, nome_meta, valor_meta, valor_atual, data_limite, descricao, status = meta
                    percentual = (valor_atual / valor_meta) * 100 if valor_meta > 0 else 0
                    emoji = "✅" if status == "concluída" else "⏳" if status == "ativa" else "❌"
                    texto_resumo += f"{emoji} {nome_meta}: R${valor_atual:.2f} / R${valor_meta:.2f} ({percentual:.1f}%)\n"
                    if data_limite:
                        texto_resumo += f"   📅 Data limite: {data_limite}\n"
                texto_resumo += "\n"
            
            # Lê o arquivo atual
            resumos = {}
            if os.path.exists(self.arquivo_resumo):
                with open(self.arquivo_resumo, 'r', encoding='utf-8') as f:
                    conteudo = f.read()
                    # Divide o conteúdo em resumos individuais
                    resumos_atuais = conteudo.split('='*50)
                    for resumo in resumos_atuais:
                        if resumo.strip():
                            # Extrai o ID do usuário do resumo
                            linhas = resumo.strip().split('\n')
                            for linha in linhas:
                                if 'ID:' in linha:
                                    id_atual = int(linha.split('ID:')[1].strip().split(')')[0])
                                    resumos[id_atual] = resumo
                                    break
            
            # Atualiza ou adiciona o resumo do usuário
            resumos[user_id] = texto_resumo
            
            # Escreve todos os resumos de volta no arquivo
            with open(self.arquivo_resumo, 'w', encoding='utf-8') as f:
                for resumo in resumos.values():
                    f.write(resumo)
            
            return True
        except Exception as e:
            print(f"Erro ao atualizar resumo: {str(e)}")
            return False 