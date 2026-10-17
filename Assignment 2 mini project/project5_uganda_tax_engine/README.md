# Mini-Project 5: Uganda Tax Engine
## Project structure

- `src/tax_engine.py`: OOP classes, money, PAYE, payroll, VAT, corporate tax and TaxPlanner.
- `project5_uganda_tax_engine.ipynb`: complete runnable demonstration and explanation.
- `tests/test_tax_engine.py`: boundary and functional tests.
- `tests/test_properties.py`: property-based tests using Hypothesis.
- `requirements.txt`: Python dependencies.

## Setup


```bash
python -m venv .venv
# Windows: .venv\Scripts\activate
# macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
python -m pytest -q
jupyter notebook project5_uganda_tax_engine.ipynb
```


## Tax rules and data provenance

- Resident monthly PAYE bands **effective 1 July 2026**: nil up to 335,000; 20% over 335,000 through 410,000; 15,000 + 25% over 410,000 through 485,000; 33,750 + 30% over 485,000 through 10 million; plus 10% surcharge on the excess over 10 million. [URA PAYE Rates](https://ura.go.ug/en/domestic-taxes/paye-rates/) and [URA notice, 7 September 2026](https://ura.go.ug/en/changes-to-paye-return-form-following-the-income-tax-amendment-act-2026/).
- Non-resident monthly PAYE: 10% through 335,000; 33,500 + 20% above 335,000 through 410,000; 48,500 + 30% above 410,000 thereafter; additional 10% surcharge above 10 million. [URA PAYE Rates](https://ura.go.ug/en/domestic-taxes/paye-rates/).
- LST paid is deductible before PAYE: [URA Employment Income](https://ura.go.ug/en/employment-income/). This program accepts a **user-specified monthly LST amount**; it does not invent a local authority assessment table.
- NSSF employee 5%, employer 10%, VAT standard 18% and resident-company income tax standard 30% follow the assignment baseline. URA confirms the 30% standard corporate tax rate in [Ask URA Commissioner General 30 (August 2026)](https://ura.go.ug/en/ask-ura-commissioner-general-30/). These are educational baseline assumptions; confirm current statutory eligibility, exemptions and amendments before live use.

## Computation design

1. `Money` is immutable, uses `Decimal` and rounds to whole UGX using `ROUND_HALF_UP`. All tax computations use decimal arithmetic; Python floats are rejected.
2. `Tax` is an abstract base class. `PAYETax`, `VATTax` and `CorporateIncomeTax` implement `calculate(TaxContext) -> TaxResult`.
3. `Payroll` uses composition: gross = basic + taxable allowances; employee NSSF = 5% gross; employer NSSF = 10% gross; PAYE base = gross - configured LST; net = gross - employee NSSF - LST - PAYE. Employee NSSF is **not** deducted from the PAYE base. Employer NSSF is not withheld from employee pay.
4. VAT invoices are VAT-exclusive. Standard-rated sales generate output VAT; standard-rated purchases generate eligible input VAT under a simplified full-credit assumption; zero-rated and exempt supplies generate no output VAT. Input VAT attributable to exempt purchases is not credited. This is **not** a full mixed-supply VAT apportionment system.
5. Corporate tax is 30% of positive revenue less allowable deductions. It omits carry-forward losses, special tax regimes, incentives and other adjustments.
6. Extension B: `TaxPlanner` compares two payroll scenarios and reports the change in net pay.

## Findings and limitations

The existing calculations. Tests are included to check the PAYE rates, non-resident tax calculations, rounding, invalid inputs, VAT and payroll comparisons. Hypothesis is also used to check that tax amounts are not negative, increase or remain the same as taxable income rises and do not exceed taxable income.

