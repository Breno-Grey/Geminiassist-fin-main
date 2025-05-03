import re
from typing import Tuple, Optional
from decimal import Decimal, InvalidOperation
import unicodedata

class ValidadorEntrada:
    """Classe para validação e normalização de entradas do usuário"""
    
    @staticmethod
    def normalizar_texto(texto: str) -> str:
        """
        Normaliza o texto removendo acentos e convertendo para minúsculas
        
        Args:
            texto: Texto a ser normalizado
            
        Returns:
            str: Texto normalizado
        """
        # Remove acentos
        texto = ''.join(c for c in unicodedata.normalize('NFD', texto)
                       if unicodedata.category(c) != 'Mn')
        # Converte para minúsculas
        return texto.lower().strip()
    
    @staticmethod
    def normalizar_valor(valor_str: str) -> Tuple[bool, Optional[Decimal], str]:
        """
        Normaliza e valida valores monetários
        
        Args:
            valor_str: String contendo o valor
            
        Returns:
            Tuple[bool, Optional[Decimal], str]:
            - bool: Se o valor é válido
            - Optional[Decimal]: Valor normalizado ou None
            - str: Mensagem de erro ou sucesso
        """
        try:
            # Remove caracteres não numéricos exceto ponto e vírgula
            valor_str = re.sub(r'[^\d,.]', '', valor_str)
            
            # Verifica se tem mais de um separador decimal
            if len(re.findall(r'[,.]', valor_str)) > 1:
                return False, None, "Valor inválido: múltiplos separadores decimais"
            
            # Substitui vírgula por ponto
            valor_str = valor_str.replace(',', '.')
            
            # Verifica se tem apenas números e um ponto
            if not re.match(r'^\d+\.?\d*$', valor_str):
                return False, None, "Valor inválido: use apenas números e um separador decimal"
            
            # Converte para Decimal
            valor = Decimal(valor_str)
            
            # Verifica se o valor é positivo
            if valor <= 0:
                return False, None, "O valor deve ser maior que zero"
            
            # Verifica se o valor é muito grande (mais de 1 bilhão)
            if valor > Decimal('1000000000'):
                return False, None, "Valor muito alto. Verifique se está correto"
            
            return True, valor, "Valor válido"
            
        except InvalidOperation:
            return False, None, "Valor inválido: formato incorreto"
    
    @staticmethod
    def corrigir_erros_comuns(texto: str) -> str:
        """
        Corrige erros comuns de digitação
        
        Args:
            texto: Texto a ser corrigido
            
        Returns:
            str: Texto corrigido
        """
        correcoes = {
            'gastei': ['gaste', 'gasteu', 'gastou', 'gastar'],
            'paguei': ['pague', 'pagou', 'pagar'],
            'comprei': ['compre', 'comprou', 'comprar'],
            'reais': ['real', 'reau', 'reauis'],
            'almoço': ['almoco', 'almosso', 'almosço'],
            'jantar': ['janta', 'jantou', 'jantar'],
            'transporte': ['transporte', 'transporte', 'transporte'],
            'uber': ['uber', 'uberr', 'uber'],
            'táxi': ['taxi', 'taxi', 'táxi'],
            'mercado': ['mercado', 'mercado', 'mercado'],
            'farmácia': ['farmacia', 'farmácia', 'farmácia'],
            'lazer': ['lazer', 'lazer', 'lazer'],
            'cinema': ['cinema', 'cinema', 'cinema'],
            'restaurante': ['restaurante', 'restaurante', 'restaurante']
        }
        
        texto = texto.lower()
        palavras = texto.split()
        
        for i, palavra in enumerate(palavras):
            for correcao, erros in correcoes.items():
                if palavra in erros:
                    palavras[i] = correcao
        
        return ' '.join(palavras)
    
    @staticmethod
    def validar_categoria(categoria: str, categorias_validas: list) -> Tuple[bool, str]:
        """
        Valida se uma categoria é válida
        
        Args:
            categoria: Categoria a ser validada
            categorias_validas: Lista de categorias válidas
            
        Returns:
            Tuple[bool, str]:
            - bool: Se a categoria é válida
            - str: Categoria normalizada ou mensagem de erro
        """
        categoria = categoria.lower().strip()
        
        # Verifica se a categoria está na lista de categorias válidas
        if categoria in [c.lower() for c in categorias_validas]:
            return True, categoria
        
        # Tenta encontrar uma categoria similar
        for cat_valida in categorias_validas:
            if ValidadorEntrada.calcular_similaridade(categoria, cat_valida.lower()) > 0.8:
                return True, cat_valida.lower()
        
        return False, f"Categoria inválida. Categorias válidas: {', '.join(categorias_validas)}"
    
    @staticmethod
    def calcular_similaridade(str1: str, str2: str) -> float:
        """
        Calcula a similaridade entre duas strings usando o algoritmo de Levenshtein
        
        Args:
            str1: Primeira string
            str2: Segunda string
            
        Returns:
            float: Similaridade entre 0 e 1
        """
        if len(str1) < len(str2):
            return ValidadorEntrada.calcular_similaridade(str2, str1)
        
        if len(str2) == 0:
            return 1.0
        
        previous_row = range(len(str2) + 1)
        for i, c1 in enumerate(str1):
            current_row = [i + 1]
            for j, c2 in enumerate(str2):
                insertions = previous_row[j + 1] + 1
                deletions = current_row[j] + 1
                substitutions = previous_row[j] + (c1 != c2)
                current_row.append(min(insertions, deletions, substitutions))
            previous_row = current_row
        
        return 1.0 - (previous_row[-1] / max(len(str1), len(str2)))
    
    @staticmethod
    def extrair_valor_e_descricao(texto: str) -> Tuple[bool, Optional[Decimal], Optional[str], str]:
        """
        Extrai valor e descrição de uma mensagem de gasto
        
        Args:
            texto: Texto da mensagem
            
        Returns:
            Tuple[bool, Optional[Decimal], Optional[str], str]:
            - bool: Se a extração foi bem sucedida
            - Optional[Decimal]: Valor extraído ou None
            - Optional[str]: Descrição extraída ou None
            - str: Mensagem de erro ou sucesso
        """
        # Padrões de regex para diferentes formatos
        padroes = [
            r'(?:gastei|paguei|comprei|foi|custou|desembolsei)\s+R?\$?\s*(\d+[.,]?\d*)\s+(?:reais?\s+)?(?:com|em|para|no|na)\s+(.+?)(?:\s+(?:em|no|na|dia|dias|semana|mês|ano|ontem|hoje|amanhã|anteontem|semana passada|mês passado|ano passado|\d{1,2}/\d{1,2}(?:/\d{4})?|\d{1,2} de \w+(?: de \d{4})?))?$',
            r'(?:gastei|paguei|comprei|foi|custou|desembolsei)\s+R?\$?\s*(\d+[.,]?\d*)\s+(?:com|em|para|no|na)\s+(.+?)(?:\s+(?:em|no|na|dia|dias|semana|mês|ano|ontem|hoje|amanhã|anteontem|semana passada|mês passado|ano passado|\d{1,2}/\d{1,2}(?:/\d{4})?|\d{1,2} de \w+(?: de \d{4})?))?$',
            r'(?:gastei|paguei|comprei|foi|custou|desembolsei)\s+R?\$?\s*(\d+[.,]?\d*)\s+reais?\s+(?:com|em|para|no|na)\s+(.+?)(?:\s+(?:em|no|na|dia|dias|semana|mês|ano|ontem|hoje|amanhã|anteontem|semana passada|mês passado|ano passado|\d{1,2}/\d{1,2}(?:/\d{4})?|\d{1,2} de \w+(?: de \d{4})?))?$'
        ]
        
        texto = ValidadorEntrada.normalizar_texto(texto)
        texto = ValidadorEntrada.corrigir_erros_comuns(texto)
        
        for padrao in padroes:
            match = re.search(padrao, texto)
            if match:
                valor_str = match.group(1)
                descricao = match.group(2).strip()
                
                # Valida o valor
                sucesso, valor, mensagem = ValidadorEntrada.normalizar_valor(valor_str)
                if not sucesso:
                    return False, None, None, mensagem
                
                return True, valor, descricao, "Valor e descrição extraídos com sucesso"
        
        return False, None, None, "Formato inválido. Use: 'Gastei X reais com Y' ou variações similares" 