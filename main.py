#!/usr/bin/env python3
# ============================================================
# G7FX Signal Engine v2 — Updated Main Runner
# ============================================================
# What's new vs v1:
#   Gap 1 fix: ADX regime filter + ATR expansion detector
#   Gap 2 fix: Merged profile detector with LVN targeting
#   Gap 3:     Confirmed footprint/CD already in Stage 3
#   Gap 4 fix: Footprint delta reader at TP1 (hold vs exit)
#
# Run in demo mode (no API key needed):
#   python main.py --demo
#
# Run live (requires OANDA key in config/settings.py):
#   python main.py --balance 10000
# ============================================================

import sys
import time
import logging
import argparse
from datetime import datetime, timezone

from config.settings   import LOG_LEVEL, LOG_FILE, INSTRUMENT
from core.data_feed    import get_synthetic_candles
from core.stage1_amt   import evaluate_stage1, build_volume_profile
from core.stage2_hypothesis import evaluate_stage2
from core.stage3_orderflow  import evaluate_stage3
from core.regime_filter     import evaluate_regime
from core.merged_profiles   import analyse_merged_profiles
from core.tp1_footprint     import read_footprint_at_tp1
from core.risk_engine       import (DrawdownTracker, assemble_final_signal,
                                     format_signal_alert)
from alerts.dispatcher import dispatch_alert

logging.basicConfig(
    level   = getattr(logging, LOG_LEVEL),
    format  = "%(asctime)s | %(levelname)-8s | %(message)s",
    handlers=[logging.StreamHandler(sys.stdout),
              logging.FileHandler(LOG_FILE)]
)
logger = logging.getLogger("main")

DIVIDER = "=" * 60

def section(title):
    print(f"\n  {title}")
    print("  " + "-" * (len(title)))

