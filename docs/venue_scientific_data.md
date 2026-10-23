# Venue research: Nature Scientific Data (Data Descriptor)

Researched 2026-10-23 from primary pages (fetched directly, full text read). Abbreviations: SD = Scientific Data.
Sources used throughout:
- [SG] https://www.nature.com/sdata/publish/submission-guidelines
- [DP] https://www.nature.com/sdata/policies/data-policies
- [REPO] https://www.nature.com/sdata/policies/repositories
- [APC] https://www.nature.com/sdata/publish/open-access
- [CODE] https://www.nature.com/sdata/policies/editorial-and-publishing-policies (section "Code availability")
- [EX] https://www.nature.com/articles/s41597-026-07945-2 (the model article)

## 1. Data Descriptor structure and limits

Order of sections [SG]: Title, Abstract, Background & Summary, Methods, Data Records, Data Overview (optional), Technical Validation, Usage Notes (optional), Data Availability, Code Availability, References, Author Contributions, Competing Interests, Acknowledgements (optional), Funding, Ethics statement (where relevant for human studies; recommended as a sub-heading in Methods).

| Item | Rule | Source |
|---|---|---|
| Title | max 110 characters incl. spaces; no colons or parentheses; no acronyms, no dataset brand names; capitalise first word and proper nouns only | [SG] |
| Abstract | recommended max 170 words; describes data and reuse, no claims of new scientific findings, no sub-headings, no download URLs | [SG] |
| Main text / Methods | no word limit ("no word length limits"; journal not printed) | [SG] |
| Figures | recommended max 8 (not a mandate); legends max 350 words; avoid general summaries/results figures | [SG] |
| Tables | recommended max 10; tables longer than one A4 page become Supplementary Tables; large tables (100s of rows) belong in the repository, not as supplement | [SG] |
| References | numbered; datasets cited via data-citation format (authors, title, repository, DOI, year) | [SG] |
| Review file | single PDF with figures/tables embedded is enough for round 1; revised version needs .docx or .tex plus separate figure files | [SG] |

Content of each section [SG]:
- Background & Summary: motivation, overview of dataset, potential reuse; cite and briefly summarise any previous publications that used the data (this is where the WebSci demo paper goes); cite some related datasets; no subjective novelty/impact claims.
- Methods: steps to create the data, experimental design, acquisition and computational processing. For secondary data: exact input data at a level that allows sourcing it (no bare homepages; give version or search terms). No general results or analyses anywhere in the paper. Previously published methods may be cited rather than restated.
- Data Records: what the dataset contains, repository, files, formats, folder structure, definitions of bespoke column names; cite each dataset with the data-citation format; no summary statistics here.
- Data Overview (optional): single paragraph plus 1-2 figures/tables of descriptive statistics. SD "do[es] not recommend" descriptive statistics at all because users can compute them; larger amounts "will be requested removed or reduced" [SG].
- Technical Validation: "the experiments, analyses or checks needed to support the technical quality of the dataset, with any supporting figures and tables" [SG]. This is the only place where evaluation numbers are expected.
- Usage Notes (optional): technical notes on access/processing. Explicitly not conclusions, selling points or worked case studies, "as we do not publish these" [SG].
- Data Availability: short statement repeating the Data Records (URLs, DOIs, accession numbers) [SG].
- Code Availability: mandatory statement on whether/how custom code can be accessed; may include software versions and parameters used to generate the dataset [SG]. Policy: authors must make previously unreported custom code available to editors, reviewers and readers; recommends GitHub plus a DOI repository (Zenodo/figshare) [CODE].

## 2. The example article [EX]

Title: "A manually interpreted geo-dataset of building footprints in complex urban poverty areas across the globe". Received 9 Mar 2026, accepted 17 Jul 2026, published 3 Aug 2026 (about 4.5 months), CC BY 4.0 article [EX].

Important observation: it is a remote-sensing, manually digitised geodata set (321,075 building polygons, 4,661 blocks, 44 areas, 35 cities). It is topically far from web crawling and has no LLM pipeline. As a structural model it is only partly useful; see the caveats below.

