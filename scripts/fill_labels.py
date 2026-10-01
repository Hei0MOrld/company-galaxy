# Some items have no en/ja label in SPARQL results (e.g. only a "mul" label). Fill from wbgetentities.
import json, urllib.parse, urllib.request, urllib.error, time
raw = json.load(open("raw.json"))
kept = {n[0] for n in json.load(open("../public/data/graph.json"))["nodes"]}
missing = [n for n in raw["nodes"] if not n["en"] and not n["ja"] and n["id"] in kept]
by_id = {n["id"]: n for n in missing}
ids = list(by_id)
PREF = ["mul", "en", "ja", "de", "fr", "es", "it", "nl", "pt", "ru", "zh", "ko", "cs", "nb", "sv", "pl"]
for i in range(0, len(ids), 50):
    url = "https://www.wikidata.org/w/api.php?" + urllib.parse.urlencode({
        "action": "wbgetentities", "ids": "|".join(ids[i:i+50]), "props": "labels", "format": "json"})
    req = urllib.request.Request(url, headers={"User-Agent": "company-graph/0.1 (hobby project)"})
    for attempt in range(6):
        try:
            ents = json.load(urllib.request.urlopen(req, timeout=60))["entities"]; break
        except urllib.error.HTTPError as err:
            if err.code != 429: raise
            time.sleep(10 * (attempt + 1))
    for q, e in ents.items():
        labels = e.get("labels", {})
        lang = next((l for l in PREF if l in labels), next(iter(labels), None))
        if lang:
            by_id[q]["en"] = labels[lang]["value"]
            if "ja" in labels: by_id[q]["ja"] = labels["ja"]["value"]
    time.sleep(1.5)
json.dump(raw, open("raw.json", "w"), ensure_ascii=False)
print("filled", sum(1 for n in missing if n["en"]), "of", len(missing))
