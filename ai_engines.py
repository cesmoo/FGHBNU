# ai_engines.py  ——  v2 Upgraded Algorithms
import numpy as np
import time
import random
from collections import defaultdict
from aiogram.types import KeyboardButton

# ==========================================================
# 🌟 Premium Emojis for AI Messages
# ==========================================================
P_AI_CHECK      = '<tg-emoji emoji-id="6210787138267515780">✅</tg-emoji>'
P_AI_CROSS      = '<tg-emoji emoji-id="6210787138267515780">❌</tg-emoji>'
P_AI_INFO       = '<tg-emoji emoji-id="6210787138267515780">ℹ️</tg-emoji>'
P_AI_HOURGLASS  = '<tg-emoji emoji-id="6210787138267515780">⏳</tg-emoji>'
P_AI_UP         = '<tg-emoji emoji-id="6210787138267515780">⬆️</tg-emoji>'
P_AI_DOWN       = '<tg-emoji emoji-id="5875180111744995604">⬇️</tg-emoji>'
P_AI_LEFT_RIGHT = '<tg-emoji emoji-id="5848119413041431362">↔️</tg-emoji>'
P_AI_SPARKLES   = '<tg-emoji emoji-id="5884289942371401145">✨</tg-emoji>'
P_AI_PATTERN    = '<tg-emoji emoji-id="6210787138267515780">🎯</tg-emoji>'
P_AI_MARTINGALE = '<tg-emoji emoji-id="6210787138267515780">🎲</tg-emoji>'
P_AI_ANTIMARTINGALE = '<tg-emoji emoji-id="5868665489092263539">🔄</tg-emoji>'
P_AI_TREND      = '<tg-emoji emoji-id="6210787138267515780">📊</tg-emoji>'
P_AI_FIBONACCI  = '<tg-emoji emoji-id="5877260593903177342">🔢</tg-emoji>'
P_AI_GOLDEN     = '<tg-emoji emoji-id="5869547610204280761">🎯</tg-emoji>'
P_AI_MOMENTUM   = '<tg-emoji emoji-id="5884248697980608904">📈</tg-emoji>'
P_AI_MONTECARLO = '<tg-emoji emoji-id="5884041323843955199">🎲</tg-emoji>'
P_AI_NEURAL     = '<tg-emoji emoji-id="5875180111744995604">🧬</tg-emoji>'
P_AI_REVERSAL   = '<tg-emoji emoji-id="5890997763331591703">⚡</tg-emoji>'
P_AI_WAVE       = '<tg-emoji emoji-id="5967574255670399788">🌊</tg-emoji>'
P_AI_CHAOS      = '<tg-emoji emoji-id="5877443460725739250">🎪</tg-emoji>'
P_AI_STAR       = '<tg-emoji emoji-id="5807868868886009920">⭐</tg-emoji>'
P_AI_ROBOT      = '<tg-emoji emoji-id="5877652234091891383">🤖</tg-emoji>'
P_AI_BRAIN      = '<tg-emoji emoji-id="5868656545634689320">🧠</tg-emoji>'

class AIEmoji:
    CHECK = "✅"; CROSS = "❌"; INFO = "ℹ️"; HOURGLASS = "⏳"
    UP = "⬆️"; DOWN = "⬇️"; LEFT_RIGHT = "↔️"; SPARKLES = "✨"
    PATTERN = "🎯"; MARTINGALE = "🎲"; ANTIMARTINGALE = "🔄"
    TREND = "📊"; FIBONACCI = "🔢"; GOLDEN = "🎯"; MOMENTUM = "📈"
    MONTECARLO = "🎲"; NEURAL = "🧬"; REVERSAL = "⚡"; WAVE = "🌊"; CHAOS = "🎪"
    CHART_UP = "📈"; CHART_DOWN = "📉"; STAR = "⭐"
    ROBOT = "🤖"; BRAIN = "🧠"

# ==========================================================
# 🎨 AI Mode Emoji IDs for Reply Keyboard
# ==========================================================
AI_MODE_EMOJIS = {
    "Pattern AI":        "6114102463747332294",
    "Martingale AI":     "6113995669385515849",
    "Anti-Martingale AI":"6210747139237088236",
    "Trend Following":   "5431577498364158238",
    "Fibonacci AI":      "5884290437459480896",
    "Golden Ratio":      "6114102463747332294",
    "Momentum AI":       "5269460053651366623",
    "Monte Carlo":       "6113995669385515849",
    "Neural Pattern":    "5212936673423274058",
    "Quick Reversal":    "6210787138267515780",
    "Wave Analysis":     "5431685735835011215",
    "Chaos Theory":      "6251379582851614396",
    "Ensemble AI":       "6300674206703027915",
    "Bayesian AI":       "5366380461746563803",
    "Markov Chain":      "6210879046272682741",
    "ML Style AI":       "6190369920304289234",
    "Circle Rnd":        "5226711870492126219",
    "Custom Pattern":    "6300853298249336390",
}

# ==========================================================
# 🔧 Shared Utility Helpers
# ==========================================================
def _to_binary(history):
    """BIG=1, SMALL=0 numeric list"""
    return [1 if x == "BIG" else 0 for x in history]

def _label(pred):
    burmese = "အကြီး" if pred == "BIG" else "အသေး"
    dot     = "🔴"    if pred == "BIG" else "🟢"
    return burmese, dot

def _entropy(seg):
    n = len(seg)
    if n == 0: return 0.0
    p = seg.count("BIG") / n
    q = 1 - p
    e = 0.0
    if p > 0: e -= p * np.log2(p)
    if q > 0: e -= q * np.log2(q)
    return e

def _streak(history):
    """Return (current_side, streak_length) from the end of history."""
    if not history: return None, 0
    side, count = history[-1], 1
    for r in reversed(history[:-1]):
        if r == side: count += 1
        else: break
    return side, count

