# ⚽ D-Jugend Wochenplaner für WhatsApp

Automatische Erstellung und Zusendung des wöchentlichen WhatsApp-Nachrichtentextes für Training & Meisterschaftsspiel direkt auf dein Smartphone via WhatsApp.

---

## 📋 Was das System macht
Jeden **Freitag um 08:00 Uhr** (oder jederzeit manuell per Klick):
1. Liest automatisch den aktuellen Spielplan deiner D-Jugend von **fussball.de** (Gegner, Anstoßzeit, Treffpunkt, Spielort/Sportplatz).
2. Fügt deine festen **Trainingszeiten (Montag & Mittwoch)** hinzu.
3. Baut eine ansprechende, übersichtliche WhatsApp-Nachricht mit Emojis.
4. Sendet die fertige Nachricht direkt per **WhatsApp an dein eigenes Handy** (über den kostenlosen Dienst CallMeBot).
5. Du musst die Nachricht nur noch antippen, weiterleiten oder in die Mannschaftsgruppe kopieren!

---

## 🚀 Einrichtung in 4 einfachen Schritten

### Schritt 1: iCal-Link auf fussball.de finden
1. Öffne im Browser (PC oder Smartphone) [fussball.de](https://www.fussball.de).
2. Suche nach deinem Verein und navigiere zu deiner **D-Jugend / D-Junioren** Mannschaft.
3. Klicke auf den Reiter **„Spielplan“**.
4. Suche den Button **„Kalender abonnieren“** bzw. **„Spielplan im iCal-Format abonnieren“** (befindet sich meist über oder unter der Spieltagsliste).
5. Klicke mit der **rechten Maustaste** darauf (am Handy lange gedrückt halten) und wähle:
   👉 **„Link-Adresse kopieren“**
6. Der Link sieht ungefähr so aus:
   `https://www.fussball.de/export.ics/-/id/0123456789ABCDEF...`
   *(Speichere dir diesen Link kurz in den Notizen)*.

---

### Schritt 2: Kostenlosen WhatsApp-Schlüssel (CallMeBot) holen (Dauert 30 Sek.)
CallMeBot ist ein kostenloser Dienst, der WhatsApp-Nachrichten an deine eigene Nummer schicken kann.

1. Speichere die Nummer **`+34 644 44 20 62`** (oder je nach aktueller Info auf [callmebot.com](https://www.callmebot.com/blog/free-api-whatsapp-messages/)) in deinen Kontakten unter z. B. „CallMeBot“ ab.
2. Sende über WhatsApp an diese Nummer folgende Nachricht:
   ```text
   I allow callmebot to send me messages
   ```
3. Du erhältst innerhalb weniger Sekunden eine Antwort per WhatsApp mit deinem persönlichen **API-Key** (z. B. `123456`).
4. Notiere dir:
   - Deine Telefonnummer mit Ländervorwahl (z. B. `+491701234567`)
   - Deinen API-Key (z. B. `123456`)

---

### Schritt 3: GitHub Repository erstellen & Secrets anlegen
Da GitHub Actions das Skript jeden Freitag völlig kostenlos in der Cloud ausführt, brauchst du keinen laufenden Computer.

1. Erstelle ein neues, privates Repository auf [GitHub](https://github.com/new) (z. B. `d-jugend-wochenplaner`).
2. Lade diese Dateien hoch oder führe im Ordner folgendes aus:
   ```bash
   git init
   git add .
   git commit -m "Initialer Wochenplaner"
   git branch -M main
   git remote add origin https://github.com/DEIN_BENUTZERNAME/d-jugend-wochenplaner.git
   git push -u origin main
   ```
3. Gehe in deinem GitHub-Repository auf **Settings** -> **Secrets and variables** -> **Actions**.
4. Klicke auf **New repository secret** und lege folgende Secrets an:

| Name | Wert / Beispiel | Pflicht? |
| :--- | :--- | :--- |
| `FUSSBALL_ICAL_URL` | Dein kopierter iCal-Link aus Schritt 1 | **Ja** |
| `CALLMEBOT_PHONE` | Deine Handynummer (z. B. `+491701234567`) | **Ja** |
| `CALLMEBOT_APIKEY` | Dein CallMeBot-Schlüssel aus Schritt 2 | **Ja** |
| `MY_TEAM_NAME` | Name deines Vereins (z. B. `TSV Musterdorf`) | Optional (für Heim/Auswärts-Erkennung) |
| `TRAINING_MONTAG_TIME` | z. B. `17:30 – 19:00 Uhr` | Optional (Standard ist 17:30 - 19:00 Uhr) |
| `TRAINING_MITTWOCH_TIME` | z. B. `17:30 – 19:00 Uhr` | Optional (Standard ist 17:30 - 19:00 Uhr) |
| `TREFFPUNKT_OFFSET_MINUTES` | z. B. `45` (Minuten vor Anstoß) | Optional (Standard ist 45 Min.) |

---

### Schritt 4: Sofort testen!
1. Klicke in deinem GitHub-Repository oben auf den Reiter **Actions**.
2. Wähle links **„D-Jugend Wochenplaner“** aus.
3. Klicke rechts auf **Run workflow** -> grüner Button **Run workflow**.
4. Nach ca. 20–30 Sekunden erhältst du die fertige Nachricht direkt auf dein WhatsApp! 🎉
5. Ab jetzt läuft das Ganze **jeden Freitag automatisch**.

---

## 📱 Beispiel der fertigen WhatsApp-Nachricht

```text
⚽ *Wochenplan D-Jugend*
Hallo zusammen! Hier ist der Plan für die nächste Woche (14.09. – 20.09.):

🏃 *TRAINING:*
• *Montag (14.09.):* 17:30 – 19:00 Uhr
• *Mittwoch (16.09.):* 17:30 – 19:00 Uhr

🏆 *HEIMSPIEL 🏠 (Samstag):*
• *Paarung:* TSV Musterdorf vs. SV Kickers 09
• *Anstoß:* Samstag, 19.09.2026 um 14:00 Uhr
• *Treffpunkt:* 13:15 Uhr (45 Min. vor Anstoß)
• *Ort / Platz:* Kunstrasenplatz 1, Sportweg 4, 12345 Stadt

👉 *Bitte gebt mir bis Sonntagabend kurz Bescheid, wer an welchen Tagen (Training & Spiel) dabei ist!*

Sportliche Grüße 👋
```
