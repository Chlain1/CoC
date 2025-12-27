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


def get_clan_from_player(api, player_tag: str) -> str | None:
    """Ermittle Clan-Tag aus Player-Tag."""
    player = api.get_player(player_tag)
    if not player:
        print(f"Warnung: Spieler {player_tag} nicht gefunden.", file=sys.stderr)
        return None
    clan = player.get("clan")
    if not clan or not clan.get("tag"):
        print(f"Warnung: Spieler {player_tag} ist in keinem Clan.", file=sys.stderr)
        return None
    return clan["tag"]


def main(argv=None):
    args = parse_args(argv)
    token = ensure_token(args.token)

    # Auto-detect clan from player if no clans specified
    if not args.clans or len(args.clans) == 0:
        player_tag = args.player_tag or os.environ.get("COC_PLAYER_TAG")
        if not player_tag:
            print(
                "Fehler: Kein Clan angegeben. Nutze --clan oder setze COC_PLAYER_TAG in .env für Auto-Erkennung.",
                file=sys.stderr,
            )
            sys.exit(2)
        
        # Lazy import here for auto-detection
        from coc_api import CocApi
        api_temp = CocApi(token)
        
        clan_tag = get_clan_from_player(api_temp, player_tag)
        if not clan_tag:
            sys.exit(2)
        
        args.clans = [clan_tag]
        print(f"Auto-erkannter Clan: {clan_tag}\n")

    # Lazy imports here so --help works without dependencies
    from coc_api import CocApi
    from stats import (
        compute_war_metrics,
        summarize_current_war,
    )

    api = CocApi(token)

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
