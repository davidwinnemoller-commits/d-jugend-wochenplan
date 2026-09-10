# ⚽ D-Jugend Wochenplaner für die JSG Hörstel / Dreierwalde II

Automatische Erstellung des wöchentlichen WhatsApp-Nachrichtentextes für Training & Meisterschaftsspiel direkt auf dein Smartphone.

---

## 🎯 Was das System macht
Jeden **Freitag um 08:00 Uhr** (oder jederzeit manuell per Klick):
1. Holt automatisch das nächste Spiel der **JSG Hörstel/Dreierwalde II** von **fussball.de** (Gegner, Anstoßzeit, Treffpunkt, genaue Sportplatz-Adresse).
2. Fügt deine festen **Trainingszeiten (Montag & Mittwoch)** hinzu.
3. Sendet eine Push-Benachrichtigung auf dein Handy mit einem **1-Klick-Button: "In WhatsApp öffnen"**.
4. WhatsApp öffnet sich direkt mit dem fertigen Text – du musst nur noch deine Mannschaftsgruppe auswählen und abschicken!

---

## 🚀 Einrichtung in 3 einfachen Schritten

### Schritt 1: Kostenlose Push-App „ntfy“ auf dem Handy installieren
Da fremde WhatsApp-Bots wie CallMeBot oft überlastet oder gesperrt sind, nutzen wir **ntfy** (100 % kostenlos, werbefrei, Open Source, ohne Registrierung, ohne Telefonnummer).

1. Installiere die kostenlose App **ntfy** auf deinem Smartphone:
   * **iPhone:** [App Store: ntfy](https://apps.apple.com/app/ntfy/id1625396347)
   * **Android:** [Google Play Store: ntfy](https://play.google.com/store/apps/details?id=io.heckel.ntfy)
2. Öffne die App, tippe auf **+** (Thema abonnieren).
3. Gib einen beliebigen geheimen Namen für dein Thema ein, z. B.:
   `hoerstel-d-jugend-trainer-8492` *(Wähle ein eigenes Wort mit ein paar Zahlen)*
4. Fertig! Auf dieses Thema schickt das Skript freitags deine Nachricht.

---

### Schritt 2: GitHub Repository anlegen & Secret eintragen
1. Erstelle ein kostenloses privates Repository auf [github.com/new](https://github.com/new) (z. B. `d-jugend-wochenplaner`).
2. Lade diesen Ordner hoch (oder per `git push`).
3. Gehe in deinem Repository auf **Settings** ➔ **Secrets and variables** ➔ **Actions**.
4. Klicke auf **New repository secret** und lege folgendes Secret an:

| Name | Wert | Beschreibung |
| :--- | :--- | :--- |
| `NTFY_TOPIC` | z. B. `hoerstel-d-jugend-trainer-8492` | Der Themen-Name aus Schritt 1 |

*(Dein fussball.de-Link und der Teamname „JSG Hörstel“ sind im Skript bereits als Standard hinterlegt!)*

---

### Schritt 3: Testen!
1. Klicke in deinem GitHub-Repository oben auf **Actions**.
2. Wähle links **„D-Jugend Wochenplaner“**.
3. Klicke auf **Run workflow** ➔ grüner Button **Run workflow**.
4. Innerhalb von 10 Sekunden ploppt die Benachrichtigung auf deinem Smartphone auf!
5. Tippe auf den Button **„In WhatsApp öffnen“** – WhatsApp startet direkt mit dem fertigen Text.

---

## 📱 Vorschau der generierten Nachricht

```text
⚽ *Wochenplan D-Jugend*
Hallo zusammen! Hier ist der Plan für die nächste Woche (14.09. – 20.09.):

🏃 *TRAINING:*
• *Montag (14.09.):* 17:30 – 19:00 Uhr
• *Mittwoch (16.09.):* 17:30 – 19:00 Uhr

🏆 *AUSWÄRTSSPIEL 🚗 (Samstag):*
• *Paarung:* Cheruskia Laggenbeck 2 vs. JSG Hörstel/Dreierwalde II
• *Anstoß:* Samstag, 19.09.2026 um 14:00 Uhr
• *Treffpunkt:* 13:15 Uhr (45 Min. vor Anstoß)
• *Ort / Sportplatz:* Rasenplatz, Carl-Keller-Stadion Platz 2, Jahnstr. 21, 49479 Ibbenbüren

👉 *Bitte gebt mir bis Sonntagabend kurz Bescheid, wer an welchen Tagen (Training & Spiel) dabei ist!*

Sportliche Grüße 👋
```
