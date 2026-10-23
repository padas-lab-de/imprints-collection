# German Imprints Collection

This repository contains the data collection and automated annotation pipeline used to build the **German Imprints Dataset**, which forms the foundation of the WebKurator.de platform.

The project enables large-scale extraction of postal addresses from legal imprint pages (*Impressum*) and automated topic classification using Large Language Models (LLMs), followed by geocoding of extracted addresses.

The resulting dataset can be used for regional web analysis, web curation, and selective web archiving.

---

## Repository Structure

* `datasets/seed_hosts.txt.gz`  
  Large list of seed hosts used for the collection (compressed due to large file size). Contains 6.56 million hosts.

* `datasets/small_sample_seed_hosts.txt`  
  Smaller sample (1,000 hosts) for testing the full pipeline.

<details>
<summary>Excerpt of <code>small_sample_seed_hosts.txt</code></summary>

```
www.rodeneggerhof.com
www.rodener-geschichtskreis.de
www.rodeneza.com
www.rodenhaeuser-kollegen.de
www.rodenhausen-electronic.de
www.rodenhausen.ch
www.rodenhausen.de
www.rodenhiser.com
www.rodenhouse-inc.com
www.rodenkirchen-aero.de
www.rodenkirchen-immobilien.de
www.rodenkirchen-steuerberater.de
www.rodenkirchen-werbetechnik.de
www.rodenkirchener-unternehmerinnen.de
www.rodenkirchenerpartyservice.de
www.rodenleather.com
www.rodenrothmotors.com
www.rodenstein-apotheke-weinheim.de
www.rodenstein-apotheke.de
www.rodenstein-cup.de
www.rodenstein-parfuemerie.de
www.rodensteiner-knappen.de
www.rodensteiner.ch
www.rodensteinerfashionmarkt.de
www.rodensteinerhof.de
www.rodensteinmuseum.de
www.rodensteinrecords.de
www.rodensteinschule-fraenkisch-crumbach.de
www.rodenstock-gfu.de
www.rodenstock-instruments.de
```

</details>

The seed list is pre-filtered to remove:

* spam and adult content
* crawler traps and problematic streaming pages
* redirects to major platforms (e.g., Facebook, YouTube, Instagram)

---

## Install Dependencies

There are two ways to install the dependencies and run the code.

### Using Poetry (recommended)

