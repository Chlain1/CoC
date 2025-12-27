#!/usr/bin/env python3
import json
from pathlib import Path

from stats import compute_war_metrics, summarize_current_war
from coc_api import _encode_tag

BASE = Path(__file__).parent


def test_tag_encoding():
    """Test, dass Tags mit/ohne # korrekt kodiert werden"""
    print("== Test: Tag-Kodierung ==")
    
    # Mit #
    tag1 = _encode_tag("#ABC123")
    print(f"#ABC123 → {tag1}")
    assert tag1 == "%23ABC123", f"Erwartet %23ABC123, bekommen {tag1}"
    
    # Ohne # (wird automatisch hinzugefügt)
    tag2 = _encode_tag("ABC123")
    print(f"ABC123 → {tag2}")
    assert tag2 == "%23ABC123", f"Erwartet %23ABC123, bekommen {tag2}"
    
    # Mit Leerzeichen (trimming)
    tag3 = _encode_tag(" #ABC123 ")
    print(f"' #ABC123 ' → {tag3}")
    assert tag3 == "%23ABC123", f"Erwartet %23ABC123, bekommen {tag3}"
    
    print("✓ Tag-Kodierung funktioniert korrekt\n")


def test_warlog_metrics():
    """Test der Kriegsstatistik-Berechnung"""
    print("== Test: Warlog Metrics ==")
    warlog_path = BASE / "samples" / "warlog_sample.json"
    data = json.loads(warlog_path.read_text(encoding="utf-8"))
    items = data.get("items") or []
    metrics = compute_war_metrics(items)
    
    for k, v in metrics.items():
        print(f"{k}: {v}")
    
    # Validierung
    assert metrics["wars"] == 2, "Sollte 2 Kriege sein"
    assert metrics["win_rate"] == 0.5, "Sollte 50% Siegquote sein (1 Sieg, 1 Niederlage)"
    assert metrics["avg_stars_for"] == 28.0, "Sollte 28 Sterne im Durchschnitt sein"
    
    print("✓ Warlog-Metriken korrekt berechnet\n")


def test_empty_warlog():
    """Test bei leerem/privatem Warlog"""
    print("== Test: Leerer Warlog (privat) ==")
    metrics = compute_war_metrics([])
    
    for k, v in metrics.items():
        print(f"{k}: {v}")
    
    assert metrics["wars"] == 0, "Sollte 0 Kriege sein"
    assert metrics["win_rate"] == 0.0, "Sollte 0% Siegquote sein"
    
    print("✓ Leerer Warlog wird korrekt behandelt\n")


def test_current_war_summary():
    """Test der aktuellen Kriegs-Top-Angreifer"""
    print("== Test: Current War Summary ==")
    currentwar_path = BASE / "samples" / "currentwar_sample.json"
    current = json.loads(currentwar_path.read_text(encoding="utf-8"))
    summary = summarize_current_war(current)
    top = summary.get("top_attackers", [])
    
    for p in top[:5]:
        print(
            f"{p['name']} | Sterne: {p['stars']} | Zerstörung: {p['destruction']:.1f}% | Angriffe: {p['attacks']}"
        )
    
    # Validierung
    assert len(top) == 2, "Sollte 2 Spieler haben"
    assert top[0]["name"] == "Alice", "Alice sollte Top sein"
    assert top[0]["stars"] == 5, "Alice sollte 5 Sterne haben"
    assert top[1]["name"] == "Bob", "Bob sollte Zweiter sein"
    
    print("✓ Current War Summary korrekt\n")


def test_player_to_clan():
    """Test der Clan-Erkennung aus Player-Daten"""
    print("== Test: Player-zu-Clan-Erkennung ==")
    player_path = BASE / "samples" / "player_sample.json"
    player = json.loads(player_path.read_text(encoding="utf-8"))
    
    clan = player.get("clan")
    assert clan is not None, "Spieler sollte in einem Clan sein"
    
    clan_tag = clan.get("tag")
    clan_name = clan.get("name")
    
    print(f"Spieler: {player.get('name')}")
    print(f"Clan-Tag: {clan_tag}")
    print(f"Clan-Name: {clan_name}")
    
    assert clan_tag == "#2JYJQ8U9V", f"Erwarteter Clan-Tag: #2JYJQ8U9V, bekommen: {clan_tag}"
    assert clan_name == "Test Clan", f"Erwarteter Clan-Name: Test Clan, bekommen: {clan_name}"
    
    print("✓ Player-zu-Clan-Erkennung funktioniert\n")


def main():
    test_tag_encoding()
    test_warlog_metrics()
    test_empty_warlog()
    test_current_war_summary()
    test_player_to_clan()
    print("=" * 50)
    print("✅ Alle Tests erfolgreich!")


if __name__ == "__main__":
    main()
