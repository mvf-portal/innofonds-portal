# -*- coding: utf-8 -*-
"""Wache: Ist der Block "Neu im Innovationsfonds" von heute?

Warum es diese Wache gibt
-------------------------
newsletter.json entsteht im taeglichen Lauf auf dem Rechner von Peter
Stegmaier (Windows-Aufgabe "Innovationsfonds-Monitor", 06:00). Laeuft der
Rechner nicht, faellt die Datei nicht weg - sie bleibt einfach vom Vortag
liegen. Die Newsletterplattform holt sie um 07:20 und baut den Block
klaglos aus alten Zahlen. Genau das faellt niemandem auf.

Gemessen wird deshalb die AUSGELIEFERTE Datei unter innofonds.m-vf.de,
nicht die im Arbeitsverzeichnis: Gebaut ist nicht ausgeliefert, und der
Unterschied hat hier schon einmal 410 Berichtsdateien still veralten
lassen.

Der Massstab ist "von heute", nicht "juenger als 24 Stunden". Faellt ein
Tag aus, ist die Datei am naechsten Morgen rund 25 Stunden alt - eine
24-Stunden-Grenze haette das gerade noch durchgewunken.

Ausgang: 0 = in Ordnung, 1 = Alarm. Der Alarm ist der fehlgeschlagene
Lauf; GitHub schickt darueber von sich aus eine Mail. Kein Secret, kein
Token, keine zweite Stelle, die gepflegt werden muss.
"""
from __future__ import annotations

import json
import os
import sys
import urllib.request
from datetime import datetime, timedelta, timezone

ADRESSE = "https://innofonds.m-vf.de/newsletter.json"
BERLIN = timezone(timedelta(hours=1))      # nur fuer die Tagesgrenze


def berliner_zeit(jetzt: datetime) -> datetime:
    """Berlin ohne zoneinfo: Sommerzeit ist letzter So im Maerz bis letzter So im Oktober."""
    def letzter_sonntag(jahr: int, monat: int) -> datetime:
        tag = datetime(jahr, monat, 31, 1, tzinfo=timezone.utc)
        return tag - timedelta(days=(tag.weekday() + 1) % 7)
    u = jetzt.astimezone(timezone.utc)
    sommer = letzter_sonntag(u.year, 3) <= u < letzter_sonntag(u.year, 10)
    return u.astimezone(timezone(timedelta(hours=2 if sommer else 1)))


def notiz(zeilen: list[str]) -> None:
    """In die Zusammenfassung des Laufs schreiben, damit man sie ohne Klick sieht."""
    pfad = os.environ.get("GITHUB_STEP_SUMMARY")
    text = "\n".join(zeilen)
    print(text)
    if pfad:
        with open(pfad, "a", encoding="utf-8") as f:
            f.write(text + "\n")


def main() -> int:
    bitte = urllib.request.Request(
        ADRESSE + "?wache=" + datetime.now(timezone.utc).strftime("%Y%m%d%H%M"),
        headers={"Cache-Control": "no-cache",
                 "User-Agent": "innofonds-wache/1.0 (+https://innofonds.m-vf.de)"})
    try:
        with urllib.request.urlopen(bitte, timeout=30) as a:
            daten = json.loads(a.read().decode("utf-8"))
    except Exception as e:                                   # noqa: BLE001
        notiz(["## Neu im Innovationsfonds: ALARM",
               "",
               f"`{ADRESSE}` ist nicht lesbar: {e}",
               "",
               "Die Newsletterplattform holt diese Datei um 07:20. Ist sie nicht",
               "erreichbar, faellt die Karte im Entwurf ersatzlos weg."])
        return 1

    stand_roh = str(daten.get("stand", ""))
    try:
        stand = datetime.fromisoformat(stand_roh).replace(tzinfo=BERLIN)
    except ValueError:
        notiz(["## Neu im Innovationsfonds: ALARM", "",
               f"Die Angabe `stand` ist unbrauchbar: `{stand_roh}`"])
        return 1

    jetzt = berliner_zeit(datetime.now(timezone.utc))
    alter = jetzt - stand.astimezone(jetzt.tzinfo)
    stunden = alter.total_seconds() / 3600
    eintraege = len(daten.get("eintraege") or daten.get("meldungen") or [])
    frisch = stand.date() == jetzt.date()

    kopf = "in Ordnung" if frisch else "ALARM"
    zeilen = [f"## Neu im Innovationsfonds: {kopf}", "",
              f"- Stand der ausgelieferten Datei: **{stand:%d.%m.%Y %H:%M}**",
              f"- Alter: {stunden:.1f} Stunden",
              f"- Eintraege im Block: {eintraege}"]
    if not frisch:
        zeilen += ["",
                   "Der taegliche Lauf hat heute nichts ausgeliefert. Die",
                   "Newsletterplattform baut den Block um 07:20 trotzdem - aus",
                   "den Zahlen von oben, ohne es zu sagen.",
                   "",
                   "Was zu tun ist: Rechner an, dann",
                   "`py run_taeglich.py` im Ordner `innovationsfonds`.",
                   "Der Lauf holt alles nach; `--ohne-auswertung` genuegt, wenn",
                   "es nur um den Block geht und nichts kosten soll."]
    notiz(zeilen)
    return 0 if frisch else 1


if __name__ == "__main__":
    sys.exit(main())
