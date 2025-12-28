#!/usr/bin/env python3
import argparse
import os
import sys
import csv
from pathlib import Path

# Lazy imports to let --help work without deps

def parse_args(argv=None):
    parser = argparse.ArgumentParser(
        description="Vergleich der Clash of Clans Kriegsperformance mehrerer Clans"
    )
    parser.add_argument(
        "--clan",
        dest="clans",
        action="append",
        help="Clan-Tag (z. B. #ABC123). Mehrfach verwendbar für Vergleich. Falls nicht angegeben, wird COC_PLAYER_TAG aus .env verwendet.",
    )
    parser.add_argument(
        "--player",
        dest="player_tag",
        default=None,
        help="Player-Tag für automatische Clan-Erkennung (überschreibt COC_PLAYER_TAG aus .env).",
    )
    parser.add_argument(
        "--wars",
        type=int,
        default=10,
        help="Anzahl der letzten Kriege für die Auswertung (Warlog Limit)",
    )
    parser.add_argument(
        "--csv",
        dest="csv_path",
        default=None,
        help="Optionaler Pfad für CSV-Export der Vergleichstabelle",
    )
    parser.add_argument(
        "--players-csv",
        dest="players_csv",
        default=None,
        help="Pfad zu einer CSV mit Spieler-Tags (Spalte 'tag' oder erste Spalte). Lädt Spielerinfos und exportiert sie als CSV.",
    )
    parser.add_argument(
        "--players-out",
        dest="players_out",
        default="players_out.csv",
        help="Zielpfad für den CSV-Export der Spielerinfos (Standard: players_out.csv).",
    )
    parser.add_argument(
        "--current-war-stats",
        dest="current_war_stats",
        action="store_true",
        help="Zeige Top-Angreifer aus dem aktuellen Krieg (falls verfügbar)",
    )
    parser.add_argument(
        "--token",
        dest="token",
        default=None,
        help="API-Token (alternativ via Umgebungsvariable COC_API_TOKEN)",
    )
    return parser.parse_args(argv)


def ensure_token(cli_token: str | None) -> str:
    # Priorität: 1. .env, 2. CLI-Argument, 3. Umgebungsvariable
    token_from_env_file = None
    try:
        from dotenv import load_dotenv
        # Suche .env im Projekt-Root (eine Ebene über src/)
        env_path = Path(__file__).parent.parent / ".env"
        if env_path.exists():
            load_dotenv(env_path)
        token_from_env_file = os.environ.get("COC_API_TOKEN")
    except ImportError:
        # python-dotenv nicht installiert, überspringe
        pass
    
    token = token_from_env_file or cli_token or os.environ.get("COC_API_TOKEN")
    if not token:
        print(
            "Fehler: Kein API-Token gefunden. Nutze .env, --token oder setze COC_API_TOKEN.",
            file=sys.stderr,
        )
        sys.exit(2)
    # Trim whitespace und newlines
    token = token.strip()
    return token


def print_table(rows):
    # rows: list of dicts with consistent keys
    if not rows:
        print("Keine Daten zum Anzeigen.")
        return
    # Determine columns order
    columns = [
        "Clan",
        "Kriege",
        "Siegquote",
        "Ø Sterne (für)",
        "Ø Sterne (gegen)",
        "Ø Zerstörung % (für)",
        "Ø Zerstörung % (gegen)",
        "Sterne/Angriff",
        "Gegner-Sterne/Angriff",
    ]
    # Print header
    print(" | ".join(columns))
    print("-" * 100)
    for r in rows:
        line = [
            r.get("clan_name", "-") or "-",
            str(r.get("wars", 0)),
            f"{r.get('win_rate', 0.0):.2f}",
            f"{r.get('avg_stars_for', 0.0):.2f}",
            f"{r.get('avg_stars_against', 0.0):.2f}",
            f"{r.get('avg_destruction_for', 0.0):.2f}",
            f"{r.get('avg_destruction_against', 0.0):.2f}",
            f"{r.get('stars_per_attack_for', 0.0):.3f}",
            f"{r.get('stars_per_attack_against', 0.0):.3f}",
        ]
        print(" | ".join(line))


