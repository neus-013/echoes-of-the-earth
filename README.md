# Albada 🌄

Joc de supervivència, granja i exploració ambientat en una prehistòria fantàstica. Desenvolupat en **Python + Pygame**, en **català**.

> **⚠️ Versió de prova (MVP)** — El joc està en desenvolupament actiu. Moltes mecàniques encara no estan implementades.

---

## Què hi ha implementat?

### Fase 0 — MVP base
- Mapa procedural 60×60 tiles (herba, aigua, arbres, roques, sorra)
- Jugador amb moviment en 4 direccions i animació de caminar
- Col·lisions amb el terreny
- Sistema de temps: cicle dia/nit amb 25 min per dia de joc
- HUD amb hora, dia, estació, eines i inventari
- Anar a dormir per avançar el dia

### Fase 1 — Agricultura i Artesania
- Llaurar terra, plantar llavors, regar cultius i collir
- Bota d'aigua amb capacitat limitada (reomplir al riu)
- Inventari amb llavors i productes recol·lectats
- Sistema d'artesania bàsic (receptes amb materials)
- Resum de fi de dia amb producció obtinguda

### Multijugador (LAN)
- Creació i unió a partides per codi de 5 caràcters
- Fins a 4 jugadors simultanis a la mateixa xarxa local (WiFi/LAN)
- Descobriment automàtic del host via UDP
- Personalització d'avatar (colors de pell, cabell, roba, ulls)
- Perfil local per usuari (les partides guardades són separades per cada ordinador)
- Sincronització del son i resum de dia entre jugadors
- Guardar i carregar partides multijugador

---

## Requisits

- **Python 3.10+**
- **Pygame 2.5+**

---

## Instal·lació i execució

### 1. Clonar el repositori

```bash
git clone https://github.com/neus-013/albada.git
cd albada
```

### 2. Crear entorn virtual i instal·lar dependències

```bash
python -m venv .venv

# Windows
.venv\Scripts\activate

# Linux / macOS
source .venv/bin/activate

pip install -r requirements.txt
```

### 3. Executar el joc

```bash
python -m src.main
```

---

## Multijugador

El multijugador funciona entre dispositius connectats a la **mateixa xarxa local** (WiFi o LAN). No cal configurar res manualment:

1. Un jugador crea una partida i obté un codi de 5 caràcters.
2. L'altre jugador selecciona "Unir-se" i introdueix el codi.
3. El host descobreix automàticament la connexió via la xarxa local.

> **Nota:** Cada ordinador ha de tenir el joc instal·lat i executant-se. El port TCP 7777 i UDP 7778 han d'estar accessibles a la xarxa local (pot caldre permetre'ls al firewall).

---

## Estructura del projecte

```
albada/
├── assets/          # Sprites i recursos gràfics
├── data/
│   └── i18n/        # Fitxers de traducció (ca.json)
├── src/
│   ├── screens/     # Pantalles del joc (títol, lobby, joc, resum...)
│   ├── systems/     # Sistemes (agricultura, inventari, eines, temps, perfil...)
│   ├── game.py      # Classe principal del joc
│   ├── network.py   # Networking TCP/UDP per multijugador
│   ├── player.py    # Lògica del jugador
│   ├── sprites.py   # Generació de sprites del jugador
│   ├── world.py     # Generació i gestió del mapa
│   ├── ui.py        # Interfície d'usuari (HUD, botons, text)
│   └── settings.py  # Constants i configuració
├── requirements.txt
├── run.py
└── README.md
```

---

## Llicència

Projecte privat — tots els drets reservats.
