# Company Galaxy

Explore parent / subsidiary / ownership links between ~23,500 companies in 3D or 2D.

- Data: [Wikidata](https://www.wikidata.org/) (CC0) — `P749` parent organization, `P355` subsidiary, `P127` owned by; companies = items with an industry (`P452`), minus schools/municipalities/etc.
- Rendering: [3d-force-graph](https://github.com/vasturiano/3d-force-graph) / [force-graph](https://github.com/vasturiano/force-graph)
- Not every company, and Wikidata is not always up to date.

Rebuild data:
```
cd scripts
# download edges (see git history for the SPARQL), then
python3 fetch_nodes.py && python3 fill_labels.py && python3 build.py
```