If you have the [Poetry](https://python-poetry.org/) package manager for Python installed already, you can simply set up everything with:

```console
poetry install
source $(poetry env info --path)/bin/activate
```

After the installation of all dependencies, you will end up in a new shell with a loaded venv. In this shell, you can run the main `ic` command. You can exit the shell at any time with `exit`.

```console
ic --help
```

To install new dependencies in an existing poetry environment, you can run the following commands with the shell environment being activated:

```console
poetry lock
poetry install
```

### Using Pip (alternative)

You can also create a venv yourself and use `pip` to install dependencies:

```console
python3 -m venv venv
source venv/bin/activate
pip install .
```

---

## Development

### Run Code Formatting

To run the code formatting, you can use the following command:

```console
isort .
black .
```

The order of the commands is important. `isort` will sort the imports in the files, and `black` will format the code.

---

## Environment Configuration

Create a `.env` file based on `.env.template`.

You must define:

* LLM API endpoint and API key
* Geocoding API endpoint (e.g., Photon)

Example for a local LLM deployment:

```env
MODEL_API_ENDPOINT = "https://llms.innkube.fim.uni-passau.de"
MODEL_API_KEY      = "sk-****"
```

Example for a local Photon instance:

```env
GEOCODING_API_ENDPOINT = "http://localhost:2322/api"
```

---

## Prompts and Annotation Code

* Topic classification prompts:
  `prompts/topic_classification/`

* Address extraction prompts:
  `prompts/address_extraction/`

* LLM processing implementation:
  `src/ic/cli/process_llm.py`

---

# Run the Pipeline

The pipeline consists of five main steps:

1. Fetch websites
2. Run LLM processing (topic + address extraction)
3. Geocode addresses
4. Merge results
5. Generate statistics

---

## 1. Fetch Imprints

To test the pipeline with the small sample:

```console
ic fetch small_sample_seed_hosts.txt
```

---

## 2. Run LLM Processing

This step performs:

* Topic classification
* Address extraction from imprint pages

```console
ic process-llm MODEL --topic
```

Replace `MODEL` with the name of your model. The `src/ic/config.py` file contains a dictionary of supported models, currently this is `Qwen3-Next`. You can add new models there if needed.

LLM results are stored in a subfolder named after the model.
This allows easy comparison of different models (e.g., ablation studies or prompt variations).

---

## 3. Geocode Extracted Addresses

After LLM processing:

```console
ic geocode MODEL
```

The `MODEL` argument is required because geocoding operates on the model-specific output directory.

We recommend running a local [Photon](https://photon.komoot.io/) instance to avoid dependency on proprietary services. Find instructions for setting up Photon in the [GitHub repository](https://github.com/komoot/photon).

---

## 4. Merge Results

This merges:

* LLM topic classification
* Extracted addresses
* Geocoded information

```console
ic merge MODEL
```

---

## 5. Generate Statistics

To compute dataset statistics:

```console
ic stats MODEL
```

This produces statistics such as:

* Number of imprints with extracted addresses
* Number of successfully geocoded addresses
* Topic distribution

---

## 6. Evaluate Against the Gold Standard

The 1,000 manually annotated pages in `evaluation/gold_standard_data.jsonl` are used to measure address extraction and topic classification quality:

```console
ic evaluate MODEL [LANGUAGE] [PROMPT_TYPE] [--limit N] [--retry-failed]
ic evaluate MODEL [LANGUAGE] [PROMPT_TYPE] --score-only
```

The first command runs the address and topic prompts over the gold items (resumable, ids already in `predictions.jsonl` are skipped) and scores them. `--score-only` only re-scores stored predictions. Output goes to `results/MODEL/LANGUAGE/PROMPT_TYPE/eval/`:

* `predictions.jsonl`: predicted address, topic, raw responses and token usage
* `metrics.json`: address accuracy per field (exact and normalized) and all-fields-correct rate; topic accuracy, macro-F1, per-class precision/recall/F1 and confusion matrix
* `errors.jsonl`: per-item errors for error analysis

Predicted topics are mapped up to their top-level category and compared at the level of the 11 gold classes. Run the tests from the repository root with `pytest`.

---

# Output Format

The final output file is located under:

```
results/MODEL/PROMPT_LANGUAGE/PROMPT_TYPE/final/*.jsonl.gz
```

Example:

```
results/Qwen3-Next/german/simple/final/*.jsonl.gz
```

Each line in the compressed JSONL file has the following structure:

<details>
<summary>Exemplary entry in the final dataset (JSON)</summary>

```json
{
  "host":"www.villa-butterblume.de",
  "main":{
    "url":"https://www.villa-butterblume.de",
    "title":"Butterblume - Willkommen",
    "description":"Butterblume, Bielefeld, Kita, Kindergarten, Elterninitiative, vegetarisch, zuckerfrei, Montessori",
    "keywords":"Gemeinn\u00fctziger, Verein, sozialer, Verein, Wohlt\u00e4tigkeit, Benefiz, gemeinn\u00fctzig, sozial, Veranstaltungen",
    "author":null,
    "main_content":"Die Kindertagesst\u00e4tte \"Villa Butterblume\" hat ihre T\u00fcren ge\u00f6ffnet.\n\nDie \"Butterblume\" ist eine Elterninitiative - gemeinsam arbeiten wir daran, einen besonderen Lern- und Lebensort f\u00fcr Kinder zu gestalten.\n\n\u00a0\n\nHierbei sind uns eine an die Montessorip\u00e4dagogik angelehnte Arbeit, Naturn\u00e4he sowie eine gesundheitsf\u00f6rderliche Ern\u00e4hrung der Kinder wichtig.\n\n\u00a0\n\nSo erreichen Sie uns:\n\n\u00a0\n\nVilla Butterblume\n\nSudbrackstra\u00dfe 43\n\n33611 Bielefeld\n\n\u00a0\n\nTelefon: 0521 39952874\n\nleitung@villa-butterblume.de\n\nUnser Laternenfest\n\nEndlich hie\u00df es wieder Laterne, Laterne... Bei sch\u00f6nstem Herbstwetter sind wir in diesem Jahr mit unseren Gespenster- und Raupenlaternen durch den Nordpark spaziert und haben an verschiedenen Kerzenstationen unsere Laternenlieder gesungen. Es war ein sch\u00f6ner Abend, den wir bei Suppe und hei\u00dfen Getr\u00e4nken an der Kita ausklingen lie\u00dfen.\u00a0\n\nNaturerlebnistag\n\nIn diesem Jahr ging unser Kitaausflug zum Naturgel\u00e4nde Primelgr\u00fcn. Ein bisschen nass war der Tag, aber im Gr\u00fcnen gab es viel zu entdecken und matschen. Wir konnten schnitzen, Holzzauberst\u00e4be herstellen, Feuer machen und picknicken. Wir freuen uns schon auf den n\u00e4chsten Ausflug, der uns sicher wieder in \"ein gr\u00fcnes Klassenzimmer\" f\u00fchren wird.\n\nDankesch\u00f6n an Firma Wolff f\u00fcr eine tolle Weihnachts\u00fcberraschung\n\nEin gro\u00dfes Dankesch\u00f6n an Firma Wolff aus unserer Nachbarschaft, die uns mit einer wunderbaren Weihnachts\u00fcberraschung erfreut hat. Wir durften unsere W\u00fcnsche wie B\u00fccher, Kreativmaterialien oder Spiele f\u00fcr die Raupen- und die Grash\u00fcpfergruppe an den weihnachtlichen Wunschbaum der Firma h\u00e4ngen, und wenig sp\u00e4ter erreichte uns eine prall gef\u00fcllte, liebevoll verpackte Geschenkkiste mit all den erf\u00fcllten W\u00fcnschen. Viel Spa\u00df hatten die Kinder in der Kita\u00a0 dann am letzten Tag vor Weihnachten beim Auspacken und Bespielen der neuen Sch\u00e4tze.\n\nBuntes Miteinander am Gartentag\n\n\u00a0\n\n\u00a0\nAm Samstag, den 21. September 2024 fand bei strahlendem Sonnenschein unser traditioneller Gartentag in der Kita Villa Butterblume statt. Rund 15 Eltern und ebenso viele Kinder packten gemeinsam an, um den Garten der Kita auf Vordermann zu bringen. Es wurden Hecken und B\u00e4ume zur\u00fcckgeschnitten, Unkraut gej\u00e4tet und kleinere Reparaturen durchgef\u00fchrt \u2013 jeder brachte sich tatkr\u00e4ftig ein.\n\u00a0\nNat\u00fcrlich blieb neben all der Arbeit auch genug Zeit, um sich auszutauschen und miteinander zu quatschen. Beim gemeinsamen Mittagessen wurden die mitgebrachten Salate genossen, und es wurde flei\u00dfig gegrillt. So wurde der Gartentag nicht nur ein produktiver, sondern auch ein geselliger Tag f\u00fcr Gro\u00df und Klein.\n\u00a0\nDer Gartentag ist ein wichtiger Teil unseres Kita-Lebens und findet zweimal im Jahr statt. Die Teilnahme an mindestens einem der beiden Tage ist f\u00fcr alle Familien verpflichtend, die keine gesonderten Aufgaben im Verein der Kita \u00fcbernehmen. So tragen alle zum Erhalt der Kita bei und leisten pro Familie 20 Arbeitsstunden im Jahr.\n\u00a0\n\nEin herzliches Dankesch\u00f6n an alle, die am Samstag mit dabei waren! Gemeinsam sorgen wir daf\u00fcr, dass unsere Kita ein sch\u00f6ner und sicherer Ort f\u00fcr unsere Kinder bleibt.\n\n10 Jahre Villa Butterblume. Das war uns ein rauschendes Fest wert.....\n\nAm 13.08.2022 haben wir unser 10j\u00e4hriges Jubil\u00e4um gefeiert.\n\n\nEs war ein sch\u00f6ner Tag mit vielen Menschen, die die Butterblume begleitet haben und aktuell begleiten, vielen tollen Attraktionen, sonnigem Wetter und guter Laune im sch\u00f6nen Bauernhausmuseum Bielefeld.\n\n\nDanke sagen wir allen Eltern der Kita, die dieses Fest auf die Beine gestellt haben.\n\n\nWir danken Arminia Bielefeld, Thalia, Firma Halfar, den Stadtwerken Bielefeld und Playmobil f\u00fcr das Erm\u00f6glichen unserer Tombola, welche sehr viele Kinderherzen hat h\u00f6her schlagen lassen.\n\n\nWeitere Eindr\u00fccke des Tages k\u00f6nnen Sie auf unserer Homepage unter \"Kita-Leben\" finden.\n\nDruckversion | Sitemap\n\u00a9 Butterblume\nLogin\n\nWebansichtMobile-Ansicht\n\nLogout | Seite bearbeiten",
    "content_length":3852,
    "content_language":"deu",
    "address":[
      
    ],
    "coords":[
      
    ]
  },
  "impressum":{
    "url":"https://www.villa-butterblume.de/impressum-datenschutz/",
    "title":"Butterblume - Impressum & Datenschutz",
    "description":"Butterblume, Bielefeld",
    "keywords":"Impressum",
    "author":null,
    "main_content":"Impressum\n\nKindertagesst\u00e4tte \"Villa Butterblume\"\nSudbrackstr. 43\n33613 Bielefeld\n\u00a0\n\nVerein: Butterblume e.V.\nSitz: Bielefeld\n\u00a0\n\nTelefon: 0521 39952874\nE-mail: leitung@villa-butterblume.de\nInternet: www.villa-butterblume.de\n\n\u00a0\n\nRegistergericht: Amtsgericht Bielefeld\nVereinsregisternummer: 4201\n\nSteuernummer: 305/5972/1414\n\u00a0\n\nVertretungsberechtige Vorstandsmitglieder:\n\nSalome Brand\n\nKim Mercedes Wollschl\u00e4ger\n\n\u00a0\n\nHaftungsausschluss:\n\nTrotz sorgf\u00e4ltiger inhaltlicher Kontrolle \u00fcbernehmen wir keine Haftung f\u00fcr den Inhalt von verlinkten Seiten. Daf\u00fcr sind ausschlie\u00dflich deren Betreiber verantwortlich.\n\n\u00a0\n\nHaftungsanspr\u00fcche, die sich auf Sch\u00e4den materieller oder ideeller Art beziehen, die durch die Nutzung oder Nichtnutzung der dargebotenen Informationen verursacht wurden, sind grunds\u00e4tzlich ausgeschlossen.\n\nDruckversion | Sitemap\n\u00a9 Butterblume\nLogin\n\nWebansichtMobile-Ansicht\n\nLogout | Seite bearbeiten",
    "content_length":907,
    "content_language":"deu",
    "address":[
      
    ],
    "coords":[
      
    ]
  },
  "datenschutz":{
    "url":"https://www.villa-butterblume.de/impressum-datenschutz/",
    "title":"Butterblume - Impressum & Datenschutz",
    "description":"Butterblume, Bielefeld",
    "keywords":"Impressum",
    "author":null,
    "main_content":"Impressum\n\nKindertagesst\u00e4tte \"Villa Butterblume\"\nSudbrackstr. 43\n33613 Bielefeld\n\u00a0\n\nVerein: Butterblume e.V.\nSitz: Bielefeld\n\u00a0\n\nTelefon: 0521 39952874\nE-mail: leitung@villa-butterblume.de\nInternet: www.villa-butterblume.de\n\n\u00a0\n\nRegistergericht: Amtsgericht Bielefeld\nVereinsregisternummer: 4201\n\nSteuernummer: 305/5972/1414\n\u00a0\n\nVertretungsberechtige Vorstandsmitglieder:\n\nSalome Brand\n\nKim Mercedes Wollschl\u00e4ger\n\n\u00a0\n\nHaftungsausschluss:\n\nTrotz sorgf\u00e4ltiger inhaltlicher Kontrolle \u00fcbernehmen wir keine Haftung f\u00fcr den Inhalt von verlinkten Seiten. Daf\u00fcr sind ausschlie\u00dflich deren Betreiber verantwortlich.\n\n\u00a0\n\nHaftungsanspr\u00fcche, die sich auf Sch\u00e4den materieller oder ideeller Art beziehen, die durch die Nutzung oder Nichtnutzung der dargebotenen Informationen verursacht wurden, sind grunds\u00e4tzlich ausgeschlossen.\n\nDruckversion | Sitemap\n\u00a9 Butterblume\nLogin\n\nWebansichtMobile-Ansicht\n\nLogout | Seite bearbeiten",
    "content_length":907,
    "content_language":"deu",
    "address":[
      
    ],
    "coords":[
      
    ]
  },
  "kontakt":{
    "url":"https://www.villa-butterblume.de/impressum-datenschutz/kontakt/",
    "title":"Butterblume - Kontakt",
    "description":"Butterblume, Bielefeld",
    "keywords":"Kontakt",
    "author":null,
    "main_content":"Kontakt\n\nKindertagesst\u00e4tte \"Villa Butterblume\"\nSudbrackstra\u00dfe 43\n33611 Bielefeld\n\nTel: 0521 39952874\n\n\nAngela Kronshage\nLeitung\nleitung@villa-butterblume.de\n\nDruckversion | Sitemap\n\u00a9 Butterblume\nLogin\n\nWebansichtMobile-Ansicht\n\nLogout | Seite bearbeiten",
    "content_length":253,
    "content_language":"deu",
    "address":[
      
    ],
    "coords":[
      
    ]
  },
  "topic":"Kindertagesst\u00e4tte",
  "address":{
    "country":"Deutschland",
    "town":"Bielefeld",
    "postalcode":"33613",
    "streetname":"Sudbrackstr.",
    "housenumber":"43"
  },
  "coords":{
    "longitude":8.53288698709467,
    "latitude":52.041731353304684,
    "num_features":6,
    "features":[
      {
        "type":"Feature",
        "properties":{
          "osm_type":"W",
          "osm_id":27329466,
          "osm_key":"highway",
          "osm_value":"residential",
          "type":"street",
          "postcode":"33611",
          "countrycode":"DE",
          "name":"Sudbrackstra\u00dfe",
          "country":"Deutschland",
          "city":"Bielefeld",
          "district":"Schildesche",
          "locality":"Sudbrack",
          "state":"Nordrhein-Westfalen",
          "extent":[
            8.5322363,
            52.0418853,
            8.5331321,
            52.0410848
          ]
        },
        "geometry":{
          "type":"Point",
          "coordinates":[
            8.53288698709467,
            52.041731353304684
          ]
        }
      },
      {
        "type":"Feature",
        "properties":{
          "osm_type":"W",
          "osm_id":438000545,
          "osm_key":"highway",
          "osm_value":"tertiary",
          "type":"street",
          "postcode":"33611",
          "countrycode":"DE",
          "name":"Sudbrackstra\u00dfe",
          "country":"Deutschland",
          "city":"Bielefeld",
          "district":"Mitte",
          "state":"Nordrhein-Westfalen",
          "extent":[
            8.5352852,
            52.037243,
            8.5386869,
            52.0360543
          ]
        },
        "geometry":{
          "type":"Point",
          "coordinates":[
            8.536964099789769,
            52.036581594653924
          ]
        }
      },
      {
        "type":"Feature",
        "properties":{
          "osm_type":"W",
          "osm_id":469353408,
          "osm_key":"highway",
          "osm_value":"tertiary",
          "type":"street",
          "postcode":"33613",
          "countrycode":"DE",
          "name":"Sudbrackstra\u00dfe",
          "country":"Deutschland",
          "city":"Bielefeld",
          "district":"Schildesche",
          "locality":"Sudbrack",
          "state":"Nordrhein-Westfalen",
          "extent":[
            8.527596,
            52.0471868,
            8.5277936,
            52.0468322
          ]
        },
        "geometry":{
          "type":"Point",
          "coordinates":[
            8.527682057285471,
            52.04700236732422
          ]
        }
      },
      {
        "type":"Feature",
        "properties":{
          "osm_type":"N",
          "osm_id":645407062,
          "osm_key":"highway",
          "osm_value":"bus_stop",
          "type":"house",
          "postcode":"33611",
          "countrycode":"DE",
          "name":"Sudbrackstra\u00dfe",
          "country":"Deutschland",
          "city":"Bielefeld",
          "district":"Mitte",
          "street":"Sudbrackstra\u00dfe",
          "state":"Nordrhein-Westfalen"
        },
        "geometry":{
          "type":"Point",
          "coordinates":[
            8.538076,
            52.0362603
          ]
        }
      },
      {
        "type":"Feature",
        "properties":{
          "osm_type":"W",
          "osm_id":130433827,
          "osm_key":"building",
          "osm_value":"kindergarten",
          "type":"house",
          "postcode":"33611",
          "housenumber":"43",
          "countrycode":"DE",
          "country":"Deutschland",
          "city":"Bielefeld",
          "district":"Mitte",
          "street":"Sudbrackstra\u00dfe",
          "state":"Nordrhein-Westfalen",
          "extent":[
            8.5323298,
            52.0382809,
            8.5326347,
            52.0381655
          ]
        },
        "geometry":{
          "type":"Point",
          "coordinates":[
            8.532479053753754,
            52.0382247
          ]
        }
      },
      {
        "type":"Feature",
        "properties":{
          "osm_type":"W",
          "osm_id":164365118,
          "osm_key":"railway",
          "osm_value":"platform",
          "type":"house",
          "postcode":"33611",
          "countrycode":"DE",
          "name":"Sudbrackstra\u00dfe",
          "country":"Deutschland",
          "city":"Bielefeld",
          "district":"Mitte",
          "street":"Schildescher Stra\u00dfe",
          "state":"Nordrhein-Westfalen",
          "extent":[
            8.5389829,
            52.0366014,
            8.5391445,
            52.0360089
          ]
        },
        "geometry":{
          "type":"Point",
          "coordinates":[
            8.539086874908559,
            52.036328049999995
          ]
        }
      }
    ]
  },
  "region":{
    "country":"Germany",
    "state":"Nordrhein-Westfalen",
    "district":"Detmold",
    "county":"Bielefeld"
  }
}
```

</details>

---

## License

This repository is licensed under the MIT License. See the LICENSE file for details.
