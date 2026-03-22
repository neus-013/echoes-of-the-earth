# DISSENY VISUAL — Echoes of the Earth

Guia de tots els sprites i elements gràfics del joc. Consulta aquest fitxer per saber què cal crear, què ja està fet, i en quin ordre implementar-ho.

**Estil:** Pixel art 32-bit, estètica cozy/cuki, paleta càlida i natural amb tocs de fantasia.

---

## 1. Terreny (32×32 px per tile)

| Sprite sheet     | Frames            | Estat         | Notes                                                             |
| ---------------- | ----------------- | ------------- | ----------------------------------------------------------------- |
| Herba            | 1 variant         | ✅ Fet        | `assets/tiles/herba.png` — 16×16, 1 frame (escalat a 32×32)       |
| Terra            | 1 variant         | ✅ Fet        | `assets/tiles/terra.png` — 16×16, 1 frame (escalat a 32×32)       |
| Aigua            | 1 variant         | ✅ Fet        | `assets/tiles/aigua.png` — 1 frame carregat                       |
| Vora / bosc dens | 4 variants        | ❌ Procedural | Límit del mapa                                                    |
| Terra llaurada   | 1 (+ fosc regada) | ✅ Fet        | `assets/tiles/terra-llaurada.png` — 1 frame + enfosquiment regada |

---

## 2. Objectes del mapa (32×32 px)

| Sprite sheet    | Frames                       | Estat         | Notes                           |
| --------------- | ---------------------------- | ------------- | ------------------------------- |
| Arbre           | 5 (sencer + 3 danys + soca)  | ❌ Procedural | Cracks progressius al tallar    |
| Roca            | 5 (sencera + 3 danys + runa) | ❌ Procedural | Cracks progressius al picar     |
| Arbust de mores | 2 (amb fruit + buit)         | ❌ Procedural | Silvestre, recol·lectable       |
| Foguera         | 3-4 frames animació          | ❌ Procedural | Ara estàtica, idealment animada |
| Llit            | 1                            | ❌ Procedural | Pells i fusta primitives        |
| Cofre           | 1 (o 2: obert/tancat)        | ❌ Procedural | Emmagatzematge                  |

---

## 3. Cultius (32×32 px, 4 tipus × 4 etapes)

Cada cultiu té 4 etapes: llavor → brosta → creixent → madura.
A més, cada cultiu silvestre té 2 estats: ple + buit.

| Sprite sheet  | Frames                 | Estat         | Notes                   |
| ------------- | ---------------------- | ------------- | ----------------------- |
| Mora (cultiu) | 4 etapes + 2 silvestre | ❌ Procedural | Petites boles vermelles |
| Patata        | 4 etapes + 2 silvestre | ❌ Procedural | Tubercle soterrat       |
| Blat          | 4 etapes + 2 silvestre | ❌ Procedural | Tiges daurades          |
| Carbassa      | 4 etapes + 2 silvestre | ❌ Procedural | Fruit gros taronja      |

---

## 4. Personatges

### 4.1 Jugador (19×40 px per frame)

| Sprite sheet                | Frames | Estat           | Notes                                 |
| --------------------------- | ------ | --------------- | ------------------------------------- |
| Cos femení — caminar avall  | 4      | ❌ Pendent      |                                       |
| Cos femení — caminar amunt  | 4      | ❌ Pendent      |                                       |
| Cos femení — caminar dreta  | 4      | ❌ Pendent      | Esquerra = flip horitzontal           |
| Cos masculí — caminar avall | 4      | ✅ Fet (actual) | `assets/player/player_walk_down.png`  |
| Cos masculí — caminar amunt | 4      | ✅ Fet (actual) | `assets/player/player_walk_up.png`    |
| Cos masculí — caminar dreta | 4      | ✅ Fet (actual) | `assets/player/player_walk_right.png` |
| Cos neutre — caminar avall  | 4      | ❌ Pendent      |                                       |
| Cos neutre — caminar amunt  | 4      | ❌ Pendent      |                                       |
| Cos neutre — caminar dreta  | 4      | ❌ Pendent      | Esquerra = flip horitzontal           |