| Example section | Content | What the Imprints project would put there |
|---|---|---|
| Abstract (~150 words) | gap, dataset size, method, three uses, "we release data, guidelines, validation" | scale (hosts, imprints, addresses), fetch+LLM+geocode method, release of data with evaluation |
| Background | SDG motivation, prior datasets (aggregated or low accuracy), earlier publications from which the data derive, statement "we provide it free of charge for the first time" | web archiving / regional web curation need; Common Crawl style corpora lack regional/address metadata; WebSci demo paper (arXiv 2609.03971) as prior publication; WebKurator.de |
| Methods: Data sources | imagery sources, selection criteria for 44 areas (six listed criteria), time steps | seed list (6.56M hosts, how built, filtering), crawl dates, fetch rules, link expansion, imprint detection |
| Methods: protocol | numbered mapping protocol, minimum mapping unit, rules for ambiguous cases | imprint-page detection rules, LLM prompts (prompts/), models, temperature, topic taxonomy, geocoding procedure |
| Data Records | formats (Shapefile), three datasets, attribute table (Table 1), download URL at DLR, study-site table in supplement | JSONL/Parquet files, per-field definitions (address fields, topic classes, coordinates, status codes), folder structure, DOI |
| Technical Validation | inter-rater reliability (Fleiss kappa 0.4-0.6 less complex, 0.3-0.4 complex; coefficient of variation of counts 20-30%), cited from an earlier study; qualitative interpreter effects; rationale text; one figure of density/size consistency | gold-set evaluation: address field accuracy, topic accuracy and macro-F1, geocoding accuracy, fetch precision/recall sample, second-annotator agreement, model comparison, error analysis |
| Usage Notes and Discussion | uncertainty advice, comparison to automated global building datasets, ethics paragraph "None of the building polygons can be traced back to any personal information" | known biases (TLD, JS-only sites, parked domains), personal-data handling, how to filter, known limits of topic evaluation |
| Data Availability | DLR-hosted, CC BY, DOI "following publication" | repository + DOI + licence |
| Code Availability | "No executable code is provided", formulas given instead | our case differs: `ic` pipeline must be released (Zenodo-archived GitHub release) |

Counts [EX]: 5 figures, 1 table (attribute table) plus Supplementary Table 1. Technical Validation is short and mostly cites prior work (ref 40); it contains agreement statistics, not performance against ground truth (it states ground truth is unknown). Methods is long and protocol-like. The example also includes a "Usage Notes and Discussion" heading with substantial discussion and literature comparison, which is looser than the stated guideline [SG]; do not rely on that being accepted for us.

Data hosting detail: hosted by the authors' institution (DLR geoservice file server) with a DOI to follow, CC BY [EX]. This suggests an institutional repository is accepted if it meets the repository requirements (see section 3), but SD says personal/informal sites are insufficient unless they meet requirements [DP].

Caveat: the user pointed at this article as a model. For a closer analogue (large LLM-processed text corpus with Technical Validation based on human review) a search found another SD descriptor, https://www.nature.com/articles/s41597-026-07753-8 (food-security data usage descriptors; LLM agreed with at least one human reviewer 80%, humans with each other 94.7%, per search snippet only, not read in full) and https://www.nature.com/articles/s41597-025-05274-4 (gold-standard NER dataset, verification steps). Not verified in depth; treat as leads.

## 3. Data availability, repositories, licensing, code

| Requirement | Detail | Source |
|---|---|---|
| Deposit timing | Round 1: data downloadable by reviewers via any URL with anonymous download (can be a temporary cloud link). From round 2: public in a formal repository. Recommended: live in the repository from the start | [SG], [REPO] |
| Repository | Must give persistent identifier (DOI default), direct https download from the DOI page, long-term preservation, anonymous peer-review route. SD does not endorse specific repositories for general data; suggests DataCite Repository Finder, FAIRsharing, re3data. Springer Nature's older recommended list (includes Zenodo, figshare) is retained but no longer enforced | [REPO] |
| Not acceptable | personal/lab websites and informal cloud storage, unless the platform meets requirements; waived for datasets >1 TB | [DP] |
| Licence (non-sensitive data) | CC0 or CC BY (or equivalent) "in most cases"; no -SA or -NC clauses except for derived data where third-party licence terms must be kept | [REPO] |
| Open at submission? | Not necessarily public at submission, but reviewers must be able to download without barriers in round 1 | [SG], [DP] |
| Compilations / copyrighted source text | Extracting small facts is fine with citation; wholesale reproduction of text or other copyrightable elements cannot be re-shared without permission unless the source is under a permissive licence; authors advised to consult institutional rights experts | [DP] |
| Updates | Describe finished datasets only; deposit a static version of what was peer reviewed; no additive updates to the paper; new descriptors for updated datasets are welcome if methods/validation changed significantly | [DP] |
| Preservation | Authors commit to preserve data at least 5 years after publication | [DP] |
| Code | Custom code must be available to editors/reviewers/readers; GitHub + Zenodo or figshare DOI recommended; Code Availability statement mandatory even if no code | [CODE], [SG] |
| Size | no stated size limit; >1 TB relaxes some rules | [DP] |

