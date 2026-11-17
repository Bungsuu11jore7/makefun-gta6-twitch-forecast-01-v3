#!/usr/bin/env python3
"""GTA VI launch-day Twitch forecast (make.fun gta6-twitch-ccu-forecast-01).

The centre is a blend of two size- and weekday-weighted views of the
case's own comparables: a local-linear fit of each hour's log viewer
ratio on log hour-1 print, and the kernel-weighted mean of those ratios.
Before pooling, every past launch is shifted into unlock time: the
day's curve jumps when the US East Coast wakes, and that midnight falls
at 04:00Z under daylight saving and 05:00Z under standard time, so a
launch is moved by the difference of its offset and the target's.
Launches whose notes name early access are left out of the pool; their
release day is already past its peak and bends the fit flat.

The spread is a lognormal width that narrows over the day: the small
hours hold the dip, the least predictable part of a launch day, while
the evening peak is the best-anchored part of the curve.

Stdlib only, no randomness, no network: the same case always gives the
same forecast bytes.
"""
import json
import math
import os
from datetime import datetime, timedelta, timezone

Z = (-1.645, -0.674, 0.0, 0.674, 1.645)
SIZE_BW = 1.8
DAY_BW = 2.0
RIDGE = 1.0
LINEAR_SHARE = 0.6
SPREAD0 = 0.23
SPREAD_SLOPE = -0.5
CENTRE_LO = -1.5
CENTRE_HI = 8.0


def parse_ts(text):
    return datetime.fromisoformat(text.replace("Z", "+00:00"))


def east_midnight_utc(day):
    """UTC hour of midnight on the US East Coast for the given date.

    Daylight saving (second Sunday of March to first Sunday of November)
    puts midnight at 04:00Z; standard time puts it at 05:00Z.
    """
    def nth_sunday(year, month, n):
        first = datetime(year, month, 1, tzinfo=timezone.utc)
        delta = (6 - first.weekday()) % 7
        return first + timedelta(days=delta + 7 * (n - 1))

    start = nth_sunday(day.year, 3, 2).date()
    end = nth_sunday(day.year, 11, 1).date()
    return 4 if start <= day.date() < end else 5


def weekday_gap(a, b):
    """Circular distance between two weekdays, 0 to 3."""
    d = abs(a - b) % 7
    return min(d, 7 - d)


def launch_curves(case):
    """Collect the usable comparables of one case.

    Returns (curves, target_weekday) where each curve is
    (log hour-1 viewers, weekday of its release day, unlock shift in
    hours relative to the target, [24 hourly viewer counts]).
    """
    try:
        day_start = parse_ts(case["day_start"])
    except Exception:
        return [], 0
    target_unlock = east_midnight_utc(day_start)
    curves = []
    for comp in case.get("comparables") or []:
        if "early-access" in (comp.get("unlock") or ""):
            continue
        try:
            comp_day = parse_ts(comp["day_start"])
        except Exception:
            continue
        hourly = comp.get("hourly") or []
        pos = None
        for i, row in enumerate(hourly):
            try:
                if parse_ts(row["from"]) == comp_day:
                    pos = i
                    break
            except Exception:
                continue
        if pos is None or pos + 24 > len(hourly):
            continue
        vals = []
        usable = True
        for k in range(24):
            try:
                vals.append(max(float(hourly[pos + k]["viewers"]), 1.0))
            except Exception:
                usable = False
                break
        if not usable:
            continue
        shift = east_midnight_utc(comp_day) - target_unlock
        curves.append((math.log(vals[0]), comp_day.weekday(), shift, vals))
    return curves, day_start.weekday()


def hour_centre(curves, log_p1, target_weekday, hour):
    """Blended centre log-ratio for one UTC hour, 2 to 24."""
    xs = []
    ys = []
    ws = []
    for c_logp1, c_weekday, shift, vals in curves:
        src = hour + shift
        if src < 1 or src > 24:
            continue
        size_w = math.exp(-0.5 * ((c_logp1 - log_p1) / SIZE_BW) ** 2)
        day_w = math.exp(
            -0.5 * (weekday_gap(c_weekday, target_weekday) / DAY_BW) ** 2
        )
        xs.append(c_logp1 - log_p1)
        ys.append(math.log(vals[src - 1] / vals[0]))
        ws.append(size_w * day_w)
    if not xs:
        return 0.0
    wsum = sum(ws)
    mean = sum(w * y for w, y in zip(ws, ys)) / wsum
    # Weighted local-linear fit y ~ a + b*x with a ridge on the slope
    # only; the intercept is the fit's value at the target's own size.
    swx = sum(w * x for w, x in zip(ws, xs))
    swy = sum(w * y for w, y in zip(ws, ys))
    swxx = sum(w * x * x for w, x in zip(ws, xs))
    swxy = sum(w * x * y for w, x, y in zip(ws, xs, ys))
    a00 = wsum
    a01 = swx
    a11 = swxx + RIDGE
    det = a00 * a11 - a01 * a01
    if abs(det) < 1e-12:
        intercept = swy / wsum
    else:
        intercept = (swy * a11 - swxy * a01) / det
    centre = LINEAR_SHARE * intercept + (1.0 - LINEAR_SHARE) * mean
    return max(CENTRE_LO, min(CENTRE_HI, centre))


def spread(hour):
    """Lognormal width for one hour: wide in the small hours, narrow late."""
    s = SPREAD0 * (1.0 + SPREAD_SLOPE * (hour - 13) / 11.0)
    return max(0.08, min(0.60, s))


def forecast_case(case):
    known = case.get("known") or []
    p1 = 1.0
    try:
        first = known[0] if isinstance(known, list) else known
        p1 = max(float(first.get("viewers") or 1), 1.0)
    except Exception:
        p1 = 1.0
    curves, target_weekday = launch_curves(case)
    log_p1 = math.log(p1)
    rows = []
    for hour in range(2, 25):
        centre = hour_centre(curves, log_p1, target_weekday, hour)
        sig = spread(hour)
        qs = []
        prev = 0.0
        for z in Z:
            q = p1 * math.exp(centre + z * sig)
            q = round(max(min(q, 1e9), 0.01), 2)
            if q < prev:
                q = prev
            qs.append(q)
            prev = q
        rows.append({"hour": hour, "q": qs})
    return {"hours": rows}


def main():
    in_dir = os.environ.get("MAKEFUN_INPUT_DIR") or "/input"
    out_dir = os.environ.get("MAKEFUN_OUTPUT_DIR") or "/output"
    os.makedirs(out_dir, exist_ok=True)
    names = sorted(n for n in os.listdir(in_dir) if n.endswith(".in"))
    for name in names:
        with open(os.path.join(in_dir, name), "r", encoding="utf-8") as fh:
            case = json.load(fh)
        out = forecast_case(case)
        with open(
            os.path.join(out_dir, name[:-3] + ".out"), "w", encoding="utf-8"
        ) as fh:
            json.dump(out, fh, separators=(",", ":"))
            fh.write("\n")


if __name__ == "__main__":
    main()
