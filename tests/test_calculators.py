from sme_agent.services.calculators import parse_number, build_break_even, build_cashflow


def test_parse_number_with_thousands():
    assert parse_number("1.234") == 1234.0
    assert parse_number("1,234") == 1234.0


def test_parse_number_with_decimals():
    assert parse_number("1234,56") == 1234.56
    assert parse_number("1234.56") == 1234.56


def test_break_even_response():
    text = "costos fijos 1000000 precio 10000 costo variable 4000"
    result = build_break_even(text)
    assert result is not None
    assert "punto de equilibrio" in result.response.lower()


def test_cashflow_response():
    text = "ingresos 2000000 gastos 1500000"
    result = build_cashflow(text)
    assert result is not None
    assert "flujo de caja" in result.response.lower()
