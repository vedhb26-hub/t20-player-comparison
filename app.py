import json
import os

import pandas as pd
import streamlit as st

HERE = os.path.dirname(os.path.abspath(__file__))
PHASES = ["powerplay", "middle", "death"]

st.set_page_config(page_title="T20 Player Comparison", layout="wide")


@st.cache_data
def load():
    bat = pd.read_csv(os.path.join(HERE, "batting.csv.gz"))
    bowl = pd.read_csv(os.path.join(HERE, "bowling.csv.gz"))
    with open(os.path.join(HERE, "players.json")) as f:
        names = json.load(f)
    return bat, bowl, names


bat, bowl, names = load()

st.title("T20 Player Comparison")

c1, c2, c3, c4 = st.columns(4)
gender = c1.selectbox("Players", ["male", "female"], format_func=lambda g: "Men" if g == "male" else "Women")
y0, y1 = int(bat["year"].min()), int(bat["year"].max())
years = c2.slider("Years", y0, y1, (max(y0, y1 - 3), y1))
comps = ["All T20", "International only"] + sorted(
    bat[bat["gender"] == gender]["comp"].loc[lambda s: s != "International"].unique().tolist())
comp = c3.selectbox("Competition", comps)
view = c4.radio("View", ["Batting", "Bowling"], horizontal=True)


def pick(df):
    df = df[(df["gender"] == gender) & df["year"].between(years[0], years[1])]
    if comp == "International only":
        df = df[df["comp"] == "International"]
    elif comp != "All T20":
        df = df[df["comp"] == comp]
    return df


def label(pid):
    return names.get(pid, pid)


def safe_div(a, b, mult=1.0, digits=1):
    return round(a / b * mult, digits) if b else None


if view == "Batting":
    d = pick(bat)
    tot = d.groupby("pid")["balls"].sum()
    ids = tot[tot >= 100].sort_values(ascending=False).index.tolist()
else:
    d = pick(bowl)
    tot = d.groupby("pid")["legal_balls"].sum()
    ids = tot[tot >= 100].sort_values(ascending=False).index.tolist()

if len(ids) < 2:
    st.write("Not enough players for this selection.")
    st.stop()

dup = pd.Series([label(i) for i in ids]).duplicated(keep=False).tolist()
shown = {i: (label(i) + " [" + i[:6] + "]" if x else label(i)) for i, x in zip(ids, dup)}
p1, p2 = st.columns(2)
a = p1.selectbox("Player 1", ids, index=0, format_func=lambda i: shown[i])
b = p2.selectbox("Player 2", ids, index=1, format_func=lambda i: shown[i])


def bat_stats(g):
    balls, runs = g["balls"].sum(), g["runs"].sum()
    outs, dots, bnd = g["outs"].sum(), g["dots"].sum(), g["boundaries"].sum()
    f = g[g["first10"] == 1]
    r = g[g["first10"] == 0]
    return {
        "Balls": int(balls), "Runs": int(runs),
        "Strike rate": safe_div(runs, balls, 100),
        "Dot %": safe_div(dots, balls, 100),
        "Boundary %": safe_div(bnd, balls, 100),
        "Balls per boundary": safe_div(balls, bnd),
        "Average": safe_div(runs, outs),
        "First 10 balls SR": safe_div(f["runs"].sum(), f["balls"].sum(), 100),
        "After 10 balls SR": safe_div(r["runs"].sum(), r["balls"].sum(), 100),
    }


def bowl_stats(g):
    lb, runs, w, dots = g["legal_balls"].sum(), g["runs"].sum(), g["wickets"].sum(), g["dots"].sum()
    return {
        "Legal balls": int(lb), "Runs conceded": int(runs), "Wickets": int(w),
        "Economy": safe_div(runs, lb, 6, 2),
        "Dot %": safe_div(dots, lb, 100),
        "Balls per wicket": safe_div(lb, w),
    }


def phase_frame(df, fn, col):
    out = {}
    for pid in (a, b):
        g = df[df["pid"] == pid]
        out[shown[pid]] = [fn(g[g["phase"] == p])[col] for p in PHASES]
    return pd.DataFrame(out, index=PHASES)


if view == "Batting":
    table = pd.DataFrame({shown[a]: bat_stats(d[d["pid"] == a]), shown[b]: bat_stats(d[d["pid"] == b])})
    st.dataframe(table.astype(object))
    st.subheader("Strike rate by phase")
    st.bar_chart(phase_frame(d, bat_stats, "Strike rate"))
    st.subheader("Dot ball % by phase")
    st.bar_chart(phase_frame(d, bat_stats, "Dot %"))
else:
    table = pd.DataFrame({shown[a]: bowl_stats(d[d["pid"] == a]), shown[b]: bowl_stats(d[d["pid"] == b])})
    st.dataframe(table.astype(object))
    st.subheader("Economy by phase")
    st.bar_chart(phase_frame(d, bowl_stats, "Economy"))

st.caption("Data: Cricsheet (cricsheet.org), ball-by-ball T20 internationals and leagues. "
           "Matches involving Afghanistan and some older matches are not included, so totals can be lower than official figures.")
