# Index constituents that have no ownership links on Wikidata are not in raw.json yet; fetch their metadata so
# index filters (e.g. Nikkei 225) show every constituent, not only the ones with links.
import json, time, urllib.parse, urllib.request
UA = "company-graph/0.1 (hobby project)"
raw = json.load(open("raw.json")); market = json.load(open("market.json"))
have = {n["id"] for n in raw["nodes"]}
want = sorted({q for ix in market["indices"] for q in ix["members"]} - have)
print("missing index members", len(want))
def sparql(q):
    req = urllib.request.Request("https://query.wikidata.org/sparql", data=urllib.parse.urlencode({"query": q}).encode(),
        headers={"Accept": "application/sparql-results+json", "User-Agent": UA})
    return json.load(urllib.request.urlopen(req, timeout=90))["results"]["bindings"]
nodes = {}
for i in range(0, len(want), 200):
    vals = " ".join("wd:" + x for x in want[i:i+200])
    for r in sparql(f"""SELECT ?item ?en ?ja ?sl ?countryLabel ?industryLabel ?enwiki ?jawiki WHERE {{
      VALUES ?item {{ {vals} }} ?item wikibase:sitelinks ?sl .
      OPTIONAL {{ ?item rdfs:label ?en FILTER(lang(?en)="en") }} OPTIONAL {{ ?item rdfs:label ?ja FILTER(lang(?ja)="ja") }}
      OPTIONAL {{ ?item wdt:P17 ?country . ?country rdfs:label ?countryLabel FILTER(lang(?countryLabel)="en") }}
      OPTIONAL {{ ?item wdt:P452 ?ind . ?ind rdfs:label ?industryLabel FILTER(lang(?industryLabel)="en") }}
      OPTIONAL {{ ?enwiki schema:about ?item ; schema:isPartOf <https://en.wikipedia.org/> }}
      OPTIONAL {{ ?jawiki schema:about ?item ; schema:isPartOf <https://ja.wikipedia.org/> }} }}"""):
        q = r["item"]["value"].rsplit("/", 1)[1]; g = lambda k: r[k]["value"] if k in r else None
        n = nodes.setdefault(q, {"id": q, "en": None, "ja": None, "sl": 0, "country": None, "industries": [], "enwiki": None, "jawiki": None, "index_member": True})
        n["en"] = n["en"] or g("en"); n["ja"] = n["ja"] or g("ja"); n["sl"] = int(g("sl") or 0)
        n["country"] = n["country"] or g("countryLabel")
        if g("industryLabel") and g("industryLabel") not in n["industries"]: n["industries"].append(g("industryLabel"))
        n["enwiki"] = n["enwiki"] or g("enwiki"); n["jawiki"] = n["jawiki"] or g("jawiki")
    time.sleep(0.5)
raw["nodes"] += list(nodes.values())
json.dump(raw, open("raw.json", "w"), ensure_ascii=False)
print("added", len(nodes))