def run_demo():
    print(f"\n{DIVIDER}")
    print("  G7FX SIGNAL ENGINE v2 — DEMO MODE")
    print("  Instrument : USD/JPY")
    print("  Date       : May 2026 (post-BoJ intervention)")
    print("  New in v2  : Regime filter | Merged profiles |")
    print("               TP1 footprint decision")
    print(DIVIDER)

    # ── Fetch synthetic data ──────────────────────────────────
    h4_df  = get_synthetic_candles("4H",  count=100)
    h1_df  = get_synthetic_candles("1H",  count=200)
    m15_df = get_synthetic_candles("15T", count=200)
    m5_df  = get_synthetic_candles("5T",  count=200)

    split    = int(len(h1_df) * 0.60)
    mid      = int(len(h1_df) * 0.80)
    old_h1   = h1_df.iloc[:split]
    prev_h1  = h1_df.iloc[split:mid]
    curr_h1  = h1_df.iloc[mid:]

    older_profile = build_volume_profile(old_h1)
    prev_profile  = build_volume_profile(prev_h1)

    # ── GAP 1 FIX: Regime filter ──────────────────────────────
    section("GAP 1 FIX — Regime Filter (ADX + ATR)")
    regime = evaluate_regime(h4_df)
    print(f"    ADX(14)     : {regime.adx}")
    print(f"    Vol ratio   : {regime.vol_ratio:.2f}x average")
    print(f"    Regime      : {regime.regime}")
    print(f"    Size mult   : {regime.size_multiplier}x")
    print(f"    Min score   : {regime.min_score}")
    for n in regime.notes:
        print(f"    → {n}")

    if regime.regime == "SUPPRESS":
        print("\n  ⛔ REGIME GATE: Signal suppressed — trending + volatile")
        print("     This is what catches BoJ intervention days.\n")
        return

    # ── STAGE 1: AMT Context ──────────────────────────────────
    section("STAGE 1 — AMT Context")
    amt_ctx = evaluate_stage1(h4_df, curr_h1, prev_profile)
    print(f"    Market state : {amt_ctx.market_state}")
    print(f"    Dominance    : {amt_ctx.dominance}")
    print(f"    Migration    : {amt_ctx.migration}")
    print(f"    Profile shape: {amt_ctx.profile.shape if amt_ctx.profile else 'N/A'}")
    print(f"    Open type    : {amt_ctx.open_type}")
    print(f"    Bias         : {amt_ctx.bias}")
    print(f"    Score        : {amt_ctx.score}/35")

    if amt_ctx.market_state == "balanced":
        print("\n  ⏸  Balanced market — no signal today.")
        return

    # ── GAP 2 FIX: Merged profiles ────────────────────────────
    section("GAP 2 FIX — Merged Profile / LVN Detector")
    direction    = "long" if amt_ctx.bias == "long" else "short"
    current_price = curr_h1['close'].iloc[-1]

    merged = analyse_merged_profiles(
        current_profile = amt_ctx.profile,
        prev_profiles   = [older_profile, prev_profile],
        current_price   = current_price,
        direction       = direction
    )

    if merged.has_adjacent_profile:
        print(f"    Adjacent profiles : YES")
        print(f"    LVN corridor      : {merged.lvn_bottom:.3f} – "
              f"{merged.lvn_top:.3f} ({merged.lvn_width_pips:.0f} pips wide)")
        print(f"    Price travels     : {merged.travel_direction}")
        print(f"    Dynamic target    : {merged.adjacent_profile_target:.3f}")
        if merged.composite_poc:
            print(f"    Composite POC     : {merged.composite_poc:.3f}")
    else:
        print(f"    Profiles not adjacent — standard VWAP target applies")
    for n in merged.notes:
        print(f"    → {n}")

    # ── STAGE 2: Hypothesis ───────────────────────────────────
    section("STAGE 2 — Hypothesis (VWAP + Confluence)")
    hypothesis = evaluate_stage2(curr_h1, m15_df, amt_ctx, INSTRUMENT)

    if hypothesis is None:
        print("  ⏸  No confluence zone at current price.")
        print("     Price is in the middle of value area — wait for extremes.")
        print(f"\n     Watch for price at:")
        if amt_ctx.profile:
            print(f"       VAH: {amt_ctx.profile.vah:.3f} (short hypothesis)")
            print(f"       VAL: {amt_ctx.profile.val:.3f} (long hypothesis)")
        return

    # Override TP with merged profile target if available
    if merged.has_adjacent_profile and merged.adjacent_profile_target:
        old_tp2 = hypothesis.tp2
        hypothesis.tp2 = merged.adjacent_profile_target
        print(f"    TP2 updated from {old_tp2:.3f} → "
              f"{merged.adjacent_profile_target:.3f} (merged profile target)")

    print(f"    Direction    : {hypothesis.direction}")
    print(f"    Entry zone   : {hypothesis.entry_low:.3f} – "
          f"{hypothesis.entry_high:.3f}")
    print(f"    Stop loss    : {hypothesis.stop_loss:.3f}")
    print(f"    TP1 (VWAP)   : {hypothesis.tp1:.3f}  "
          f"(R:R {hypothesis.rr_tp1}:1)")
    print(f"    TP2 (target) : {hypothesis.tp2:.3f}  "
          f"(R:R {hypothesis.rr_tp2}:1)")
    print(f"    Confirmed    : "
          f"{'✅ Yes' if hypothesis.confirmed else '⏳ Awaiting M15 candle'}")
    print(f"    Score        : {hypothesis.stage2_score}/35")
    if hypothesis.confluence:
        print(f"    Levels       : "
              f"{', '.join(hypothesis.confluence.levels)}")

    # ── STAGE 3: Order flow ───────────────────────────────────
    section("STAGE 3 — Order Flow (CD + Footprint proxy)")
    of_reading = evaluate_stage3(m15_df, curr_h1, hypothesis)
    print(f"    CD signal    : {of_reading.cd_signal}")
    print(f"    Footprint    : {of_reading.fp_signal}")
    print(f"    Score        : {of_reading.stage3_score}/30")
    print(f"    Suppress     : "
          f"{'⚠️  YES — signal killed' if of_reading.suppress else '✅ No'}")

    if of_reading.suppress:
        print("\n  ⛔ Order flow conflicts with signal direction — suppressed.")
        return

    # ── GAP 4 FIX: TP1 Footprint decision ────────────────────
    section("GAP 4 FIX — TP1 Footprint Decision (Hold vs Exit)")
    tp1_reading = read_footprint_at_tp1(
        m5_df       = m5_df,
        tp1_price   = hypothesis.tp1,
        direction   = direction
    )
    print(f"    Scenario     : {tp1_reading.scenario}")
    print(f"    Decision     : {tp1_reading.decision}")
    print(f"    Buy vol avg  : {tp1_reading.avg_buy_vol:.0f}")
    print(f"    Sell vol avg : {tp1_reading.avg_sell_vol:.0f}")
    print(f"    Confidence   : {tp1_reading.confidence}%")
    for n in tp1_reading.notes:
        print(f"    → {n}")

    # ── Final signal assembly ─────────────────────────────────
    section("FINAL SIGNAL")
    dd_tracker = DrawdownTracker(initial_balance=10_000)
    dd_tracker.update(9_850)

    signal = assemble_final_signal(
        amt_ctx         = amt_ctx,
        hypothesis      = hypothesis,
        of_reading      = of_reading,
        account_balance = dd_tracker.current,
        dd_tracker      = dd_tracker,
        pair            = INSTRUMENT
    )

    # Apply regime size multiplier
    if signal and regime.size_multiplier != 1.0:
        signal.lot_size = round(signal.lot_size * regime.size_multiplier, 2)
        signal.all_notes.append(
            f"Position size adjusted: {regime.size_multiplier}x "
            f"(regime={regime.regime})"
        )

    if signal is None:
        print("  ❌ No signal emitted (score below threshold or filter blocked)\n")
    else:
        # Add TP1 footprint note to signal
        signal.all_notes.append(
            f"TP1 footprint: {tp1_reading.scenario} → {tp1_reading.decision}"
        )
        dispatch_alert(signal)
        print(f"\n  ✅ Signal emitted.\n")

    print(DIVIDER + "\n")