def _ema_ratio(history, span):
    """Exponential-weighted BIG ratio over last `span` items."""
    seg = history[-span:]
    if not seg: return 0.5
    alpha = 2 / (len(seg) + 1)
    w_sum = w_big = 0.0
    weight = 1.0
    for r in reversed(seg):
        w_big  += weight * (1 if r == "BIG" else 0)
        w_sum  += weight
        weight *= (1 - alpha)
    return w_big / w_sum if w_sum else 0.5


# ============================================================
# 1. Pattern AI  —  v2: 25 patterns, recency-weighted, 30-item lookback
# ============================================================
def detect_active_pattern(history_list):
    if len(history_list) < 4: return None, None

    PATTERNS = [
        # 2-item
        ("BB",   ["BIG","BIG"],                            "SMALL"),
        ("SS",   ["SMALL","SMALL"],                        "BIG"),
        ("BS",   ["BIG","SMALL"],                          "BIG"),
        ("SB",   ["SMALL","BIG"],                          "SMALL"),
        # 3-item
        ("BBB",  ["BIG","BIG","BIG"],                      "BIG"),
        ("SSS",  ["SMALL","SMALL","SMALL"],                "SMALL"),
        ("BBS",  ["BIG","BIG","SMALL"],                    "BIG"),
        ("BSS",  ["BIG","SMALL","SMALL"],                  "BIG"),
        ("SBB",  ["SMALL","BIG","BIG"],                    "SMALL"),
        ("SSB",  ["SMALL","SMALL","BIG"],                  "SMALL"),
        ("BSB",  ["BIG","SMALL","BIG"],                    "BIG"),
        ("SBS",  ["SMALL","BIG","SMALL"],                  "SMALL"),
        # 4-item
        ("BBSS", ["BIG","BIG","SMALL","SMALL"],            "BIG"),
        ("SSBB", ["SMALL","SMALL","BIG","BIG"],            "SMALL"),
        ("BSBS", ["BIG","SMALL","BIG","SMALL"],            "BIG"),
        ("SBSB", ["SMALL","BIG","SMALL","BIG"],            "SMALL"),
        ("BBBS", ["BIG","BIG","BIG","SMALL"],              "BIG"),
        ("SSSB", ["SMALL","SMALL","SMALL","BIG"],          "SMALL"),
        ("BSSS", ["BIG","SMALL","SMALL","SMALL"],          "BIG"),
        ("SBBB", ["SMALL","BIG","BIG","BIG"],              "SMALL"),
        # 5-item
        ("BSSBS",["BIG","SMALL","SMALL","BIG","SMALL"],    "BIG"),
        ("SBBSB",["SMALL","BIG","BIG","SMALL","BIG"],      "SMALL"),
        ("BSBSB",["BIG","SMALL","BIG","SMALL","BIG"],      "SMALL"),
        ("SBSBS",["SMALL","BIG","SMALL","BIG","SMALL"],    "BIG"),
        ("BBBSS",["BIG","BIG","BIG","SMALL","SMALL"],      "BIG"),
        ("SSSBB",["SMALL","SMALL","SMALL","BIG","BIG"],    "SMALL"),
    ]

    recent = history_list[-30:]
    best_pattern, best_score, best_next = None, 0, None

    for name, seq, nxt in PATTERNS:
        plen = len(seq)
        if len(recent) < plen: continue
        # Recency-weighted scoring: later matches score higher
        score = 0.0
        for i in range(len(recent) - plen + 1):
            if recent[i:i+plen] == seq:
                recency_weight = 1.0 + (i / max(len(recent), 1))   # later = heavier
                score += recency_weight * plen
        if score > best_score:
            best_score, best_pattern, best_next = score, name, nxt

    # Require minimum evidence
    if best_score < len(best_next or "") * 1.5 if best_next else True:
        if best_score < 2.0:
            return None, None
    return best_pattern, best_next

def pattern_predict(history_docs):
    if len(history_docs) < 8:
        return "BIG", f"{P_AI_PATTERN} BIG (အကြီး) 🔴", 55.0, f"{P_AI_HOURGLASS} Pattern: Data စုဆောင်းဆဲ..."
    docs = list(reversed(history_docs))
    all_history = [d.get('size', 'BIG') for d in docs]
    active_pattern, next_pred = detect_active_pattern(all_history)
    if active_pattern and next_pred:
        burmese, dot = _label(next_pred)
        conf = min(60 + len(active_pattern) * 3, 82)
        return next_pred, f"{P_AI_PATTERN} {next_pred} ({burmese}) {dot}", conf, \
               f"{P_AI_PATTERN} Pattern: {active_pattern} → {next_pred}"
    b = all_history[-20:].count("BIG"); s = 20 - b
    pred = "BIG" if b >= s else "SMALL"
    burmese, dot = _label(pred)
    return pred, f"{P_AI_PATTERN} {pred} ({burmese}) {dot}", 55.0, \
           f"{P_AI_INFO} Freq BIG:{b} SMALL:{s}"


# ============================================================
# 2. Martingale AI  —  v2: multi-window contrarian with weighted consensus
# ============================================================
def martingale_predict(history_docs):
    if len(history_docs) < 5:
        return "BIG", f"{P_AI_MARTINGALE} BIG (အကြီး) 🔴", 60.0, f"{P_AI_HOURGLASS} Martingale: Data စုဆောင်းဆဲ..."
    docs = list(reversed(history_docs))
    all_history = [d.get('size', 'BIG') for d in docs]

    windows   = [(5, 1.0), (10, 1.5), (20, 2.0)]
    big_score = small_score = 0.0

    for win, w in windows:
        seg = all_history[-win:]
        if len(seg) < win // 2: continue
        big_cnt = seg.count("BIG")
        if big_cnt > len(seg) / 2:
            small_score += w          # contrarian: BIG dominant → bet SMALL
        elif big_cnt < len(seg) / 2:
            big_score   += w

    # Streak boost: if last 3 are same, contrarian is stronger
    side, streak = _streak(all_history)
    if streak >= 3:
        if side == "BIG":   small_score += 1.5
        else:               big_score   += 1.5

    total = big_score + small_score
    if total == 0: total = 1
    if big_score > small_score:
        conf = min(55 + (big_score / total) * 30, 82)
        return "BIG", f"{P_AI_MARTINGALE} BIG (အကြီး) 🔴", conf, \
               f"{P_AI_MARTINGALE} Multi-Win Contrarian → BIG ({conf:.0f}%)"
    else:
        conf = min(55 + (small_score / total) * 30, 82)
        return "SMALL", f"{P_AI_MARTINGALE} SMALL (အသေး) 🟢", conf, \
               f"{P_AI_MARTINGALE} Multi-Win Contrarian → SMALL ({conf:.0f}%)"


