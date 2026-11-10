# D50-poi-second-pass (2026-11-09, gold-set module, E49)

Context: first cleanup of topics/poi_v2.jsonl merged (9c556cc): 796 -> 779 nodes (3 duplicates, 2 empty roots, 12 near-duplicate merges, 1 wrong parent, 10 name fixes); details results/E49/poi_v2_cleanup.md. The agent left non-obvious items as they are:
- general and specific classes as siblings after the flattening (Restaurant / Italienisches Restaurant, Arzt / Kardiologe, Bar / Cocktailbar);
- overlaps across roots (Hafen oder Marina / Hafen, Berghütte / Hütte, Wohnwagenpark / Wohnmobilpark, Markt / Marktplatz, Kinderbetreuungsdienst / Kindertagesstätte / Kindergarten / Vorschule);
- possible synonyms (Fabrik / Hersteller, Lager / Lagereinrichtung, Metzger / Fleisch- und Meeresfrüchteladen / Wurstladen, Baubedarfsgeschäft / Baumarkt, Notdienst / Notfallzentrum / Notaufnahme, ...);
- questionable parents (Apotheke under Einzelhandel, natural features like Baum, Vulkan, Fluss under Sport und Freizeit, ...);
- awkward or US-centric names (Kapitolgebäude, Schwesternschaftshaus, Staats- oder Provinzpark, Kuruyemişçi-Shop, ...).

Question: second pass on these items?
Recommend B: E49 shows which overlaps cause real errors; fix those then, with evidence.
- A: second pass now: lead agent merges synonyms and moves questionable parents; user reviews the change list.
- B: leave as is; handle general-vs-specific in prompt and scoring; after the E49 pilot, fix only the classes that cause confusions.
- C: user reviews the list and edits the file personally.

Answer (user, 2026-11-10): A. Verbatim: "Regarding D50, I like your cleanup steps so far. So the duplicates removed, the empty top-level categories removed, and also the near duplicates merged, as well as the wrong parent identified. Regarding the name fixes, what I would like to ask you here is looking up the Foursquare schema. Please look it up in the internet. It was the original schema that we translated into German and then restructured. And in this process of translation and then restructuring, there might have been some mistakes or misconceptions sneaking in. And now, in the end, we actually don't need the schema in German anymore, but we need it in English. So what I would like you to ask is to connect back the German schema items to the English original ones. And in this process, go ahead with cleaning and improving the schema by merging and revising, etc. Regarding D50A concretely, go ahead with the second round now."
Action: poi_v3 in English, each node linked to its Foursquare category, second-pass cleanup (agent, E49).
