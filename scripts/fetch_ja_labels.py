# Japanese labels for the country / industry names used in graph.json (built from English labels).
import json, time, urllib.parse, urllib.request
UA = "company-graph/0.1 (hobby project)"
g = json.load(open("../public/data/graph.json"))
def sparql(q):
    req = urllib.request.Request("https://query.wikidata.org/sparql", data=urllib.parse.urlencode({"query": q}).encode(),
        headers={"Accept": "application/sparql-results+json", "User-Agent": UA})
    return json.load(urllib.request.urlopen(req, timeout=90))["results"]["bindings"]
out = {}
for key in ("countries", "industries"):
    names = g[key]; m = {}
    # Countries: prefer items with an ISO 3166 code so "Georgia" resolves to the country, not the US state.
    passes = ["?item wdt:P297 [] .", ""] if key == "countries" else [""]
    for extra in passes:
        todo = [n for n in names if n not in m]
        for i in range(0, len(todo), 80):
            vals = " ".join(json.dumps(n) + "@en" for n in todo[i:i+80])
            rows = sparql(f"""SELECT ?en ?ja WHERE {{ VALUES ?en {{ {vals} }} ?item rdfs:label ?en . {extra}
              ?item rdfs:label ?ja FILTER(lang(?ja)="ja") }}""")
            for r in rows: m.setdefault(r["en"]["value"], r["ja"]["value"])
            time.sleep(0.5)
    out[key] = m
    print(key, len(m), "/", len(names))
json.dump(out, open("ja_labels.json", "w"), ensure_ascii=False)
