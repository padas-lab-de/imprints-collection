# D49-topic-study-setup (2026-11-09, gold-set module)

Context: the user asked for a study of the best LLM prompting strategy to classify a website (homepage and/or imprint) into a given topic schema, for two schemas:
- POI schema: topics/poi_v2.jsonl (user upload "categories_20260311_KOPIE_V2.jsonl"; 796 names, same names and order as topics/categories.jsonl, but 400 parents changed: 10 roots marked with parent == name, max depth 2, inner nodes Ausbildung, Finanzdienstleistung, Gesundheits- und Schönheitsservice, Strafverfolgung und öffentliche Sicherheit, Lebensmittel- und Getränkeeinzelhandel; roots "Ereignis" and "Sehenswürdigkeiten und im Freien" have no children; duplicate names Karaoke-Bar, Rathaus, Rettungsdienst).
- Business schema: Klassifikation der Wirtschaftszweige (WZ 2025), Bundesagentur für Arbeit page https://statistik.arbeitsagentur.de/DE/Navigation/Grundlagen/Klassifikationen/Klassifikation-der-Wirtschaftszweige/Klassifikation-der-Wirtschaftszweige-Nav.html
The goal is a trade-off: the deepest hierarchy level that is predicted reliably and precisely, not necessarily the leaf. Experiment: E49-topic-schema-strategy.

Questions asked (lead, AskUserQuestion) and answers (user, 2026-11-09):
1. Reference labels: "Agent dev set (Recommended)": Claude subagents label ~200 gold hosts in both schemas at all levels from the captured homepage and imprint text; double-checked; lead verifies a sample; no API cost. Human gold labels later confirm the winner.
2. Gold labelling also labels the new schemas: "Yes, after the study (Recommended)": the tool asks for both schemas at the level the study picks; labelling starts after that.
3. Label count: "One main + optional extra (Recommended)": score on the main category; up to 2 extra for a lenient score.
4. Models: "Innkube only for now (Recommended)": qwen38-27b, gemma4-31b-it, qwen-agentworld-35b-a3b, soofi-s-isar-preview (+ octen-embedding-8b, qwen3-reranker-4b for candidate narrowing). No OpenRouter key in .env.

Lead calls (assumed): topics/poi_v2.jsonl is added next to topics/categories.jsonl; production (`ic process-llm`) is not changed until the study ends.
