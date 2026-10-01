import csv, json, time, urllib.parse, urllib.request, glob

UA = "company-graph/0.1 (hobby project)"
def sparql(q):
    for attempt in range(4):
        try:
            req = urllib.request.Request("https://query.wikidata.org/sparql",
                data=urllib.parse.urlencode({"query": q}).encode(),
                headers={"Accept": "application/sparql-results+json", "User-Agent": UA})
            return json.load(urllib.request.urlopen(req, timeout=90))["results"]["bindings"]
        except Exception as e:
            print("retry", attempt, e); time.sleep(5 * (attempt + 1))
    raise RuntimeError("failed")

edges = set()
for path, kind in [("edges_P749.csv", "parent"), ("edges_P355.csv", "parent"), ("edges_P127.csv", "owner")]:
    for row in csv.DictReader(open(path)):
        c = row["child"].rsplit("/", 1)[1]; p = row["parent"].rsplit("/", 1)[1]
        if c != p:
            edges.add((p, c, kind))
# parent beats owner when both exist
best = {}
for p, c, k in edges:
    if best.get((p, c)) != "parent":
        best[(p, c)] = k
ids = sorted({x for e in best for x in e})
print(len(best), "edges", len(ids), "nodes")

nodes = {}
B = 300
for i in range(0, len(ids), B):
    vals = " ".join("wd:" + x for x in ids[i:i+B])
    q = f"""SELECT ?item ?en ?ja ?sl ?countryLabel ?industryLabel ?enwiki ?jawiki WHERE {{
      VALUES ?item {{ {vals} }}
      ?item wikibase:sitelinks ?sl .
      OPTIONAL {{ ?item rdfs:label ?en FILTER(lang(?en)="en") }}
      OPTIONAL {{ ?item rdfs:label ?ja FILTER(lang(?ja)="ja") }}
      OPTIONAL {{ ?item wdt:P17 ?country . ?country rdfs:label ?countryLabel FILTER(lang(?countryLabel)="en") }}
      OPTIONAL {{ ?item wdt:P452 ?ind . ?ind rdfs:label ?industryLabel FILTER(lang(?industryLabel)="en") }}
      OPTIONAL {{ ?enwiki schema:about ?item ; schema:isPartOf <https://en.wikipedia.org/> }}
      OPTIONAL {{ ?jawiki schema:about ?item ; schema:isPartOf <https://ja.wikipedia.org/> }}
    }}"""
    for r in sparql(q):
        qid = r["item"]["value"].rsplit("/", 1)[1]
        n = nodes.setdefault(qid, {"id": qid, "en": None, "ja": None, "sl": 0, "country": None, "industries": [], "enwiki": None, "jawiki": None})
        g = lambda k: r[k]["value"] if k in r else None
        n["en"] = n["en"] or g("en"); n["ja"] = n["ja"] or g("ja")
        n["sl"] = int(g("sl") or 0); n["country"] = n["country"] or g("countryLabel")
        ind = g("industryLabel")
        if ind and ind not in n["industries"]: n["industries"].append(ind)
        n["enwiki"] = n["enwiki"] or g("enwiki"); n["jawiki"] = n["jawiki"] or g("jawiki")
    print(f"{min(i+B, len(ids))}/{len(ids)}", flush=True)
    time.sleep(0.5)

json.dump({"nodes": list(nodes.values()), "edges": [[p, c, k] for (p, c), k in best.items()]},
          open("raw.json", "w"), ensure_ascii=False)
print("done", len(nodes))
