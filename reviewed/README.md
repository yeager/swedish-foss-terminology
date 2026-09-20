# Ordlistor från språkgranskningar

Denna utgåva innehåller **104 821 uppslag i 130 projektordlistor**.

[glossaries](glossaries/) innehåller CSV och TBX med korta termer och gränssnittsfraser från granskningarna. [data](data/) är motsvarande JSONL-källa och [stats.json](stats.json) innehåller verifierade antal. Uppslagen är avgränsade till respektive projekt och kontext; de ersätter inte den allmänna termbanken.

Granskningsunderlagen inventerades den 20 september 2026. Den offentliga översättningssamlingen lästes vid revision `67e6d27877c9cfd6b6dbc74bd852b10bdbe09c3c` av [yeager/translations](https://github.com/yeager/translations). Senare arbete i andra pågående granskningar ingår inte automatiskt.

Underlaget omfattar individuella beslut i FreeCADs 36 filer, bekräftade rättelser från Translation Project, GNOME och Ubuntu-granskningen, tidigare granskade filleveranser samt ändrade tvåspråkiga poster i översättningssamlingens granskningscommits. Automatiska varningar utan språkbeslut räknas inte som granskade rättelser.

`publication_status` skiljer lokala rättelser, inskickade förslag, publiceringskvitton, granskade filleveranser och ändringar i granskningscommits åt. En granskad filleverans bevisar inte att varje oförändrad post har ett separat registrerat radbeslut. Ingen av dessa beteckningar innebär formellt godkännande i Crowdin eller Weblate. FreeCADs ordlista är lokalt granskad; helfilsimporten nekas av Crowdin för filformatet glossary.

Varje post innehåller projekt, komponent, ursprunglig kontext, källtext, svensk text, hänvisning och SHA-256 för granskningsunderlaget. En källa kan ha flera korrekta svenska översättningar. Välj utifrån projekt, betydelse och kontext; ersätt aldrig globalt enbart utifrån det engelska ordet. Metadata och kontrolltecken bevaras i exporterna.

## Urval och format

Urvalet omfattar enskilda käll- och målformer, högst sex ord och 65 tecken i källtexten samt högst 100 tecken på svenska. Kodmallar, flerradstext, formatparametrar, identiska egennamn och uttryckligen olösta kontextfrågor väljs bort. Urvalet är en extraktion ur granskningsunderlagen; det är inte en ny, oberoende språklig granskning av varje uppslag.

CSV-kolumnerna är `id,source,canonical,project,component,context,note,scope,review_id,publication_status,reference,evidence_sha256,source_evidence`. TBX 2008 innehåller samma engelska/svenska termpar och bevarar metadata i en anteckning för varje begrepp. Filerna har inga fabricerade konsensusvärden. Använd kontexten även när ett uppslag saknar separat definition.

```sh
python3 scripts/reviewed.py
python3 scripts/reviewed.py --write
```

Kontrollen jämför samtliga termpar och metadata mellan JSONL, CSV och TBX. För import i ett projekt, välj dess ordlista och kontrollera först hur målverktyget hanterar flera betydelser av samma källterm.

## Avgränsning och spårbarhet

Källtexter som saknades i publiceringskvitton återställdes med kvalificerade projekt- och sträng-ID:n från Crowdin-exporter och Weblates API. API-källan och dess kontrollsumma sparas i `source_evidence`. Källtext och översättning kopplas aldrig ihop enbart genom ordens position i en fil. `inventory.json` redovisar underlag, undantag och kompletterande lokala rättelser.

23 pluralposter i Bitwarden, en pluralpost i PCSX2 och 30 poster i Libre Menu Editor fick kompletterande lokala rättelser vid insamlingen. De har särskild publiceringsstatus och är inte rapporterade som uppladdade till respektive översättningsplattform. Kontrollsumman i `evidence` avser det lästa granskningsunderlaget, medan länken kan gå till projektets översättningsvy; en levande Crowdin- eller Weblate-sida är inte ett oföränderligt arkiv.
