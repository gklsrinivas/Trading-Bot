# G7FX Signal Engine — Phase 1

A Python signal engine built on Neerav Vadera's G7FX methodology:
**Auction Market Theory (Stage 1) + VWAP/Profile Confluence (Stage 2) + Order Flow (Stage 3)**

Designed for USD/JPY on OANDA, targeting <5% max drawdown.

---

## Project Structure

```
g7fx_signal_app/
├── main.py                    # Main runner (demo + live modes)
├── config/
│   └── settings.py            # All parameters (API keys, risk, kill zones)
├── core/
│   ├── data_feed.py           # OANDA API connector + synthetic data
│   ├── stage1_amt.py          # AMT context: profile, dominance, migration
│   ├── stage2_hypothesis.py   # VWAP, confluence zones, entry/exit logic
│   ├── stage3_orderflow.py    # Cumulative delta + footprint proxy
│   └── risk_engine.py         # Position sizing, drawdown, signal assembly
└── alerts/
    └── dispatcher.py          # Email + webhook alert delivery
```

---


## Documentation

- [Project Overview](PROJECT_OVERVIEW.md)
- [Run Guide & Signal Setup](RUN_AND_SIGNALS.md)

---

## Quick Start

### 1. Install dependencies
```bash
pip install oandapyV20 pandas numpy
```

### 2. Run in demo mode (no API key needed)
```bash
python main.py --demo
```

### 3. Configure for live trading
Edit `config/settings.py`:
```python
OANDA_API_KEY    = "your-key-here"
OANDA_ACCOUNT_ID = "your-account-id"
OANDA_ENVIRONMENT = "practice"   # Start with practice!
```

Then run:
```bash
python main.py --balance 10000
```

---

## Signal Logic Flow

```
Every 15 minutes:

STAGE 1 — AMT Context (H4 + H1)
  ├── Build volume profile (POC, VAH, VAL)
  ├── Classify profile shape (D / P / b / skewed)
  ├── Detect dominance (buyers / sellers / balanced)
  ├── Detect value migration (bullish / bearish / none)
  └── Classify session open type
         ↓ (if imbalanced + bias established)

STAGE 2 — Hypothesis (H1 + M15)
  ├── Calculate VWAP + ±1σ, ±2σ bands
  ├── Calculate anchored VWAP (from last swing)
  ├── Find confluence zones (static + dynamic levels within 10 pips)
  ├── Check M15 rejection candle at zone
  └── Build entry / SL / TP with R:R validation
         ↓ (if confluence found + R:R ≥ 1.5:1)

STAGE 3 — Order Flow (M15 tick volume proxy)
  ├── Compute cumulative delta (tick volume proxy)
  ├── Detect CD divergence (bullish / bearish / confirms)
  ├── Detect footprint patterns (absorption / exhaustion / stacked)
  └── Gate: SUPPRESS if CD conflicts with direction
         ↓ (if not suppressed + score ≥ 60)

RISK ENGINE
  ├── Kill zone check (London / NY open only)
  ├── Drawdown check (pause at 4.5%, close at 4.8%)
  ├── Position size (1% risk, 0.5% in high-vol conditions)
  └── Emit FinalSignal → Dispatch alert
```

---

## Risk Controls

| Condition | Action |
|-----------|--------|
| Drawdown 3.5% | Reduce position size to 0.5% risk |
| Drawdown 4.5% | Pause all new signals |
| Drawdown 4.8% | Close all open positions |
| Outside kill zone | Hold hypothesis, no entry |
| Stage 3 conflict | Suppress signal entirely |
| R:R < 1.5:1 | Reject hypothesis |

---

## Current USDJPY Context (May 4, 2026)

- Price: ~157.20 (post-BoJ intervention)
- AMT state: Imbalanced, bearish value migration
- Short hypothesis zone: 158.20–158.50 (score ~72)
- Long hypothesis zone: 155.97–156.30 (score ~58)
- No current signal: price is at VWAP/POC (centre of value area)
- BoJ intervention risk: reduce position size to 0.5%

---

## Phase 2 Roadmap

- [ ] Replace tick volume proxy with CME forex futures (6E/6B) via IBKR + Rithmic
- [ ] True bid/ask delta classification from L2 tick data
- [ ] Full footprint chart computation and pattern detection
- [ ] Multi-pair support (EUR/USD, GBP/USD)
- [ ] Mobile app frontend (React Native) with live signal cards
- [ ] Economic calendar API integration (news blackout automation)
- [ ] SEBI/NFA compliance layer if distributing signals commercially

---

## Disclaimer

This software is for educational purposes. Trading forex carries significant risk.
Always test on a practice account before live deployment.
Past signal performance does not guarantee future results.
US traders: consult NFA regulations before operating a commercial signal service.
