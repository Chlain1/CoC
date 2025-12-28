# Clash of Clans Kriegsperformance Vergleich (CLI)

Ein schlankes Python-Tool, das die offizielle Clash of Clans API nutzt, um die Kriegsperformance von Clans auszuwerten und statistisch zu vergleichen.

## Voraussetzungen
- Python 3.8+
- API Token von https://developer.clashofclans.com/
- Umgebung: Linux (getestet), sollte plattformunabhängig funktionieren

## Installation
1. Repository lokal haben (dieser Ordner).
2. Abhängigkeiten installieren:

```bash
python3 -m pip install -r requirements.txt
```

3. API-Token konfigurieren (Priorität: .env > CLI-Flag > Umgebungsvariable):

**Option A: .env-Datei (empfohlen)**
```bash
cp .env.example .env
# Bearbeite .env und trage deinen Token UND Player-Tag ein:
# COC_API_TOKEN=dein_api_token_hier
# COC_PLAYER_TAG=ABC123XYZ  (OHNE # am Anfang!)
#
# Mit gesetztem COC_PLAYER_TAG wird dein Clan automatisch erkannt!
```

**Option B: Umgebungsvariable**
```bash
export COC_API_TOKEN="<dein_token>"
```

**Option C: CLI-Flag**
```bash
python3 src/cli.py --token "<dein_token>" ...
```

## Nutzung

**Automatisch (mit COC_PLAYER_TAG in .env):**
```bash
# Zeigt Statistik deines Clans über die letzten 10 Kriege
python3 src/cli.py

# Oder mit spezifischer Kriegsanzahl
python3 src/cli.py --wars 20

# Mit aktuellen Kriegsstatistiken
python3 src/cli.py --current-war-stats
```

**Manuell - Vergleich mehrerer Clans:**
Vergleich mehrerer Clans über die letzten N Kriege:

```bash
python3 src/cli.py --clan "#CLAN1" --clan "#CLAN2" --wars 10
```

CSV-Export der Vergleichstabelle:

```bash
python3 src/cli.py --clan "#CLAN1" --clan "#CLAN2" --wars 20 --csv comparison.csv
```

Spielerinfos aus CSV mit Tags laden und als CSV exportieren (Spalte `tag` oder erste Spalte):

```bash
python3 src/cli.py --players-csv player_tags.csv --players-out players_out.csv
```

Aktuelle Kriegs-Top-Angreifer pro Clan anzeigen (falls verfügbar):

```bash
python3 src/cli.py --clan "#CLAN1" --current-war-stats
```

Token alternativ direkt übergeben:

```bash
python3 src/cli.py --clan "#CLAN1" --wars 10 --token "<dein_token>"
```

## Was wird verglichen?
- Anzahl berücksichtigter Kriege
- Siegquote
- Durchschnittliche Sterne (für/gegen)
- Durchschnittliche Zerstörung in % (für/gegen)
- Offensiv-Effizienz (Sterne pro Angriff)
- Defensiv-Effizienz (gegnerische Sterne pro gegnerischem Angriff)

Optional: Zusammenfassung der aktuellen Kriegs-Performance der Spieler (Top-Angreifer nach Sternen/Prozent).

## Hinweise
- Clan-Tags müssen mit `#` beginnen (z. B. `#ABC123`). Das Tool kodiert sie automatisch für die API.
- Einige Daten (z. B. detaillierte Spielerstatistiken) sind nur im aktuellen Krieg verfügbar; der Warlog liefert aggregierte Werte pro Krieg.
- Bei privaten/fehlenden Warlogs oder wenn kein Krieg läuft, werden entsprechende Hinweise ausgegeben und die betroffenen Teile übersprungen.

## Offline-Test
Es gibt Beispiel-Dateien unter `src/samples/`, die den Aufbau der API-Antworten skizzieren. Diese können für Offline-Validierung der Metrikfunktionen genutzt werden.

## Lizenz
Dieses Tool ist ausschließlich zu Demonstrationszwecken gedacht und nutzt die öffentlich dokumentierte API von Supercell (Clash of Clans). Beachte bitte die Nutzungsbedingungen der API.
