from decimal import Decimal, ROUND_HALF_UP, ROUND_DOWN

def calcular_ats(salario_base: Decimal, anos_servico: int) -> Decimal:
    """
    Calcula o Adicional por Tempo de Serviço (ATS) da UEFS.
    
    Args:
        salario_base (Decimal): Salário base do servidor.
        anos_servico (int): Tempo de serviço em anos.
        
    Returns:
        Decimal: O valor calculado do ATS.
        
    Raises:
        ValueError: Se salario_base ou anos_servico forem negativos.
    """
    if salario_base < Decimal("0"):
        raise ValueError("O salário base não pode ser negativo.")
    if anos_servico < 0:
        raise ValueError("Os anos de serviço não podem ser negativos.")
        
    if anos_servico < 5:
        percentual = Decimal("0.00")
    else:
        # Menos de 5 anos: 0%
        # Exatamente 5 anos: 5%
        # Acima de 5 anos: 5% + 1% por ano adicional completo.
        # Que simplifica matematicamente para: anos_servico %
        percentual = Decimal(anos_servico) / Decimal("100")
        
    valor_ats = salario_base * percentual
    return valor_ats.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def calcular_percentual_simples(valor_base: Decimal, percentual: Decimal) -> Decimal:
    """
    Calcula um percentual simples aplicado sobre uma base de cálculo (Insalubridade/CET).
    
    Args:
        valor_base (Decimal): O valor base para aplicação do percentual.
        percentual (Decimal): O percentual a ser aplicado (ex: 20.00 para 20%).
        
    Returns:
        Decimal: O resultado do cálculo, arredondado para 2 casas decimais (ROUND_HALF_UP).
        
    Raises:
        ValueError: Se valor_base ou percentual forem negativos.
    """
    if valor_base < Decimal("0"):
        raise ValueError("O valor base não pode ser negativo.")
    if percentual < Decimal("0"):
        raise ValueError("O percentual não pode ser negativo.")
        
    resultado = valor_base * (percentual / Decimal("100"))
    return resultado.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def calcular_estabilidade(valor_simbolo: Decimal, percentual_incorporacao: Decimal) -> Decimal:
    """
    Calcula o valor da estabilidade econômica baseado no valor do símbolo e no percentual de incorporação.
    
    Args:
        valor_simbolo (Decimal): O valor de vencimento da função comissionada.
        percentual_incorporacao (Decimal): O percentual de incorporação do símbolo (ex: 30.00 para 30%).
        
    Returns:
        Decimal: O valor calculado da estabilidade, arredondado para 2 casas decimais (ROUND_HALF_UP).
        
    Raises:
        ValueError: Se valor_simbolo ou percentual_incorporacao forem negativos.
    """
    if valor_simbolo < Decimal("0"):
        raise ValueError("O valor do símbolo não pode ser negativo.")
    if percentual_incorporacao < Decimal("0"):
        raise ValueError("O percentual de incorporação não pode ser negativo.")
        
    resultado = valor_simbolo * (percentual_incorporacao / Decimal("100"))
    return resultado.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def calcular_proporcionalidade_dias(diferenca_mensal: Decimal, dias_novo_cargo: int) -> Decimal:
    """
    Calcula a proporcionalidade diária de uma diferença salarial no mês de transição.
    
    Args:
        diferenca_mensal (Decimal): A diferença salarial mensal integral da rubrica.
        dias_novo_cargo (int): Número de dias sob as novas regras do cargo.
        
    Returns:
        Decimal: O valor proporcional calculado para o mês de transição, arredondado para 2 casas decimais.
        
    Raises:
        ValueError: Se diferenca_mensal ou dias_novo_cargo forem negativos.
    """
    if diferenca_mensal < Decimal("0"):
        raise ValueError("A diferença mensal não pode ser negativa.")
    if dias_novo_cargo < 0:
        raise ValueError("Os dias do novo cargo não podem ser negativos.")
        
    # a) Calcule o valor diário dividindo a diferenca_mensal por Decimal("30.0").
    valor_diario = diferenca_mensal / Decimal("30.0")
    
    # b) TRUNQUE esse valor diário na 3ª casa decimal.
    valor_diario_truncado = valor_diario.quantize(Decimal("0.001"), rounding=ROUND_DOWN)
    
    # c) Multiplique o valor diário truncado pelos dias_novo_cargo.
    resultado_multiplicacao = valor_diario_truncado * Decimal(dias_novo_cargo)
    
    # d) Aplique o arredondamento financeiro final (ROUND_HALF_UP com 2 casas decimais)
    return resultado_multiplicacao.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
