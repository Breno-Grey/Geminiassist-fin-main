import sqlite3
from datetime import datetime, timedelta
import logging
from collections import defaultdict
import re
import os
import matplotlib.pyplot as plt
from io import BytesIO

# Configuração do logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

class GastosManager:
    def __init__(self, db_name='gastos.db'):
        self.db_name = db_name
        self.conn = sqlite3.connect(db_name)
        self.cursor = self.conn.cursor()
        self.criar_tabelas()
        self.logger = self.configurar_logger()

    def criar_tabelas(self):
        """Cria as tabelas necessárias no banco de dados"""
        # Tabela de gastos
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS gastos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                valor REAL NOT NULL,
                categoria TEXT NOT NULL,
                descricao TEXT,
                data TEXT NOT NULL
            )
        ''')
        
        # Tabela de receitas
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS receitas (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                valor REAL NOT NULL,
                categoria TEXT NOT NULL,
                descricao TEXT,
                data TEXT NOT NULL
            )
        ''')
        
        # Tabela de configurações
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS configuracoes (
                chave TEXT PRIMARY KEY,
                valor TEXT NOT NULL
            )
        ''')
        
        # Tabela de metas
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS metas (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nome TEXT NOT NULL,
                valor_meta REAL NOT NULL,
                valor_atual REAL DEFAULT 0,
                data_limite TEXT,
                descricao TEXT,
                status TEXT DEFAULT 'ativa'
            )
        ''')
        
        self.conn.commit()

    def configurar_logger(self):
        return logger

    def _processar_data(self, texto_data):
        """Processa texto contendo referências de data"""
        hoje = datetime.now()
        texto_data = texto_data.lower().strip()
        
        # Mapeamento de datas relativas
        datas_relativas = {
            'ontem': hoje - timedelta(days=1),
            'hoje': hoje,
            'amanhã': hoje + timedelta(days=1),
            'anteontem': hoje - timedelta(days=2),
            'semana passada': hoje - timedelta(weeks=1),
            'mês passado': hoje - timedelta(days=30),
            'ano passado': hoje - timedelta(days=365)
        }
        
        # Verifica datas relativas
        for palavra, data in datas_relativas.items():
            if palavra in texto_data:
                return data.strftime('%Y-%m-%d %H:%M:%S')
        
        # Tenta identificar padrões de data
        padroes_data = [
            (r'(\d{1,2})/(\d{1,2})/(\d{4})', '%d/%m/%Y'),  # DD/MM/YYYY
            (r'(\d{1,2})/(\d{1,2})', '%d/%m'),  # DD/MM (assume ano atual)
            (r'(\d{1,2}) de (\w+)', '%d de %B'),  # DD de Mês
            (r'(\d{1,2}) de (\w+) de (\d{4})', '%d de %B de %Y')  # DD de Mês de YYYY
        ]
        
        for padrao, formato in padroes_data:
            match = re.search(padrao, texto_data)
            if match:
                try:
                    # Se o formato não inclui ano, usa o ano atual
                    if '%Y' not in formato:
                        data_str = match.group(0) + f" de {hoje.year}"
                        formato = formato + " de %Y"
                    else:
                        data_str = match.group(0)
                    
                    # Converte mês por extenso para número
                    meses = {
                        'janeiro': '01', 'fevereiro': '02', 'março': '03', 'abril': '04',
                        'maio': '05', 'junho': '06', 'julho': '07', 'agosto': '08',
                        'setembro': '09', 'outubro': '10', 'novembro': '11', 'dezembro': '12'
                    }
                    
                    for mes_extenso, mes_numero in meses.items():
                        data_str = data_str.replace(mes_extenso, mes_numero)
                    
                    data = datetime.strptime(data_str, formato)
                    return data.strftime('%Y-%m-%d %H:%M:%S')
                except ValueError:
                    continue
        
        # Se não encontrar nenhuma data, usa a data atual
        return hoje.strftime('%Y-%m-%d %H:%M:%S')

    def limpar_historico(self):
        """
        Limpa todo o histórico de gastos, mantendo apenas as categorias padrão
        
        Returns:
            bool: True se o histórico foi limpo com sucesso, False caso contrário
        """
        try:
            # Remove todos os gastos
            self.cursor.execute('DELETE FROM gastos')
            
            # Remove todas as categorias exceto as padrão
            categorias_padrao = [
                'Alimentação', 'Transporte', 'Moradia', 'Lazer',
                'Saúde', 'Educação', 'Vestuário', 'Outros'
            ]
            
            self.cursor.execute('''
                DELETE FROM categorias 
                WHERE nome NOT IN ({})
            '''.format(','.join(['?'] * len(categorias_padrao))), categorias_padrao)
            
            self.conn.commit()
            self.logger.info("Histórico de gastos limpo com sucesso")
            return True
            
        except Exception as e:
            self.logger.error(f"Erro ao limpar histórico: {e}")
            return False

    def adicionar_gasto(self, valor, descricao, categoria_nome, data=None):
        """
        Adiciona um novo gasto
        
        Args:
            valor: Valor do gasto
            descricao: Descrição do gasto
            categoria_nome: Nome da categoria
            data: Data do gasto (opcional)
        """
        try:
            # Obtém ou cria a categoria
            self.cursor.execute(
                'INSERT OR IGNORE INTO categorias (nome) VALUES (?)',
                (categoria_nome,)
            )
            self.cursor.execute(
                'SELECT id FROM categorias WHERE nome = ?',
                (categoria_nome,)
            )
            categoria_id = self.cursor.fetchone()[0]

            # Se não houver data especificada, usa a data atual
            if data is None:
                data = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

            # Insere o gasto
            self.cursor.execute('''
                INSERT INTO gastos 
                (valor, descricao, categoria_id, data)
                VALUES (?, ?, ?, ?)
            ''', (
                valor,
                descricao,
                categoria_id,
                data
            ))

            self.conn.commit()
            self.logger.info(f"Gasto adicionado: {descricao} - R${valor} em {data}")
            return True

        except Exception as e:
            self.logger.error(f"Erro ao adicionar gasto: {e}")
            return False

    def get_gastos(self, data_inicio=None, data_fim=None, categoria=None):
        """
        Obtém gastos com filtros opcionais
        
        Args:
            data_inicio: Data inicial (opcional)
            data_fim: Data final (opcional)
            categoria: Nome da categoria (opcional)
        """
        try:
            query = '''
                SELECT g.valor, g.descricao, c.nome as categoria, g.data
                FROM gastos g
                JOIN categorias c ON g.categoria_id = c.id
                WHERE 1=1
            '''
            params = []

            if data_inicio:
                query += ' AND g.data >= ?'
                params.append(data_inicio)
            if data_fim:
                query += ' AND g.data <= ?'
                params.append(data_fim)
            if categoria:
                query += ' AND c.nome = ?'
                params.append(categoria)

            query += ' ORDER BY g.data DESC'
            
            self.cursor.execute(query, params)
            return self.cursor.fetchall()

        except Exception as e:
            self.logger.error(f"Erro ao obter gastos: {e}")
            return []

    def get_resumo(self, data_inicio=None, data_fim=None):
        """
        Gera um resumo dos gastos por categoria
        
        Args:
            data_inicio: Data inicial (opcional)
            data_fim: Data final (opcional)
        """
        try:
            gastos = self.get_gastos(data_inicio, data_fim)
            
            # Agrupa gastos por categoria
            gastos_por_categoria = defaultdict(float)
            total_gastos = 0
            
            for valor, _, categoria, _ in gastos:
                gastos_por_categoria[categoria] += valor
                total_gastos += valor
            
            # Calcula percentuais
            resumo = []
            for categoria, valor in gastos_por_categoria.items():
                percentual = (valor / total_gastos) * 100 if total_gastos > 0 else 0
                resumo.append((categoria, valor, percentual))
            
            # Ordena por valor (maior para menor)
            resumo.sort(key=lambda x: x[1], reverse=True)
            
            # Obtém o salário
            salario = self.get_salario()
            
            # Obtém o resumo de receitas
            resumo_receitas, total_receitas = self.get_resumo_receitas(data_inicio, data_fim)
            
            # Obtém as metas
            metas = self.get_metas()
            
            # Prepara o texto do resumo
            resumo_texto = "📊 Resumo Financeiro\n\n"
            
            # Seção de Renda
            resumo_texto += "💰 Renda:\n"
            if salario:
                resumo_texto += f"• Salário: R${salario:.2f}\n"
            resumo_texto += f"• Outras receitas: R${total_receitas:.2f}\n"
            if salario:
                resumo_texto += f"• Renda total: R${salario + total_receitas:.2f}\n"
            resumo_texto += "\n"
            
            # Seção de Gastos
            resumo_texto += "💵 Gastos:\n"
            for categoria, valor, percentual in resumo:
                resumo_texto += f"• {categoria}: R${valor:.2f} ({percentual:.1f}%)\n"
            resumo_texto += f"• Total gasto: R${total_gastos:.2f}\n"
            if salario:
                percentual_salario = (total_gastos / salario) * 100 if salario > 0 else 0
                resumo_texto += f"• {percentual_salario:.1f}% do salário\n"
            resumo_texto += "\n"
            
            # Seção de Saldo
            resumo_texto += "📈 Saldo:\n"
            if salario:
                saldo = (salario + total_receitas) - total_gastos
                resumo_texto += f"• Saldo mensal: R${saldo:.2f}\n"
                if saldo > 0:
                    resumo_texto += f"• Você economizou {saldo/salario*100:.1f}% do seu salário\n"
                else:
                    resumo_texto += "• Você gastou mais do que recebeu este mês\n"
            else:
                resumo_texto += f"• Saldo: R${total_receitas - total_gastos:.2f}\n"
            resumo_texto += "\n"
            
            # Seção de Metas
            if metas:
                metas_ativas = [m for m in metas if m[6] == "ativa"]
                if metas_ativas:
                    resumo_texto += "🎯 Metas em Andamento:\n"
                    for meta in metas_ativas:
                        id_meta, nome, valor_meta, valor_atual, data_limite, descricao, status = meta
                        percentual = (valor_atual / valor_meta) * 100 if valor_meta > 0 else 0
                        resumo_texto += f"• {nome}: R${valor_atual:.2f} / R${valor_meta:.2f} ({percentual:.1f}%)\n"
            
            return resumo, total_gastos, resumo_texto
            
        except Exception as e:
            self.logger.error(f"Erro ao gerar resumo: {e}")
            return [], 0, "Erro ao gerar resumo"

    def get_categorias(self):
        """Retorna todas as categorias disponíveis"""
        try:
            self.cursor.execute('SELECT nome FROM categorias ORDER BY nome')
            return [row[0] for row in self.cursor.fetchall()]
        except Exception as e:
            self.logger.error(f"Erro ao obter categorias: {e}")
            return []

    def close(self):
        """Fecha a conexão com o banco de dados"""
        if self.conn:
            self.conn.close()
            self.logger.info("Conexão com o banco de dados fechada")

    def processar_mensagem_gasto(self, mensagem):
        """
        Processa uma mensagem de texto no formato "Gastei X reais com Y" e suas variações
        
        Args:
            mensagem: String contendo a mensagem do gasto
            
        Returns:
            tuple: (sucesso, resposta)
            - sucesso: bool indicando se o gasto foi registrado
            - resposta: string com mensagem de sucesso ou erro
        """
        try:
            # Padrões de regex para diferentes formatos
            padroes = [
                r'gastei\s+(\d+[.,]?\d*)\s+reais?\s+(?:com|em|para|no|na)\s+(.+?)(?:\s+(?:em|no|na|dia|dias|semana|mês|ano|ontem|hoje|amanhã|anteontem|semana passada|mês passado|ano passado|\d{1,2}/\d{1,2}(?:/\d{4})?|\d{1,2} de \w+(?: de \d{4})?))?$',
                r'gastei\s+(\d+[.,]?\d*)\s+(?:com|em|para|no|na)\s+(.+?)(?:\s+(?:em|no|na|dia|dias|semana|mês|ano|ontem|hoje|amanhã|anteontem|semana passada|mês passado|ano passado|\d{1,2}/\d{1,2}(?:/\d{4})?|\d{1,2} de \w+(?: de \d{4})?))?$',
                r'gastei\s+R?\$?\s*(\d+[.,]?\d*)\s+(?:com|em|para|no|na)\s+(.+?)(?:\s+(?:em|no|na|dia|dias|semana|mês|ano|ontem|hoje|amanhã|anteontem|semana passada|mês passado|ano passado|\d{1,2}/\d{1,2}(?:/\d{4})?|\d{1,2} de \w+(?: de \d{4})?))?$',
                r'gastei\s+R?\$?\s*(\d+[.,]?\d*)\s+reais?\s+(?:com|em|para|no|na)\s+(.+?)(?:\s+(?:em|no|na|dia|dias|semana|mês|ano|ontem|hoje|amanhã|anteontem|semana passada|mês passado|ano passado|\d{1,2}/\d{1,2}(?:/\d{4})?|\d{1,2} de \w+(?: de \d{4})?))?$',
                r'paguei\s+R?\$?\s*(\d+[.,]?\d*)\s+(?:em|com|para|no|na)\s+(.+?)(?:\s+(?:em|no|na|dia|dias|semana|mês|ano|ontem|hoje|amanhã|anteontem|semana passada|mês passado|ano passado|\d{1,2}/\d{1,2}(?:/\d{4})?|\d{1,2} de \w+(?: de \d{4})?))?$',
                r'foi\s+R?\$?\s*(\d+[.,]?\d*)\s+(?:em|com|para|no|na)\s+(.+?)(?:\s+(?:em|no|na|dia|dias|semana|mês|ano|ontem|hoje|amanhã|anteontem|semana passada|mês passado|ano passado|\d{1,2}/\d{1,2}(?:/\d{4})?|\d{1,2} de \w+(?: de \d{4})?))?$',
                r'custou\s+R?\$?\s*(\d+[.,]?\d*)\s+(?:em|com|para|no|na)\s+(.+?)(?:\s+(?:em|no|na|dia|dias|semana|mês|ano|ontem|hoje|amanhã|anteontem|semana passada|mês passado|ano passado|\d{1,2}/\d{1,2}(?:/\d{4})?|\d{1,2} de \w+(?: de \d{4})?))?$',
                r'desembolsei\s+R?\$?\s*(\d+[.,]?\d*)\s+(?:em|com|para|no|na)\s+(.+?)(?:\s+(?:em|no|na|dia|dias|semana|mês|ano|ontem|hoje|amanhã|anteontem|semana passada|mês passado|ano passado|\d{1,2}/\d{1,2}(?:/\d{4})?|\d{1,2} de \w+(?: de \d{4})?))?$'
            ]
            
            mensagem = mensagem.lower().strip()
            
            for padrao in padroes:
                match = re.search(padrao, mensagem)
                if match:
                    valor_str = match.group(1).replace(',', '.')
                    descricao = match.group(2).strip()
                    
                    # Extrai a parte da data se existir
                    data_part = None
                    if len(match.groups()) > 2 and match.group(3):
                        data_part = match.group(3).strip()
                    
                    try:
                        valor = float(valor_str)
                        if valor <= 0:
                            return False, "O valor do gasto deve ser maior que zero."
                        
                        # Tenta determinar a categoria automaticamente
                        categoria = self._determinar_categoria(descricao)
                        
                        # Processa a data se existir
                        data = None
                        if data_part:
                            data = self._processar_data(data_part)
                        
                        # Adiciona o gasto
                        if self.adicionar_gasto(valor, descricao, categoria, data):
                            data_str = f" em {data_part}" if data_part else ""
                            return True, f"Gasto registrado: R${valor:.2f} com {descricao}{data_str} (categoria: {categoria})"
                        else:
                            return False, "Erro ao registrar o gasto."
                            
                    except ValueError:
                        return False, "Valor inválido. Use números para o valor do gasto."
            
            return False, "Formato inválido. Use: 'Gastei X reais com Y' ou variações similares."
            
        except Exception as e:
            self.logger.error(f"Erro ao processar mensagem: {e}")
            return False, "Erro ao processar a mensagem."

    def _determinar_categoria(self, descricao):
        """
        Tenta determinar a categoria automaticamente baseado na descrição
        
        Args:
            descricao: String com a descrição do gasto
            
        Returns:
            string: Nome da categoria determinada
        """
        descricao = descricao.lower()
        
        # Mapeamento de palavras-chave para categorias
        mapeamento = {
    'alimentação': [
        'mercado', 'alimentação', 'supermercado', 'hipermercado', 'padaria', 'açougue', 'sacolão', 'feira', 'hortifruti',
        'restaurante', 'lanchonete', 'bar', 'cafeteria', 'delivery', 'ifood', 'ubereats', 'rappi',
        'comida', 'almoço', 'jantar', 'café', 'chá', 'lanche', 'refeição', 'marmita', 'quentinha',
        'self-service', 'buffet', 'fast food', 'mc donalds', 'burguer king', 'pizza', 'pizzaria',
        'hamburguer', 'hamburgueria', 'pastel', 'pastelaria', 'sushi', 'temaki', 'japonês',
        'churrasco', 'espetinho', 'cerveja', 'refrigerante', 'suco', 'água', 'sorvete', 'doceria',
        'sobremesa', 'confeitaria', 'snack', 'petisco', 'bolo', 'biscoito', 'bala', 'chocolate'
    ],
    'transporte': [
        'uber', '99', 'transporte', 'táxi', 'corrida', 'app transporte', 'ônibus', 'metrô', 'trem', 'bilhete único',
        'passagem', 'transporte público', 'van', 'fretado', 'combustível', 'gasolina', 'etanol',
        'álcool', 'diesel', 'posto', 'abastecimento', 'estacionamento', 'zona azul', 'pedágio',
        'ipva', 'licenciamento', 'guincho', 'oficina', 'auto center', 'lava rápido', 'rodízio',
        'multas', 'seguro veicular', 'financiamento carro', 'carro', 'moto', 'bicicleta', 'bike',
        'patinete', 'bicicletário', 'translado', 'aluguel de carro', 'locadora', 'manutenção carro'
    ],
    'moradia': [
        'aluguel','moradia' , 'condomínio', 'prestação', 'parcela casa', 'luz', 'energia', 'eletricidade', 'água',
        'internet', 'wi-fi', 'telefone', 'celular fixo', 'gás', 'ipt', 'iptu', 'manutenção', 'reparo',
        'obra', 'serviço doméstico', 'faxina', 'limpeza', 'zelador', 'porteiro', 'portaria',
        'móveis', 'mobília', 'eletrodoméstico', 'geladeira', 'fogão', 'máquina de lavar',
        'armário', 'sofá', 'decoração', 'cortina', 'tapete', 'iluminação', 'seguro residencial',
        'construção', 'materiais de construção', 'imobiliária', 'financiamento'
    ],
    'lazer': [
        'cinema','lazer' , 'teatro', 'show', 'festival', 'evento', 'festa', 'balada', 'barzinho', 'karaokê',
        'parque', 'passeio', 'viagem', 'hotel', 'pousada', 'airbnb', 'resort', 'ingresso', 'excursão',
        'turismo', 'hobby', 'jogo', 'games', 'videogame', 'playstation', 'xbox', 'nintendo',
        'livro', 'revista', 'leitura', 'quadrinhos', 'música', 'spotify', 'streaming',
        'netflix', 'prime video', 'hbo max', 'globo play', 'disney+', 'youtube premium', 'podcast',
        'assinatura lazer', 'diversão', 'entretenimento'
    ],
    'saúde': [
        'médico', 'saúde', 'consulta', 'especialista', 'exame', 'checkup', 'ultrassom', 'raio-x', 'tomografia',
        'psicólogo', 'terapeuta', 'terapia', 'psi', 'nutricionista', 'personal trainer', 'academia',
        'farmácia', 'remédio', 'medicamento', 'genérico', 'plano de saúde', 'convênio médico',
        'coparticipação', 'dentista', 'ortodontia', 'limpeza dental', 'hospital', 'clínica',
        'pronto socorro', 'vacina', 'injeção', 'teste', 'óculos', 'ótica', 'colírio',
        'fisioterapia', 'pilates', 'massagem', 'quiropraxia', 'acupuntura', 'cirurgia'
    ],
    'educação': [
        'curso', 'educação', 'cursos', 'curso online', 'ead', 'faculdade', 'mensalidade', 'matrícula', 'inscrição',
        'pós-graduação', 'mestrado', 'doutorado', 'universidade', 'colégio', 'escola', 'creche',
        'livro', 'apostila', 'material escolar', 'papelaria', 'caneta', 'caderno', 'mochila',
        'plataforma de ensino', 'ensino à distância', 'alura', 'udemy', 'hotmart', 'rocketseat',
        'idioma', 'inglês', 'espanhol', 'francês', 'aula particular', 'professor', 'reforço', 'ensino'
    ],
    'vestuário': [
        'roupa','vestuário', 'camisa', 'camiseta', 'blusa', 'calça', 'shorts', 'bermuda', 'vestido', 'saia',
        'casaco', 'jaqueta', 'moletom', 'roupa íntima', 'cueca', 'calcinha', 'sutiã', 'pijama',
        'roupa de cama', 'toalha', 'chinelo', 'sapato', 'tênis', 'sandália', 'bota', 'meia',
        'boné', 'óculos', 'óculos de sol', 'relógio', 'bolsa', 'mochila', 'cinto', 'acessório',
        'joia', 'bijuteria', 'loja de roupa', 'shopping', 'outlet', 'moda', 'estilo', 'roupa fitness'
    ]
}
        
        # Verifica se alguma palavra-chave está presente na descrição
        for categoria, palavras in mapeamento.items():
            if any(palavra in descricao for palavra in palavras):
                return categoria
                
        # Se não encontrar nenhuma correspondência, retorna 'Outros'
        return 'Outros'

    def definir_salario(self, valor):
        """
        Define o salário do usuário
        
        Args:
            valor: Valor do salário
        """
        try:
            self.cursor.execute('''
                INSERT OR REPLACE INTO configuracoes (chave, valor)
                VALUES ('salario', ?)
            ''', (str(valor),))
            
            self.conn.commit()
            self.logger.info(f"Salário definido: R${valor}")
            return True
            
        except Exception as e:
            self.logger.error(f"Erro ao definir salário: {e}")
            return False

    def get_salario(self):
        """
        Obtém o salário do usuário
        
        Returns:
            float: Valor do salário ou None se não definido
        """
        try:
            self.cursor.execute('''
                SELECT valor FROM configuracoes WHERE chave = 'salario'
            ''')
            resultado = self.cursor.fetchone()
            
            if resultado:
                return float(resultado[0])
            return None
            
        except Exception as e:
            self.logger.error(f"Erro ao obter salário: {e}")
            return None

    def get_resumo_detalhado(self, data_inicio=None, data_fim=None):
        """Gera um resumo detalhado dos gastos"""
        try:
            # Obtém o salário
            salario = self.get_salario()
            
            # Obtém o resumo de gastos
            resumo_gastos, total_gastos, _ = self.get_resumo(data_inicio, data_fim)
            
            # Obtém o resumo de receitas
            resumo_receitas, total_receitas = self.get_resumo_receitas(data_inicio, data_fim)
            
            # Obtém as metas
            metas = self.get_metas()
            
            # Prepara o texto do resumo
            resumo_texto = "📊 Análise Financeira Detalhada\n\n"
            
            # Seção de Renda
            resumo_texto += "💰 Renda Mensal:\n"
            if salario:
                resumo_texto += f"• Salário: R${salario:.2f}\n"
            else:
                resumo_texto += "• Salário: Não definido\n"
            resumo_texto += f"• Outras receitas: R${total_receitas:.2f}\n"
            if salario:
                resumo_texto += f"• Renda total: R${salario + total_receitas:.2f}\n"
            resumo_texto += "\n"
            
            # Seção de Gastos
            resumo_texto += "💵 Gastos por Categoria:\n"
            for categoria, valor, percentual in resumo_gastos:
                resumo_texto += f"• {categoria}: R${valor:.2f} ({percentual:.1f}%)\n"
            resumo_texto += f"• Total gasto: R${total_gastos:.2f}\n"
            if salario:
                percentual_salario = (total_gastos / salario) * 100 if salario > 0 else 0
                resumo_texto += f"• {percentual_salario:.1f}% do salário\n"
            resumo_texto += "\n"
            
            # Seção de Saldo
            resumo_texto += "📈 Saldo:\n"
            if salario:
                saldo = (salario + total_receitas) - total_gastos
                resumo_texto += f"• Saldo mensal: R${saldo:.2f}\n"
                if saldo > 0:
                    resumo_texto += f"• Você economizou {saldo/salario*100:.1f}% do seu salário\n"
                else:
                    resumo_texto += "• Você gastou mais do que recebeu este mês\n"
            else:
                resumo_texto += f"• Saldo: R${total_receitas - total_gastos:.2f}\n"
            resumo_texto += "\n"
            
            # Seção de Metas
            if metas:
                metas_ativas = [m for m in metas if m[6] == "ativa"]
                metas_concluidas = [m for m in metas if m[6] == "concluída"]
                
                if metas_ativas:
                    resumo_texto += "⏳ Metas em Andamento:\n"
                    for meta in metas_ativas:
                        id_meta, nome, valor_meta, valor_atual, data_limite, descricao, status = meta
                        percentual = (valor_atual / valor_meta) * 100 if valor_meta > 0 else 0
                        resumo_texto += f"• {nome}:\n"
                        resumo_texto += f"  💰 Meta: R${valor_meta:.2f}\n"
                        resumo_texto += f"  💵 Atual: R${valor_atual:.2f} ({percentual:.1f}%)\n"
                        if data_limite:
                            resumo_texto += f"  📅 Data limite: {data_limite}\n"
                        if descricao:
                            resumo_texto += f"  📝 {descricao}\n"
                        resumo_texto += "\n"
                
                if metas_concluidas:
                    resumo_texto += "✅ Metas Concluídas:\n"
                    for meta in metas_concluidas:
                        id_meta, nome, valor_meta, valor_atual, data_limite, descricao, status = meta
                        resumo_texto += f"• {nome}: R${valor_meta:.2f}\n"
                        if descricao:
                            resumo_texto += f"  📝 {descricao}\n"
                        resumo_texto += "\n"
            else:
                resumo_texto += "🎯 Você ainda não tem metas definidas.\n"
                resumo_texto += "Use /metas criar para definir suas metas financeiras.\n"
            
            # Gera o gráfico de pizza
            grafico_bytes = self.gerar_grafico(resumo_gastos)
            
            return resumo_texto, grafico_bytes
            
        except Exception as e:
            self.logger.error(f"Erro ao gerar resumo detalhado: {str(e)}")
            return "Erro ao gerar resumo detalhado", None

    def gerar_grafico(self, gastos):
        """Gera um gráfico de pizza com os gastos por categoria"""
        try:
            # Prepara os dados
            categorias = [gasto[0] for gasto in gastos]
            valores = [gasto[1] for gasto in gastos]
            percentuais = [gasto[2] for gasto in gastos]
            
            # Cria a figura e os eixos
            plt.figure(figsize=(10, 8))
            
            # Cria o gráfico de pizza
            patches, texts, autotexts = plt.pie(valores, labels=categorias, autopct='%1.1f%%',
                                              startangle=90, pctdistance=0.85,
                                              wedgeprops=dict(width=0.5))
            
            # Ajusta o estilo do texto
            plt.setp(autotexts, size=8, weight="bold")
            plt.setp(texts, size=8)
            
            # Adiciona título
            plt.title("Distribuição de Gastos por Categoria", pad=20)
            
            # Ajusta o layout
            plt.axis('equal')
            
            # Salva o gráfico em bytes
            buffer = BytesIO()
            plt.savefig(buffer, format='png', bbox_inches='tight', dpi=300)
            plt.close()
            buffer.seek(0)
            return buffer.getvalue()
            
        except Exception as e:
            self.logger.error(f"Erro ao gerar gráfico: {str(e)}")
            return None

    def adicionar_receita(self, valor, descricao, categoria="Outros", data=None):
        """
        Adiciona uma nova receita
        
        Args:
            valor: Valor da receita
            descricao: Descrição da receita
            categoria: Categoria da receita (opcional)
            data: Data da receita (opcional)
        """
        try:
            # Se não houver data especificada, usa a data atual
            if data is None:
                data = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

            # Insere a receita
            self.cursor.execute('''
                INSERT INTO receitas 
                (valor, descricao, categoria, data)
                VALUES (?, ?, ?, ?)
            ''', (
                valor,
                descricao,
                categoria,
                data
            ))

            self.conn.commit()
            self.logger.info(f"Receita adicionada: {descricao} - R${valor} em {data}")
            return True

        except Exception as e:
            self.logger.error(f"Erro ao adicionar receita: {e}")
            return False

    def get_receitas(self, data_inicio=None, data_fim=None, categoria=None):
        """
        Obtém receitas com filtros opcionais
        
        Args:
            data_inicio: Data inicial (opcional)
            data_fim: Data final (opcional)
            categoria: Nome da categoria (opcional)
        """
        try:
            query = '''
                SELECT valor, descricao, categoria, data
                FROM receitas
                WHERE 1=1
            '''
            params = []

            if data_inicio:
                query += ' AND data >= ?'
                params.append(data_inicio)
            if data_fim:
                query += ' AND data <= ?'
                params.append(data_fim)
            if categoria:
                query += ' AND categoria = ?'
                params.append(categoria)

            query += ' ORDER BY data DESC'
            
            self.cursor.execute(query, params)
            return self.cursor.fetchall()

        except Exception as e:
            self.logger.error(f"Erro ao obter receitas: {e}")
            return []

    def get_resumo_receitas(self, data_inicio=None, data_fim=None):
        """
        Gera um resumo das receitas por categoria
        
        Args:
            data_inicio: Data inicial (opcional)
            data_fim: Data final (opcional)
        """
        try:
            receitas = self.get_receitas(data_inicio, data_fim)
            
            # Agrupa receitas por categoria
            receitas_por_categoria = defaultdict(float)
            total_receitas = 0
            
            for valor, _, categoria, _ in receitas:
                receitas_por_categoria[categoria] += valor
                total_receitas += valor
            
            # Calcula percentuais
            resumo = []
            for categoria, valor in receitas_por_categoria.items():
                percentual = (valor / total_receitas) * 100 if total_receitas > 0 else 0
                resumo.append((categoria, valor, percentual))
            
            # Ordena por valor (maior para menor)
            resumo.sort(key=lambda x: x[1], reverse=True)
            
            return resumo, total_receitas

        except Exception as e:
            self.logger.error(f"Erro ao gerar resumo de receitas: {e}")
            return [], 0

    def processar_mensagem_receita(self, mensagem):
        """
        Processa uma mensagem de texto no formato "Ganhei X reais com Y" e suas variações
        
        Args:
            mensagem: String contendo a mensagem da receita
            
        Returns:
            tuple: (sucesso, resposta)
            - sucesso: bool indicando se a receita foi registrada
            - resposta: string com mensagem de sucesso ou erro
        """
        try:
            # Padrões de regex para diferentes formatos
            padroes = [
                r'ganhei\s+(\d+[.,]?\d*)\s+reais?\s+(?:com|em|para|no|na)\s+(.+?)(?:\s+(?:em|no|na|dia|dias|semana|mês|ano|ontem|hoje|amanhã|anteontem|semana passada|mês passado|ano passado|\d{1,2}/\d{1,2}(?:/\d{4})?|\d{1,2} de \w+(?: de \d{4})?))?$',
                r'recebi\s+(\d+[.,]?\d*)\s+reais?\s+(?:com|em|para|no|na)\s+(.+?)(?:\s+(?:em|no|na|dia|dias|semana|mês|ano|ontem|hoje|amanhã|anteontem|semana passada|mês passado|ano passado|\d{1,2}/\d{1,2}(?:/\d{4})?|\d{1,2} de \w+(?: de \d{4})?))?$',
                r'consegui\s+(\d+[.,]?\d*)\s+reais?\s+(?:com|em|para|no|na)\s+(.+?)(?:\s+(?:em|no|na|dia|dias|semana|mês|ano|ontem|hoje|amanhã|anteontem|semana passada|mês passado|ano passado|\d{1,2}/\d{1,2}(?:/\d{4})?|\d{1,2} de \w+(?: de \d{4})?))?$',
                r'fiz\s+(\d+[.,]?\d*)\s+reais?\s+(?:com|em|para|no|na)\s+(.+?)(?:\s+(?:em|no|na|dia|dias|semana|mês|ano|ontem|hoje|amanhã|anteontem|semana passada|mês passado|ano passado|\d{1,2}/\d{1,2}(?:/\d{4})?|\d{1,2} de \w+(?: de \d{4})?))?$',
                r'vendi\s+(\d+[.,]?\d*)\s+reais?\s+(?:com|em|para|no|na)\s+(.+?)(?:\s+(?:em|no|na|dia|dias|semana|mês|ano|ontem|hoje|amanhã|anteontem|semana passada|mês passado|ano passado|\d{1,2}/\d{1,2}(?:/\d{4})?|\d{1,2} de \w+(?: de \d{4})?))?$'
            ]
            
            mensagem = mensagem.lower().strip()
            
            for padrao in padroes:
                match = re.search(padrao, mensagem)
                if match:
                    valor_str = match.group(1).replace(',', '.')
                    descricao = match.group(2).strip()
                    
                    # Extrai a parte da data se existir
                    data_part = None
                    if len(match.groups()) > 2 and match.group(3):
                        data_part = match.group(3).strip()
                    
                    try:
                        valor = float(valor_str)
                        if valor <= 0:
                            return False, "O valor da receita deve ser maior que zero."
                        
                        # Tenta determinar a categoria automaticamente
                        categoria = self._determinar_categoria_receita(descricao)
                        
                        # Processa a data se existir
                        data = None
                        if data_part:
                            data = self._processar_data(data_part)
                        
                        # Adiciona a receita
                        if self.adicionar_receita(valor, descricao, categoria, data):
                            data_str = f" em {data_part}" if data_part else ""
                            return True, f"Receita registrada: R${valor:.2f} com {descricao}{data_str} (categoria: {categoria})"
                        else:
                            return False, "Erro ao registrar a receita."
                            
                    except ValueError:
                        return False, "Valor inválido. Use números para o valor da receita."
            
            return False, "Formato inválido. Use: 'Ganhei X reais com Y' ou variações similares."
            
        except Exception as e:
            self.logger.error(f"Erro ao processar mensagem de receita: {e}")
            return False, "Erro ao processar a mensagem."

    def _determinar_categoria_receita(self, descricao):
        """
        Tenta determinar a categoria automaticamente baseado na descrição da receita
        
        Args:
            descricao: String com a descrição da receita
            
        Returns:
            string: Nome da categoria determinada
        """
        descricao = descricao.lower()
        
        # Mapeamento de palavras-chave para categorias de receita
        mapeamento = {
            'Salário': ['salário', 'salario', 'pagamento', 'remuneração', 'remuneracao', 'pro-labore'],
            'Freelance': ['freelance', 'freela', 'trabalho', 'serviço', 'servico', 'projeto', 'contrato'],
            'Investimentos': ['investimento', 'renda', 'dividendos', 'juros', 'aplicação', 'aplicacao'],
            'Vendas': ['venda', 'vendas', 'produto', 'mercadoria', 'item', 'artigo'],
            'Presentes': ['presente', 'doação', 'doacao', 'presentearam', 'ganhei', 'consegui'],
            'Outros': ['outros', 'diversos', 'miscelânea', 'miscelanea']
        }
        
        # Verifica se alguma palavra-chave está presente na descrição
        for categoria, palavras in mapeamento.items():
            if any(palavra in descricao for palavra in palavras):
                return categoria
                
        # Se não encontrar nenhuma correspondência, retorna 'Outros'
        return 'Outros'

    def definir_nome_usuario(self, nome):
        """
        Define o nome do usuário
        
        Args:
            nome: Nome do usuário
        """
        try:
            self.cursor.execute('''
                INSERT OR REPLACE INTO configuracoes (chave, valor)
                VALUES ('nome_usuario', ?)
            ''', (nome,))
            
            self.conn.commit()
            self.logger.info(f"Nome do usuário definido: {nome}")
            return True
            
        except Exception as e:
            self.logger.error(f"Erro ao definir nome do usuário: {e}")
            return False

    def get_nome_usuario(self):
        """
        Obtém o nome do usuário
        
        Returns:
            string: Nome do usuário ou None se não definido
        """
        try:
            self.cursor.execute('''
                SELECT valor FROM configuracoes WHERE chave = 'nome_usuario'
            ''')
            resultado = self.cursor.fetchone()
            
            if resultado:
                return resultado[0]
            return None
            
        except Exception as e:
            self.logger.error(f"Erro ao obter nome do usuário: {e}")
            return None

    def definir_meta(self, nome, valor_meta, data_limite=None, descricao=None):
        """Define uma nova meta financeira"""
        try:
            self.cursor.execute('''
                INSERT INTO metas (nome, valor_meta, data_limite, descricao)
                VALUES (?, ?, ?, ?)
            ''', (nome, valor_meta, data_limite, descricao))
            self.conn.commit()
            self.logger.info(f"Meta '{nome}' definida com sucesso")
            return True
        except Exception as e:
            self.logger.error(f"Erro ao definir meta: {str(e)}")
            return False

    def atualizar_meta(self, meta_id, valor_atual=None, status=None):
        """Atualiza o progresso ou status de uma meta"""
        try:
            if valor_atual is not None:
                self.cursor.execute('''
                    UPDATE metas SET valor_atual = ?
                    WHERE id = ?
                ''', (valor_atual, meta_id))
            if status is not None:
                self.cursor.execute('''
                    UPDATE metas SET status = ?
                    WHERE id = ?
                ''', (status, meta_id))
            self.conn.commit()
            self.logger.info(f"Meta {meta_id} atualizada com sucesso")
            return True
        except Exception as e:
            self.logger.error(f"Erro ao atualizar meta: {str(e)}")
            return False

    def get_metas(self):
        """Retorna todas as metas do usuário"""
        try:
            self.cursor.execute('''
                SELECT id, nome, valor_meta, valor_atual, data_limite, descricao, status
                FROM metas
                ORDER BY status, data_limite
            ''')
            return self.cursor.fetchall()
        except Exception as e:
            self.logger.error(f"Erro ao buscar metas: {str(e)}")
            return []

    def registrar_contribuicao_meta(self, meta_id, valor):
        """
        Registra uma contribuição para uma meta e atualiza seu progresso
        
        Args:
            meta_id: ID da meta
            valor: Valor da contribuição
            
        Returns:
            tuple: (sucesso, mensagem)
        """
        try:
            # Obtém os dados atuais da meta
            self.cursor.execute('''
                SELECT valor_meta, valor_atual, nome, status
                FROM metas
                WHERE id = ?
            ''', (meta_id,))
            resultado = self.cursor.fetchone()
            
            if not resultado:
                return False, "Meta não encontrada"
                
            valor_meta, valor_atual, nome, status = resultado
            
            if status != "ativa":
                return False, f"A meta '{nome}' não está ativa"
            
            # Atualiza o valor atual, tratando o caso de valor_atual ser None
            if valor_atual is None:
                valor_atual = 0
            novo_valor = valor_atual + valor
            
            self.cursor.execute('''
                UPDATE metas
                SET valor_atual = ?
                WHERE id = ?
            ''', (novo_valor, meta_id))
            
            # Verifica se a meta foi concluída
            if novo_valor >= valor_meta:
                self.cursor.execute('''
                    UPDATE metas
                    SET status = 'concluída'
                    WHERE id = ?
                ''', (meta_id,))
                status = "concluída"
            
            self.conn.commit()
            
            # Calcula o percentual
            percentual = (novo_valor / valor_meta) * 100
            
            # Prepara a mensagem de retorno
            mensagem = f"✅ Contribuição registrada para a meta '{nome}':\n\n"
            mensagem += f"💰 Valor adicionado: R${valor:.2f}\n"
            mensagem += f"💵 Total acumulado: R${novo_valor:.2f}\n"
            mensagem += f"🎯 Meta: R${valor_meta:.2f} ({percentual:.1f}%)\n"
            
            if status == "concluída":
                mensagem += "\n🎉 Parabéns! Você atingiu sua meta!"
            
            return True, mensagem
            
        except Exception as e:
            self.logger.error(f"Erro ao registrar contribuição: {str(e)}")
            return False, "Erro ao registrar contribuição"

    def processar_mensagem_meta(self, mensagem):
        """Processa mensagens relacionadas a metas financeiras"""
        try:
            # Padrões para identificar contribuições para metas
            padroes = [
                r'(?:juntei|adicionei|contribuí|coloquei|depositei|reservei|guardei|economizei|poupei|salvei)\s+([\d,.]+)\s+(?:reais|r\$|r\$\s*)?(?:\s+para\s+a\s+meta\s+|\s+na\s+meta\s+|\s+para\s+)(.+)',
                r'(?:adicionei|coloquei|depositei|reservei|guardei|economizei|poupei|salvei)\s+([\d,.]+)\s+(?:reais|r\$|r\$\s*)?\s+(?:para|na)\s+(?:minha\s+)?meta\s+(?:de\s+)?(.+)',
                r'(?:meta|objetivo)\s+(.+)\s+(?:recebeu|ganhou|teve|obteve)\s+([\d,.]+)\s+(?:reais|r\$|r\$\s*)?',
                r'atualizei\s+(?:a\s+)?meta\s+(.+)\s+(?:para|com)\s+([\d,.]+)\s+(?:reais|r\$|r\$\s*)?',
                r'progresso\s+(?:da\s+)?meta\s+(.+)\s+(?:agora\s+é|está\s+em)\s+([\d,.]+)\s+(?:reais|r\$|r\$\s*)?',
                r'juntei\s+([\d,.]+)\s+(?:reais|r\$|r\$\s*)?\s+para\s+a\s+meta\s+(.+)',
                r'adicionei\s+([\d,.]+)\s+(?:reais|r\$|r\$\s*)?\s+na\s+meta\s+(.+)',
                r'contribuí\s+([\d,.]+)\s+(?:reais|r\$|r\$\s*)?\s+para\s+a\s+meta\s+(.+)',
                r'meta\s+(.+)\s+recebeu\s+([\d,.]+)\s+(?:reais|r\$|r\$\s*)?',
                r'atualizei\s+a\s+meta\s+(.+)\s+para\s+([\d,.]+)\s+(?:reais|r\$|r\$\s*)?',
                r'progresso\s+da\s+meta\s+(.+)\s+agora\s+é\s+([\d,.]+)\s+(?:reais|r\$|r\$\s*)?'
            ]
            
            for padrao in padroes:
                match = re.search(padrao, mensagem.lower())
                if match:
                    # Extrai o valor e o nome da meta
                    if len(match.groups()) == 2:
                        valor = float(match.group(1).replace(',', '.'))
                        nome_meta = match.group(2).strip()
                    else:
                        valor = float(match.group(2).replace(',', '.'))
                        nome_meta = match.group(1).strip()
                    
                    # Busca a meta pelo nome
                    metas = self.get_metas()
                    for meta in metas:
                        if meta[1].lower() == nome_meta.lower():
                            return self.registrar_contribuicao_meta(meta[0], valor)
                    
                    return False, f"Não encontrei a meta '{nome_meta}'. Verifique se o nome está correto."
            
            # Padrões para criar metas
            padroes_criar = [
                r'(?:quero|vou|preciso|desejo|pretendo)\s+(?:criar|fazer|estabelecer|definir|ter)\s+(?:uma\s+)?meta\s+(?:de\s+)?(.+)\s+(?:com|de|no\s+valor\s+de)\s+([\d,.]+)\s+(?:reais|r\$|r\$\s*)?(?:\s+para\s+o\s+dia\s+(\d{2}/\d{2}/\d{4}))?',
                r'(?:nova\s+)?meta\s+(?:chamada|nomeada|de\s+nome)\s+(.+)\s+(?:com|de|no\s+valor\s+de)\s+([\d,.]+)\s+(?:reais|r\$|r\$\s*)?(?:\s+para\s+o\s+dia\s+(\d{2}/\d{2}/\d{4}))?',
                r'(?:vou|quero|preciso)\s+(?:guardar|economizar|poupar|juntar)\s+([\d,.]+)\s+(?:reais|r\$|r\$\s*)?\s+(?:para|com\s+a\s+meta\s+de)\s+(.+)'
            ]
            
            for padrao in padroes_criar:
                match = re.search(padrao, mensagem.lower())
                if match:
                    if len(match.groups()) == 3:
                        nome = match.group(1).strip()
                        valor = float(match.group(2).replace(',', '.'))
                        data_limite = match.group(3)
                    else:
                        nome = match.group(2).strip()
                        valor = float(match.group(1).replace(',', '.'))
                        data_limite = None
                    
                    if self.definir_meta(nome, valor, data_limite):
                        return True, f"✅ Meta '{nome}' criada com sucesso!\n💰 Valor: R${valor:.2f}\n📅 Data limite: {data_limite if data_limite else 'Não definida'}"
                    else:
                        return False, "❌ Erro ao criar meta. Tente novamente."
            
            # Padrões para ver metas
            padroes_ver = [
                r'(?:mostre|mostra|veja|ver|quero\s+ver|quero\s+saber)\s+(?:minhas\s+)?(?:metas|objetivos)',
                r'(?:como\s+estão|qual\s+é\s+o\s+progresso\s+das|progresso\s+das)\s+(?:minhas\s+)?(?:metas|objetivos)',
                r'(?:metas|objetivos)\s+(?:atual|atualizado|atualizada)'
            ]
            
            for padrao in padroes_ver:
                if re.search(padrao, mensagem.lower()):
                    metas = self.get_metas()
                    if not metas:
                        return True, "🎯 Você ainda não tem metas definidas. Use /metas criar para criar uma nova meta."
                    
                    mensagem = "🎯 Suas Metas Financeiras:\n\n"
                    for meta in metas:
                        id_meta, nome, valor_meta, valor_atual, data_limite, descricao, status = meta
                        percentual = (valor_atual / valor_meta) * 100 if valor_meta > 0 else 0
                        emoji = "✅" if status == "concluída" else "⏳" if status == "ativa" else "❌"
                        mensagem += f"{emoji} {nome}:\n"
                        mensagem += f"💰 Meta: R${valor_meta:.2f}\n"
                        mensagem += f"💵 Atual: R${valor_atual:.2f} ({percentual:.1f}%)\n"
                        if data_limite:
                            mensagem += f"📅 Data limite: {data_limite}\n"
                        if descricao:
                            mensagem += f"📝 {descricao}\n"
                        mensagem += "\n"
                    return True, mensagem
            
            return False, None
            
        except Exception as e:
            print(f"Erro ao processar mensagem de meta: {str(e)}")
            return False, None

    def remover_meta(self, meta_id):
        """Remove uma meta pelo ID"""
        try:
            self.cursor.execute('''
                DELETE FROM metas
                WHERE id = ?
            ''', (meta_id,))
            self.conn.commit()
            self.logger.info(f"Meta {meta_id} removida com sucesso")
            return True
        except Exception as e:
            self.logger.error(f"Erro ao remover meta: {str(e)}")
            return False

    def editar_meta(self, meta_id, nome=None, valor_meta=None, data_limite=None, descricao=None):
        """Edita os dados de uma meta existente"""
        try:
            # Prepara a query de atualização
            campos = []
            valores = []
            
            if nome is not None:
                campos.append("nome = ?")
                valores.append(nome)
            
            if valor_meta is not None:
                campos.append("valor_meta = ?")
                valores.append(valor_meta)
            
            if data_limite is not None:
                campos.append("data_limite = ?")
                valores.append(data_limite)
            
            if descricao is not None:
                campos.append("descricao = ?")
                valores.append(descricao)
            
            if not campos:
                return False
                
            # Adiciona o ID ao final da lista de valores
            valores.append(meta_id)
            
            # Monta e executa a query
            query = f'''
                UPDATE metas
                SET {", ".join(campos)}
                WHERE id = ?
            '''
            
            self.cursor.execute(query, valores)
            self.conn.commit()
            self.logger.info(f"Meta {meta_id} editada com sucesso")
            return True
            
        except Exception as e:
            self.logger.error(f"Erro ao editar meta: {str(e)}")
            return False

