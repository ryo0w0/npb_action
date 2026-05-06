#!/usr/bin/env python3
"""
NPB 一軍試合速報スクレイパー
スポーツナビの日程ページ (baseball.yahoo.co.jp/npb/schedule/) から
当日の試合を取得して data/today.json に書き出す。
依存: Python 3.8+ 標準ライブラリのみ (html.parser使用)
"""
import json, re, datetime, pathlib, sys, urllib.request
from html.parser import HTMLParser

URL = "https://baseball.yahoo.co.jp/npb/schedule/"
HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; NPBWidget/1.0; +https://github.com)"}

STADIUM_LEAGUE = {
    "東京ドーム": "Central", "横浜": "Central", "バンテリンドーム": "Central",
    "甲子園": "Central", "マツダスタジアム": "Central", "明治神宮": "Central",
    "ベルーナドーム": "Pacific", "京セラD大阪": "Pacific", "楽天モバイル": "Pacific",
    "みずほPayPay": "Pacific", "エスコン": "Pacific", "ZOZOマリン": "Pacific",
}
TEAM_EN = {
    "巨人": "Giants", "ヤクルト": "Swallows", "DeNA": "BayStars",
    "中日": "Dragons", "阀神": "Tigers", "広島": "Carp",
    "ソフトバンク": "Hawks", "日本ハム": "Fighters", "オリックス": "Buffaloes",
    "楽天": "Eagles", "西武": "Lions", "ロッテ": "Marines",
}
TEAM_COLOR = {
    "巨人": "#F97316", "ヤクルト": "#3B82F6", "DeNA": "#1D4ED8",
    "中日": "#0EA5E9", "阀神": "#FACC15", "広島": "#EF4444",
    "ソフトバンク": "#F59E0B", "日本ハム": "#6366F1", "オリックス": "#14B8A6",
    "楽天": "#DC2626", "西武": "#3B82F6", "ロッテ": "#0F766E",
}

class ScoreParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.games = []
        self._cur = None
        self._league = "Unknown"
        self._in_title = False
        self._in_venue = False
        self._in_home = False
        self._in_away = False
        self._in_score_left = False
        self._in_score_right = False
        self._in_link = False
        self._in_player_home = False
        self._in_player_away = False
        self._in_player_item = False
        self._is_live = False
        self._is_finished = False

    def handle_starttag(self, tag, attrs):
        cls = dict(attrs).get("class", "")
        if tag == "h1" and "bb-score__title" in cls:
            self._in_title = True
            return
        if tag == "li" and "bb-score__item" in cls:
            self._cur = {
                "league": self._league,
                "stadium": "", "home_team": "", "away_team": "",
                "home_score": None, "away_score": None,
                "status": "", "live": False, "finished": False,
                "home_player": "", "away_player": "",
            }
            self._is_live = "bb-score__item--live" in cls
            self._is_finished = "bb-score__item--end" in cls
            return
        if self._cur is None:
            return
        if tag == "span" and "bb-score__venue" in cls:
            self._in_venue = True
        elif tag == "p" and "bb-score__homeLogo" in cls:
            self._in_home = True
        elif tag == "p" and "bb-score__awayLogo" in cls:
            self._in_away = True
        elif tag == "span" and "bb-score__score--left" in cls:
            self._in_score_left = True
        elif tag == "span" and "bb-score__score--right" in cls:
            self._in_score_right = True
        elif tag == "p" and "bb-score__link" in cls:
            self._in_link = True
        elif tag == "div" and "bb-score__playerHome" in cls:
            self._in_player_home = True
        elif tag == "div" and "bb-score__playerAway" in cls:
            self._in_player_away = True
        elif tag == "li" and "bb-score__player" in cls:
            self._in_player_item = True

    def handle_endtag(self, tag):
        if tag == "h1":
            self._in_title = False
        if tag == "li" and self._cur and self._cur.get("home_team"):
            self.games.append(self._cur)
            self._cur = None
            self._in_player_home = False
            self._in_player_away = False
        self._in_venue = False
        self._in_home = False
        self._in_away = False
        self._in_score_left = False
        self._in_score_right = False
        self._in_link = False
        if tag == "li":
            self._in_player_item = False

    def handle_data(self, data):
        data = data.strip()
        if not data:
            return
        if self._in_title:
            if "セ" in data:
                self._league = "Central"
            elif "パ" in data:
                self._league = "Pacific"
            return
        if self._cur is None:
            return
        if self._in_venue:
            self._cur["stadium"] = data
        elif self._in_home:
            self._cur["home_team"] = data
        elif self._in_away:
            self._cur["away_team"] = data
        elif self._in_score_left:
            try: self._cur["home_score"] = int(data)
            except: pass
        elif self._in_score_right:
            try: self._cur["away_score"] = int(data)
            except: pass
        elif self._in_link:
            self._cur["status"] = data
            self._cur["live"] = self._is_live
            self._cur["finished"] = "試合終了" in data or self._is_finished
        elif self._in_player_item:
            if self._in_player_home:
                self._cur["home_player"] = data
            elif self._in_player_away:
                self._cur["away_player"] = data


def get_league(stadium):
    for k, v in STADIUM_LEAGUE.items():
        if k in stadium:
            return v
    return "Unknown"


def scrape():
    jst = datetime.timezone(datetime.timedelta(hours=9))
    now = datetime.datetime.now(jst)

    req = urllib.request.Request(URL, headers=HEADERS)
    try:
        with urllib.request.urlopen(req, timeout=15) as r:
            html = r.read().decode("utf-8", errors="replace")
    except Exception as e:
        print(f"[ERROR] fetch failed: {e}", file=sys.stderr)
        sys.exit(1)

    parser = ScoreParser()
    parser.feed(html)

    for g in parser.games:
        if g["league"] == "Unknown":
            g["league"] = get_league(g["stadium"])
        g["home_team_en"] = TEAM_EN.get(g["home_team"], g["home_team"])
        g["away_team_en"] = TEAM_EN.get(g["away_team"], g["away_team"])
        g["home_color"] = TEAM_COLOR.get(g["home_team"], "#6B7280")
        g["away_color"] = TEAM_COLOR.get(g["away_team"], "#6B7280")

    out = {
        "updated_at": now.isoformat(),
        "date": now.strftime("%Y-%m-%d"),
        "source": "baseball.yahoo.co.jp",
        "games": parser.games,
    }

    pathlib.Path("data").mkdir(exist_ok=True)
    pathlib.Path("data/today.json").write_text(
        json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(f"[OK] {len(parser.games)} games written -> data/today.json")


if __name__ == "__main__":
    scrape()
