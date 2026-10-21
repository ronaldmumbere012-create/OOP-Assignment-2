"""Property-based PAYE checks (requires hypothesis from requirements.txt)."""
import pytest
hypothesis = pytest.importorskip('hypothesis')
from hypothesis import given, strategies as st
from src.tax_engine import PAYETax, TaxContext, ugx

@given(st.integers(min_value=0, max_value=10**11), st.sampled_from(['resident','nonresident']))
def test_tax_nonnegative_and_bounded(income, residency):
    tax = PAYETax().calculate(TaxContext(ugx(income), residency=residency)).tax.amount
    assert 0 <= tax <= income

@given(st.integers(min_value=0, max_value=10**11),
       st.integers(min_value=0, max_value=10**8),
       st.sampled_from(['resident','nonresident']))
def test_tax_monotone(income, increase, residency):
    tax = PAYETax()
    first = tax.calculate(TaxContext(ugx(income), residency=residency)).tax
    second = tax.calculate(TaxContext(ugx(income + increase), residency=residency)).tax
    assert first.amount <= second.amount