## 4. Personal data and web-scraped data

What SD says [DP]:
- SD's "Human Data" policy targets "sensitive human data": information from human participants or patients where sharing "may put those individuals at risk of harm"; data "simply of human origin but not subject to specific risks" is distinguished from it. Main criterion is anonymity; highest risk is identifiable data combined with sensitive fields (religion, race, health, sexual identity, politics).
- Authors of a human-derived dataset must submit the Human Data Checklist. Open route needs data "fully anonymised or exhibit extremely low risks of re-identification and/or do not contain any sensitive fields". Otherwise controlled access (registration, Data Usage Agreement, verified users). "As open as possible, as closed as necessary".
- Secondary data from public sources: usually not under the human-data policy, but authors must check the right to redistribute; ethics approval for secondary use not required by the journal.
- Closest analogue to our case: social media outputs "are classed as human data and cannot typically be indexed or re-published without participant consent", regardless of copyright or platform terms, because they may be personal data "not knowingly made publicly, even if available to all". Exemptions possible for corporate/official accounts. "Re-sharing data from more transactional outputs, such as classified advertisements, or messaging apps is rarely supported even when ... publicly available." Aggregated or non-personal statistics are typically allowed. An editor could treat Impressum data of private persons similarly. This is inference, not a stated rule for Impressum.
- Editors can override: if the editor judges data more sensitive than open sharing allows, controlled access may be requested [DP].

German/EU law (authoritative statute texts; this is not legal advice, flag for counsel/data protection officer):
- Impressum duty: section 5 Digitale-Dienste-Gesetz (DDG) requires providers of business-like digital services to keep name, address (for legal persons also form, representative), electronic contact details, register data etc. permanently available: https://www.gesetze-im-internet.de/ddg/__5.html . This publication is mandated for commercial/"geschaeftsmaessig" services, so private hobby sites need not have one; sole traders and freelancers do, with a natural person's name and address. The legal purpose is provider identification, not free reuse; legal publicity does not by itself settle GDPR lawfulness of a secondary dataset (my inference, not found in a source).
- Research provisions: section 27 BDSG allows processing of special categories of data (Art. 9 GDPR) for research without consent when necessary and interests overwhelmingly prevail, restricts data-subject rights (Art. 15, 16, 18, 21) where they would make research impossible or seriously impair it, and requires anonymisation as soon as the research purpose permits: https://www.gesetze-im-internet.de/bdsg_2018/__27.html . That section covers special-category data; names/addresses/phones/emails are ordinary personal data, so Art. 6 GDPR (e.g. legitimate interests, Art. 6(1)(f); research safeguards in Art. 89) is the relevant ground. I did not find a source applying this to Impressum data; the web search returned only practical Impressum guidance, nothing on research reuse.
- Not found: any authoritative statement on whether releasing a dataset of Impressum addresses publicly is lawful. Needs the university's data protection officer. Also not checked: Austrian/Swiss law (the dataset includes .at/.ch), database-right and copyright of Impressum text, robots.txt/TDM exception (section 60d UrhG).

## 5. APC and peer review

- APC: GBP 2,150 / USD 2,690 / EUR 2,390, plus VAT where applicable; price fixed at acceptance date; waivers for lowest-income countries, case-by-case otherwise; Springer Nature institutional open-access agreements may cover it (check Uni Passau eligibility) [APC]. APC waiver or discount requests go in the submission system, not the cover letter [SG].
- Review process: initial technical check (files, data, code, scope); reviewers get about 10 days; typically two rounds; one month for revisions; editorial board member handles; no impact assessment, in-scope technically sound papers go to review [SG].
- Reviewers access data: round 1 via anonymous download URL; access instructions must be in the article file itself, not the cover letter (cover letters are invisible to reviewers) [SG]. For sensitive human data, a representative non-sensitive sample or an anonymous bypass must be provided; the journal cannot vet reviewers or distribute passwords individually [DP].
- Papers outside scope (research papers without shared data) are rejected [SG].

## 6. Gap list versus current material (per docs/status.md)

