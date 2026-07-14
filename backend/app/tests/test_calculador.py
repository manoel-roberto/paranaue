import pytest
from decimal import Decimal
from app.services.calculador import (
    calcular_ats,
    calcular_percentual_simples,
    calcular_estabilidade,
    calcular_proporcionalidade_dias,
)

def test_calcular_ats_retorna_valor_correto_com_cinco_anos():
    """
    Testa se o cálculo do ATS retorna o valor correto para 5 anos de serviço
    com salário base de 5000.00 (esperado: 250.00).
    Seguindo o padrão AAA (Arrange, Act, Assert).
    """
    # Arrange
    salario_base = Decimal("5000.00")
    anos_servico = 5
    resultado_esperado = Decimal("250.00")

    # Act
    resultado_obtido = calcular_ats(salario_base, anos_servico)

    # Assert
    assert resultado_obtido == resultado_esperado


def test_calcular_ats_retorna_zero_com_menos_de_cinco_anos():
    """
    Testa se o cálculo do ATS retorna 0.00 para menos de 5 anos de serviço
    (ex: 4 anos) com salário base de 5000.00.
    """
    # Arrange
    salario_base = Decimal("5000.00")
    anos_servico = 4
    resultado_esperado = Decimal("0.00")

    # Act
    resultado_obtido = calcular_ats(salario_base, anos_servico)

    # Assert
    assert resultado_obtido == resultado_esperado


def test_calcular_ats_lanca_erro_com_salario_negativo():
    """
    Verifica se ValueError é lançado quando o salário base é negativo.
    """
    # Arrange
    salario_base = Decimal("-5000.00")
    anos_servico = 5

    # Act & Assert
    with pytest.raises(ValueError, match="O salário base não pode ser negativo."):
        calcular_ats(salario_base, anos_servico)


def test_calcular_ats_lanca_erro_com_anos_servico_negativos():
    """
    Verifica se ValueError é lançado quando os anos de serviço são negativos.
    """
    # Arrange
    salario_base = Decimal("5000.00")
    anos_servico = -1

    # Act & Assert
    with pytest.raises(ValueError, match="Os anos de serviço não podem ser negativos."):
        calcular_ats(salario_base, anos_servico)


# --- Testes para calcular_percentual_simples (Insalubridade/CET) ---

def test_calcular_percentual_simples_sucesso_insalubridade():
    """
    Verifica o cálculo de insalubridade de 20% sobre base de 3000.00.
    """
    # Arrange
    valor_base = Decimal("3000.00")
    percentual = Decimal("20.00")
    resultado_esperado = Decimal("600.00")

    # Act
    resultado_obtido = calcular_percentual_simples(valor_base, percentual)

    # Assert
    assert resultado_obtido == resultado_esperado


def test_calcular_percentual_simples_sucesso_cet():
    """
    Verifica o cálculo de CET de 125% sobre base de 4253.15 com dízima e arredondamento.
    Cálculo: 4253.15 * 1.25 = 5316.4375 -> Arredondado para 5316.44.
    """
    # Arrange
    valor_base = Decimal("4253.15")
    percentual = Decimal("125.00")
    resultado_esperado = Decimal("5316.44")

    # Act
    resultado_obtido = calcular_percentual_simples(valor_base, percentual)

    # Assert
    assert resultado_obtido == resultado_esperado


def test_calcular_percentual_simples_lanca_erro_com_base_negativa():
    """
    Verifica se ValueError é lançado quando a base de cálculo é negativa.
    """
    # Arrange
    valor_base = Decimal("-3000.00")
    percentual = Decimal("20.00")

    # Act & Assert
    with pytest.raises(ValueError, match="O valor base não pode ser negativo."):
        calcular_percentual_simples(valor_base, percentual)


def test_calcular_percentual_simples_lanca_erro_com_percentual_negativo():
    """
    Verifica se ValueError é lançado quando o percentual é negativo.
    """
    # Arrange
    valor_base = Decimal("3000.00")
    percentual = Decimal("-20.00")

    # Act & Assert
    with pytest.raises(ValueError, match="O percentual não pode ser negativo."):
        calcular_percentual_simples(valor_base, percentual)


# --- Testes para calcular_estabilidade (Estabilidade Econômica) ---

