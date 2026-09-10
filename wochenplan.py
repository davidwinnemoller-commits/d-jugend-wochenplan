#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Wochenplan-Ersteller für D-Jugend Trainer
Liest den iCal-Kalender von fussball.de aus und versendet
freitags automatisch die WhatsApp-Nachricht via CallMeBot.
"""

import os
import sys
import datetime
import urllib.parse
import requests
from icalendar import Calendar
from dateutil import tz

# Standard-Konfigurationen (können über Umgebungsvariablen / Secrets angepasst werden)
FUSSBALL_ICAL_URL = os.getenv("FUSSBALL_ICAL_URL", "").strip()
CALLMEBOT_PHONE = os.getenv("CALLMEBOT_PHONE", "").strip()
CALLMEBOT_APIKEY = os.getenv("CALLMEBOT_APIKEY", "").strip()
MY_TEAM_NAME = os.getenv("MY_TEAM_NAME", "").strip()

TRAINING_MO_TIME = os.getenv("TRAINING_MONTAG_TIME", "17:30 – 19:00 Uhr").strip()
TRAINING_MI_TIME = os.getenv("TRAINING_MITTWOCH_TIME", "17:30 – 19:00 Uhr").strip()
TREFFPUNKT_MINUTEN = int(os.getenv("TREFFPUNKT_OFFSET_MINUTES", "45"))

# Lokale Zeitzone Deutschland
LOCAL_TZ = tz.gettz("Europe/Berlin")

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
        ref_date = datetime.datetime.now(LOCAL_TZ).date()

    # Nächsten Montag berechnen:
    # 0 = Mo, 4 = Fr
    days_until_next_monday = (7 - ref_date.weekday()) % 7
    if days_until_next_monday == 0:
        days_until_next_monday = 7  # Wenn heute Montag ist, nimm nächsten Montag

    next_monday = ref_date + datetime.timedelta(days=days_until_next_monday)
    next_sunday = next_monday + datetime.timedelta(days=6)

    return next_monday, next_sunday


def fetch_and_parse_events(ical_url: str):
    """Lädt die .ics Datei von fussball.de und parst alle Termine."""
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    response = requests.get(ical_url, headers=headers, timeout=20)
    response.raise_for_status()

    cal = Calendar.from_ical(response.content)
    events = []

    for component in cal.walk():
        if component.name == "VEVENT":
            dtstart = component.get("dtstart").dt
            
            # Zeitzone sicherstellen
            if isinstance(dtstart, datetime.datetime):
                if dtstart.tzinfo is None:
                    dtstart = dtstart.replace(tzinfo=LOCAL_TZ)
                else:
                    dtstart = dtstart.astimezone(LOCAL_TZ)
            elif isinstance(dtstart, datetime.date):
                dtstart = datetime.datetime.combine(dtstart, datetime.time(0, 0), tzinfo=LOCAL_TZ)

            summary = str(component.get("summary", "")).strip()
            location = str(component.get("location", "")).strip()
            description = str(component.get("description", "")).strip()

            events.append({
                "start": dtstart,
                "summary": summary,
                "location": location,
                "description": description
            })

    # Sortieren nach Startdatum
    events.sort(key=lambda x: x["start"])
    return events


def parse_match_details(summary: str, my_team: str):
    """
    Versucht Gegner, Heim/Auswärts aus dem Titel zu extrahieren.
    fussball.de nutzt häufig: 'Heimteam : Gastteam' oder 'Heimteam - Gastteam'
    """
    clean_summary = summary
    # Häufige Präfixe wie 'D-Junioren Kreisklasse: ' entfernen
    if ":" in clean_summary and ("-" in clean_summary or "vs" in clean_summary or ":" in clean_summary):
        # Wenn vor dem ersten Doppelpunkt z.B. die Liga steht
        parts = clean_summary.split(":", 1)
        if any(w in parts[0].lower() for w in ["junioren", "jugend", "liga", "klasse", "staffel", "pokal"]):
            clean_summary = parts[1].strip()

    delimiter = " - " if " - " in clean_summary else (" : " if " : " in clean_summary else " vs. ")
    
    if delimiter in clean_summary:
        teams = clean_summary.split(delimiter, 1)
        team_a = teams[0].strip()
        team_b = teams[1].strip()

        if my_team:
            if my_team.lower() in team_a.lower():
                return {"type": "Heimspiel 🏠", "opponent": team_b, "headline": f"{team_a} vs. {team_b}"}
            elif my_team.lower() in team_b.lower():
                return {"type": "Auswärtsspiel 🚗", "opponent": team_a, "headline": f"{team_a} vs. {team_b}"}

        return {"type": "Spiel", "opponent": f"{team_a} vs. {team_b}", "headline": f"{team_a} vs. {team_b}"}

    return {"type": "Spiel", "opponent": clean_summary, "headline": clean_summary}


def build_whatsapp_message(target_monday: datetime.date, target_sunday: datetime.date, events: list):
    """Baut den formatierten Nachrichtentext für die WhatsApp-Gruppe."""
    target_wednesday = target_monday + datetime.timedelta(days=2)

    # Nach Spielen in dieser Woche suchen (insbesondere Wochenende)
    week_matches = [
        ev for ev in events
        if target_monday <= ev["start"].date() <= target_sunday
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
            
            # Treffpunkt berechnen
            treffpunkt_dt = match["start"] - datetime.timedelta(minutes=TREFFPUNKT_MINUTEN)
            treffpunkt_time = treffpunkt_dt.strftime("%H:%M")

            details = parse_match_details(match["summary"], MY_TEAM_NAME)
            location = match["location"] or "Wird noch bekanntgegeben"

            lines.extend([
                f"🏆 *{details['type'].upper()} ({weekday_name}):*",
                f"• *Paarung:* {details['headline']}",
                f"• *Anstoß:* {weekday_name}, {date_formatted} um {kickoff_time} Uhr",
                f"• *Treffpunkt:* {treffpunkt_time} Uhr ({TREFFPUNKT_MINUTEN} Min. vor Anstoß)",
                f"• *Ort / Platz:* {location}",
                ""
            ])

    lines.extend([
        "👉 *Bitte gebt mir bis Sonntagabend kurz Bescheid, wer an welchen Tagen (Training & Spiel) dabei ist!*",
        "",
        "Sportliche Grüße 👋"
    ])

    return "\n".join(lines)


def send_whatsapp_callmebot(phone: str, apikey: str, text: str):
    """Sendet die Nachricht per CallMeBot WhatsApp API."""
    base_url = "https://api.callmebot.com/whatsapp.php"
    encoded_text = urllib.parse.quote(text)
    
    # CallMeBot verlangt standardmäßig phone, text, apikey
    url = f"{base_url}?phone={phone}&text={encoded_text}&apikey={apikey}"
    
    response = requests.get(url, timeout=30)
    if response.status_code == 200 and "error" not in response.text.lower():
        print("✅ WhatsApp-Nachricht erfolgreich via CallMeBot versendet!")
        return True
    else:
        print(f"❌ Fehler beim Versenden via CallMeBot: HTTP {response.status_code}")
        print(f"Antwort: {response.text}")
        return False


def main():
    print("=== D-Jugend Wochenplaner gestartet ===")

    if not FUSSBALL_ICAL_URL:
        print("❌ FEHLER: Keine FUSSBALL_ICAL_URL konfiguriert!")
        sys.exit(1)

    # Zielwoche berechnen
    next_monday, next_sunday = get_target_week_range()
    print(f"Ermittle Termine für Zeitraum: {next_monday} bis {next_sunday}")

    # Termine von fussball.de laden
    print(f"Lade iCal-Kalender von: {FUSSBALL_ICAL_URL[:60]}...")
    try:
        events = fetch_and_parse_events(FUSSBALL_ICAL_URL)
        print(f"Erfolgreich {len(events)} Termine im Kalender gefunden.")
    except Exception as e:
        print(f"❌ Fehler beim Laden/Parsen des Kalenders: {e}")
        sys.exit(1)

    # Text generieren
    message_text = build_whatsapp_message(next_monday, next_sunday, events)
    print("\n--- Generierter Nachrichtentext: ---")
    print(message_text)
    print("------------------------------------\n")

    # WhatsApp-Versand via CallMeBot (falls Zugangsdaten vorhanden)
    if CALLMEBOT_PHONE and CALLMEBOT_APIKEY:
        print("Sende Nachricht an deine WhatsApp-Nummer...")
        success = send_whatsapp_callmebot(CALLMEBOT_PHONE, CALLMEBOT_APIKEY, message_text)
        if not success:
            sys.exit(1)
    else:
        print("ℹ️ Hinweis: CALLMEBOT_PHONE oder CALLMEBOT_APIKEY nicht gesetzt. Nachricht wird nur in der Konsole ausgegeben (Testmodus).")


if __name__ == "__main__":
    main()
