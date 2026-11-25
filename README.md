# CLEAR-REG
**AI-Powered Event Registration Cleaner with Explainable Data Auditing**

CLEAR-REG reads `data/registrations.csv`, asks Gemini to extract five fields from each original registration entry, then uses plain Python to fact-check, clean, validate and detect duplicates. It writes the three required reports plus an explainability audit log.

## Folder structure
- `main.py` — command-line entry point
- `python/cleaner.py` — fact-checking, cleaning, validation, duplicate detection and reports
- `python/gemini_client.py` — Gemini API integration
- `data/registrations.csv` — supplied sample input (25 entries)
- `system_prompt.txt` — five-role system prompt with two JSON examples
- `evaluation.py` — five deterministic evaluation cases
- `red_team.py` — three red-team scenarios
- `outputs/` — generated reports
- `reports/` — project documentation and submission notes

## Setup (Windows / VS Code)
1. Install Python 3.10 or later.
2. Open this folder in VS Code.
3. In Terminal run:
   ```bash
   python -m venv .venv
   .venv\Scripts\activate
   pip install -r requirements.txt
   ```
4. Copy `.env.example` to `.env`.
5. Generate a Gemini API key in Google AI Studio and paste it after `GEMINI_API_KEY=` in `.env`. Do not share the key or commit `.env`.
6. Run a one-row API check:
   ```bash
   python main.py --limit 1
   ```
7. Run all registrations:
   ```bash
   python main.py
   ```

## Testing
Run:
```bash
python evaluation.py
python red_team.py
```
The evaluation harness tests the deterministic Python rules. The red-team script displays the three required adversarial scenarios. Save actual screenshots/logs after running and review any failures; do not claim tests passed unless the terminal output confirms it.

## Output files
- `outputs/clean_list.csv` — valid registrations only
- `outputs/problems.csv` — every `needs_fix` or `duplicate` record and its reason
- `outputs/summary.txt` — counts and valid records by branch/year
- `outputs/audit_log.csv` — additional field-level trace of original, extracted and cleaned values

## Human checkpoint
The event team must review `problems.csv` and contact students to confirm or correct details. CLEAR-REG does not silently repair phone numbers or email addresses.

## Important
The Gemini key is private. `.env` is excluded by `.gitignore`; never paste the key into Python code, screenshots, reports, or GitHub. The API model name and free-tier limits may change; check Google AI Studio for the currently available model and quota.