def write_csv(rows, path):
    if not rows:
        print("Keine Daten zum Export.")
        return
    fieldnames = [
        "clan_tag",
        "clan_name",
        "wars",
        "win_rate",
        "avg_stars_for",
        "avg_stars_against",
        "avg_destruction_for",
        "avg_destruction_against",
        "stars_per_attack_for",
        "stars_per_attack_against",
    ]
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for r in rows:
            writer.writerow({k: r.get(k) for k in fieldnames})
    print(f"CSV exportiert: {path}")


def write_player_csv(rows, path):
    if not rows:
        print("Keine Spieler-Daten zum Export.")
        return
    fieldnames = [
        "tag",
        "name",
        "clan_tag",
        "clan_name",
        "role",
        "town_hall",
        "town_hall_weapon",
        "exp_level",
        "trophies",
        "best_trophies",
        "war_stars",
        "attack_wins",
        "defense_wins",
        "donations",
        "donations_received",
        "league",
        "builder_hall",
        "versus_trophies",
        "best_versus_trophies",
    ]
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for r in rows:
            writer.writerow({k: r.get(k) for k in fieldnames})
    print(f"Spieler-CSV exportiert: {path}")


def print_player_details(p):
    print(f"\n=== Spieler-Info: {p.get('name')} ({p.get('tag')}) ===")
    print(f"Town Hall: {p.get('townHallLevel')} (Weapon: {p.get('townHallWeaponLevel', '-')})")
    print(f"XP Level: {p.get('expLevel')} | War Stars: {p.get('warStars')}")
    print(f"Trophies: {p.get('trophies')} (Best: {p.get('bestTrophies')})")
    
    clan = p.get("clan")
    if clan:
        print(f"Clan: {clan.get('name')} ({clan.get('tag')}) - {p.get('role')}")
    else:
        print("Clan: Kein Clan")
        
    league = p.get("league")
    if league:
        print(f"League: {league.get('name')}")
        
    print(f"Attack Wins: {p.get('attackWins')} | Defense Wins: {p.get('defenseWins')}")
    print(f"Donations: {p.get('donations')} | Received: {p.get('donationsReceived')}")
    
    # Builder Base
    if p.get('builderHallLevel'):
        print(f"Builder Hall: {p.get('builderHallLevel')} | Trophies: {p.get('versusTrophies')} (Best: {p.get('bestVersusTrophies')})")
    
    # Labels
    labels = p.get("labels", [])
    if labels:
        l_str = ", ".join([l['name'] for l in labels])
        print(f"Labels: {l_str}")

    # Heroes
    heroes = p.get("heroes", [])
    if heroes:
        h_str = ", ".join([f"{h['name']} ({h['level']})" for h in heroes if h.get('village') == 'home'])
        print(f"Heroes: {h_str}")
        
    # Troops
    troops = p.get("troops", [])
    if troops:
        home_troops = [t for t in troops if t.get('village') == 'home']
        if home_troops:
            t_str = ", ".join([f"{t['name']} ({t['level']})" for t in home_troops])
            print(f"Troops: {t_str}")
            
    spells = p.get("spells", [])
    if spells:
        s_str = ", ".join([f"{s['name']} ({s['level']})" for s in spells])
        print(f"Spells: {s_str}")
    print("=" * 60 + "\n")


def read_player_tags_csv(path: str) -> list[str]:
    tags: list[str] = []
    with open(path, newline="", encoding="utf-8") as f:
        reader = csv.reader(f)
        first = next(reader, None)
        if first is None:
            return []

        # Falls Header 'tag' enthält, nutze entsprechende Spalte, sonst erste Spalte
        tag_idx = 0
        if any(col.lower() == "tag" for col in first):
            tag_idx = next(i for i, col in enumerate(first) if col.lower() == "tag")
        else:
            tags.append(first[tag_idx].strip())

        for row in reader:
            if len(row) <= tag_idx:
                continue
            tags.append(row[tag_idx].strip())

    # Filter leere Einträge
    return [t for t in tags if t]


def player_to_row(p: dict) -> dict:
    clan = p.get("clan") or {}
    league = p.get("league") or {}
    return {
        "tag": p.get("tag"),
        "name": p.get("name"),
        "clan_tag": clan.get("tag"),
        "clan_name": clan.get("name"),
        "role": p.get("role"),
        "town_hall": p.get("townHallLevel"),
        "town_hall_weapon": p.get("townHallWeaponLevel"),
        "exp_level": p.get("expLevel"),
        "trophies": p.get("trophies"),
        "best_trophies": p.get("bestTrophies"),
        "war_stars": p.get("warStars"),
        "attack_wins": p.get("attackWins"),
        "defense_wins": p.get("defenseWins"),
        "donations": p.get("donations"),
        "donations_received": p.get("donationsReceived"),
        "league": league.get("name"),
        "builder_hall": p.get("builderHallLevel"),
        "versus_trophies": p.get("versusTrophies"),
        "best_versus_trophies": p.get("bestVersusTrophies"),
    }