# ============================================================
# 3. Anti-Martingale AI  —  v2: full-history streak + exponential confidence
# ============================================================
def anti_martingale_predict(history_docs):
    if len(history_docs) < 5:
        return "BIG", f"{P_AI_ANTIMARTINGALE} BIG (အကြီး) 🔴", 60.0, f"{P_AI_HOURGLASS} Anti-Martingale: Data စုဆောင်းဆဲ..."
    docs = list(reversed(history_docs))
    all_history = [d.get('size', 'BIG') for d in docs]
    side, streak = _streak(all_history)

    if streak >= 2:
        # Exponential confidence: 65 + 5*(streak-1), capped at 84
        conf = min(65 + 5 * (streak - 1), 84)
        burmese, dot = _label(side)
        return side, f"{P_AI_ANTIMARTINGALE} {side} ({burmese}) {dot}", conf, \
               f"{P_AI_ANTIMARTINGALE} Streak ×{streak} → Follow"
    else:
        # No streak: use short-window trend
        recent = all_history[-6:]
        big_r  = recent.count("BIG") / len(recent)
        pred   = "BIG" if big_r >= 0.5 else "SMALL"
        burmese, dot = _label(pred)
        return pred, f"{P_AI_ANTIMARTINGALE} {pred} ({burmese}) {dot}", 60.0, \
               f"{P_AI_ANTIMARTINGALE} No streak → Short trend"


# ============================================================
# 4. Trend Following  —  v2: EMA-style 3-timeframe with signal strength
# ============================================================
def trend_following_predict(history_docs):
    if len(history_docs) < 8:
        return "BIG", f"{P_AI_TREND} BIG (အကြီး) 🔴", 58.0, f"{P_AI_HOURGLASS} Trend: Data စုဆောင်းဆဲ..."
    docs = list(reversed(history_docs))
    all_history = [d.get('size', 'BIG') for d in docs]

    spans   = [3, 7, 15]
    ema_vals = [_ema_ratio(all_history, s) for s in spans]
    # Signal: short > mid > long  →  BIG uptrend
    big_signals = small_signals = 0
    for i in range(len(ema_vals) - 1):
        if   ema_vals[i] > ema_vals[i+1] + 0.05: big_signals   += 1
        elif ema_vals[i] < ema_vals[i+1] - 0.05: small_signals += 1

    slope = ema_vals[0] - ema_vals[-1]   # short EMA minus long EMA

    if big_signals >= 2 or (big_signals == 1 and slope > 0.1):
        conf = min(62 + big_signals * 8 + abs(slope) * 40, 83)
        return "BIG",   f"{P_AI_TREND} BIG (အကြီး) 🔴",   conf, \
               f"{P_AI_TREND} EMA↑ {ema_vals[0]*100:.0f}%→{ema_vals[-1]*100:.0f}%"
    elif small_signals >= 2 or (small_signals == 1 and slope < -0.1):
        conf = min(62 + small_signals * 8 + abs(slope) * 40, 83)
        return "SMALL", f"{P_AI_TREND} SMALL (အသေး) 🟢", conf, \
               f"{P_AI_TREND} EMA↓ {ema_vals[0]*100:.0f}%→{ema_vals[-1]*100:.0f}%"
    else:
        last = all_history[-1]; burmese, dot = _label(last)
        return last, f"{P_AI_TREND} {last} ({burmese}) {dot}", 58.0, \
               f"{P_AI_TREND} Sideways ({ema_vals[0]*100:.0f}%)"