# Exemplo de uso
if __name__ == '__main__':
    gm = GastosManager()
    
    try:
        # Teste de processamento de mensagens
        mensagens = [
            "Gastei 50 reais com almoço",
            "Gastei R$100 no mercado",
            "Gastei 200 reais com uber",
            "Gastei 1500 com aluguel",
            "Gastei 80 reais na farmácia"
        ]
        
        for msg in mensagens:
            sucesso, resposta = gm.processar_mensagem_gasto(msg)
            print(f"Mensagem: {msg}")
            print(f"Resposta: {resposta}\n")
        
        # Gera resumo
        resumo, total, resumo_texto = gm.get_resumo()
        print(f"\nTotal gasto: R${total:.2f}")
        print("\nResumo por categoria:")
        for categoria, valor, percentual in resumo:
            print(f"{categoria}: R${valor:.2f} ({percentual:.1f}%)")
            
        # Gera resumo detalhado
        resumo_detalhado, grafico_bytes = gm.get_resumo_detalhado()
        print(f"\n{resumo_texto}")
        
        # Exibe gráfico
        if grafico_bytes:
            import matplotlib.pyplot as plt
            plt.figure(figsize=(10, 10))
            plt.imshow(grafico_bytes)
            plt.title('Análise de Gastos')
            plt.axis('off')
            plt.show()
            
    finally:
        gm.close() 