| Data Descriptor need | Have | Gap |
|---|---|---|
| Dataset description, motivation | WebSci demo paper (arXiv 2609.03971), README | rewrite as descriptor; related-dataset citations (Common Crawl, etc.) |
| Methods: seed list, fetch, imprint detection | pipeline code; E4/E5 yield analysis; E6 fetch fixes in progress | final frozen crawl on the larger snapshot; versions, dates, parameters; seed list provenance (6.56M hosts) |
| Methods: LLM extraction + geocoding | code, prompts, models (Qwen3.8-27B, Gemma4-31B on innkube) | paper model Qwen3-Next no longer served; old results gone, paper numbers not reproducible (status.md); must re-run the full dataset with the model(s) that are published |
| Data Records | none | file format decision, schema/field definitions, folder structure, repository deposit with DOI |
| Technical Validation | E2: 1,000 gold items, address 0.904/0.953 and topic acc 0.736/0.752, macro-F1 ~0.6 for two models; error analysis started; D11 homepage topic eval, D12 location metric (E7 in flight); D8 plan: +300 hard items and second annotator on 200 | geocoding validation (D9: automatic consistency + manual 100), inter-annotator agreement, fetch precision sample (E6), topic eval on homepages (E7), statistics on final snapshot |
| Usage Notes | none | biases (TLD yield .de 79.7% vs .com 30.4%, JS-only sites), field semantics, empty-address caveat, known stats bug |
| Data/Code availability | repo is MIT licensed | dataset licence decision, Zenodo archive of code, repository for data |
| Personal data / ethics | none | legal assessment, data-minimisation or access-control decision, Human Data Checklist if required |
| Figures | none for the journal | study overview figure, validation figures, map of geographic distribution |

Model comparison: SD disallows results/analyses outside Technical Validation and discourages "worked case studies" [SG], so a model comparison is best framed as a Technical Validation justification for the chosen extraction model and as quality documentation, not as a headline contribution. The example descriptor treats comparison of interpreters as validation of consistency (kappa, CV) inside Technical Validation [EX]. Comparable LLM-annotation descriptors report LLM-vs-human agreement as validation (food-security descriptor, snippet-level only: https://www.nature.com/articles/s41597-026-07753-8). I did not find a descriptor with a multi-model benchmark as a main contribution; a benchmark paper would more naturally target an ML/NLP venue.

## Implications for the project

- Keep the paper a data paper: dataset size and structure in Data Records, evaluation only in Technical Validation (gold set, model comparison, error analysis, geocoding checks). Headline contributions D4 (model comparison) should be reframed accordingly; keep descriptive statistics to one short Data Overview.
- The personal-data question is the main risk. Imprints of sole traders and private persons contain names, addresses, phones, emails. SD treats re-sharing of transactional or personal-origin public posts as rarely supportable; plan for either (a) a public release with personal fields removed/reduced (e.g. drop email/phone/person names, coarsen addresses of natural persons) plus controlled access to the full data, or (b) a documented legal basis. Decide before depositing; consult the university's data protection officer.
- Plan the deposit now: Zenodo or figshare (or institutional DOI repository) with CC BY or CC0; reviewers need anonymous download in round 1, so a private-link deposit is needed at submission. Multi-GB/TB size is acceptable (>1 TB relaxes rules). Freeze a static snapshot: the paper must describe a finished dataset, no later additive updates.
- Code Availability: archive the `ic` repo on Zenodo with a DOI (MIT licence already present), record model versions, prompts, parameters, seeds.
- Budget about EUR 2,390 plus VAT APC; check whether Uni Passau has a Springer Nature open-access agreement.
- Do not copy the example's topic or Technical Validation style one to one: it is a manual geodata set whose validation rests on prior work. Our Technical Validation should present fresh numbers against ground truth, which reviewers will likely expect.
- Freeze the pipeline (E6 fetch fixes, E7 evaluation) before producing the final snapshot so that every reported number refers to the released data.

## Open questions for the user

1. Is a public release of the full address/person fields acceptable to you and Uni Passau, or should the public version be reduced (no natural-person names, emails, phones) with a controlled-access full version? Who is the data protection contact?
2. Which licence: CC BY (attribution) or CC0? Do Impressum texts raise copyright concerns you want checked?
3. Which repository (Zenodo, figshare, Uni Passau)? Is the dataset expected to exceed 1 TB?
4. Does Uni Passau have a Springer Nature open-access agreement or other APC funding?
5. Should the released data include raw Impressum text or only extracted structured fields (affects personal-data and copyright exposure and "rawness" expectations)?
6. Is the model comparison still wanted as a headline claim, given that SD limits results to Technical Validation? Alternatively split it into a separate paper?
7. Timeline: no deadline in D1; SD turnaround in the example was about 4.5 months from receipt to publication.