# ============================================================
# 5. Fibonacci AI  —  v2: 8 levels (1-55), confidence-weighted voting
# ============================================================
def fibonacci_predict(history_docs):
    if len(history_docs) < 10:
        return "BIG", f"{P_AI_FIBONACCI} BIG (အကြီး) 🔴", 55.0, f"{P_AI_HOURGLASS} Fibonacci: Data စုဆောင်းဆဲ..."
    docs = list(reversed(history_docs))
    all_history = [d.get('size', 'BIG') for d in docs]

    fib_levels = [2, 3, 5, 8, 13, 21, 34, 55]
    big_w = small_w = 0.0

    for idx, level in enumerate(fib_levels):
        if len(all_history) < level: continue
        seg     = all_history[-level:]
        big_pct = seg.count("BIG") / level
        weight  = 1.0 / (idx + 1)      # shorter levels = higher weight (more recent signal)

        if big_pct > 0.618:   small_w += weight   # overbought → SMALL
        elif big_pct < 0.382: big_w   += weight   # oversold   → BIG
        else:
            # Neutral zone: follow trend inside zone
            mid_trend = all_history[-min(level//2, len(all_history)):].count("BIG") / min(level//2, len(all_history))
            if mid_trend > 0.5: big_w   += weight * 0.5
            else:               small_w += weight * 0.5

    total = big_w + small_w
    if total == 0: total = 1
    if big_w >= small_w:
        conf = min(58 + (big_w / total) * 28, 84)
        return "BIG",   f"{P_AI_FIBONACCI} BIG (အကြီး) 🔴",   conf, \
               f"{P_AI_FIBONACCI} Fib8 → BIG ({conf:.0f}%)"
    else:
        conf = min(58 + (small_w / total) * 28, 84)
        return "SMALL", f"{P_AI_FIBONACCI} SMALL (အသေး) 🟢", conf, \
               f"{P_AI_FIBONACCI} Fib8 → SMALL ({conf:.0f}%)"


# ============================================================
# 6. Golden Ratio  —  v2: 3-scale consensus + trend slope confirmation
# ============================================================
def golden_ratio_predict(history_docs):
    if len(history_docs) < 12:
        return "BIG", f"{P_AI_GOLDEN} BIG (အကြီး) 🔴", 55.0, f"{P_AI_HOURGLASS} Golden Ratio: Data စုဆောင်းဆဲ..."
    docs = list(reversed(history_docs))
    all_history = [d.get('size', 'BIG') for d in docs]

    lookbacks = [8, 13, 21]
    votes_big = votes_small = 0

    for lb in lookbacks:
        seg = all_history[-min(lb, len(all_history)):]
        r   = seg.count("BIG") / len(seg)
        if   r > 0.618: votes_small += 1
        elif r < 0.382: votes_big   += 1
        # neutral: no vote

    # Slope: 5-item vs 13-item EMA
    slope = _ema_ratio(all_history, 5) - _ema_ratio(all_history, 13)

    if votes_big > votes_small or (votes_big == votes_small and slope > 0.05):
        conf = min(60 + votes_big * 8 + abs(slope) * 20, 84)
        return "BIG",   f"{P_AI_GOLDEN} BIG (အကြီး) 🔴",   conf, \
               f"{P_AI_GOLDEN} φ-Scale {votes_big}:Oversold {P_AI_UP}"
    elif votes_small > votes_big or (votes_big == votes_small and slope < -0.05):
        conf = min(60 + votes_small * 8 + abs(slope) * 20, 84)
        return "SMALL", f"{P_AI_GOLDEN} SMALL (အသေး) 🟢", conf, \
               f"{P_AI_GOLDEN} φ-Scale {votes_small}:Overbought {P_AI_DOWN}"
    else:
        last = all_history[-1]; burmese, dot = _label(last)
        r21  = all_history[-21:].count("BIG") / 21
        return last, f"{P_AI_GOLDEN} {last} ({burmese}) {dot}", 62.0, \
               f"{P_AI_GOLDEN} φ-Zone {r21*100:.1f}% (Neutral)"


# ============================================================
# 7. Momentum AI  —  v2: exponential weights over 10 items + acceleration
# ============================================================
def momentum_predict(history_docs):
    if len(history_docs) < 6:
        return "BIG", f"{P_AI_MOMENTUM} BIG (အကြီး) 🔴", 55.0, f"{P_AI_HOURGLASS} Momentum: Data စုဆောင်းဆဲ..."
    docs = list(reversed(history_docs))
    all_history = [d.get('size', 'BIG') for d in docs]

    # Exponential weights: most recent has highest weight
    window = all_history[-10:]
    n      = len(window)
    alpha  = 0.3
    score  = 0.0
    w      = 1.0
    for r in reversed(window):
        score += w * (1 if r == "BIG" else -1)
        w     *= (1 - alpha)

    # Acceleration: compare first-half vs second-half momentum
    if n >= 6:
        half = n // 2
        m1   = sum(1 if r == "BIG" else -1 for r in window[:half])
        m2   = sum(1 if r == "BIG" else -1 for r in window[half:])
        accel = m2 - m1       # positive = accelerating BIG
    else:
        accel = 0

    total_signal = score + accel * 0.3
    threshold    = 1.0

    if total_signal > threshold:
        conf = min(58 + abs(total_signal) * 5, 85)
        return "BIG",   f"{P_AI_MOMENTUM} BIG (အကြီး) 🔴",   conf, \
               f"{P_AI_MOMENTUM} Momentum +{total_signal:.2f} {P_AI_UP}"
    elif total_signal < -threshold:
        conf = min(58 + abs(total_signal) * 5, 85)
        return "SMALL", f"{P_AI_MOMENTUM} SMALL (အသေး) 🟢", conf, \
               f"{P_AI_MOMENTUM} Momentum {total_signal:.2f} {P_AI_DOWN}"
    else:
        last = all_history[-1]; burmese, dot = _label(last)
        return last, f"{P_AI_MOMENTUM} {last} ({burmese}) {dot}", 57.0, \
               f"{P_AI_MOMENTUM} Weak signal ({total_signal:.2f})"


# ============================================================
# 8. Monte Carlo  —  v2: 5000 sims, recency-weighted probability
# ============================================================
def monte_carlo_predict(history_docs):
    if len(history_docs) < 15:
        return "BIG", f"{P_AI_MONTECARLO} BIG (အကြီး) 🔴", 55.0, f"{P_AI_HOURGLASS} Monte Carlo: Data စုဆောင်းဆဲ..."
    docs = list(reversed(history_docs))
    all_history = [d.get('size', 'BIG') for d in docs]

    # Recency-weighted BIG probability (half-life = 10 rounds)
    half_life  = 10.0
    weights    = [np.exp(-np.log(2) * i / half_life) for i in range(len(all_history))][::-1]
    w_big      = sum(w for w, r in zip(weights, all_history) if r == "BIG")
    w_total    = sum(weights)
    big_prob   = w_big / w_total if w_total > 0 else 0.5

    # Run 5000 simulations
    np.random.seed(int(time.time()) % (2**31 - 1))
    sims     = np.random.random(5000)
    big_wins = int(np.sum(sims < big_prob))

    if big_wins > 2500:
        prob = big_wins / 5000 * 100
        return "BIG",   f"{P_AI_MONTECARLO} BIG (အကြီး) 🔴",   min(prob, 82), \
               f"{P_AI_MONTECARLO} 5K-Sim BIG {prob:.1f}% (p={big_prob:.2f})"
    else:
        prob = (5000 - big_wins) / 5000 * 100
        return "SMALL", f"{P_AI_MONTECARLO} SMALL (အသေး) 🟢", min(prob, 82), \
               f"{P_AI_MONTECARLO} 5K-Sim SMALL {prob:.1f}% (p={1-big_prob:.2f})"


# ============================================================
# 9. Neural Pattern  —  v2: multi-window k-NN (3,5,7) with distance weighting
# ============================================================
def neural_pattern_predict(history_docs):
    if len(history_docs) < 10:
        return "BIG", f"{P_AI_NEURAL} BIG (အကြီး) 🔴", 55.0, f"{P_AI_HOURGLASS} Neural: Data စုဆောင်းဆဲ..."
    docs = list(reversed(history_docs))
    all_history = [d.get('size', 'BIG') for d in docs]

    big_score = small_score = 0.0

    for win in [3, 5, 7]:
        if len(all_history) < win + 3: continue
        query = all_history[-win:]
        matches_big = matches_small = 0.0
        for i in range(len(all_history) - win):
            candidate = all_history[i:i+win]
            # Hamming similarity
            match_count = sum(a == b for a, b in zip(query, candidate))
            if match_count < win - 1: continue          # at least (win-1) match
            weight = match_count / win                  # distance weight
            nxt    = all_history[i + win]
            if   nxt == "BIG":   matches_big   += weight
            else:                matches_small  += weight
        total_w = matches_big + matches_small
        if total_w > 0:
            w_factor = 1.0 / win                       # shorter window = higher weight
            big_score   += (matches_big   / total_w) * w_factor
            small_score += (matches_small / total_w) * w_factor

    total = big_score + small_score
    if total > 0:
        if big_score > small_score:
            conf = min(58 + (big_score / total) * 30, 86)
            return "BIG",   f"{P_AI_NEURAL} BIG (အကြီး) 🔴",   conf, \
                   f"{P_AI_NEURAL} kNN-3W BIG {big_score/total*100:.0f}%"
        else:
            conf = min(58 + (small_score / total) * 30, 86)
            return "SMALL", f"{P_AI_NEURAL} SMALL (အသေး) 🟢", conf, \
                   f"{P_AI_NEURAL} kNN-3W SMALL {small_score/total*100:.0f}%"
    return "BIG", f"{P_AI_NEURAL} BIG (အကြီး) 🔴", 55.0, f"{P_AI_NEURAL} No match found"


# ============================================================
# 10. Quick Reversal  —  v2: multi-window alternation with streak context
# ============================================================
def quick_reversal_predict(history_docs):
    if len(history_docs) < 5:
        return "BIG", f"{P_AI_REVERSAL} BIG (အကြီး) 🔴", 55.0, f"{P_AI_HOURGLASS} Reversal: Data စုဆောင်းဆဲ..."
    docs = list(reversed(history_docs))
    all_history = [d.get('size', 'BIG') for d in docs]

    alt_scores = []
    for win in [4, 6, 8, 10]:
        seg = all_history[-win:]
        if len(seg) < win: continue
        alts      = sum(1 for i in range(1, len(seg)) if seg[i] != seg[i-1])
        alt_rate  = alts / (len(seg) - 1)
        alt_scores.append(alt_rate)

    avg_alt = sum(alt_scores) / len(alt_scores) if alt_scores else 0
    side, streak = _streak(all_history)

    if avg_alt > 0.70:                            # Strong alternation mode
        predicted = "SMALL" if side == "BIG" else "BIG"
        conf      = min(60 + avg_alt * 25, 84)
        burmese, dot = _label(predicted)
        return predicted, f"{P_AI_REVERSAL} {predicted} ({burmese}) {dot}", conf, \
               f"{P_AI_REVERSAL} Alt {avg_alt*100:.0f}% → Reverse"
    elif streak >= 3 and avg_alt < 0.40:          # Streak mode: follow streak
        conf = min(62 + streak * 4, 80)
        burmese, dot = _label(side)
        return side, f"{P_AI_REVERSAL} {side} ({burmese}) {dot}", conf, \
               f"{P_AI_REVERSAL} Streak ×{streak} (Low alt {avg_alt*100:.0f}%)"
    else:
        last = all_history[-1]; burmese, dot = _label(last)
        return last, f"{P_AI_REVERSAL} {last} ({burmese}) {dot}", 58.0, \
               f"{P_AI_REVERSAL} Neutral alt {avg_alt*100:.0f}%"


# ============================================================
# 11. Wave Analysis  —  v2: impulse/correction with depth & momentum check
# ============================================================
def wave_analysis_predict(history_docs):
    if len(history_docs) < 8:
        return "BIG", f"{P_AI_WAVE} BIG (အကြီး) 🔴", 55.0, f"{P_AI_HOURGLASS} Wave: Data စုဆောင်းဆဲ..."
    docs = list(reversed(history_docs))
    all_history = [d.get('size', 'BIG') for d in docs]

    # Build wave list
    waves = []
    current, count = all_history[0], 1
    for r in all_history[1:]:
        if r == current: count += 1
        else: waves.append((current, count)); current = r; count = 1
    waves.append((current, count))

    if len(waves) < 3:
        last = all_history[-1]; burmese, dot = _label(last)
        return last, f"{P_AI_WAVE} {last} ({burmese}) {dot}", 56.0, f"{P_AI_WAVE} Building waves..."

    last_w  = waves[-1]    # (side, len)
    prev_w  = waves[-2]
    prev2_w = waves[-3] if len(waves) >= 3 else None

    # Impulse: long wave still in progress → continue
    if last_w[1] >= 3:
        momentum_confirm = _ema_ratio(all_history, 5) > 0.5 if last_w[0] == "BIG" else _ema_ratio(all_history, 5) < 0.5
        conf = min(65 + last_w[1] * 3 + (5 if momentum_confirm else 0), 84)
        burmese, dot = _label(last_w[0])
        return last_w[0], f"{P_AI_WAVE} {last_w[0]} ({burmese}) {dot}", conf, \
               f"{P_AI_WAVE} Impulse W:{last_w[1]} → Continue"

    # Correction: short last wave → reversal likely
    if last_w[1] <= 2 and prev_w[1] >= 3:
        predicted = "SMALL" if last_w[0] == "BIG" else "BIG"
        # Depth check: correction depth matches prev wave
        ratio = last_w[1] / prev_w[1]
        conf  = min(68 + (1 - ratio) * 20, 83)
        burmese, dot = _label(predicted)
        return predicted, f"{P_AI_WAVE} {predicted} ({burmese}) {dot}", conf, \
               f"{P_AI_WAVE} Correction ({ratio:.0%}) → {predicted}"

    # Default: follow last wave
    last = all_history[-1]; burmese, dot = _label(last)
    return last, f"{P_AI_WAVE} {last} ({burmese}) {dot}", 58.0, \
           f"{P_AI_WAVE} W{len(waves)} tracking..."


# ============================================================
# 12. Chaos Theory  —  v2: multi-scale entropy + run-length analysis
# ============================================================
def chaos_theory_predict(history_docs):
    if len(history_docs) < 10:
        return "BIG", f"{P_AI_CHAOS} BIG (အကြီး) 🔴", 55.0, f"{P_AI_HOURGLASS} Chaos: Data စုဆောင်းဆဲ..."
    docs = list(reversed(history_docs))
    all_history = [d.get('size', 'BIG') for d in docs]

    scales  = [3, 5, 8, 13, 20]
    entropies = [_entropy(all_history[-s:]) for s in scales if len(all_history) >= s]

    # Entropy trend: increasing = more random (contrarian), decreasing = more ordered (follow)
    if len(entropies) >= 3:
        e_trend = entropies[-1] - entropies[0]          # positive = getting more chaotic
    else:
        e_trend = 0

    # Run-length analysis: average consecutive-same length
    run_lengths = []
    current, cnt = all_history[-20:][0], 1
    for r in all_history[-20:][1:]:
        if r == current: cnt += 1
        else: run_lengths.append(cnt); current = r; cnt = 1
    run_lengths.append(cnt)
    avg_run = sum(run_lengths) / len(run_lengths) if run_lengths else 1.5

    # Low entropy + low avg run → alternating chaos → reversal
    e_now  = entropies[-1] if entropies else 1.0
    side, streak = _streak(all_history)

    if e_now > 0.95 and avg_run < 1.5:          # Near max entropy + short runs
        predicted = "SMALL" if side == "BIG" else "BIG"
        burmese, dot = _label(predicted)
        return predicted, f"{P_AI_CHAOS} {predicted} ({burmese}) {dot}", 67.0, \
               f"{P_AI_CHAOS} MaxEntropy+AltMode → {predicted}"

    elif e_now < 0.6 and avg_run >= 2.5:         # Low entropy + long runs → momentum
        burmese, dot = _label(side)
        return side, f"{P_AI_CHAOS} {side} ({burmese}) {dot}", 70.0, \
               f"{P_AI_CHAOS} OrderedMode run={avg_run:.1f} → {side}"

    elif e_trend > 0.2:                           # Getting more chaotic → contrarian
        predicted = "SMALL" if side == "BIG" else "BIG"
        burmese, dot = _label(predicted)
        return predicted, f"{P_AI_CHAOS} {predicted} ({burmese}) {dot}", 63.0, \
               f"{P_AI_CHAOS} Entropy↑ {e_now:.2f} → {predicted}"

    else:
        majority = "BIG" if all_history[-8:].count("BIG") > 4 else "SMALL"
        burmese, dot = _label(majority)
        return majority, f"{P_AI_CHAOS} {majority} ({burmese}) {dot}", 58.0, \
               f"{P_AI_CHAOS} Stable H={e_now:.2f}"


# ============================================================
# 13. Ensemble AI  —  v2: confidence-weighted voting (not equal votes)
# ============================================================
def ensemble_predict(history_docs):
    if len(history_docs) < 10:
        return "BIG", f"{P_AI_ROBOT} BIG (အကြီး) 🔴", 55.0, f"{P_AI_HOURGLASS} Ensemble: Data စုဆောင်းဆဲ..."

    predictors = [
        pattern_predict, martingale_predict, anti_martingale_predict,
        trend_following_predict, fibonacci_predict, golden_ratio_predict,
        momentum_predict, monte_carlo_predict, neural_pattern_predict,
        quick_reversal_predict, wave_analysis_predict, chaos_theory_predict,
        bayesian_predict, markov_chain_predict, ml_style_predict,
    ]
    big_w = small_w = 0.0
    big_n = small_n = 0

    for predictor in predictors:
        try:
            size, _, prob, _ = predictor(history_docs)
            weight = max(prob - 50, 0) / 50    # confidence above 50% as weight
            if size == "BIG":
                big_w   += weight; big_n   += 1
            else:
                small_w += weight; small_n += 1
        except:
            pass

    total_w = big_w + small_w
    if total_w == 0: total_w = 1

    if big_w >= small_w:
        conf = min(58 + (big_w / total_w) * 30, 90)
        return "BIG",   f"{P_AI_ROBOT} BIG (အကြီး) 🔴",   conf, \
               f"{P_AI_ROBOT} Ensemble {big_n}AI→BIG W:{big_w:.1f}:{small_w:.1f}"
    else:
        conf = min(58 + (small_w / total_w) * 30, 90)
        return "SMALL", f"{P_AI_ROBOT} SMALL (အသေး) 🟢", conf, \
               f"{P_AI_ROBOT} Ensemble {small_n}AI→SMALL W:{small_w:.1f}:{big_w:.1f}"


# ============================================================
# 14. Bayesian AI  —  v2: 2nd-order P(next | prev2, prev1) with 1st-order fallback
# ============================================================
def bayesian_predict(history_docs):
    if len(history_docs) < 10:
        return "BIG", f"{P_AI_BRAIN} BIG (အကြီး) 🔴", 55.0, f"{P_AI_HOURGLASS} Bayesian: Data စုဆောင်းဆဲ..."
    docs = list(reversed(history_docs))
    all_history = [d.get('size', 'BIG') for d in docs]
    recent = all_history[-30:]

    # 2nd-order counts
    counts2 = defaultdict(lambda: {"BIG": 0, "SMALL": 0})
    for i in range(2, len(recent)):
        state = (recent[i-2], recent[i-1])
        counts2[state][recent[i]] += 1

    state2 = (recent[-2], recent[-1])
    c2 = counts2.get(state2, {"BIG": 0, "SMALL": 0})
    total2 = c2["BIG"] + c2["SMALL"]

    if total2 >= 3:                              # enough 2nd-order evidence
        p_big = c2["BIG"] / total2
        pred  = "BIG" if p_big >= 0.5 else "SMALL"
        conf  = min(55 + abs(p_big - 0.5) * 60 + 10, 84)
        burmese, dot = _label(pred)
        return pred, f"{P_AI_BRAIN} {pred} ({burmese}) {dot}", conf, \
               f"{P_AI_BRAIN} 2nd-Order P={p_big*100:.0f}% (n={total2})"

    # Fallback: 1st-order
    counts1 = defaultdict(lambda: {"BIG": 0, "SMALL": 0})
    for i in range(1, len(recent)):
        counts1[recent[i-1]][recent[i]] += 1

    state1 = recent[-1]
    c1     = counts1.get(state1, {"BIG": 0, "SMALL": 0})
    total1 = c1["BIG"] + c1["SMALL"]

    if total1 > 0:
        p_big = c1["BIG"] / total1
        pred  = "BIG" if p_big >= 0.5 else "SMALL"
        conf  = min(55 + abs(p_big - 0.5) * 50, 78)
        burmese, dot = _label(pred)
        return pred, f"{P_AI_BRAIN} {pred} ({burmese}) {dot}", conf, \
               f"{P_AI_BRAIN} 1st-Order P(·|{state1})={p_big*100:.0f}%"

    last = all_history[-1]; burmese, dot = _label(last)
    return last, f"{P_AI_BRAIN} {last} ({burmese}) {dot}", 55.0, \
           f"{P_AI_BRAIN} Bayesian: Insufficient data"


# ============================================================
# 15. Markov Chain  —  v2: 3rd-order → 2nd → 1st hierarchical fallback
# ============================================================
def markov_chain_predict(history_docs):
    if len(history_docs) < 8:
        return "BIG", f"{P_AI_INFO} BIG (အကြီး) 🔴", 55.0, f"{P_AI_HOURGLASS} Markov: Data စုဆောင်းဆဲ..."
    docs = list(reversed(history_docs))
    all_history = [d.get('size', 'BIG') for d in docs]

    # Try 3rd-order first, then 2nd, then 1st
    for order in [3, 2, 1]:
        trans = defaultdict(lambda: {"BIG": 0, "SMALL": 0})
        for i in range(order, len(all_history)):
            state = tuple(all_history[i-order:i])
            trans[state][all_history[i]] += 1

        current = tuple(all_history[-order:])
        c       = trans.get(current, {"BIG": 0, "SMALL": 0})
        total   = c["BIG"] + c["SMALL"]

        min_samples = max(2, 4 - order)         # higher order needs fewer absolute samples
        if total >= min_samples:
            p_big = c["BIG"] / total
            pred  = "BIG" if p_big >= 0.5 else "SMALL"
            conf  = min(55 + abs(p_big - 0.5) * 55 + order * 3, 85)
            burmese, dot = _label(pred)
            return pred, f"{P_AI_INFO} {pred} ({burmese}) {dot}", conf, \
                   f"{P_AI_INFO} Markov-{order}rd {p_big*100:.0f}% (n={total})"

    last = all_history[-1]; burmese, dot = _label(last)
    return last, f"{P_AI_INFO} {last} ({burmese}) {dot}", 56.0, \
           f"{P_AI_INFO} Markov: sparse transitions"


# ============================================================
# 16. ML Style AI  —  v2: 8 features + optimized weights
# ============================================================
def ml_style_predict(history_docs):
    if len(history_docs) < 12:
        return "BIG", f"{P_AI_SPARKLES} BIG (အကြီး) 🔴", 55.0, f"{P_AI_HOURGLASS} ML Style: Data စုဆောင်းဆဲ..."
    docs = list(reversed(history_docs))
    all_history = [d.get('size', 'BIG') for d in docs]

    # Feature engineering
    r3  = all_history[-3:].count("BIG")  / 3
    r5  = all_history[-5:].count("BIG")  / 5
    r10 = all_history[-10:].count("BIG") / 10
    r20 = all_history[-min(20, len(all_history)):].count("BIG") / min(20, len(all_history))

    trend    = r5 - r10                          # short vs mid trend
    slope2   = r3 - r5                           # acceleration

    _, streak = _streak(all_history)
    streak_feat = streak / 8.0                   # normalize streak (max ~8)

    alt_4 = sum(1 for i in range(1, 4) if all_history[-4:][i] != all_history[-4:][i-1]) / 3
    entropy_feat = _entropy(all_history[-8:])    # 0=ordered, 1=random

    # Weighted feature sum (positive → BIG, negative → SMALL)
    score = (
        (r3  - 0.5) * 0.30 +
        (r5  - 0.5) * 0.22 +
        (r10 - 0.5) * 0.15 +
        (r20 - 0.5) * 0.08 +
        trend        * 0.12 +
        slope2       * 0.07 +
        (streak_feat * (1 if all_history[-1] == "BIG" else -1)) * 0.04 +
        (alt_4 - 0.5) * -0.02   # high alternation slightly penalizes follow
    )

    # Entropy dampening: near max entropy → reduce confidence
    damp = 1 - (entropy_feat - 0.5) * 0.4

    threshold = 0.04
    if score > threshold:
        conf = min(55 + abs(score) * 100 * damp, 82)
        return "BIG",   f"{P_AI_SPARKLES} BIG (အကြီး) 🔴",   conf, \
               f"{P_AI_SPARKLES} ML8F +{score:.3f}→BIG H={entropy_feat:.2f}"
    elif score < -threshold:
        conf = min(55 + abs(score) * 100 * damp, 82)
        return "SMALL", f"{P_AI_SPARKLES} SMALL (အသေး) 🟢", conf, \
               f"{P_AI_SPARKLES} ML8F {score:.3f}→SMALL H={entropy_feat:.2f}"
    else:
        last = all_history[-1]; burmese, dot = _label(last)
        return last, f"{P_AI_SPARKLES} {last} ({burmese}) {dot}", 55.0, \
               f"{P_AI_SPARKLES} ML8F Neutral {score:.4f}"


# ============================================================
# 17. Circle Rnd  —  unchanged (random by design)
# ============================================================
def circle_rnd_predict(history_docs):
    predicted = random.choice(["BIG", "SMALL"])
    burmese, dot = _label(predicted)
    return predicted, f"{P_AI_STAR} {predicted} ({burmese}) {dot}", \
           round(random.uniform(50.0, 65.0), 1), "🎡 Circle Rnd: Spinner"


# ============================================================
# 18. Custom Pattern  —  unchanged (user-defined)
# ============================================================
def custom_pattern_predict(history_docs, user_pattern="B"):
    if not user_pattern: user_pattern = "B"
    pattern    = user_pattern.upper()
    valid_chars = [c for c in pattern if c in ['B', 'S']]
    if not valid_chars: return "B", "🛠️ B (Custom Pattern)", 100.0, "Custom Pattern"
    clean_pattern = "".join(valid_chars)
    index = len(history_docs) % len(clean_pattern)
    c = clean_pattern[index]
    full = "BIG" if c == "B" else "SMALL"
    return full, f"🛠️ {full} (Custom Pattern)", 100.0, "Custom Pattern"


# ==========================================
# 📊 AI Modes Dictionary
# ==========================================
AI_MODE_NAMES = {
    "pattern":          "Pattern AI",
    "martingale":       "Martingale AI",
    "anti_martingale":  "Anti-Martingale AI",
    "trend_following":  "Trend Following",
    "fibonacci":        "Fibonacci AI",
    "golden_ratio":     "Golden Ratio",
    "momentum":         "Momentum AI",
    "monte_carlo":      "Monte Carlo",
    "neural_pattern":   "Neural Pattern",
    "quick_reversal":   "Quick Reversal",
    "wave_analysis":    "Wave Analysis",
    "chaos_theory":     "Chaos Theory",
    "ensemble":         "Ensemble AI",
    "bayesian":         "Bayesian AI",
    "markov_chain":     "Markov Chain",
    "ml_style":         "ML Style AI",
    "circle_rnd":       "Circle Rnd",
    "custom_pattern":   "🛠️ Set Pattern",
}

AI_MODES = {
    "pattern":          {"func": pattern_predict,           "name": AI_MODE_NAMES["pattern"],         "desc": "Pattern v2 (26 patterns, recency)"},
    "martingale":       {"func": martingale_predict,        "name": AI_MODE_NAMES["martingale"],      "desc": "Multi-Win Contrarian"},
    "anti_martingale":  {"func": anti_martingale_predict,   "name": AI_MODE_NAMES["anti_martingale"], "desc": "Exp-Streak Follow"},
    "trend_following":  {"func": trend_following_predict,   "name": AI_MODE_NAMES["trend_following"], "desc": "EMA 3-Timeframe"},
    "fibonacci":        {"func": fibonacci_predict,         "name": AI_MODE_NAMES["fibonacci"],       "desc": "Fib8 Weighted"},
    "golden_ratio":     {"func": golden_ratio_predict,      "name": AI_MODE_NAMES["golden_ratio"],    "desc": "φ 3-Scale Consensus"},
    "momentum":         {"func": momentum_predict,          "name": AI_MODE_NAMES["momentum"],        "desc": "ExpDecay+Acceleration"},
    "monte_carlo":      {"func": monte_carlo_predict,       "name": AI_MODE_NAMES["monte_carlo"],     "desc": "5000-Sim Recency-Weighted"},
    "neural_pattern":   {"func": neural_pattern_predict,    "name": AI_MODE_NAMES["neural_pattern"],  "desc": "kNN Multi-Window"},
    "quick_reversal":   {"func": quick_reversal_predict,    "name": AI_MODE_NAMES["quick_reversal"],  "desc": "Multi-Win Alternation"},
    "wave_analysis":    {"func": wave_analysis_predict,     "name": AI_MODE_NAMES["wave_analysis"],   "desc": "Impulse/Correction v2"},
    "chaos_theory":     {"func": chaos_theory_predict,      "name": AI_MODE_NAMES["chaos_theory"],    "desc": "Entropy+RunLength"},
    "ensemble":         {"func": ensemble_predict,          "name": AI_MODE_NAMES["ensemble"],        "desc": "15 AI Confidence-Weighted"},
    "bayesian":         {"func": bayesian_predict,          "name": AI_MODE_NAMES["bayesian"],        "desc": "2nd-Order Conditional"},
    "markov_chain":     {"func": markov_chain_predict,      "name": AI_MODE_NAMES["markov_chain"],    "desc": "3rd-Order Hierarchical"},
    "ml_style":         {"func": ml_style_predict,          "name": AI_MODE_NAMES["ml_style"],        "desc": "8-Feature Weighted"},
    "circle_rnd":       {"func": circle_rnd_predict,        "name": AI_MODE_NAMES["circle_rnd"],      "desc": "Random Wheel Spin"},
    "custom_pattern":   {"func": custom_pattern_predict,    "name": AI_MODE_NAMES["custom_pattern"],  "desc": "User စိတ်ကြိုက် Pattern"},
}

def get_prediction(history_docs, mode, user_pattern=None):
    if mode == "custom_pattern":
        return custom_pattern_predict(history_docs, user_pattern)
    mode_info = AI_MODES.get(mode)
    if mode_info: return mode_info["func"](history_docs)
    return AI_MODES["pattern"]["func"](history_docs)

def get_ai_mode_buttons():
    buttons = []
    for mode_key, mode_info in AI_MODES.items():
        mode_name = mode_info["name"]
        emoji_id  = AI_MODE_EMOJIS.get(mode_name, "6300853298249336390")
        btn = KeyboardButton(text=mode_name, icon_custom_emoji_id=emoji_id, style="primary")
        buttons.append(btn)
    return buttons
