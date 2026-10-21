"""Educational Uganda tax engine, FY 2026/27 (from 1 July 2026).

Sources and limitations are documented in README.md. This is not tax advice.
All money uses Decimal and rounds to the nearest whole UGX, HALF_UP.
"""
from __future__ import annotations
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import date
from decimal import Decimal, ROUND_HALF_UP
from typing import Literal


class TaxError(Exception):
    """Base error for tax calculation and validation."""


class InvalidIncomeError(TaxError):
    """Invalid money, income, deduction or tax input."""


class NoScheduleForDateError(TaxError):
    """A requested date has no configured tax schedule."""


def decimal_value(value: str | int | Decimal) -> Decimal:
    """Convert without binary floating-point arithmetic; reject float explicitly."""
    if isinstance(value, bool) or isinstance(value, float):
        raise InvalidIncomeError('Use int, str or Decimal; float is prohibited.')
    try:
        number = Decimal(value)
    except (ValueError, TypeError, ArithmeticError) as exc:
        raise InvalidIncomeError(f'Invalid money value: {value!r}') from exc
    if not number.is_finite():
        raise InvalidIncomeError('Money must be finite.')
    return number


@dataclass(frozen=True)
class Money:
    """Immutable UGX value object rounded to whole shillings, HALF_UP."""
    amount: Decimal

    def __post_init__(self) -> None:
        value = decimal_value(self.amount)
        object.__setattr__(self, 'amount', value.quantize(Decimal('1'), rounding=ROUND_HALF_UP))

    def __add__(self, other: Money) -> Money:
        if not isinstance(other, Money):
            return NotImplemented
        return Money(self.amount + other.amount)

    def __sub__(self, other: Money) -> Money:
        if not isinstance(other, Money):
            return NotImplemented
        return Money(self.amount - other.amount)

    def __mul__(self, other: str | int | Decimal) -> Money:
        return Money(self.amount * decimal_value(other))

    def __rmul__(self, other: str | int | Decimal) -> Money:
        return self.__mul__(other)

    def __lt__(self, other: Money) -> bool:
        if not isinstance(other, Money):
            return NotImplemented
        return self.amount < other.amount

    def __repr__(self) -> str:
        return f'Money(UGX {self.amount:,.0f})'

    def __str__(self) -> str:
        return f'UGX {self.amount:,.0f}'


def ugx(value: str | int | Decimal) -> Money:
    return Money(decimal_value(value))


def nonnegative(value: Money, label: str) -> None:
    if value.amount < 0:
        raise InvalidIncomeError(f'{label} cannot be negative.')


@dataclass(frozen=True)
class TaxContext:
    """Inputs for an individual tax calculation."""
    amount: Money
    on_date: date = date(2026, 10, 1)
    residency: Literal['resident', 'nonresident'] = 'resident'

    def __post_init__(self) -> None:
        nonnegative(self.amount, 'Taxable amount')
        if self.residency not in ('resident', 'nonresident'):
            raise TaxError('residency must be resident or nonresident.')
        if not isinstance(self.on_date, date):
            raise TaxError('on_date must be a datetime.date.')


@dataclass(frozen=True)
class TaxResult:
    name: str
    taxable_base: Money
    tax: Money
    explanation: str


class Tax(ABC):
    """Abstract tax interface: subclasses must calculate a TaxResult."""
    @abstractmethod
    def calculate(self, ctx: TaxContext) -> TaxResult:
        raise NotImplementedError


class PAYETax(Tax):
    """Monthly resident and nonresident PAYE schedules effective 1 July 2026."""
    EFFECTIVE = date(2026, 7, 1)

    def calculate(self, ctx: TaxContext) -> TaxResult:
        if ctx.on_date < self.EFFECTIVE:
            raise NoScheduleForDateError('PAYE schedule configured only from 2026-07-01.')
        x = ctx.amount.amount
        if ctx.residency == 'resident':
            if x <= 335000:
                tax = Decimal(0)
            elif x <= 410000:
                tax = (x - 335000) * Decimal('0.20')
            elif x <= 485000:
                tax = 15000 + (x - 410000) * Decimal('0.25')
            else:
                tax = 33750 + (x - 485000) * Decimal('0.30')
                if x > 10000000:
                    tax += (x - 10000000) * Decimal('0.10')
        else:
            if x <= 335000:
                tax = x * Decimal('0.10')
            elif x <= 410000:
                tax = 33500 + (x - 335000) * Decimal('0.20')
            else:
                tax = 48500 + (x - 410000) * Decimal('0.30')
                if x > 10000000:
                    tax += (x - 10000000) * Decimal('0.10')
        return TaxResult('Monthly PAYE', ctx.amount, ugx(tax),
                         f'{ctx.residency} schedule, effective from 1 July 2026')


