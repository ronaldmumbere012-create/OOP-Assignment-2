"""Deterministic boundary, OOP, payroll, VAT and corporate tax checks."""
from datetime import date
from decimal import Decimal
import pytest
from src.tax_engine import (Money, ugx, PAYETax, TaxContext, Payroll, VATTax,
    Invoice, CorporateIncomeTax, TaxPlanner, InvalidIncomeError, NoScheduleForDateError)

@pytest.mark.parametrize('income,expected', [
    (335000, 0), (335001, 0), (410000, 15000), (410001, 15000),
    (485000, 33750), (485001, 33750), (10000000, 2888250),
    (10000001, 2888250), (11000000, 3288250)
])
def test_resident_boundaries(income, expected):
    assert PAYETax().calculate(TaxContext(ugx(income))).tax == ugx(expected)

@pytest.mark.parametrize('income,expected', [
    (0, 0), (335000, 33500), (335001, 33500),
    (410000, 48500), (410001, 48500),
    (10000000, 2925500), (10000001, 2925500)
])
def test_nonresident_boundaries(income, expected):
    assert PAYETax().calculate(TaxContext(ugx(income), residency='nonresident')).tax == ugx(expected)

def test_money_operators_and_rounding():
    assert ugx('100.50') == ugx(101)
    assert ugx(100) + ugx(20) == ugx(120)
    assert ugx(100) * Decimal('0.05') == ugx(5)
    assert ugx(99) < ugx(100)
    assert repr(ugx(100)) == 'Money(UGX 100)'
    with pytest.raises(InvalidIncomeError):
        ugx(0.1)

def test_payroll_and_employer_cost():
    result = Payroll().calculate(ugx(1000000), lst=ugx(10000))
    assert result.paye_base == ugx(990000)
    assert result.paye == ugx(185250)
    assert result.employee_nssf == ugx(50000)
    assert result.employer_nssf == ugx(100000)
    assert result.net_pay == ugx(754750)
    assert result.employer_total_cost == ugx(1100000)

def test_vat_three_categories():
    invoices = [Invoice('S1','sale','standard',ugx(1000000)),
                Invoice('S2','sale','zero',ugx(500000)),
                Invoice('S3','sale','exempt',ugx(300000)),
                Invoice('P1','purchase','standard',ugx(200000)),
                Invoice('P2','purchase','exempt',ugx(100000))]
    result = VATTax().invoices(invoices)
    assert result.output_vat == ugx(180000)
    assert result.input_vat == ugx(36000)
    assert result.vat_payable == ugx(144000)

def test_corporate_income_tax():
    result = CorporateIncomeTax().from_accounts(ugx(10000000), ugx(6000000))
    assert result.tax == ugx(1200000)
    assert CorporateIncomeTax().from_accounts(ugx(1), ugx(2)).tax == ugx(0)

def test_schedule_and_invalid_inputs():
    with pytest.raises(NoScheduleForDateError):
        PAYETax().calculate(TaxContext(ugx(1000000), on_date=date(2025, 1, 1)))
    with pytest.raises(InvalidIncomeError):
        TaxContext(ugx(-1))
    with pytest.raises(InvalidIncomeError):
        Payroll().calculate(ugx(100000), lst=ugx(200000))

def test_taxplanner():
    a = {'basic': ugx(1000000)}
    b = {'basic': ugx(1200000)}
    comparison = TaxPlanner().compare(a,b)
    assert comparison.net_pay_difference == comparison.second.net_pay - comparison.first.net_pay
