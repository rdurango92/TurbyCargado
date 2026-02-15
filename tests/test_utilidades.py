import pytest

from utilidades import calcular_tiempo_carga


def test_calcular_tiempo_carga_normal():
    result = calcular_tiempo_carga(0.20, 0.60, 0.01)
    assert result == 40


def test_calcular_tiempo_carga_invalid_target():
    with pytest.raises(ValueError, match="mayor que la carga inicial"):
        calcular_tiempo_carga(0.50, 0.50, 0.01)

