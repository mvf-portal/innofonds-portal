# -*- coding: utf-8 -*-
"""Einmalige Diagnose: Was bekommt der GitHub-Runner wirklich?

Peter Stegmaier am 06.10.2026: "die 0 einträge klärem"

Die Wache meldet "Eintraege im Block: 0", obwohl die ausgelieferte
Datei 14 Ergebnisse enthaelt. Gemessen vom Arbeitsplatz aus - mit
demselben Cache-Buster und demselben User-Agent - kommen 14. Nur der
Runner sieht null.

Diese Datei raet nicht, sondern schreibt auf, was ankommt: Status,
Kopfzeilen, Byte-Laenge, die ersten Zeichen und die Typen der Felder.
Danach wird sie wieder entfernt; sie gehoert nicht in den Dauerbetrieb.
"""
import json
import urllib.request
from datetime import datetime, timezone

ADRESSE = "https://innofonds.m-vf.de/newsletter.json"


def hole(adresse: str, kopf: dict) -> None:
    print(f"\n=== {adresse}")
    print(f"    Kopfzeilen der Anfrage: {kopf}")
    bitte = urllib.request.Request(adresse, headers=kopf)
    try:
        with urllib.request.urlopen(bitte, timeout=30) as a:
            roh = a.read()
            print(f"    Status: {a.status}")
            for k in ("Content-Type", "Content-Length", "Content-Encoding",
                      "cf-cache-status", "age", "last-modified", "etag",
                      "x-served-by", "server"):
                w = a.headers.get(k)
                if w:
                    print(f"    {k}: {w}")
    except Exception as e:                                   # noqa: BLE001
        print(f"    FEHLER: {type(e).__name__}: {e}")
        return

    print(f"    Bytes empfangen: {len(roh)}")
    print(f"    erste 16 Bytes : {roh[:16]!r}")
    try:
        text = roh.decode("utf-8")
    except UnicodeDecodeError as e:
        print(f"    decode('utf-8') scheitert: {e}")
        return
    print(f"    Zeichen        : {len(text)}")
    try:
        d = json.loads(text)
    except Exception as e:                                   # noqa: BLE001
        print(f"    json.loads scheitert: {e}")
        print(f"    Anfang: {text[:200]!r}")
        return

    print(f"    Schlüssel      : {list(d.keys())}")
    print(f"    stand          : {d.get('stand')!r}")
    for feld in ("ergebnisse", "wartet"):
        w = d.get(feld)
        print(f"    {feld:<14} : Typ {type(w).__name__}, "
              f"len={len(w) if hasattr(w, '__len__') else '–'}")
        if isinstance(w, list) and w:
            print(f"                     erstes: "
                  f"{json.dumps(w[0], ensure_ascii=False)[:120]}")


def main() -> int:
    marke = datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S")
    # 1. Genau wie die Wache
    hole(ADRESSE + "?wache=" + marke[:12],
         {"Cache-Control": "no-cache",
          "User-Agent": "innofonds-wache/1.0 "
                        "(+https://innofonds.m-vf.de)"})
    # 2. Ohne Cache-Buster
    hole(ADRESSE,
         {"Cache-Control": "no-cache",
          "User-Agent": "innofonds-wache/1.0 "
                        "(+https://innofonds.m-vf.de)"})
    # 3. Mit Browserkennung - Cloudflare behandelt nackte Klienten
    #    anders, das ist hier schon einmal aufgefallen (error 1010).
    hole(ADRESSE + "?diag=" + marke,
         {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                        "AppleWebKit/537.36 (KHTML, like Gecko) "
                        "Chrome/140.0 Safari/537.36",
          "Accept": "application/json,text/plain,*/*"})
    # 4. Direkt von GitHub Pages, ohne Cloudflare davor
    hole("https://mvf-portal.github.io/innofonds-portal/newsletter.json",
         {"User-Agent": "innofonds-wache/1.0"})
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
