# Stock index membership + listing exchanges for the companies in graph.json -> market.json
import json, re, time, urllib.parse, urllib.request
UA = "company-graph/0.1 (hobby project)"
def get(url, data=None, accept="application/json"):
    req = urllib.request.Request(url, data=data, headers={"Accept": accept, "User-Agent": UA})
    return json.load(urllib.request.urlopen(req, timeout=120))
def sparql(q):
    return get("https://query.wikidata.org/sparql", urllib.parse.urlencode({"query": q}).encode(), "application/sparql-results+json")["results"]["bindings"]
qid = lambda u: u.rsplit("/", 1)[1]

# Wikidata "part of" (P361) is reasonably filled for these; Nikkei 225 is not (8 members), so it comes from Wikipedia.
INDICES = [("Q242345", "S&P 500", "S&P 500"), ("Q180816", "Dow Jones Industrial Average", "ダウ平均"),
           ("Q507306", "NASDAQ-100", "NASDAQ-100"), ("Q466496", "FTSE 100", "FTSE 100"), ("Q155718", "DAX", "DAX"),
           ("Q648828", "CAC 40", "CAC 40"), ("Q981010", "Euro Stoxx 50", "ユーロ・ストックス50"),
           ("Q938032", "IBEX 35", "IBEX 35"), ("Q666714", "Swiss Market Index", "SMI")]
indices = []
for q, en, ja in INDICES:
    # Statement-level query so former constituents (with an end date, P582) are excluded.
    rows = sparql(f"SELECT DISTINCT ?c WHERE {{ ?c p:P361 ?st . ?st ps:P361 wd:{q} . FILTER NOT EXISTS {{ ?st pq:P582 [] }} ?st wikibase:rank ?r FILTER(?r != wikibase:DeprecatedRank) }}")
    indices.append({"id": q, "en": en, "ja": ja, "members": sorted({qid(r["c"]["value"]) for r in rows})})
    print(en, len(indices[-1]["members"])); time.sleep(0.5)

# Nikkei 225: the "Components" section of the English Wikipedia article lists every constituent as a wiki link.
wt = get("https://en.wikipedia.org/w/api.php?action=parse&page=Nikkei_225&prop=wikitext&format=json&formatversion=2")["parse"]["wikitext"]
sec = wt[wt.index("==Components=="):wt.index("==Statistics")]
asof = re.search(r"As of ([A-Z][a-z]+ \d{4})", sec)
titles = []
for line in sec.splitlines():
    # Lines look like "*[[Name]] ...", "*The [[Name]] ...", "*'''[[Name]] ...'''": take the first link on lines carrying a stock code.
    m = re.match(r"\*[^\[]*\[\[([^\]|#]+)", line) if "{{tyo" in line else None
    if m: titles.append(m.group(1).strip())
members = set()
for i in range(0, len(titles), 50):
    j = get("https://en.wikipedia.org/w/api.php?" + urllib.parse.urlencode({"action": "query", "titles": "|".join(titles[i:i+50]),
        "prop": "pageprops", "ppprop": "wikibase_item", "redirects": 1, "format": "json", "formatversion": 2}))
    for p in j["query"]["pages"]:
        if p.get("pageprops", {}).get("wikibase_item"): members.add(p["pageprops"]["wikibase_item"])
indices.insert(0, {"id": "Q507338", "en": "Nikkei 225", "ja": "日経225", "members": sorted(members),
                   "note": f"Wikipedia, as of {asof.group(1) if asof else '?'}"})
print("Nikkei 225 titles", len(titles), "-> items", len(members))

# Listing exchanges (P414).
rows = sparql("""SELECT ?c ?ex ?en ?ja WHERE { ?c wdt:P414 ?ex . ?c wdt:P452 [] .
  OPTIONAL { ?ex rdfs:label ?en FILTER(lang(?en)="en") } OPTIONAL { ?ex rdfs:label ?ja FILTER(lang(?ja)="ja") } }""")
exchanges = {}
for r in rows:
    e = exchanges.setdefault(qid(r["ex"]["value"]), {"id": qid(r["ex"]["value"]), "en": r.get("en", {}).get("value"), "ja": r.get("ja", {}).get("value"), "members": set()})
    e["members"].add(qid(r["c"]["value"]))
ex = sorted(exchanges.values(), key=lambda e: -len(e["members"]))
for e in ex: e["members"] = sorted(e["members"])
print("exchanges", len(ex), [(e["en"], len(e["members"])) for e in ex[:8]])
json.dump({"indices": indices, "exchanges": ex}, open("market.json", "w"), ensure_ascii=False)
