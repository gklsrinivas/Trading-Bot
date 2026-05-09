# Run Guide & Signal Delivery

This guide shows exactly how to run the bot and where signals appear.

## 1) Prerequisites

- Python 3.10+
- `pip`
- OANDA API credentials (**only** for live mode)

## 2) Install dependencies

```bash
pip install oandapyV20 pandas numpy
```

## 3) Quick test (demo mode)

Demo mode uses synthetic candles and is the safest way to validate setup.

```bash
python main.py --demo
```

Expected result:
- You will see Stage 1 → Stage 2 → Stage 3 evaluation output in terminal.
- If all filters pass, a final signal is printed and logged.

## 4) Configure live mode

Open `config/settings.py` and set:

- `OANDA_API_KEY = "..."`
- `OANDA_ACCOUNT_ID = "..."`
- `OANDA_ENVIRONMENT = "practice"` (recommended first)

Also review these risk controls before going live:
- `ACCOUNT_RISK_PERCENT`
- `DRAWDOWN_WARN_PCT`
- `DRAWDOWN_PAUSE_PCT`
- `DRAWDOWN_CLOSE_PCT`

## 5) Start live mode

```bash
python main.py --balance 10000
```

`--balance` initializes the drawdown tracker baseline.

## 6) How to get signals

Signals can be consumed in 3 ways:

### A. Terminal (immediate)
- Live and demo runs both print signal decisions directly in console.

### B. Log file (persistent)
Default log file: `g7fx_signals.log`

```bash
tail -f g7fx_signals.log
```

### C. Alerts (email/webhook)
In `config/settings.py`:

- Email:
  - `ALERT_EMAIL_ENABLED = True`
  - Fill SMTP host, port, user, password, from/to addresses.
- Webhook:
  - `ALERT_WEBHOOK_ENABLED = True`
  - Set `ALERT_WEBHOOK_URL` (Discord/Slack/custom endpoint).

When a qualified signal is emitted, `alerts/dispatcher.py` sends it through enabled channels.

## 7) Why you might not see frequent signals

No signal is expected when any gate fails, for example:
- Balanced/indecisive AMT context,
- Weak or missing confluence,
- Risk/reward below minimum,
- Order-flow proxy conflict,
- Drawdown pause active,
- Time filter/kill-zone restrictions.

This is intentional signal filtering, not necessarily a runtime error.

## 8) Practical startup checklist

1. Run demo mode once and confirm stage output is visible.
2. Add OANDA credentials and keep environment on `practice`.
3. Enable webhook alerts and verify receipt.
4. Start live mode with conservative risk settings.
5. Monitor `g7fx_signals.log` during London/NY sessions.
