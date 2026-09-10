#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Wochenplan-Ersteller für D-Jugend Trainer (JSG Hörstel / Dreierwalde II)
Reines Python 3 (Standardbibliothek - keine externen Abhängigkeiten erforderlich).
Liest die Spieldaten von fussball.de aus und sendet die fertige Nachricht
freitags automatisch auf dein Smartphone (z. B. via ntfy Push oder Telegram).
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
# KONFIGURATION (über Secrets / Umgebungsvariablen)
# ==========================================
# Dein Team-Link oder die Team-ID von fussball.de
FUSSBALL_URL_OR_ID = os.getenv(
    "FUSSBALL_URL_OR_ID", 
    "https://www.fussball.de/ajax.team.matchplan/-/mode/PAGE/team-id/0200HNN2LG000000VS548984VSUCHKOE"
).strip()

# Eigener Vereinsname (für Erkennung von Heim- vs. Auswärtsspiel)
MY_TEAM_NAME = os.getenv("MY_TEAM_NAME", "JSG Hörstel").strip()

# ntfy.sh Topic für kostenlose Push-Benachrichtigungen aufs Handy
# Wähle ein eigenes, geheimes Thema (z. B. d-jugend-hoerstel-trainer-xyz123)
NTFY_TOPIC = os.getenv("NTFY_TOPIC", "").strip()

# Telegram (optional, falls Telegram genutzt werden soll)
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "").strip()
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "").strip()

# Trainingszeiten
TRAINING_MO_TIME = os.getenv("TRAINING_MONTAG_TIME", "17:30 – 19:00 Uhr").strip()
TRAINING_MI_TIME = os.getenv("TRAINING_MITTWOCH_TIME", "17:30 – 19:00 Uhr").strip()
TREFFPUNKT_MINUTEN = int(os.getenv("TREFFPUNKT_OFFSET_MINUTES", "45"))

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
    """
    Ermittelt den Zeitraum der nächsten Spielwoche (Montag bis Sonntag).
    Wenn das Skript freitags ausgeführt wird, ist der nächste Montag in 3 Tagen.
    """
    if ref_date is None:
        ref_date = datetime.date.today()

    days_until_next_monday = (7 - ref_date.weekday()) % 7
    if days_until_next_monday == 0:
        days_until_next_monday = 7  # Wenn heute Montag ist, nimm nächsten Montag

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


def fetch_matches_from_fussball_de(url_or_id: str):
    """
    Lädt den Spielplan mit Spielstätten über den fussball.de JSON-Endpoint.
    """
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

    # Blöcke nach 'row-headline visible-small' aufteilen
    blocks = re.split(r'<tr class="row-headline visible-small">', raw_html)
    matches = []

    for block in blocks[1:]:
        headline_m = re.search(r'<td[^>]*>(.*?)</td>', block)
        headline = headline_m.group(1).strip() if headline_m else ""

        # Clubs auslesen
        clubs = re.findall(r'<div class="club-name">\s*(.*?)\s*</div>', block, re.DOTALL)
        clean_clubs = [re.sub(r'&#\d+;', '', c).strip().replace('/ ', '/') for c in clubs]

        # Venue (Sportplatz mit Adresse)
        venue_m = re.search(r'row-venue.*?<td colspan="3">\s*(.*?)\s*</td>', block, re.DOTALL)
        venue = venue_m.group(1).strip() if venue_m else "Wird noch bekanntgegeben"
        venue = " ".join(venue.split())

        # Datum und Zeit auslesen
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
                "venue": venue
            })

    matches.sort(key=lambda x: x["start"])
    return matches


