import typing as t


def _safe_get(d: dict, *keys, default=None):
    cur = d
    for k in keys:
        if not isinstance(cur, dict):
            return default
        cur = cur.get(k)
        if cur is None:
            return default
    return cur


def compute_war_metrics(warlog_items: list[dict]) -> dict:
    """Aggregiere Kennzahlen aus Warlog-Einträgen.
    Erwarteter Strukturteil pro Item (API):
    - item['result'] in {'win','lose','tie'} (optional)
    - item['clan'] / item['opponent'] mit Feldern: 'stars', 'destructionPercentage', 'attacks'
    """
    if not warlog_items:
        return {
            "wars": 0,
            "win_rate": 0.0,
            "avg_stars_for": 0.0,
            "avg_stars_against": 0.0,
            "avg_destruction_for": 0.0,
            "avg_destruction_against": 0.0,
            "stars_per_attack_for": 0.0,
            "stars_per_attack_against": 0.0,
        }

    wars = len(warlog_items)
    wins = 0
    ties = 0

    stars_for = 0.0
    stars_against = 0.0
    destr_for = 0.0
    destr_against = 0.0
    attacks_for = 0
    attacks_against = 0

    for item in warlog_items:
        res = item.get("result")
        if res == "win":
            wins += 1
        elif res == "tie":
            ties += 1

        cf = _safe_get(item, "clan", default={}) or {}
        co = _safe_get(item, "opponent", default={}) or {}

        stars_for += float(cf.get("stars") or 0)
        stars_against += float(co.get("stars") or 0)
        destr_for += float(cf.get("destructionPercentage") or 0.0)
        destr_against += float(co.get("destructionPercentage") or 0.0)
        attacks_for += int(cf.get("attacks") or 0)
        attacks_against += int(co.get("attacks") or 0)

    avg_stars_for = stars_for / wars
    avg_stars_against = stars_against / wars
    avg_destruction_for = destr_for / wars
    avg_destruction_against = destr_against / wars

    stars_per_attack_for = (stars_for / attacks_for) if attacks_for > 0 else 0.0
    stars_per_attack_against = (stars_against / attacks_against) if attacks_against > 0 else 0.0

    # Definiere Siegquote als (Wins + 0.5*Ties)/Wars
    win_rate = (wins + 0.5 * ties) / wars

    return {
        "wars": wars,
        "win_rate": win_rate,
        "avg_stars_for": avg_stars_for,
        "avg_stars_against": avg_stars_against,
        "avg_destruction_for": avg_destruction_for,
        "avg_destruction_against": avg_destruction_against,
        "stars_per_attack_for": stars_per_attack_for,
        "stars_per_attack_against": stars_per_attack_against,
    }


def summarize_current_war(current: dict) -> dict:
    """Extrahiere einfache Spieler-Statistiken aus dem aktuellen Krieg.
    Liefert Top-Angreifer basierend auf summierten Sternen/Zerstörung.
    Struktur (vereinfachte Annahme): current['clan']['members'] mit 'attacks': [{stars, destructionPercentage}, ...]
    """
    members = _safe_get(current, "clan", "members", default=[]) or []
    players: list[dict] = []
    for m in members:
        attacks = m.get("attacks") or []
        total_stars = 0
        total_destr = 0.0
        count = 0
        for a in attacks:
            total_stars += int(a.get("stars") or 0)
            total_destr += float(a.get("destructionPercentage") or 0.0)
            count += 1
        players.append({
            "name": m.get("name") or "-",
            "tag": m.get("tag") or "-",
            "attacks": count,
            "stars": total_stars,
            "destruction": total_destr,
            "avg_destruction": (total_destr / count) if count > 0 else 0.0,
        })

    # Sortiere nach Sternen, dann Zerstörung
    players.sort(key=lambda p: (p["stars"], p["destruction"]), reverse=True)

    return {
        "top_attackers": players,
    }
