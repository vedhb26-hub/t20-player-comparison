import csv
import gzip
import json
import os
import zipfile
from collections import defaultdict

HERE = os.path.dirname(os.path.abspath(__file__))
ZIP_PATH = os.path.join(HERE, "all_json.zip")
NOT_BOWLER_WICKET = {"run out", "retired hurt", "retired out", "obstructing the field"}


def phase_of(over):
    return "powerplay" if over <= 5 else ("middle" if over <= 14 else "death")


def main():
    bat = defaultdict(lambda: [0, 0, 0, 0, 0])
    bowl = defaultdict(lambda: [0, 0, 0, 0])
    names = {}
    matches = 0
    with zipfile.ZipFile(ZIP_PATH) as z:
        for n in z.namelist():
            if not n.endswith(".json"):
                continue
            data = json.loads(z.read(n))
            info = data["info"]
            if info.get("match_type") not in ("T20", "IT20"):
                continue
            matches += 1
            year = int(info["dates"][0][:4])
            gender = info.get("gender", "")
            if info["match_type"] == "IT20":
                comp = "Unofficial T20 international"
            elif info.get("team_type") == "international":
                comp = "International"
            else:
                comp = info.get("event", {}).get("name") or "Other T20"
            reg = info.get("registry", {}).get("people", {})
            for inn in data.get("innings", []):
                if inn.get("super_over"):
                    continue
                faced = {}
                for ov in inn.get("overs", []):
                    ph = phase_of(ov["over"])
                    for d in ov["deliveries"]:
                        ex = d.get("extras", {})
                        wide = "wides" in ex
                        noball = "noballs" in ex
                        r = d["runs"]["batter"]
                        wk = d.get("wickets", [])
                        b, bw = d["batter"], d["bowler"]
                        bid, bwid = reg.get(b, b), reg.get(bw, bw)
                        names[bid] = b
                        names[bwid] = bw
                        if not wide:
                            faced[b] = faced.get(b, 0) + 1
                            early = 1 if faced[b] <= 10 else 0
                            a = bat[(bid, year, gender, comp, ph, early)]
                            a[0] += 1
                            a[1] += r
                            a[2] += 1 if r == 0 else 0
                            a[3] += 1 if r in (4, 6) else 0
                        out = any(w["player_out"] == b for w in wk)
                        if out:
                            bat[(bid, year, gender, comp, ph, 1 if faced.get(b, 0) <= 10 else 0)][4] += 1
                        legal = 0 if (wide or noball) else 1
                        runs = r + ex.get("wides", 0) + ex.get("noballs", 0)
                        c = bowl[(bwid, year, gender, comp, ph)]
                        c[0] += legal
                        c[1] += runs
                        c[2] += 1 if any(w["kind"] not in NOT_BOWLER_WICKET for w in wk) else 0
                        c[3] += 1 if runs == 0 else 0
    with gzip.open(os.path.join(HERE, "batting.csv.gz"), "wt", newline="") as f:
        w = csv.writer(f)
        w.writerow(["pid", "year", "gender", "comp", "phase", "first10", "balls", "runs", "dots", "boundaries", "outs"])
        for k, v in bat.items():
            w.writerow(list(k) + v)
    with gzip.open(os.path.join(HERE, "bowling.csv.gz"), "wt", newline="") as f:
        w = csv.writer(f)
        w.writerow(["pid", "year", "gender", "comp", "phase", "legal_balls", "runs", "wickets", "dots"])
        for k, v in bowl.items():
            w.writerow(list(k) + v)
    with open(os.path.join(HERE, "players.json"), "w") as f:
        json.dump(names, f)
    print("matches", matches, "bat rows", len(bat), "bowl rows", len(bowl), "players", len(names))


if __name__ == "__main__":
    main()
