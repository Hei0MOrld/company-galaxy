# raw.json (Wikidata dump) -> public/data/graph.json (compact form for the browser)
import json, collections, os, re

raw = json.load(open(os.path.join(os.path.dirname(__file__), "raw.json")))
# Wikidata's "industry" (P452) is also set on schools, municipalities, ministries, clubs etc.
# Drop anything tagged with a clearly non-company industry, and anything tagged only with soft ones.
HARD = re.compile(r"primary education|secondary education|higher education|administration publique|public administration|foreign affairs|government|religio|political|military|defen[cs]e", re.I)
SOFT = re.compile(r"education|sport|research|membership organisation|charit|non-profit|library|museum|association football", re.I)
def is_company(n):
    ind = n["industries"]
    if any(HARD.search(i) for i in ind): return False
    return not all(SOFT.search(i) for i in ind)

# Stock index constituents (scripts/fetch_market.py + fetch_extra.py) are kept even without ownership links.
mpath = os.path.join(os.path.dirname(__file__), "market.json")
market = json.load(open(mpath)) if os.path.exists(mpath) else {"indices": [], "exchanges": []}
index_members = {q for ix in market["indices"] for q in ix["members"]}
nodes = {n["id"]: n for n in raw["nodes"] if n["id"] in index_members or is_company(n)}
edges = [(p, c, k) for p, c, k in raw["edges"] if p in nodes and c in nodes]
linked = {x for p, c, _ in edges for x in (p, c)}
nodes = {q: n for q, n in nodes.items() if q in linked or q in index_members}

def name(n):
    return n["en"] or n["ja"] or n["id"]

# Industry: keep the most common label per node so colouring is stable.
ind_count = collections.Counter(i for n in nodes.values() for i in n["industries"])
def main_industry(n):
    return max(n["industries"], key=lambda i: ind_count[i]) if n["industries"] else None

countries = [c for c, _ in collections.Counter(n["country"] for n in nodes.values() if n["country"]).most_common()]
industries = [i for i, _ in collections.Counter(main_industry(n) for n in nodes.values() if main_industry(n)).most_common()]
ci = {c: i for i, c in enumerate(countries)}
ii = {c: i for i, c in enumerate(industries)}

ids = sorted(nodes, key=lambda q: -nodes[q]["sl"])
idx = {q: i for i, q in enumerate(ids)}

def wiki(url, prefix):
    return url[len(prefix):] if url and url.startswith(prefix) else None

out_nodes = []
for q in ids:
    n = nodes[q]
    out_nodes.append([
        q,
        name(n),
        n["ja"] if n["ja"] and n["ja"] != n["en"] else None,
        ci.get(n["country"], -1),
        ii.get(main_industry(n), -1),
        n["sl"],
        wiki(n["enwiki"], "https://en.wikipedia.org/wiki/"),
        wiki(n["jawiki"], "https://ja.wikipedia.org/wiki/"),
    ])

out = {
    "source": "Wikidata (CC0)",
    "countries": countries,
    "industries": industries,
    "nodes": out_nodes,
    # [parentIndex, childIndex, 0=parent/subsidiary 1=owned by]
    "edges": [[idx[p], idx[c], 0 if k == "parent" else 1] for p, c, k in edges],
}
# Filters: index constituents and listing exchanges, as lists of node indices.
out["indices"] = [{"en": ix["en"], "ja": ix["ja"], "note": ix.get("note"), "members": sorted(idx[q] for q in ix["members"] if q in idx)}
                  for ix in market["indices"]]
exs = [{"en": e["en"], "ja": e["ja"], "members": sorted(idx[q] for q in e["members"] if q in idx)} for e in market["exchanges"]]
out["exchanges"] = sorted([e for e in exs if len(e["members"]) >= 20], key=lambda e: -len(e["members"]))

# Japanese names for countries/industries, keyed by English label (scripts/fetch_ja_labels.py).
ja_path = os.path.join(os.path.dirname(__file__), "ja_labels.json")
ja = json.load(open(ja_path)) if os.path.exists(ja_path) else {}
for key in ("countries", "industries"):
    out[key + "_ja"] = [ja.get(key, {}).get(n) for n in out[key]]
dst = os.path.join(os.path.dirname(__file__), "..", "public", "data", "graph.json")
json.dump(out, open(dst, "w"), ensure_ascii=False, separators=(",", ":"))
print(len(out_nodes), "nodes", len(out["edges"]), "edges", os.path.getsize(dst) // 1024, "KB")