**Personalització per palette swap:**

- Pell: 4 paletes
- Cabell: 5 paletes
- Roba: 5 paletes
- Ulls: 4 paletes
- **Combinacions totals per cos:** 400

**Nota:** Caldrà adaptar el sistema de palette swap per a cada tipus de cos. El jugador tria cos + colors a la pantalla de creació d'avatar.

### 4.2 NPCs

| Sprite sheet                      | Frames     | Estat      | Notes                   |
| --------------------------------- | ---------- | ---------- | ----------------------- |
| NPC genèric 1 — caminar (4 dirs)  | 4 × 3 dirs | ❌ Pendent | Membre del clan, vilatà |
| NPC genèric 2 — caminar (4 dirs)  | 4 × 3 dirs | ❌ Pendent | Variació de vilatà      |
| NPC comerciant — caminar (4 dirs) | 4 × 3 dirs | ❌ Pendent | Clan extern, comerç     |
| NPC ancià/savi — caminar (4 dirs) | 4 × 3 dirs | ❌ Pendent | Guia, missions          |

**Nota:** Els NPCs no estan implementats al codi encara. Quan s'afegeixin, necessitaran sprites propis (no palette swap del jugador) per diferenciar-los visualment.

---

## 5. Icones d'objectes i eines (16×16 px)

| Sprite sheet | Frames                                  | Estat         | Notes           |
| ------------ | --------------------------------------- | ------------- | --------------- |
| Recursos     | 3 (fusta, pedra, mores)                 | ❌ Procedural | HUD i inventari |
| Collites     | 4 (mora, patata, blat, carbassa)        | ❌ Procedural |                 |
| Llavors      | 4 (una per cultiu)                      | ❌ Procedural |                 |
| Eines        | 3 (eina de pedra, aixada, bota d'aigua) | ❌ Procedural |                 |
| Cofre        | 1                                       | ❌ Procedural | Per l'inventari |

---

## 6. Pantalles i UI

| Element              | Mida    | Estat         | Notes                                     |
| -------------------- | ------- | ------------- | ----------------------------------------- |
| Il·lustració títol   | 640×360 | ❌ Procedural | Paisatge prehistòric de fons              |
| Elements HUD (atlas) | Variat  | ❌ Procedural | Slots, barra energia, marc selecció, etc. |

---

## Ordre d'implementació recomanat

| Prioritat | Grup                                    | Impacte visual                         |
| --------- | --------------------------------------- | -------------------------------------- |
| 🥇 1      | Herba + Aigua + Vora                    | Massiu — tot el mapa canvia d'un cop   |
| 🥈 2      | Arbre + Roca + Arbust                   | Alt — els objectes principals del mapa |
| 🥉 3      | Cultius (4×4 etapes + silvestres)       | Alt — completa el gameplay visual      |
| 4         | Foguera + Llit + Cofre                  | Mitjà — objectes menors del mapa       |
| 5         | Icones 16×16 (recursos, eines, llavors) | Mitjà — poleix l'inventari/HUD         |
| 6         | Cossos jugador (femení + neutre)        | Mitjà — opcions de personalització     |
| 7         | Il·lustració títol                      | Baix — només la pantalla inicial       |
| 8         | Elements HUD                            | Baix — polir la interfície             |
| 9         | NPCs                                    | Futur — quan s'implementin al codi     |

---

## Resum

| Categoria     | Sprites totals                            | Fets       |
| ------------- | ----------------------------------------- | ---------- |
| Terreny       | ~22 frames                                | 0          |
| Objectes mapa | ~16 frames                                | 0          |
| Cultius       | ~24 frames                                | 0          |
| Jugador       | ~36 frames (3 cossos × 3 dirs × 4 frames) | 12 (1 cos) |
| NPCs          | ~48 frames (4 NPCs × 3 dirs × 4 frames)   | 0          |
| Icones        | ~15 frames                                | 0          |
| Pantalles/UI  | ~10 elements                              | 0          |
| **TOTAL**     | **~171 frames**                           | **12**     |
