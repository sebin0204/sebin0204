"""GitHub 프로필 통계 카드(SVG) 생성 스크립트 — GitHub Actions에서 실행됩니다."""
import json, os, sys, urllib.request
from html import escape

USER = os.environ.get("GH_USER", "sebin0204")
# 내가 직접 작성하지 않은 언어 (Dual-tales AI 서버는 팀원 코드)
EXCLUDE_LANGS = {"Python"}
OUT = os.path.join(os.path.dirname(__file__), "..", "assets")
QUERY = """query($login:String!){user(login:$login){
  contributionsCollection{totalCommitContributions totalPullRequestContributions totalIssueContributions
    contributionCalendar{totalContributions}}
  repositoriesContributedTo(first:1,contributionTypes:[COMMIT,PULL_REQUEST,REPOSITORY]){totalCount}
  repositories(ownerAffiliations:OWNER,first:100){nodes{name stargazerCount
    languages(first:10,orderBy:{field:SIZE,direction:DESC}){edges{size node{name color}}}}}}}"""

def fetch():
    if len(sys.argv) > 1:  # 로컬 테스트: python stats.py sample.json
        return json.load(open(sys.argv[1]))
    req = urllib.request.Request("https://api.github.com/graphql",
        data=json.dumps({"query": QUERY, "variables": {"login": USER}}).encode(),
        headers={"Authorization": f"bearer {os.environ['GITHUB_TOKEN']}", "Content-Type": "application/json"})
    data = json.load(urllib.request.urlopen(req))
    if "errors" in data:
        raise SystemExit(data["errors"])
    return data["data"]["user"]

FONT = "font-family='Segoe UI,Apple SD Gothic Neo,Noto Sans KR,sans-serif'"
STYLE = """<style>
  .bg{fill:#fff;stroke:#e4e2e2}.t{fill:#2f80ed;font-size:16px;font-weight:700}
  .l{fill:#434d58;font-size:13px}.v{fill:#434d58;font-size:13px;font-weight:700}
  @media (prefers-color-scheme:dark){.bg{fill:#0d1117;stroke:#30363d}.t{fill:#58a6ff}.l,.v{fill:#c9d1d9}}
</style>"""

def card(w, h, title, body):
    return (f"<svg xmlns='http://www.w3.org/2000/svg' width='{w}' height='{h}' viewBox='0 0 {w} {h}' {FONT}>{STYLE}"
            f"<rect class='bg' x='0.5' y='0.5' rx='6' width='{w-1}' height='{h-1}'/>"
            f"<text class='t' x='25' y='35'>{escape(title)}</text>{body}</svg>")

def stats_svg(u):
    c = u["contributionsCollection"]
    rows = [("⭐ Total Stars", sum(r["stargazerCount"] for r in u["repositories"]["nodes"])),
            ("🕑 Commits (last year)", c["totalCommitContributions"]),
            ("🔀 Pull Requests", c["totalPullRequestContributions"]),
            ("❗ Issues", c["totalIssueContributions"]),
            ("📦 Contributed to", u["repositoriesContributedTo"]["totalCount"])]
    body = "".join(f"<text class='l' x='25' y='{70+i*25}'>{escape(k)}</text>"
                   f"<text class='v' x='300' y='{70+i*25}' text-anchor='end'>{v}</text>" for i, (k, v) in enumerate(rows))
    return card(330, 195, "sebin0204's GitHub Stats", body)

def langs_svg(u):
    total = {}
    for r in u["repositories"]["nodes"]:
        if r["name"].lower() == USER.lower():
            continue
        for e in r["languages"]["edges"]:
            n = e["node"]["name"]
            if n in EXCLUDE_LANGS:
                continue
            s, col = total.get(n, (0, e["node"]["color"] or "#8b949e"))
            total[n] = (s + e["size"], col)
    top = sorted(total.items(), key=lambda x: -x[1][0])[:6]
    whole = sum(s for _, (s, _) in top) or 1
    x, bar = 25.0, ""
    for n, (s, col) in top:
        w = 280 * s / whole
        bar += f"<rect x='{x:.2f}' y='50' width='{w:.2f}' height='8' fill='{col}'/>"
        x += w
    bar = f"<clipPath id='c'><rect x='25' y='50' width='280' height='8' rx='4'/></clipPath><g clip-path='url(#c)'>{bar}</g>"
    items = ""
    for i, (n, (s, col)) in enumerate(top):
        cx, cy = 25 + (i % 2) * 145, 85 + (i // 2) * 25
        items += (f"<circle cx='{cx+5}' cy='{cy-4}' r='5' fill='{col}'/>"
                  f"<text class='l' x='{cx+16}' y='{cy}'>{escape(n)} {100*s/whole:.1f}%</text>")
    return card(330, 195, "Most Used Languages", bar + items)

if __name__ == "__main__":
    u = fetch()
    os.makedirs(OUT, exist_ok=True)
    open(os.path.join(OUT, "stats.svg"), "w").write(stats_svg(u))
    open(os.path.join(OUT, "top-langs.svg"), "w").write(langs_svg(u))
    print("generated")