def build_whatsapp_message(target_monday: datetime.date, target_sunday: datetime.date, matches: list):
    """Erstellt den fertigen Text für die WhatsApp-Gruppe."""
    target_wednesday = target_monday + datetime.timedelta(days=2)

    # Nach Spielen in dieser Woche suchen
    week_matches = [
        m for m in matches
        if target_monday <= m["start"].date() <= target_sunday
    ]

    mo_str = target_monday.strftime("%d.%m.")
    mi_str = target_wednesday.strftime("%d.%m.")

    lines = [
        "⚽ *Wochenplan D-Jugend*",
        f"Hallo zusammen! Hier ist der Plan für die nächste Woche ({mo_str} – {target_sunday.strftime('%d.%m.')}):",
        "",
        "🏃 *TRAINING:*",
        f"• *Montag ({mo_str}):* {TRAINING_MO_TIME}",
        f"• *Mittwoch ({mi_str}):* {TRAINING_MI_TIME}",
        ""
    ]

    if not week_matches:
        lines.extend([
            "🏆 *SPIEL:*",
            "• *Spielfrei am Wochenende!* Keine Meisterschaftsbegegnung eingetragen.",
            ""
        ])
    else:
        for match in week_matches:
            m_date = match["start"].date()
            weekday_name = DAYS_DE.get(m_date.weekday(), "Spieltag")
            kickoff_time = match["start"].strftime("%H:%M")
            date_formatted = match["start"].strftime("%d.%m.%Y")

            # Treffpunkt
            treffpunkt_dt = match["start"] - datetime.timedelta(minutes=TREFFPUNKT_MINUTEN)
            treffpunkt_time = treffpunkt_dt.strftime("%H:%M")

            home = match["home"]
            away = match["away"]

            is_home = MY_TEAM_NAME.lower() in home.lower()
            is_away = MY_TEAM_NAME.lower() in away.lower()

            if is_home:
                spiel_typ = "HEIMSPIEL 🏠"
            elif is_away:
                spiel_typ = "AUSWÄRTSSPIEL 🚗"
            else:
                spiel_typ = "SPIEL"

            lines.extend([
                f"🏆 *{spiel_typ} ({weekday_name}):*",
                f"• *Paarung:* {home} vs. {away}",
                f"• *Anstoß:* {weekday_name}, {date_formatted} um {kickoff_time} Uhr",
                f"• *Treffpunkt:* {treffpunkt_time} Uhr ({TREFFPUNKT_MINUTEN} Min. vor Anstoß)",
                f"• *Ort / Sportplatz:* {match['venue']}",
                ""
            ])

    lines.extend([
        "👉 *Bitte gebt mir bis Sonntagabend kurz Bescheid, wer an welchen Tagen (Training & Spiel) dabei ist!*",
        "",
        "Sportliche Grüße 👋"
    ])

    return "\n".join(lines)


def send_via_ntfy(topic: str, text: str):
    """
    Sendet eine Push-Benachrichtigung über ntfy.sh direkt aufs Smartphone.
    Mit 1-Klick-Button 'In WhatsApp öffnen'!
    """
    url = f"https://ntfy.sh/{topic}"
    encoded_text = urllib.parse.quote(text)
    
    headers = {
        "Title": "⚽ D-Jugend Wochenplan".encode("utf-8"),
        "Tags": "soccer,calendar",
        # Push-Aktionen: 1) WhatsApp direkt öffnen, 2) Text in Zwischenablage kopieren
        "Actions": f"view, In WhatsApp öffnen, whatsapp://send?text={encoded_text}; copy, Text kopieren, {text}"
    }

    req = urllib.request.Request(url, data=text.encode("utf-8"), headers=headers, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=20) as resp:
            if resp.status == 200:
                print(f"✅ Push-Benachrichtigung erfolgreich an ntfy-Thema '{topic}' gesendet!")
                return True
    except Exception as e:
        print(f"❌ ntfy Fehler: {e}")
        return False
    return False


def send_via_telegram(bot_token: str, chat_id: str, text: str):
    """Sendet die Nachricht per Telegram Bot."""
    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    payload = json.dumps({
        "chat_id": chat_id,
        "text": text,
        "parse_mode": "Markdown"
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
    print(f"Ermittle Termine für Zeitraum: {next_monday} bis {next_sunday}")

    try:
        matches = fetch_matches_from_fussball_de(FUSSBALL_URL_OR_ID)
        print(f"Erfolgreich {len(matches)} Spiele aus fussball.de geladen.")
    except Exception as e:
        print(f"❌ Fehler beim Laden von fussball.de: {e}")
        sys.exit(1)

    message_text = build_whatsapp_message(next_monday, next_sunday, matches)
    print("\n--- Generierter Nachrichtentext: ---")
    print(message_text)
    print("------------------------------------\n")

    # Versand via ntfy Push
    if NTFY_TOPIC:
        print(f"Sende Push an ntfy.sh/{NTFY_TOPIC}...")
        send_via_ntfy(NTFY_TOPIC, message_text)

    # Versand via Telegram
    if TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID:
        print("Sende Nachricht via Telegram...")
        send_via_telegram(TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID, message_text)

    if not NTFY_TOPIC and not (TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID):
        print("ℹ️ Kein Benachrichtigungskanal (NTFY_TOPIC oder TELEGRAM) gesetzt. Nur Konsolenausgabe.")


if __name__ == "__main__":
    main()
