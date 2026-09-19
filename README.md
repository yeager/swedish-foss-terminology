# Swedish FOSS Terminology Database

**Kanonisk svensk terminologi för öppen källkod — den största samlade terminologibanken för svenska FOSS-översättningar**

[![License: CC BY 4.0](https://img.shields.io/badge/License-CC%20BY%204.0-lightgrey.svg)](https://creativecommons.org/licenses/by/4.0/)
[![Terms](https://img.shields.io/badge/Terms-326K-blue.svg)](#statistik)
[![Projects](https://img.shields.io/badge/Projects-3299-green.svg)](#projektomfattning)

## Vad det är

Denna terminologibank innehåller den största samlade terminologin för svenska översättningar av öppen källkodsprogramvara (FOSS). Databasen har extraherat och analyserat 326 000+ termer från 3 299 projekt, inklusive stora ekosystem som GNOME, KDE, Mozilla, Ubuntu, LibreOffice och hundratals andra projekt.

## Aktuell export och kontroll

Den aktuella exporten innehåller 325 936 termpar. CSV- och JSON-filerna är den
fullständiga källan; TBX-exporten innehåller 325 934 XML-kompatibla poster.
Två poster med XML-förbjudna kontrolltecken redovisas separat i
`swedish-foss.excluded.json`, så att data aldrig tyst ändras för att passa ett
format. Kontrollskript och CI jämför exporternas text, översättning och
konfidens innan ändringar publiceras.

### Kärnfunktioner

- **Omfattande täckning**: 325 936 extraherade termpar (engelska → svenska)
- **Kvalitetssäkrad**: 95.9% av termerna har stark konsensus (≥80% överensstämmelse)
- **Domänspecifik**: 134 466 domänspecifika anpassningar för olika programvarukontexter
- **Format**: CSV, TBX (TermBase eXchange), JSON och genererad Weblate CSV
- **Fri att använda**: CC BY 4.0-licens för maximal återanvändning

## Statistik

- **Totalt antal termer:** 325 936
- **Stark konsensus (≥80%):** 312 532 (95.9%)
- **Svag konsensus (50-79%):** 12 632 (3.9%) 
- **Splittrad konsensus (<50%):** 772 (0.2%)
- **Domänspecifika overrides:** 134 466
- **Projektomfattning:** 3 299 projekt

## Format och filer

### 📁 Tillgängliga format

| Fil | Format | Användningsområde |
|-----|--------|------------------|
| `termbank-flat.csv` | CSV | Allmän import, analys, databehandling |
| `swedish-foss.tbx` | TBX 2008 (MARTIF) | CAT-verktyg och Weblate; 325 934 XML-kompatibla poster |
| `weblate-glossary.json` | Egen JSON-struktur | Maskinläsbar export med anteckningar; konvertera till CSV för Weblate |
| `swedish-foss.excluded.json` | JSON | Två poster med kontrolltecken som XML 1.0 inte kan representera |

### 📊 CSV-struktur

```csv
source,canonical,confidence
Cancel,Avbryt,1.0
Save,Spara,1.0
...
```

**Kolumner:**
- `source`: Ursprunglig engelsk term
- `canonical`: Kanonisk svensk översättning
- `confidence`: Konsensusandel (0–1); `0.9` motsvarar 90 %. Värdet anger överensstämmelse i källmaterialet, inte garanterad språklig korrekthet.

## Användning

### Weblate Glossary Import

```bash
# Kör i en klon av detta repo (Python 3.10+, inga extra beroenden).
python3 scripts/exports.py --weblate weblate-glossary.csv
```

Ladda upp den genererade filen i ordlistans svenska översättning i Weblate med
filformatet **CSV file** och teckenkodningen UTF-8. Exporten använder kolumnerna
`source`, `target` och `developer_comments` enligt
[Weblates CSV-dokumentation](https://docs.weblate.org/en/latest/formats/csv.html).
Anteckningar om konfidens och domänvarianter bevaras. CSV-formatet överför inte
JSON-fältet `flag`; markera vid behov termer som terminologi i Weblate.

`weblate-glossary.json` är ett eget exportformat, inte ett direktimportformat
för Weblate. Det tidigare kommandot `weblate import_glossary` var felaktigt.

### CAT-verktyg (Trados, memoQ, etc.)

1. Ladda ner `swedish-foss.tbx`
2. Importera som termbank i ditt CAT-verktyg
3. Aktivera terminologikontroll för svenska översättningsprojekt

### Egna verktyg och analys

```python
import pandas as pd

# Läs terminologin
terms = pd.read_csv('termbank-flat.csv')

# Filtrera på hög konfidensgrad
high_confidence = terms[terms['confidence'].astype(float) >= 0.9]

# CSV-exporten innehåller inte domänfält eller förekomstfrekvenser.
```

## Kontroll och återgenerering

```bash
python3 scripts/exports.py
python3 scripts/exports.py --tbx swedish-foss.tbx
python3 -m pip install -r requirements-dev.txt
python3 -m pytest -q
```

Kontrollen jämför källtext, översättning och konfidens mellan CSV, JSON och TBX,
och upptäcker dubbletter, ogiltiga värden, felaktiga språkattribut och saknade
poster. Tester verifierar också import via Translate Toolkit, som Weblate
använder. TBX följer
[2008 års MARTIF-struktur](https://www.tbxinfo.net/validating-a-tbx-file/)
med `xml:lang`, och vagnreturer kodas som `&#13;` för att överleva XML-import.

Två poster innehåller U+001F eller U+001B, som är förbjudna i XML 1.0.
De finns kvar oförändrade i CSV och JSON samt i `swedish-foss.excluded.json`,
och utelämnas uttryckligen från TBX. Den tidigare TBX-exporten tog bort dessa
kontrolltecken ur texterna utan att dokumentera förändringen.

Statistiken om konsensus kan räknas från CSV-exporten. Projektantal och
uppgifter om domänanpassningar kommer från den ursprungliga insamlingen;
den platta exporten innehåller inte underlaget för att verifiera dem.

## Projektomfattning

Terminologin är extraherad från följande kategorierna av FOSS-projekt:

### 🖥️ Desktop Environments & Window Managers
- **GNOME** (gnome-shell, nautilus, gedit, etc.)
- **KDE** (plasma, dolphin, kate, etc.)  
- **XFCE** (thunar, xfce4-panel, etc.)
- **MATE**, **Cinnamon**, **LXDE**

### 🌐 Web Browsers & Internet
- **Mozilla Firefox** (inkl. Thunderbird)
- **Chromium** ecosystem
- **Web standards** (HTML5, CSS, JavaScript)

### 📊 Office & Productivity  
- **LibreOffice** (Writer, Calc, Impress, Draw)
- **GIMP**, **Inkscape**, **Blender**
- **Evolution**, **Geary** (e-postklienter)

### ⚙️ System & Development
- **Ubuntu**, **Debian**, **Fedora** (pakethantering)
- **Git**, **autotools**, **CMake**
- **GCC**, **Python**, **GTK+**, **Qt**

### 🎮 Multimedia & Gaming  
- **VLC**, **GStreamer**, **PulseAudio**
- **Steam**, **WINE**, **Lutris**

## Exempel på inkonsistenta termer

*Dessa termer kräver extra uppmärksamhet vid översättning:*

| Engelsk term | Antal varianter | Konfidensgrad | Rekommendation |
|--------------|-----------------|---------------|----------------|
| Bottom | 12 | 31.4% | **Kontextuell:** "Nedre" (UI), "Botten" (fysisk) |
| Top | 12 | 26.6% | **Kontextuell:** "Övre" (UI), "Toppen" (fysisk) |
| D | 11 | 22.2% | **Förkorta inte:** Använd fullständiga termer |
| Completed | 10 | 34.3% | **"Slutförd"** (standard), "Klar" (informell) |
| Note | 10 | 41.1% | **"Anteckning"** (allmänt), "Obs" (kort varning) |
| Custom | 10 | 73.1% | **"Anpassad"** (rekommenderat) |
| Success | 10 | 72.2% | **"Lyckades"** (verb), "Framgång" (substantiv) |
| Body | 9 | 40.4% | **Kontextuell:** "Brödtext", "Huvuddel", "Kropp" |
| Complete | 9 | 26.3% | **"Fullständig"** (adjektiv), "Slutför" (verb) |
| Power | 9 | 48.9% | **"Ström"** (el), "Kraft" (allmänt) |
| Rate | 9 | 29.4% | **"Hastighet"** (teknik), "Betyg" (utvärdering) |
| Unmute | 9 | 20.0% | **"Aktivera ljud"** (rekommenderat) |
| Collapse | 8 | 40.5% | **"Fäll ihop"** (UI), "Kollapsa" (teknisk) |
| Controls | 8 | 65.0% | **"Kontroller"** (rekommenderat) |
| File not found | 8 | 47.3% | **"Filen hittades inte"** (standard) |
| Fix | 8 | 25.0% | **"Åtgärda"** (formell), "Fixa" (informell) |

*CSV-exporten innehåller kanonisk översättning och konsensusandel, men inte antalet varianter.*

## Bidrag och förbättringar

### 🤝 Hur du bidrar

1. **Rapportera inkonsistenser**: Öppna en issue med konkreta exempel
2. **Föreslå förbättringar**: Pull requests för README, dokumentation
3. **Domänexpertis**: Bidra med terminologi från specifika FOSS-områden
4. **Kvalitetsgranskning**: Hjälp till att granska låg-konfidensfall

### 📋 Bidragsriktlinjer

- **Belägga förslag**: Referera till etablerade svenska IT-termer eller språkråd
- **Konsensus**: Sträva efter terminologi som fungerar över projektgränser  
- **Kontext**: Förklara när en term bör användas vs alternativ
- **Källor**: Hänvisa till officiella översättningsprojekt eller standarder

## Licens

Detta arbete är licensierat under [Creative Commons Attribution 4.0 International License](https://creativecommons.org/licenses/by/4.0/).

**Du får:**
- ✅ Använda terminologin kommersiellt
- ✅ Ändra och bygga vidare på materialet  
- ✅ Distribuera i alla format och media

**Du måste:**
- 📝 Tillskriva originalverket (länka till detta repo)
- 📝 Ange om du gjort ändringar

## Kontakt och support

- **Repository**: https://github.com/yeager/swedish-foss-terminology
- **Issues**: [Rapportera problem eller föreslå förbättringar](https://github.com/yeager/swedish-foss-terminology/issues)
- **Diskussioner**: [Community diskussioner](https://github.com/yeager/swedish-foss-terminology/discussions)

---

**Utvecklat av svenska FOSS-översättningscommunity • Underhålls av @yeager**

*Denna terminologibank representerar kollektiv kunskap från hundratals svenska översättare som arbetat med FOSS-projekt under mer än två decennier.*
