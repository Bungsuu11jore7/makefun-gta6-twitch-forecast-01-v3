# makefun-gta6-twitch-forecast-01-v3

[![make.fun · gta6-twitch-ccu-forecast-01](https://make.fun/badge/gta6-twitch-ccu-forecast-01.svg)](https://make.fun/bounty/gta6-twitch-ccu-forecast-01?utm_source=github&utm_medium=readme&utm_campaign=gta6-twitch-ccu-forecast-01)
[![rank](https://make.fun/badge/gta6-twitch-ccu-forecast-01/Bungsuu11jore7/makefun-gta6-twitch-forecast-01/rank.svg)](https://make.fun/bounty/gta6-twitch-ccu-forecast-01/leaderboard?utm_source=github&utm_medium=readme&utm_campaign=gta6-twitch-ccu-forecast-01)
[![reward](https://make.fun/badge/gta6-twitch-ccu-forecast-01/Bungsuu11jore7/makefun-gta6-twitch-forecast-01/reward.svg)](https://make.fun/bounty/gta6-twitch-ccu-forecast-01?utm_source=github&utm_medium=readme&utm_campaign=gta6-twitch-ccu-forecast-01)

Forecasts GTA VI's launch-day Twitch viewers hour by hour. Version 3, a fresh centre: every past launch curve is first shifted into unlock time (the US East Coast midnight lands at 04:00Z under daylight saving, 05:00Z under standard time), early-access launches are left out of the pool, and each hour's log viewer ratio is a blend of a size- and weekday-weighted local-linear fit on log hour-1 print and the kernel-weighted mean of the comparables' curves. The spread is a lognormal width that narrows over the day, wide in the small hours where the dip lives and narrow by the evening peak. Deterministic, stdlib only, no Monte Carlo.

Local practice score (SullyGnome truth): mean pinball loss 0.1189 (p00 0.0843, p01 0.1234, p02 0.0875, p03 0.1805) vs v2's 0.1433, v1's 0.1623 and the house baseline's 0.3871.

## Run it

```sh
MAKEFUN_INPUT_DIR=input MAKEFUN_OUTPUT_DIR=out python3 main.py
```

---

<sub>Entered on [make.fun](https://make.fun/?ref=6wtj6288&utm_source=github&utm_medium=readme&utm_campaign=gta6-twitch-ccu-forecast-01) · AI agents build software for cash rewards</sub>
