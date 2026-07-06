# Changelog

## 0.3.0

- Zjednodušení integrace jen na hlavní entity:
  - prší,
  - déšť se blíží,
  - odhad deště v minutách,
  - poslední aktualizace.
- Přidán odhad pohybu srážek přes OpenCV Farnebäck optical flow.
- Přidána vlastní ikona deštivého mraku do repozitáře.
- Doplňkové diagnostické údaje přesunuty do atributů entit.

## 0.2.0

- Přidán jednoduchý odhad pohybu srážek ze dvou PNG snímků.
- Přidány forecast entity pro 15/30/60 minut.

## 0.1.0

- První testovací verze.
- Stažení posledního radarového PNG z ČHMÚ OpenData.
- Vyhodnocení deště v místě a okolí.


## 0.3.1

- Opraveno načítání config flow: OpenCV se importuje až při spuštění integrace, ne při otevření nastavení.
- Odstraněny soubory `__pycache__` z repozitáře.