def test_calcular_estabilidade_sucesso():
    """
    Verifica o cálculo de estabilidade de 100% sobre símbolo de 5000.00.
    """
    # Arrange
    valor_simbolo = Decimal("5000.00")
    percentual_incorporacao = Decimal("100.00")
    resultado_esperado = Decimal("5000.00")

    # Act
    resultado_obtido = calcular_estabilidade(valor_simbolo, percentual_incorporacao)

    # Assert
    assert resultado_obtido == resultado_esperado


def test_calcular_estabilidade_sucesso_arredondamento():
    """
    Verifica cálculo de estabilidade de 30% sobre símbolo de 3145.67 com arredondamento.
    Cálculo: 3145.67 * 0.30 = 943.701 -> Arredondado para 943.70.
    """
    # Arrange
    valor_simbolo = Decimal("3145.67")
    percentual_incorporacao = Decimal("30.00")
    resultado_esperado = Decimal("943.70")

    # Act
    resultado_obtido = calcular_estabilidade(valor_simbolo, percentual_incorporacao)

    # Assert
    assert resultado_obtido == resultado_esperado


def test_calcular_estabilidade_lanca_erro_com_simbolo_negativo():
    """
    Verifica se ValueError é lançado quando o valor do símbolo é negativo.
    """
    # Arrange
    valor_simbolo = Decimal("-1000.00")
    percentual_incorporacao = Decimal("100.00")

    # Act & Assert
    with pytest.raises(ValueError, match="O valor do símbolo não pode ser negativo."):
        calcular_estabilidade(valor_simbolo, percentual_incorporacao)


def test_calcular_estabilidade_lanca_erro_com_percentual_negativo():
    """
    Verifica se ValueError é lançado quando o percentual de incorporação é negativo.
    """
    # Arrange
    valor_simbolo = Decimal("1000.00")
    percentual_incorporacao = Decimal("-50.00")

    # Act & Assert
    with pytest.raises(ValueError, match="O percentual de incorporação não pode ser negativo."):
        calcular_estabilidade(valor_simbolo, percentual_incorporacao)


# --- Testes para calcular_proporcionalidade_dias (Proporcionalidade Diária) ---

def test_calcular_proporcionalidade_dias_sucesso_sem_dizima():
    """
    Verifica proporcionalidade para diferença de 880.00 e 15 dias.
    Cálculo: 880.00 / 30.0 = 29.33333... -> Truncar para 29.333 -> 29.333 * 15 = 439.995 -> Arredondado para 440.00.
    """
    # Arrange
    diferenca_mensal = Decimal("880.00")
    dias_novo_cargo = 15
    resultado_esperado = Decimal("440.00")

    # Act
    resultado_obtido = calcular_proporcionalidade_dias(diferenca_mensal, dias_novo_cargo)

    # Assert
    assert resultado_obtido == resultado_esperado


def test_calcular_proporcionalidade_dias_sucesso_com_dizima():
    """
    Verifica proporcionalidade com dízima e arredondamento para diferença de 1000.00 e 14 dias.
    Cálculo: 1000.00 / 30.0 = 33.33333... -> Truncar para 33.333 -> 33.333 * 14 = 466.662 -> Arredondado para 466.66.
    """
    # Arrange
    diferenca_mensal = Decimal("1000.00")
    dias_novo_cargo = 14
    resultado_esperado = Decimal("466.66")

    # Act
    resultado_obtido = calcular_proporcionalidade_dias(diferenca_mensal, dias_novo_cargo)

    # Assert
    assert resultado_obtido == resultado_esperado


def test_calcular_proporcionalidade_dias_lanca_erro_com_diferenca_negativa():
    """
    Verifica se ValueError é lançado quando a diferença mensal é negativa.
    """
    # Arrange
    diferenca_mensal = Decimal("-100.00")
    dias_novo_cargo = 15

    # Act & Assert
    with pytest.raises(ValueError, match="A diferença mensal não pode ser negativa."):
        calcular_proporcionalidade_dias(diferenca_mensal, dias_novo_cargo)


def test_calcular_proporcionalidade_dias_lanca_erro_com_dias_negativos():
    """
    Verifica se ValueError é lançado quando os dias no novo cargo são negativos.
    """
    # Arrange
    diferenca_mensal = Decimal("100.00")
    dias_novo_cargo = -5

    # Act & Assert
    with pytest.raises(ValueError, match="Os dias do novo cargo não podem ser negativos."):
        calcular_proporcionalidade_dias(diferenca_mensal, dias_novo_cargo)
