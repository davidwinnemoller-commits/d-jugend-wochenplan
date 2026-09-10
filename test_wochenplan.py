import datetime
from wochenplan import get_target_week_range, parse_match_details, build_whatsapp_message

def test_dates():
    # Testen an einem Freitag
    friday = datetime.date(2026, 9, 11) # Freitag
    next_mo, next_so = get_target_week_range(friday)
    print(f"Freitag {friday} -> Nächster Montag: {next_mo}, Sonntag: {next_so}")
    assert next_mo == datetime.date(2026, 9, 14)
    assert next_so == datetime.date(2026, 9, 20)

    # Testen an einem Donnerstag
    thursday = datetime.date(2026, 9, 10)
    next_mo_th, next_so_th = get_target_week_range(thursday)
    assert next_mo_th == datetime.date(2026, 9, 14)

def test_details():
    res1 = parse_match_details("D-Junioren Kreisliga: SV Kickers 09 - FC Dynamo", "SV Kickers 09")
    print("Match 1:", res1)
    assert "Heimspiel" in res1["type"]

    res2 = parse_match_details("FC Dynamo : SV Kickers 09", "SV Kickers 09")
    print("Match 2:", res2)
    assert "Auswärtsspiel" in res2["type"]

def test_message_builder():
    mo = datetime.date(2026, 9, 14)
    so = datetime.date(2026, 9, 20)
    mock_events = [
        {
            "start": datetime.datetime(2026, 9, 19, 14, 0, tzinfo=datetime.timezone.utc),
            "summary": "D-Jugend: SV Kickers 09 - TSV Ballzauber",
            "location": "Sportplatz Am Hain, Sportweg 4, 12345 Stadt",
            "description": "Meisterschaftsspiel"
        }
    ]
    msg = build_whatsapp_message(mo, so, mock_events)
    print("\n--- Test Nachricht ---")
    print(msg)
    print("----------------------")
    assert "TSV Ballzauber" in msg
    assert "14:00 Uhr" in msg

if __name__ == "__main__":
    test_dates()
    test_details()
    test_message_builder()
    print("Alle Tests erfolgreich bestanden!")
