# Mini-Project 5: Uganda Tax Engine

MSCS & MSDS OOP with Python, Advent 2026. The uploaded **Assignment 2** calls the Uganda Tax Engine *Mini-Project 2*. It is named **Project 5** here to continue the user's prior Project 1–4 sequence.

## Project structure

```text
Project_5_Uganda_Tax_Engine_Clean/
├── project5_uganda_tax_engine.ipynb   # Main deliverable: executable notebook
├── src/
│   ├── __init__.py                    # Makes src an importable package
│   └── tax_engine.py                  # OOP tax engine
├── tests/
│   ├── test_tax_engine.py             # Boundary and functional tests
│   └── test_properties.py             # Hypothesis property-based tests
├── requirements.txt                   # Dependencies
├── pyproject.toml                     # Test discovery/import configuration
├── .gitignore                         # Excludes local caches and environments
└── README.md                          # Instructions and tax assumptions
```

## Installation and execution on Windows (PowerShell)

Open **the extracted project folder** in VS Code, then use its terminal.
Confirm that `requirements.txt`, `src` and the notebook are visible in this folder.

```powershell
cd "D:\\MSDS\\OOP\\Assignment 2 mini project\\Project_5_Uganda_Tax_Engine_Clean"
python -m pip install -r requirements.txt
python -m pytest -q
python -m notebook
```

Run the notebook using **Kernel → Restart Kernel and Run All Cells**.

**Important:** Run commands from the project root, **not** inside `src` or `tests`.
Do not run `python src/tax_engine.py` to launch the project: the notebook is the
required main deliverable and imports `from src.tax_engine import ...`.

If `python -m venv .venv` fails with a Windows launcher copy error, a virtual
environment is optional for this assignment. Use `python -m pip install -r
requirements.txt` with your existing Python interpreter. If you prefer a
virtual environment, try `py -3.13 -m venv .venv` with an installed stable
Python version, then `.\.venv\Scripts\Activate.ps1`. If activation
is blocked by PowerShell policy, run `.\.venv\Scripts\python.exe`
directly instead of changing system policy.

If you see `ModuleNotFoundError: No module named 'src'`, check:

1. You extracted the ZIP rather than opening a file inside it.
2. Your terminal's current folder contains `src/tax_engine.py`.
3. `src/__init__.py` exists.
4. You launched Jupyter from the same project root.
5. You did not create a second nested `project5_uganda_tax_engine` folder and open the wrong one.

Check imports directly:

```powershell
python -c "from src.tax_engine import PAYETax, TaxPlanner; print('Imports OK')"
```

## Assignment coverage

The supplied assignment PDF labels this exercise **Mini-Project 2: Uganda Tax
Engine**. The project retains the name **Project 5** for consistency with the
student's earlier project numbering. It covers both PAYE residencies, NSSF,
configurable LST, three VAT supply types, corporate income tax, the abstract
`Tax` interface, a `Money` value object, custom exceptions, boundary and
property-based tests and **Extension B: TaxPlanner**. The notebook is the
required executable `.ipynb` deliverable.

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

The OOP design enables each tax type to be calculated through a common interface, while payroll and scenario planning reuse existing components. Unit tests check PAYE band boundaries, non-resident schedules, rounding, input validation, VAT calculations and scenario comparison. Hypothesis tests check non-negativity, monotonicity and that PAYE does not exceed taxable income.

The project is a teaching implementation, **not a production tax filing system**. It implements only the PAYE schedule beginning 1 July 2026 and raises an explicit error for earlier dates. VAT invoice eligibility, LST assessment, sector-specific company taxation and other payroll deductions require further rules. The illustrative invoices and payroll examples are invented teaching cases, not URA records.

## Academic integrity and AI disclosure

AI assistance was used to draft and review Python code, tests, documentation and the notebook. The student should review all source references, run all tests, verify calculations and be able to explain each line during the viva.
