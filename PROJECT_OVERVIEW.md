# Project Overview

## Purpose

This repository contains a **rule-based FX signal engine** for **USD/JPY** inspired by the G7FX methodology. The system is designed to evaluate market context, detect structured trade opportunities, and emit alerts only when strict filters are satisfied.

It is primarily a **signal generation and risk-filtering engine**, not a guaranteed auto-execution strategy.

## What the engine does each cycle

The runner in `main.py` orchestrates a staged pipeline:

1. **Regime filter** checks trend/volatility conditions (can suppress trading in unstable regimes).
2. **Stage 1 (AMT Context)** builds profile context and directional bias.
3. **Stage 2 (Hypothesis)** finds confluence and candidate entry/SL/TP levels.
4. **Stage 3 (Order-flow proxy)** validates or suppresses the hypothesis.
5. **Risk engine** applies drawdown and sizing constraints before final emission.
6. **Alert dispatcher** sends the final signal to enabled channels.

## Signal quality gates

A signal is emitted only if all major gates pass:
- Market context supports a directional hypothesis,
- Confluence and minimum R:R are valid,
- Order-flow proxy does not conflict,
- Drawdown and operational risk checks allow new entries,
- Composite score meets threshold.

If any gate fails, the system intentionally returns **no-trade**.

## Main components

- `main.py` — runtime entrypoint and orchestration loop.
- `config/settings.py` — API, risk, alert, and scoring settings.
- `core/stage1_amt.py` — market profile and AMT context logic.
- `core/stage2_hypothesis.py` — VWAP/confluence trade hypothesis builder.
- `core/stage3_orderflow.py` — order-flow proxy confirmation/suppression.
- `core/risk_engine.py` — drawdown logic, sizing, and signal assembly.
- `alerts/dispatcher.py` — outbound email/webhook signal delivery.

## Intended usage

- Start with demo mode to verify behavior.
- Run with OANDA `practice` credentials before any live deployment.
- Use alerts/logging as signal distribution channels.
- Tune risk parameters conservatively before production usage.
