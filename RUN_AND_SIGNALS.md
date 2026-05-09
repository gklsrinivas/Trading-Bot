# Run Guide (Beginner Friendly)

If you are new to coding, follow this document **top to bottom**. Do not skip steps.

---

## What you need before starting

1. A computer with internet.
2. This project folder downloaded (or cloned) to your computer.
3. Python 3.10 or newer installed.
4. (Optional for live mode) OANDA practice account + API key.

> Demo mode does **not** need OANDA credentials.

---

## Step 1 — Open terminal in this project folder

You should be inside the folder that contains `main.py`.

- Example folder name: `Trading-Bot`

---

## Step 2 — Create and activate a virtual environment

A virtual environment avoids system Python errors and is recommended for everyone.

### macOS / Linux

```bash
python3 -m venv .venv
source .venv/bin/activate
```

### Windows (PowerShell)

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
```

### Windows (Command Prompt / CMD)

```cmd
py -m venv .venv
.venv\Scripts\activate.bat
```

If activation worked, you will usually see `(.venv)` at the start of your terminal line.

---

## Step 3 — Install required packages

Run this after the environment is active:

```bash
python -m pip install --upgrade pip
python -m pip install pandas numpy oandapyV20
```

---

## Step 4 — Run in demo mode (first run)

```bash
python main.py --demo
```

What you should see:
- Stage-by-stage analysis output.
- Final signal decision (`emitted`, `suppressed`, or `no-trade`).

If this works, your installation is correct.

---

## Step 5 — (Optional) Configure live/practice mode

Open `config/settings.py` and update:

- `OANDA_API_KEY`
- `OANDA_ACCOUNT_ID`
- `OANDA_ENVIRONMENT = "practice"` (recommended)

Also review risk settings before live usage:
- `ACCOUNT_RISK_PERCENT`
- `DRAWDOWN_WARN_PCT`
- `DRAWDOWN_PAUSE_PCT`
- `DRAWDOWN_CLOSE_PCT`

---

## Step 6 — Start live/practice run

```bash
python main.py --balance 10000
```

This keeps running and evaluates data continuously.

---

## Step 7 — How to receive signals

You can get signals in 3 places:

1. **Terminal output** (instant)
2. **Log file** `g7fx_signals.log` (saved history)
3. **Email/Webhook alerts** (if enabled)

To watch the log in real time:

### macOS / Linux
```bash
tail -f g7fx_signals.log
```

### Windows PowerShell
```powershell
Get-Content .\g7fx_signals.log -Wait
```

To enable alerts, edit `config/settings.py`:
- Email: set `ALERT_EMAIL_ENABLED = True` and fill SMTP fields.
- Webhook: set `ALERT_WEBHOOK_ENABLED = True` and set `ALERT_WEBHOOK_URL`.

---

## Common issues and quick fixes

### `pip: command not found`
Use:
```bash
python3 -m pip --version
```
or on Windows:
```powershell
py -m pip --version
```

### `externally-managed-environment`
You are installing globally. Use the virtual environment steps above.

### `ModuleNotFoundError: pandas` (or similar)
Your environment is not active or dependencies were not installed there.
Re-activate `.venv` and run install again.

---

## First-time checklist (non-technical)

- [ ] I opened terminal in the project folder.
- [ ] I created `.venv`.
- [ ] I activated `.venv`.
- [ ] I installed packages with `python -m pip ...`.
- [ ] I ran `python main.py --demo` successfully.
- [ ] I can see output in terminal and/or `g7fx_signals.log`.