def run_live(account_balance=10_000):
    try:
        from core.data_feed import OandaFeed
        feed = OandaFeed()
    except Exception as e:
        print(f"OANDA connection failed: {e}")
        print("Check your API key in config/settings.py")
        return

    dd_tracker    = DrawdownTracker(initial_balance=account_balance)
    prev_profile  = None
    older_profile = None
    cycle         = 0

    logger.info(f"G7FX Signal Engine v2 started | {INSTRUMENT}")

    while True:
        try:
            cycle += 1
            now = datetime.now(timezone.utc)
            logger.info(f"Cycle {cycle} | {now.strftime('%Y-%m-%d %H:%M UTC')}")

            h4_df  = feed.get_candles("H4",  count=100)
            h1_df  = feed.get_candles("H1",  count=200)
            m15_df = feed.get_candles("M15", count=100)
            m5_df  = feed.get_candles("M5",  count=150)

            balance  = feed.get_account_balance()
            dd_state = dd_tracker.update(balance)

            if not dd_tracker.can_trade():
                logger.warning(f"Trading paused — drawdown {dd_state.drawdown_pct:.2%}")
                time.sleep(900)
                continue

            # Gap 1: Regime gate first
            regime = evaluate_regime(h4_df)
            if regime.regime == "SUPPRESS":
                logger.info("Regime SUPPRESS — skipping cycle")
                time.sleep(900)
                continue

            split   = max(50, len(h1_df) - 100)
            prev_h1 = h1_df.iloc[:split]
            curr_h1 = h1_df.iloc[split:]

            if prev_profile is None:
                prev_profile = build_volume_profile(prev_h1)

            amt_ctx = evaluate_stage1(h4_df, curr_h1, prev_profile)

            # Gap 2: Merged profiles
            direction = "long" if amt_ctx.bias == "long" else "short"
            merged = analyse_merged_profiles(
                amt_ctx.profile,
                [p for p in [older_profile, prev_profile] if p],
                curr_h1['close'].iloc[-1],
                direction
            )

            hypothesis = evaluate_stage2(curr_h1, m15_df, amt_ctx, INSTRUMENT)
            if hypothesis:
                if merged.has_adjacent_profile and merged.adjacent_profile_target:
                    hypothesis.tp2 = merged.adjacent_profile_target

                of_reading = evaluate_stage3(m15_df, curr_h1, hypothesis)

                # Gap 4: TP1 footprint decision
                tp1_reading = read_footprint_at_tp1(
                    m5_df, hypothesis.tp1, direction)

                signal = assemble_final_signal(
                    amt_ctx, hypothesis, of_reading,
                    balance, dd_tracker, INSTRUMENT
                )
                if signal:
                    if regime.size_multiplier != 1.0:
                        signal.lot_size = round(
                            signal.lot_size * regime.size_multiplier, 2)
                    signal.all_notes.append(
                        f"TP1 decision: {tp1_reading.decision}")
                    dispatch_alert(signal)

            # Rotate profiles every 24 cycles (~6h)
            if cycle % 24 == 0:
                older_profile = prev_profile
                prev_profile  = build_volume_profile(h1_df.tail(100))
                logger.info("Profiles rotated")

            time.sleep(900)   # 15 minutes

        except KeyboardInterrupt:
            logger.info("Engine stopped by user")
            break
        except Exception as e:
            logger.error(f"Cycle error: {e}", exc_info=True)
            time.sleep(60)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="G7FX Signal Engine v2")
    parser.add_argument("--demo",    action="store_true",
                        help="Run in demo mode (no API key needed)")
    parser.add_argument("--balance", type=float, default=10_000,
                        help="Starting account balance in USD")
    args = parser.parse_args()

    if args.demo:
        run_demo()
    else:
        run_live(account_balance=args.balance)