def main(argv=None):
    args = parse_args(argv)
    token = ensure_token(args.token)

    # Lazy imports
    from coc_api import CocApi
    from stats import (
        compute_war_metrics,
        summarize_current_war,
    )
    
    api = CocApi(token)

    # Spieler-CSV-Modus: Liste von Tags einlesen, Spielerinfos exportieren
    if args.players_csv:
        tags = read_player_tags_csv(args.players_csv)
        if not tags:
            print(f"Fehler: Keine Spieler-Tags in {args.players_csv} gefunden.", file=sys.stderr)
            sys.exit(2)

        player_rows = []
        for tag in tags:
            player = api.get_player(tag)
            if not player:
                print(f"Warnung: Spieler {tag} nicht gefunden oder Fehler beim Abruf.", file=sys.stderr)
                continue
            player_rows.append(player_to_row(player))

        if not player_rows:
            print("Fehler: Keine Spieler konnten geladen werden.", file=sys.stderr)
            sys.exit(2)

        write_player_csv(player_rows, args.players_out)
        return

    # Player Info & Auto-detect clan
    player_tag = args.player_tag or os.environ.get("COC_PLAYER_TAG")
    
    if player_tag:
        player = api.get_player(player_tag)
        if player:
            print_player_details(player)
            # Auto-detect clan if needed
            if not args.clans:
                clan = player.get("clan")
                if clan and clan.get("tag"):
                    args.clans = [clan["tag"]]
                    print(f"Auto-erkannter Clan: {clan['tag']} ({clan.get('name')})\n")
                else:
                    print(f"Warnung: Spieler {player_tag} ist in keinem Clan.", file=sys.stderr)
        else:
            if args.player_tag or not args.clans:
                print(f"Warnung: Spieler {player_tag} nicht gefunden.", file=sys.stderr)

    if not args.clans:
        print(
            "Fehler: Kein Clan angegeben. Nutze --clan oder setze COC_PLAYER_TAG in .env für Auto-Erkennung.",
            file=sys.stderr,
        )
        sys.exit(2)

    # Vergleichsmetriken pro Clan
    comparison_rows = []
    for tag in args.clans:
        warlog = api.get_warlog(tag, limit=args.wars)
        if warlog is None:
            print(f"Warnung: Warlog für {tag} nicht verfügbar oder Fehler.")
            continue
        metrics = compute_war_metrics(warlog)
        # Zusatz: Clanname aus Warlog (falls vorhanden)
        clan_name = None
        if warlog:
            # Der eigene Clan steht pro Eintrag unter item['clan']
            # Wir nehmen den ersten Eintrag als Quelle für den Namen.
            first = warlog[0]
            clan_name = (first.get("clan") or {}).get("name")
        metrics["clan_tag"] = tag
        metrics["clan_name"] = clan_name or tag
        comparison_rows.append(metrics)

    print_table(comparison_rows)

    if args.csv_path:
        write_csv(comparison_rows, args.csv_path)

    # Optional: aktuelle Kriegsstats
    if args.current_war_stats:
        print("\nAktuelle Kriegs-Top-Angreifer (falls verfügbar):")
        for tag in args.clans:
            current = api.get_currentwar(tag)
            if current is None or (current.get("state") not in ("inWar", "warEnded")):
                print(f"- {tag}: kein aktiver Krieg oder keine Daten.")
                continue
            summary = summarize_current_war(current)
            clan_name = (current.get("clan") or {}).get("name") or tag
            print(f"\nClan: {clan_name}")
            top = summary.get("top_attackers", [])
            if not top:
                print("Keine Angriffsdetails vorhanden.")
            else:
                print("Name | Sterne | Zerstörung% | Angriffe")
                print("-" * 60)
                for p in top[:5]:
                    print(
                        f"{p.get('name','-')} | {p.get('stars',0)} | "
                        f"{p.get('destruction',0.0):.1f} | {p.get('attacks',0)}"
                    )


if __name__ == "__main__":
    main()