@dataclass(frozen=True)
class PayrollResult:
    gross: Money
    employee_nssf: Money
    employer_nssf: Money
    local_service_tax: Money
    paye_base: Money
    paye: Money
    net_pay: Money
    employer_total_cost: Money


class Payroll:
    """Payroll pipeline: gross = basic + taxable allowances.

    LST is deducted from PAYE chargeable income; employee NSSF is NOT deducted
    from PAYE base in this educational implementation. Employer NSSF is not
    withheld from the employee. LST amount is an externally supplied monthly
    amount, not an invented LST rate schedule.
    """
    def __init__(self, paye: PAYETax | None = None) -> None:
        self.paye = paye or PAYETax()

    def calculate(self, basic: Money, allowances: Money = ugx(0),
                  lst: Money = ugx(0), residency: str = 'resident',
                  on_date: date = date(2026, 10, 1)) -> PayrollResult:
        for label, amount in [('Basic pay', basic), ('Allowances', allowances), ('LST', lst)]:
            nonnegative(amount, label)
        gross = basic + allowances
        if lst.amount > gross.amount:
            raise InvalidIncomeError('LST cannot exceed gross employment income.')
        employee_nssf = gross * Decimal('0.05')
        employer_nssf = gross * Decimal('0.10')
        paye_base = gross - lst
        paye = self.paye.calculate(TaxContext(paye_base, on_date, residency)).tax
        net_pay = gross - employee_nssf - lst - paye
        if net_pay.amount < 0:
            raise InvalidIncomeError('Calculated net pay is negative; check LST input.')
        return PayrollResult(gross, employee_nssf, employer_nssf, lst,
                             paye_base, paye, net_pay, gross + employer_nssf)


SupplyType = Literal['standard', 'zero', 'exempt']
InvoiceDirection = Literal['sale', 'purchase']


@dataclass(frozen=True)
class Invoice:
    """Invoice amount is exclusive of VAT. Purchase VAT must be supported by evidence.

    Eligible input VAT is assumed claimable for standard-rated purchases;
    purchases assigned to exempt supplies are disallowed in this simplified model.
    """
    reference: str
    direction: InvoiceDirection
    category: SupplyType
    net_amount: Money

    def __post_init__(self) -> None:
        nonnegative(self.net_amount, 'Invoice net amount')
        if self.direction not in ('sale', 'purchase'):
            raise TaxError('direction must be sale or purchase.')
        if self.category not in ('standard', 'zero', 'exempt'):
            raise TaxError('category must be standard, zero or exempt.')
        if not self.reference.strip():
            raise TaxError('Invoice reference is required.')


@dataclass(frozen=True)
class VATResult:
    output_vat: Money
    input_vat: Money
    net_vat: Money
    vat_payable: Money
    credit_balance: Money


class VATTax(Tax):
    RATE = Decimal('0.18')

    def calculate(self, ctx: TaxContext) -> TaxResult:
        return TaxResult('VAT on standard-rated amount', ctx.amount,
                         ctx.amount * self.RATE, '18% of VAT-exclusive amount')

    def invoices(self, invoices: list[Invoice]) -> VATResult:
        output_vat = ugx(0)
        input_vat = ugx(0)
        for invoice in invoices:
            vat = self.calculate(TaxContext(invoice.net_amount)).tax if invoice.category == 'standard' else ugx(0)
            if invoice.direction == 'sale':
                output_vat = output_vat + vat
            elif invoice.category == 'standard':
                input_vat = input_vat + vat
        net = output_vat - input_vat
        return VATResult(output_vat, input_vat, net,
                         ugx(max(Decimal(0), net.amount)),
                         ugx(max(Decimal(0), -net.amount)))


class CorporateIncomeTax(Tax):
    RATE = Decimal('0.30')

    def calculate(self, ctx: TaxContext) -> TaxResult:
        return TaxResult('Corporate income tax', ctx.amount,
                         ctx.amount * self.RATE, '30% standard resident-company rate')

    def from_accounts(self, revenue: Money, allowable_deductions: Money) -> TaxResult:
        nonnegative(revenue, 'Revenue')
        nonnegative(allowable_deductions, 'Allowable deductions')
        chargeable = ugx(max(Decimal(0), (revenue - allowable_deductions).amount))
        return self.calculate(TaxContext(chargeable))


@dataclass(frozen=True)
class PlanningComparison:
    first: PayrollResult
    second: PayrollResult
    net_pay_difference: Money


class TaxPlanner:
    """Extension B: compare two PAYE/payroll scenarios on a like-for-like basis."""
    def __init__(self, payroll: Payroll | None = None) -> None:
        self.payroll = payroll or Payroll()

    def compare(self, first: dict, second: dict) -> PlanningComparison:
        a = self.payroll.calculate(**first)
        b = self.payroll.calculate(**second)
        return PlanningComparison(a, b, b.net_pay - a.net_pay)
