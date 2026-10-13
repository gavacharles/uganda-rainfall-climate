"""Kampala flood catalogue (D0), 2017-2026, from the GDELT DOC 2.0 news index (no login), plus manually verified
earlier events in data/kd/flood_events.csv.

Method: query GDELT month by month for English-language articles mentioning Kampala together with flooding terms;
keep articles whose title mentions flooding/heavy rain; an article's event day is its publication date (UTC+3), or the
day before for articles published before 10:00 (morning-after reporting). A flood day = a day (or two consecutive days)
reported by >= 2 distinct outlets. Outputs data/kd/gdelt_articles.csv, data/kd/flood_catalogue.csv.
"""
import re
import time

import pandas as pd
import requests

from common import ROOT

KD = ROOT / "data" / "kd"
API = "https://api.gdeltproject.org/api/v2/doc/doc"
Q = '(Kampala OR KCCA OR Bwaise OR Kalerwe OR Nakivubo OR Lubigi OR Kinawataka) (flood OR floods OR flooding OR downpour OR "heavy rain")'
TITLE = re.compile(r"flood|downpour|heavy rain|rainstorm|storm|submerg|drown|washed away|stranded|rains? (cause|leave|wreak|paralys)", re.I)
EVENT = re.compile(r"cut off|cuts off|wash(es|ed)? away|submerg|stranded|marooned|dead|die|kill|drown|bod(y|ies)|swept|displac|"
                   r"paralys|disrupt|traffic|block|impassable|homes|houses|leaves .* (flooded|under water)|after .*(rain|downpour)|"
                   r"heavy rain|downpour|flash flood|floods? (hit|ravage|sweep|batter|wreak|cause)", re.I)
NOT_EVENT = re.compile(r"spaghetti|lubricant|market|masterplan|master plan|compensation|plan to|planning board|why kampala|"
                       r"will soon|set to rid|upgrades to|named as|opinion|editorial|letter", re.I)
PLACE = re.compile(r"kampala|kcca|bwaise|kalerwe|nakivubo|lubigi|kinawataka|kyambogo|banda|nalukolongo|kawempe|"
                   r"nakawa|rubaga|makindye|ntinda|kisenyi|katwe|wakiso|mukono|entebbe road|jinja road|northern bypass", re.I)


def _get(start, end):
    params = dict(query=Q, mode="artlist", maxrecords=250, format="json", sort="dateasc",
                  startdatetime=start.strftime("%Y%m%d%H%M%S"), enddatetime=end.strftime("%Y%m%d%H%M%S"))
    for attempt in range(24):
        try:
            r = requests.get(API, params=params, timeout=120)
        except requests.RequestException:
            time.sleep(30)
            continue
        if r.status_code == 429:
            time.sleep(300)
            continue
        time.sleep(300)
        try:
            return r.json().get("articles", [])
        except ValueError:
            return []  # empty body = nothing matched
    return None


def _window(start, end, depth=0):
    """Fetch [start, end); split in half while the 250-article cap is hit (down to ~2 days)."""
    arts = _get(start, end)
    if arts is None:
        print(f"{start:%Y-%m-%d} FAILED", flush=True)
        raise RuntimeError("window failed")
    if len(arts) >= 250 and (end - start) > pd.Timedelta(days=2):
        mid = start + (end - start) / 2
        return _window(start, mid, depth + 1) + _window(mid, end, depth + 1)
    print(f"{'  ' * depth}{start:%Y-%m-%d} - {end:%Y-%m-%d}: {len(arts)}{' (capped)' if len(arts) >= 250 else ''}", flush=True)
    return arts


def fetch():
    """Quarterly windows (split adaptively when capped), cached one file per quarter."""
    f = KD / "gdelt_articles.csv"
    cache = KD / "gdelt"
    cache.mkdir(exist_ok=True)
    for start in pd.date_range("2017-01-01", "2026-10-01", freq="QS"):
        out = cache / f"{start:%Y-%m}.csv"
        if out.exists():
            continue
        end = min(start + pd.offsets.QuarterBegin(1, startingMonth=1), pd.Timestamp("2026-10-13"))
        try:
            arts = _window(start, end)
        except RuntimeError:
            continue  # not cached: retried on the next run
        pd.DataFrame([dict(seendate=a.get("seendate"), title=a.get("title", ""), domain=a.get("domain", ""),
                           url=a.get("url", ""), lang=a.get("language", ""), country=a.get("sourcecountry", ""))
                      for a in arts], columns=["seendate", "title", "domain", "url", "lang", "country"]).to_csv(out, index=False)
    df = pd.concat([pd.read_csv(x) for x in sorted(cache.glob("*.csv"))], ignore_index=True).drop_duplicates("url")
    df["seendate"] = pd.to_datetime(df.seendate, format="%Y%m%dT%H%M%SZ")
    df.to_csv(f, index=False)
    return df


def build():
    df = fetch()
    df = df.assign(title=df.title.fillna(""), url=df.url.fillna(""))
    df = df[(df.lang == "English") & df.title.str.contains(TITLE) & (df.title.str.contains(PLACE) | df.url.str.contains(PLACE))
            & df.title.str.contains(EVENT) & ~df.title.str.contains(NOT_EVENT)]
    df = df.drop_duplicates("url")
    local = df.seendate + pd.Timedelta(hours=3)
    df["day"] = (local - pd.to_timedelta((local.dt.hour < 10).astype(int), unit="D")).dt.normalize()
    by = df.groupby("day").agg(n_outlets=("domain", "nunique"), n_articles=("url", "size"),
                               titles=("title", lambda v: " | ".join(list(dict.fromkeys(v))[:4])),
                               urls=("url", lambda v: " ".join(list(v)[:3])))
    # merge consecutive days into one event; keep events with >= 2 outlets
    by = by.reset_index().sort_values("day")
    by["grp"] = (by.day.diff().dt.days.fillna(99) > 1).cumsum()
    ev = by.groupby("grp").agg(start=("day", "min"), end=("day", "max"), n_outlets=("n_outlets", "sum"),
                               n_articles=("n_articles", "sum"), titles=("titles", " | ".join), urls=("urls", " ".join))
    ev = ev[ev.n_outlets >= 2].reset_index(drop=True)
    ev["deaths_mentioned"] = ev.titles.str.contains(r"dead|die|kill|drown|bod(y|ies)", case=False)
    ev.to_csv(KD / "flood_catalogue_gdelt.csv", index=False)
    print(len(df), "relevant articles;", len(ev), "events with >= 2 outlets")
    print(ev[["start", "end", "n_outlets", "titles"]].assign(titles=ev.titles.str[:110]).to_string())
    return ev


if __name__ == "__main__":
    build()
