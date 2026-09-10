#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Wochenplan-Ersteller für D-Jugend Trainer (JSG Hörstel / Dreierwalde II)
Reines Python 3 (Standardbibliothek - keine externen Abhängigkeiten erforderlich).
Liest die Spieldaten von fussball.de aus und sendet die fertige Nachricht
freitags automatisch auf dein Smartphone (via ntfy Push oder Telegram).
"""

import os
import sys
import re
import datetime
import urllib.parse
import urllib.request
import json

# UTF-8 Ausgabe für Windows-Konsolen sicherstellen
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

# ==========================================
# KONFIGURATION
# ==========================================
FUSSBALL_URL_OR_ID = os.getenv(
    "FUSSBALL_URL_OR_ID", 
    "https://www.fussball.de/ajax.team.matchplan/-/mode/PAGE/team-id/0200HNN2LG000000VS548984VSUCHKOE"
).strip()

MY_TEAM_NAME = os.getenv("MY_TEAM_NAME", "JSG Hörstel").strip()
NTFY_TOPIC = os.getenv("NTFY_TOPIC", "").strip()
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "").strip()
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "").strip()

# Treffpunkt vor dem Spiel (in Minuten) - immer 45 Minuten vor Anstoß
TREFFPUNKT_MINUTEN = int(os.getenv("TREFFPUNKT_OFFSET_MINUTES", "45"))

# Automatische Wort- und Phrasen-Rotation (standardmäßig AKTIVIERT)
VARIATION_MODE = os.getenv("VARIATION_MODE", "true").lower() in ("true", "1", "yes")

DAYS_DE = {
    0: "Montag",
    1: "Dienstag",
    2: "Mittwoch",
    3: "Donnerstag",
    4: "Freitag",
    5: "Samstag",
    6: "Sonntag"
}


def get_target_week_range(ref_date: datetime.date = None):
    """Ermittelt Montag bis Sonntag der kommenden Spielwoche."""
    if ref_date is None:
        ref_date = datetime.date.today()

    days_until_next_monday = (7 - ref_date.weekday()) % 7
    if days_until_next_monday == 0:
        days_until_next_monday = 7

    next_monday = ref_date + datetime.timedelta(days=days_until_next_monday)
    next_sunday = next_monday + datetime.timedelta(days=6)
    return next_monday, next_sunday


def extract_team_id(url_or_id: str) -> str:
    """Extrahiert die team-id aus einer URL oder gibt die ID direkt zurück."""
    m = re.search(r'team-id/([A-Za-z0-9]+)', url_or_id)
    if m:
        return m.group(1)
    if re.match(r'^[A-Za-z0-9]{20,}$', url_or_id):
        return url_or_id
    return ""


def parse_venue_details(venue_raw: str):
    """
    Teilt die fussball.de Spielstätte sauber in:
    - ort (z. B. Hörstel, Ibbenbüren)
    - adresse (z. B. Jahnstr. 21, 49479 Ibbenbüren)
    - stadion_name (z. B. Carl-Keller-Stadion Platz 2)
    """
    if not venue_raw or venue_raw == "Wird noch bekanntgegeben":
        return {
            "ort": "Wird noch bekanntgegeben",
            "adresse": "",
            "stadion": "am Sportplatz"
        }

    parts = [p.strip() for p in venue_raw.split(',') if p.strip()]

    # Ort meist im letzten Teil (z. B. '49479 Ibbenbüren' -> 'Ibbenbüren')
    ort = parts[-1]
    ort = re.sub(r'^\d{5}\s*', '', ort).strip()

    # Stadion / Platzname meist im 2. Teil
    stadion = parts[1] if len(parts) >= 2 else "am Stadion"

    # Adresse (Straße + PLZ/Ort)
    adresse = ", ".join(parts[2:]) if len(parts) >= 3 else venue_raw

    return {
        "ort": ort,
        "adresse": adresse,
        "stadion": stadion
    }


def fetch_matches_from_fussball_de(url_or_id: str):
    """Lädt den Spielplan mit Spielstätten über den fussball.de JSON-Endpoint."""
    team_id = extract_team_id(url_or_id)
    if not team_id:
        raise ValueError(f"Konnte keine gültige Team-ID finden in: {url_or_id}")

    endpoint = (
        f"https://www.fussball.de/ajax.team.matchplan/-/mime-type/JSON/mode/PAGE/"
        f"prev-season-allowed/false/show-filter/false/show-venues/true/team-id/{team_id}"
    )

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
        "Accept": "application/json, text/plain, */*"
    }

    req = urllib.request.Request(endpoint, headers=headers)
    with urllib.request.urlopen(req, timeout=20) as resp:
        content = resp.read().decode("utf-8")

    data = json.loads(content)
    raw_html = data.get("html", "")
    if not raw_html:
        return []

    blocks = re.split(r'<tr class="row-headline visible-small">', raw_html)
    matches = []

    for block in blocks[1:]:
        headline_m = re.search(r'<td[^>]*>(.*?)</td>', block)
        headline = headline_m.group(1).strip() if headline_m else ""

        clubs = re.findall(r'<div class="club-name">\s*(.*?)\s*</div>', block, re.DOTALL)
        clean_clubs = [re.sub(r'&#\d+;', '', c).strip().replace('/ ', '/') for c in clubs]

        venue_m = re.search(r'row-venue.*?<td colspan="3">\s*(.*?)\s*</td>', block, re.DOTALL)
        venue = venue_m.group(1).strip() if venue_m else "Wird noch bekanntgegeben"
        venue = " ".join(venue.split())

        date_m = re.search(r'(\d{2}\.\d{2}\.\d{4})', headline)
        time_m = re.search(r'(\d{2}:\d{2})', headline)

        if date_m and time_m:
            dt_str = f"{date_m.group(1)} {time_m.group(1)}"
            dt = datetime.datetime.strptime(dt_str, "%d.%m.%Y %H:%M")

            home_team = clean_clubs[0] if len(clean_clubs) > 0 else "Heim"
            away_team = clean_clubs[1] if len(clean_clubs) > 1 else "Gast"

            matches.append({
                "start": dt,
                "headline": headline,
                "home": home_team,
                "away": away_team,
                "venue_raw": venue,
                "venue_info": parse_venue_details(venue)
            })

    matches.sort(key=lambda x: x["start"])
    return matches


def build_message(target_monday: datetime.date, target_sunday: datetime.date, matches: list, vary: bool = True):
    """
    Erstellt die Nachricht mit vermerktem Anstoß und automatischer Phrasen-Rotation.
    """
    week_matches = [
        m for m in matches
        if target_monday <= m["start"].date() <= target_sunday
    ]

    # Kalenderwoche für deterministische, wöchentliche Abwechslung
    kw = target_monday.isocalendar()[1]

    if not week_matches:
        if vary:
            spielfrei_pool = [
                "Moin zusammen, nächste Woche haben wir spielfrei! Wir sehen uns Montag und Mittwoch ganz normal beim Training. Schönes Wochenende ⚽",
                "Hallo zusammen, am kommenden Wochenende steht kein Spiel an (spielfrei). Bitte trotzdem für die Trainings abstimmen! Schönes Wochenende 👋",
                "Moin Moin ins Team, nächstes Wochenende haben wir spielfrei! Montag & Mittwoch ist wie gewohnt Training. Schönes Wochenende! ⚽"
            ]
            return spielfrei_pool[kw % len(spielfrei_pool)]
        else:
            return "Moin zusammen, nächste Woche haben wir spielfrei! Gerne einmal abstimmen wer bei den Trainings dabei ist.\nSchönes Wochenende"

    match = week_matches[0]
    dt = match["start"]
    weekday_name = DAYS_DE.get(dt.weekday(), "Samstag")
    datum_str = dt.strftime("%d.%m.") # z. B. (19.09.)

    # Treffpunkt & Anstoßzeit
    anstoß_str = f"{dt.strftime('%H:%M')} Uhr"
    treffpunkt_dt = dt - datetime.timedelta(minutes=TREFFPUNKT_MINUTEN)
    treffpunkt_str = f"{treffpunkt_dt.strftime('%H:%M')} Uhr"

    # Heim oder Auswärts
    is_home = MY_TEAM_NAME.lower() in match["home"].lower()
    gegner = match["away"] if is_home else match["home"]
    venue = match["venue_info"]
    spielort = venue["ort"]
    adresse = venue["adresse"]

    if not vary:
        # Fester statischer Text (mit Anstoß vermerkt)
        if is_home:
            return (
                f"Moin zusammen, nächste Woche {weekday_name} ({datum_str}) haben wir unser nächstes Spiel gegen {gegner} in {spielort}. "
                f"Anstoß ist um {anstoß_str}, dazu treffen wir uns um {treffpunkt_str} in {spielort} am Stadion. "
                f"Gerne einmal abstimmen wer dabei ist auch für die Trainings!\n"
                f"Schönes Wochenende"
            )
        else:
            return (
                f"Moin zusammen, nächste Woche {weekday_name} ({datum_str}) haben wir unser nächstes Spiel gegen {gegner} in {spielort}. "
                f"Anstoß ist um {anstoß_str}, dazu treffen wir uns um {treffpunkt_str} in {spielort} am Stadion. {adresse}. "
                f"Gerne einmal abstimmen wer dabei ist auch für die Trainings!\n"
                f"Schönes Wochenende"
            )

    # AUTOMATISCHE ROTATION (Verschiedene Bausteine, jede Woche neu kombiniert)
    begruessungen = [
        "Moin zusammen,",
        "Hallo zusammen,",
        "Moin Moin ins Team,",
        "Hi zusammen,",
        "Moin,"
    ]
    einleitungen = [
        f"nächste Woche {weekday_name} ({datum_str}) haben wir unser nächstes Spiel gegen {gegner} in {spielort}.",
        f"am kommenden {weekday_name} ({datum_str}) steht unser nächstes Spiel gegen {gegner} in {spielort} an.",
        f"am {weekday_name} ({datum_str}) geht es wieder rund! Wir spielen gegen {gegner} in {spielort}.",
        f"nächste Woche {weekday_name} ({datum_str}) wartet das nächste Match auf uns gegen {gegner} in {spielort}."
    ]
    treff_bausteine = [
        f"Anstoß ist um {anstoß_str}, dazu treffen wir uns um {treffpunkt_str} in {spielort} am Stadion.",
        f"Anpfiff ist um {anstoß_str} – Treffpunkt ist um {treffpunkt_str} in {spielort} direkt am Stadion.",
        f"Das Spiel beginnt um {anstoß_str}. Wir treffen uns um {treffpunkt_str} in {spielort} am Stadion.",
        f"Anstoß ist um {anstoß_str}, Treffpunkt ist um {treffpunkt_str} in {spielort} am Stadion."
    ]
    abstimm_bausteine = [
        "Gerne einmal abstimmen wer dabei ist auch für die Trainings!",
        "Bitte stimmt zeitnah ab, wer beim Spiel und bei den Trainings dabei ist!",
        "Gebt bitte kurz Rückmeldung, wer am Wochenende und beim Training dabei sein kann!",
        "Tragt euch bitte kurz ein, wer für das Spiel und die Trainings dabei ist!"
    ]
    gruesse = [
        "Schönes Wochenende ⚽",
        "Euch allen ein schönes Wochenende! 👍",
        "Schönes Wochenende und bis Montag! 👋",
        "Habt ein erholsames Wochenende! ⚽"
    ]

    begr = begruessungen[kw % len(begruessungen)]
    einl = einleitungen[(kw + 1) % len(einleitungen)]
    treff = treff_bausteine[(kw + 2) % len(treff_bausteine)]
    abst = abstimm_bausteine[(kw + 3) % len(abstimm_bausteine)]
    schluss = gruesse[kw % len(gruesse)]

    if is_home:
        return f"{begr} {einl} {treff} {abst}\n{schluss}"
    else:
        return f"{begr} {einl} {treff} {adresse}. {abst}\n{schluss}"


def send_via_ntfy(topic: str, text: str):
    """Sendet Push-Benachrichtigung via ntfy.sh mit WhatsApp- und Kopier-Button."""
    url = "https://ntfy.sh"
    encoded_text = urllib.parse.quote(text)

    payload = {
        "topic": topic,
        "title": "⚽ D-Jugend Wochenplan",
        "message": text,
        "tags": ["soccer", "calendar"],
        "actions": [
            {
                "action": "view",
                "label": "In WhatsApp öffnen",
                "url": f"whatsapp://send?text={encoded_text}"
            },
            {
                "action": "copy",
                "label": "Text kopieren",
                "value": text
            }
        ]
    }

    req = urllib.request.Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json; charset=utf-8"},
        method="POST"
    )
    try:
        with urllib.request.urlopen(req, timeout=20) as resp:
            if resp.status == 200:
                print(f"✅ Push-Benachrichtigung erfolgreich an ntfy-Thema '{topic}' gesendet!")
                return True
    except urllib.error.HTTPError as e:
        error_body = e.read().decode("utf-8", errors="replace")
        print(f"❌ ntfy HTTP Fehler {e.code}: {error_body}")
        raise
    except Exception as e:
        print(f"❌ ntfy Fehler: {e}")
        raise
    return False


def send_via_telegram(bot_token: str, chat_id: str, text: str):
    """Sendet Nachricht per Telegram."""
    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    payload = json.dumps({
        "chat_id": chat_id,
        "text": text
    }).encode("utf-8")
    
    headers = {"Content-Type": "application/json"}
    req = urllib.request.Request(url, data=payload, headers=headers, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=20) as resp:
            if resp.status == 200:
                print("✅ Nachricht erfolgreich via Telegram gesendet!")
                return True
    except Exception as e:
        print(f"❌ Telegram Fehler: {e}")
        return False
    return False


def main():
    print("=== D-Jugend Wochenplaner gestartet ===")

    next_monday, next_sunday = get_target_week_range()
    print(f"Ermittle Spiel für Zeitraum: {next_monday} bis {next_sunday}")

    try:
        matches = fetch_matches_from_fussball_de(FUSSBALL_URL_OR_ID)
        print(f"Erfolgreich {len(matches)} Spiele aus fussball.de geladen.")
    except Exception as e:
        print(f"❌ Fehler beim Laden von fussball.de: {e}")
        sys.exit(1)

    message_text = build_message(next_monday, next_sunday, matches, vary=VARIATION_MODE)
    print("\n--- Generierter Nachrichtentext: ---")
    print(message_text)
    print("------------------------------------\n")

    if NTFY_TOPIC:
        print(f"Sende Push an ntfy.sh/{NTFY_TOPIC}...")
        send_via_ntfy(NTFY_TOPIC, message_text)

    if TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID:
        print("Sende Nachricht via Telegram...")
        send_via_telegram(TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID, message_text)

    if not NTFY_TOPIC and not (TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID):
        print("ℹ️ Kein Kanal (NTFY_TOPIC) gesetzt. Nur Konsolenausgabe.")


if __name__ == "__main__":
    main()
