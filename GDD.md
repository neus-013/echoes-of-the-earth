# DOCUMENT DE DISSENY DEL JOC (GDD)

### Versió 1.1 — 14 de Març de 2026

---

## 1. VISIÓ GENERAL

### 1.1 Concepte

Un joc de supervivència, exploració i construcció de civilització ambientat en una prehistòria fantàstica.
El jugador es perd explorant la natura i ha de sobreviure, crear un clan, fer aliances amb altres clans i evolucionar a través de quatre èpoques històriques, des de la supervivència primitiva fins a una civilització avançada amb elements de fantasia, energies místiques i criatures fantàstiques.

### 1.2 Ganxo (Pitch)

> "Et perds explorant la natura. Sol/a, sense res. Sobreviu, explora, cultiva, crea el teu clan i evoluciona la teva civilització a través de les èpoques... però no pateixis, sempre podràs comptar amb l'ajuda de forces espirituals!"

### 1.3 Gènere

Simulació de vida / Granja / Exploració / Construcció de civilització

### 1.4 Inspiracions principals

- **Roots of Pacha** (estètica, ambientació prehistòrica, progressió tribal)
- **Stardew Valley** (mecàniques de granja, relacions, estacions)
- **Civilization** (evolució per èpoques, arbre de tecnologia)
- Elements originals: energies fantàstiques, criatures místiques, sistema de clans

### 1.5 Estil Visual

- **Pixel art 32-bit**, estètica cuki i cozy
- Paleta de colors càlida i natural amb tocs de fantasia (brillantors, partícules d'energia)
- Inspirat visualment en Roots of Pacha
- Molt personalitzable (avatar, construccions, pintura, decoració)

### 1.6 Plataforma

- Windows (PC) — potencialment Steam
- Multijugador des del disseny base

### 1.7 Idioma inicial

- **Català** (primer idioma, amb sistema d'i18n preparat per a més idiomes)

---

## 2. MECÀNIQUES PRINCIPALS

### 2.1 Core Loop

```
EXPLORAR → RECOL·LECTAR → CULTIVAR → MILLORAR → INTERCANVIAR → REPETIR
```

Totes les activitats es desbloquegen progressivament mitjançant l'exploració i la interacció:

| Activitat              | Com es desbloqueja                                   |
| ---------------------- | ---------------------------------------------------- |
| Recol·lecció           | Disponible des de l'inici                            |
| Artesania bàsica       | Després de recol·lectar certs materials              |
| Agricultura            | Després de trobar llavors i aprendre a cultivar      |
| Domesticació/Ramaderia | Després de domesticar el primer animal salvatge      |
| Pesca                  | Després de crear eines de pesca o una zona d'aigua   |
| Mineria                | Després de crear eines i trobar l'entrada d'una cova |
| Cuina                  | Després de descobrir el foc / construir un fogó      |
| Construcció            | Després d'establir un campament base                 |
| Comerç                 | Després de contactar amb el primer clan extern       |

### 2.2 Sistema de Temps

| Element                      | Valor                                                   |
| ---------------------------- | ------------------------------------------------------- |
| Durada d'un dia (real)       | 25 minuts (més llarg que Stardew ~13min / Roots ~18min) |
| Dies per estació             | 30                                                      |
| Estacions per any            | 4 (Primavera, Estiu, Tardor, Hivern)                    |
| Durada total d'un any (real) | ~50 hores de joc                                        |

#### Cicle del dia:

- **Matinada** (06:00-08:00): Ambient de rosada, poca visibilitat, criatures nocturnes marxen
- **Matí** (08:00-12:00): Llum plena, ombres direcció oest als elements
- **Migdia** (12:00-14:00): Migdia, llum una mica més càlida, sombra circular inferior als elements
- **Tarda** (14:00-19:00): Llum daurada, ombres direcció est als elements
- **Vespre** (19:00-21:00): Ambient taronja, es comença a fer fosc
- **Nit** (21:00-02:00): Fosc, els NPCs tornen a casa i van a dormir

#### Fi del dia (Dormir):

El jugador **ha de dormir** per acabar el dia (al llit del campament/casa). En dormir:

1. **Pantalla de resum del dia**: PG guanyats, activitats realitzades, objectes recol·lectats
2. **Resum de vendes** (si n'ha fet): objectes venuts, monedes/objectes obtinguts
3. **Acumulats**: PG totals, monedes totals (si s'ha desbloquejat la moneda)
4. **Guardat automàtic** de la partida
5. El dia següent comença a les 06:00

### 2.3 Activitats Detallades

#### Agricultura (5 cultius per estació = 20 totals)

- Preparar terra, plantar llavors, regar, collir, millorar terra (fems -> fertilitzants)
- Cada cultiu té un temps de creixement diferent, alguns es mantenen després de recolectar
- Qualitat dels cultius (Normal → Bona → Excel·lent → Mística)
- Evoluciona amb l'època (eines manuals → eines millorades → sistemes de reg i recollida)

#### Pesca (5 peixos per estació = 20 totals)

- Diferents zones de pesca (riu, llac, mar, aigües subterrànies)
- Mini-joc de pesca
- Peixos rars i llegendaris per estació
- Qualitat dels peixos (Normal → Bona → Excel·lent → Mística)
- Evoluciona amb l'època (eines manuals → eines millorades → sistemes de pesca i cria)

#### Ramaderia (1-3 animals per zona del mapa)

- Domesticació d'animals salvatges (mini-joc/procés de confiança)
- Productes animals (llet, ous, llana, altres pelatjes, mel, plomes, tòfones)
- Animals de companyia (no productius, però donen felicitat)
- Animals fantàstics en zones especials

#### Caça

- Trampes de caça per obtenir carn (similar a Roots of Pacha)
- Les trampes es col·loquen al mapa i es recullen al dia següent
- No es maten animals domesticats — la carn s'obté únicament per trampes de caça
- Evoluciona amb l'època (trampes bàsiques → trampes millorades)

#### Mineria

- **Una cova per bioma** (7 coves totals, com a Roots of Pacha)
- Cada cova té un mapa d'habitacions interconnectades
- Minerals, gemmes, cristalls d'energia específics de cada bioma
- Enemies (criatures d'energia fosca) a certes habitacions — combat en temps real senzill (estil Stardew)
- Eliminar criatures dona recursos (minerals, gemmes, objectes rars)
- **Totem del Guardià** a cada cova: oferir objectes específics per desbloquejar un mini-joc
- Al completar el mini-joc, el jugador **adopta la forma del guardià** temporalment
- Amb la forma del guardià, es pot accedir a zones ocultes de la cova
- Les 7 energies són essencials per completar el joc

#### Cuina

- Receptes que es descobreixen experimentant o per NPCs
- Plats donen **energia i vida** (la font principal de recuperació)
- Qualitat dels plats (Normal → Bona → Excel·lent → Mística)
- Valor superior als productes que s'utilitzen, els productes més top per intercanvi o venta
- No es combina amb alquímia — són sistemes separats

#### Alquímia

- **Infusions**: begudes amb efectes temporals (velocitat, sort, visió nocturna...)
- **Unguents de sanació**: curen vida de forma ràpida
- **Pocions d'habilitats**: buffs temporals per a activitats específiques (+pesca, +mineria, +agricultura...)
- Qualitat (Normal → Bona → Excel·lent → Mística)
- Ingredients: herbes, flors, extractes, essències naturals, cristalls d'energia
- Receptes es descobreixen experimentant o per NPCs/Guardians

#### Construcció

- Cases, magatzems, estables, tanques, camins, decoració, edificis
- Tot personalitzable amb pintura i estils
- El temple central (creix amb la progressió)

#### Vehicles

Els vehicles es desbloquegen per època i permeten transport i comerç:

| Vehicle       | Època                 | Ús                                       |
| ------------- | --------------------- | ---------------------------------------- |
| **Carro**     | Primera Civilització  | Comerç entre ciutats/clans               |
| **Baixell**   | Primera Civilització  | Accés a l'Illa Tropical                  |
| **Bicicleta** | Primera Civilització  | Transport personal ràpid                 |
| **Furgoneta** | Civilització Avançada | Comerç entre ciutats (més capacitat)     |
| **Tren**      | Civilització Avançada | Transport ràpid entre biomes (estacions) |
| **Moto**      | Civilització Avançada | Transport personal molt ràpid            |

#### Lluita

- Combat **senzill en temps real** (estil Stardew Valley)
- Només dins de les **habitacions de les coves**
- Armes cos a cos (1v1): bastons, llances, espases... evolucionen per època
- El jugador **només es desmaia** (mai mort) — apareix al llit amb vida mínima
- Les criatures d'energia fosca **no són un enemic final** — són obstacles recurrents
- Eliminar-les dona **recursos** (minerals, gemmes, objectes rars)

### 2.4 Energia i Stamina

- El jugador té una barra d'energia que es gasta amb accions
- Al acabar-se l'energia el jugador no pot fer més accions i disminueix la velocitat
- Es recupera menjant, dormint, o amb fonts d'energia mística
- A mesura que progressa, la barra creix
- El jugador també té una barra de vida que es gasta amb combat o intoxicació
- Al acabar-se la vida el jugador apareix al llit desmaiat, amb vida mínima
- La vida es recupera menjant, amb fonts d'energia o poc a poc automàticament
- A mesura que progressa, la barra de vida creix

---

## 3. PROGRESSIÓ I ECONOMIA

### 3.1 Les 4 Èpoques

| Època | Nom                       | Descripció                                                                                      | Punts Globals Necessaris |
| ----- | ------------------------- | ----------------------------------------------------------------------------------------------- | ------------------------ |
| 1     | **Supervivència**         | Sol/a, recol·lectar, primers refugis, descobrir el foc                                          | 0 - 3.000                |
| 2     | **Tribu**                 | Primeres amistats, formació del clan, agricultura bàsica                                        | 3.000 - 8.000            |
| 3     | **Comunitat**             | Aliances amb clans, comerç, construcció estructurada                                            | 8.000 - 15.000           |
| 4     | **Primera Civilització**  | Primera civilització (inspiració medieval), edificis estructurats, primers vehicles sense motor | 15.000 - 25.000          |
| 5     | **Civilització Avançada** | Civilització moderna cozy, edificis contemporanis, vehicles amb motor, tecnologia avançada      | 25.000+                  |

### 3.2 Sistema de Punts Globals (PG)

Tot suma Punts Globals, que són la mesura de progrés del joc:

| Acció                         | PG guanyats (aproximat) |
| ----------------------------- | ----------------------- |
| Pujar nivell d'activitat      | +50                     |
| Completar una missió          | +25-100                 |
| Domesticar un animal          | +30                     |
| Descobrir una nova zona       | +75                     |
| Fer amistat (nou nivell)      | +30                     |
| Vendre/Intercanviar           | +15                     |
| Millorar una eina             | +25                     |
| Cuinar una recepta nova       | +15                     |
| Construir una estructura nova | +50-150                 |
| Millorar una energia          | +100                    |

### 3.3 Nivells d'Habilitat

Cada camp té nivells (1-10) que es pugen practicant:

- **Agricultura** → Millors collites, millors llavors, eines millorades
- **Ramaderia** → Animals més feliços, millors productes, domesticació més fàcil, reproducció
- **Pesca** → Peixos rars, millor mini-joc, noves zones
- **Mineria** → Desbloqueig d'habitacions, minerals rars, lluita, pedres precioses
- **Cuina** → Receptes avançades, millor qualitat, més poders
- **Alquimia** → Elaboració de pocions i remeis medicinals, millora d'aquests
- **Artesania** → Objectes de millor qualitat, nous dissenys, més valor
- **Construcció** → Estructures més grans, nous materials, modernització
- **Social** → Millors diàlegs, regals més efectius, comerç avantatjós
- **Exploració** → Mapa revelat, troballes rares
- **Lluita** → Millora atac i eines de lluita (contra les criatures d'energia focsa)
- **Energia Mística** → Desbloqueig i millora de l'energia de la naturalesa (ajuda en agricultura, ramaderia, pesca, mineria, social, alquimia, lluita)

### 3.4 Economia Evolutiva

| Fase   | Sistema econòmic                                        | Desbloqueig                     |
| ------ | ------------------------------------------------------- | ------------------------------- |
| Fase 0 | **Res** — Autosuficiència total                         | Inici del joc                   |
| Fase 1 | **Trueque** — Intercanvi directe d'objectes             | Primer contacte amb clan extern |
| Fase 2 | **Moneda primitiva** — Petxines                         | Aliança estable amb 1+ clan     |
| Fase 3 | **Cistell de contribucions** — Fons comunitari del clan | Formació de comunitat           |
| Fase 4 | **Moneda avançada** — Encunyació pròpia                 | Civilització avançada           |

### 3.5 Arbre de Tecnologia

- Es desbloqueja amb Punts Globals
- Organitzat en branques: Agricultura, Ramaderia, Pesca, Mineria, Exploració, Construcció, Social, Energia, Artesania, Cuina, Alquimia, Lluita
- Cada desbloqueix afegeix o millora una part del **Temple Central**
- El Temple és el símbol visual del progrés del jugador
- Comença sense existir → Fonaments → Estructura bàsica → Temple decorat → Temple resplendent

### 3.6 Missions

- **Missions principals**: Guien la història (obligatòries per avançar d'època)
- **Missions secundàries**: Opcionals, donen PG + recompenses
- **Missions de clan**: Col·laboratives (dissenyades per multijugador)

---

## 4. MÓN I MAPA

### 4.1 Estructura del Mapa (Fix)

El mapa és fix però les zones es desbloquegen progressivament.

```
                    ┌─────────────┐
                    │  MUNTANYA   │
                    │  (Neu/Fred) │
                    └──────┬──────┘
                           │
        ┌──────────┐  ┌────┴─────┐   ┌──────────┐
        │  DESERT  ├──┤  BOSC    ├───┤  SELVA   │
        │          │  │ (INICI)  │   │ Tropical │
        └─────┬────┘  └────┬─────┘   └────┬─────┘
              │            │              │
              │     ┌──────┴──────┐  ┌────┴─────┐
              └─────│   SAVANA    ├──┤  PLATJA  │
                    │             │  │          │
                    └─────────────┘  └────┬─────┘
                                          │
                                    ┌─────┴─────┐
                                    │   ILLA    │
                                    │ TROPICAL  │
                                    └───────────┘
```

### 4.2 Zones del Mapa

| Zona               | Bioma                        | Animals (1-3)                        | Recursos clau                    | Desbloqueig            |
| ------------------ | ---------------------------- | ------------------------------------ | -------------------------------- | ---------------------- |
| **Bosc**           | Temperat, arbres caducifolis | Llop, Cérvol, Conills                | Fusta, baies, herbes             | Inici                  |
| **Selva Tropical** | Humit, vegetació densa       | Tigre, Mico, Serp, Papallona mística | Fruites exòtiques, lianes, flors | Exploració bàsica      |
| **Savana**         | Sec, herba alta              | Bisó, Estruç, Lleó, Mamut            | Herba, argila, plantes           | Travessar el bosc      |
| **Platja**         | Costa, sorra, roques         | Cranc                                | Petxines, coco                   | Arribar als límits est |
| **Illa Tropical**  | Paradís, palmeres            | Tortuga, Lloro                       | Coco, perles, corall             | Construir una barca    |
| **Muntanya**       | Fred, neu, coves             | Cabra muntanyesa, Marta              | Minerals, cristalls, gel         | Escalar ruta nord      |
| **Desert**         | Àrid, dunes, oasis           | Escorpí, Fènec, Dromedari            | Cactus, figa de moro, fòssils    | Creuar pas oest        |

### 4.3 Coves i Guardians (1 per bioma)

Cada bioma té una cova amb un Guardià vinculat a la seva energia (sistema similar a Roots of Pacha):

| Bioma             | Guardià           | Energia          | Poder del Guardià                  |
| ----------------- | ----------------- | ---------------- | ---------------------------------- |
| **Bosc**          | Esperit del Bosc  | Flora (Verda)    | Travessar arrels i vegetació densa |
| **Selva**         | Papallona Gegant  | Essència (Rosa)  | Volar per zones elevades           |
| **Savana**        | Gran Mamut        | Fauna (Taronja)  | Trencar murs de roca               |
| **Platja**        | Sirena de Corall  | Aigua (Blava)    | Nedar per zones inundades          |
| **Illa Tropical** | Tortuga Ancestral | Sol (Groga)      | Resistir zones de llum intensa     |
| **Muntanya**      | Serp de Gel       | Foc (Vermella)   | Travessar zones de lava/foc        |
| **Desert**        | Fènix de Sorra    | Antiga (Violeta) | Travessar zones de sorra movedissa |

**Mecànica de desbloqueig:**

1. Trobar el **Totem del Guardià** dins la cova
2. Oferir objectes específics al totem (ofrenes)
3. Completar un **mini-joc** de connexió amb el guardià
4. **Adoptar la forma del guardià** temporalment per accedir a zones ocultes
5. Les 7 energies són **essencials** per completar el joc

### 4.4 Criatures Fantàstiques (Ambient)

- **Orbes Lluminosos**: Petites criatures d'energia que apareixen de nit (totes les zones)
- **Criatures d'energia fosca**: Enemies a les habitacions de les coves (donen recursos en ser eliminades)

### 4.5 Mida del Mapa

| Concepte                    | Petit       | Manejable (RECOMANAT) | Gran          |
| --------------------------- | ----------- | --------------------- | ------------- |
| Zona de granja              | 20x20 tiles | **40x40 tiles**       | 80x80 tiles   |
| Zona explorable (per bioma) | 30x30 tiles | **60x60 tiles**       | 120x120 tiles |
| Tiles totals (aprox.)       | ~6.300      | ~25.200               | ~100.800      |
| Temps per recórrer tot      | ~15 min     | **~45-60 min**        | ~3+ hores     |

**Recomanació: Manejable (40x40 granja, 60x60 per zona)**
Prou gran per explorar amb gust, prou petit per no perdre's constantment.

---

## 5. PERSONATGES I RELACIONS

### 5.1 El Jugador

- Avatar completament personalitzable:
  - Cos: pell, alçada, forma corporal
  - Cara: ulls, nas, boca, marques facials, tatuatges tribals, barba
  - Cabell: estil, color
  - Roba: pintable, tenyible, combinable
  - Accessoris: collars, braçalets, pintura corporal
- Personalització evolutiva (nous estils amb cada època)

### 5.2 Estructura de Clans

| Clan                 | Ubicació         | Especialitat          | NPCs                    |
| -------------------- | ---------------- | --------------------- | ----------------------- |
| **Clan del jugador** | Bosc (base)      | Creix amb el jugador  | 0→8 membres reclutables |
| **Clan del Riu**     | Vora de la selva | Pesca i herbes        | 4-5 membres             |
| **Clan de la Pedra** | Muntanya         | Mineria i construcció | 4-5 membres             |
| **Clan del Sol**     | Platja           | Navegació i comerç    | 4-5 membres             |
| **Clan de l'Arena**  | Desert           | Energia mística       | 4-5 membres             |

**Total NPCs aproximat: 25-30** (manejable, cada un amb personalitat pròpia)

### 5.3 Sistema de Relacions

```
Desconegut → Conegut → Amic → Amic Íntim → [Parella → Matrimoni → Fills]
   (0)        (1)      (2-4)    (5-7)        (8)       (9)       (10)
```

- **Nivells d'amistat**: 0-10 (pujable amb regals, converses, missions conjuntes)
- **Parella**: Disponible amb NPCs marcats com "romançables" (8-10 per joc) i amb altres jugadors (mode multijugador)
- **Matrimoni**: Cerimònia tribal, l'NPC es muda al teu clan o els jugadors escullen casa on murar-se (multijugador)
- **Fills**: Un temps després del matrimoni, si es té cuna, poden apareixer fills que creixen (NPCs decoratius, ajuden al clan)
- **Separació**: Possible si la relació baixa de nivell (amb conseqüències narratives)

### 5.4 NPCs Reclutables (Clan del Jugador)

El jugador pot convèncer fins a 8 NPCs per unir-se al seu clan:

- Cada un té una especialitat (granger, pescador, miner, cuiner, constructor, místic...)
- Ajuden automàticament en tasques (especialment útil en multijugador)
- Tenen rutines diàries pròpies

### 5.5 Evolució Visual dels NPCs

- Els NPCs (i jugadors) **evolucionen visualment** amb cada època (roba, accessoris, estil)
- Són **sempre els mateixos personatges** — no apareixen NPCs nous per època
- Els clans **no creixen** més enllà de la seva mida inicial
- L'evolució visual reflecteix el progrés de la civilització (tribal → primera civilització → civilització avançada)

---

## 6. ELEMENTS DE FANTASIA

### 6.1 Energies Místiques

- **Energia Flora (Verda)**: Creixement, agricultura, plantes (Bosc)
- **Energia Fauna (Taronja)**: Domesticació, productes, animals (Savana)
- **Energia Aigua (Blava)**: Aigua, pesca, calma (Platja)
- **Energia Foc (Vermella)**: Foc, forja, força (Muntanya)
- **Energia Sol (Groga)**: Sol, vida, felicitat, social (Illa tropical)
- **Energia Antiga (Violeta)**: Misteri, coneixement ancestral (Desert)
- **Energia Essència (Rosa)**: Essències naturals, extractes, alquimia (Selva)

### 6.2 Guardians i Coves

- Cada energia té un **Guardià** que habita la cova del seu bioma
- Els Guardians són **servents o encarnacions** de les seves energies
- Es troben explorant i interactuant amb tot el que el mapa ofereix
- Oferir objectes al **Totem** de cada cova desbloqueja un mini-joc
- Completar el mini-joc permet **adoptar la forma del Guardià**
- La forma del Guardià dona un poder especial per accedir a zones ocultes de la cova
- A mesura que cada energia està de la nostra part, ajuda amb el seu tipus d'activitat
- Les **7 energies són essencials** per completar el joc
- Necessàries per avançar en l'arbre de tecnologia (branques avançades)

---

## 7. PERSONALITZACIÓ I ESTÈTICA

### 7.1 Personalització de l'Avatar

- Editor d'avatar complet a l'inici + editor del avatar a la configuració de la partida
- Roba pintable amb sistema de colors (tenyir amb pigments naturals)
- Pintura corporal i facial (tribal, evoluciona per època)
- Accessoris i roba craftejables

### 7.2 Personalització de Construccions

- Totes les estructures pintables (parets, terra, sostre)
- Múltiples estils de mobles per època
- Sistema de decoració interior i exterior
- Camins, tanques, jardins decoratius personalitzables

### 7.3 Sistema de Pintura

- Pigments obtinguts de recursos naturals (flors, minerals, baies)
- Paleta de colors que creix a mesura que es descobreixen nous pigments
- Aplicable a: roba, construccions, mobles, tanques, camins
- Patrons i dissenys desbloquejables

---

## 8. MULTIJUGADOR

### 8.1 Filosofia

> El joc es dissenya primer per a multijugador, després s'adapta per a un sol jugador.

### 8.2 Característiques Multi

- **Co-op**: 2-4 jugadors en el mateix món
- **Clan compartit**: Tots els jugadors formen part del mateix clan
- **Tasques col·laboratives**: Algunes missions requereixen cooperació
- **Construcció conjunta**: Qualsevol jugador pot construir/decorar
- **Economia compartida**: Cistell de contribucions comú
- **Independents**: Cada jugador pot explorar zones diferents simultàniament, cinturó (barra ràpida d'eines) i inventari separats per jugador

### 8.3 Adaptació Single Player

- Més NPCs reclutables compensen la falta de jugadors humans
- Missions col·laboratives es poden fer amb NPCs del clan
- El temps de joc no depèn d'altres jugadors

### 8.4 Arquitectura Tècnica (Networking)

- Client-servidor (un jugador és host o servidor dedicat)
- Sincronització d'estat del món
- Interpolació de moviment
- Sistema de lobby per connectar partides

---

## 9. EVENTS I FESTIVALS

### 9.1 Events per Estació (1 per estació = 4 per any)

| Estació       | Event                     | Descripció                                                                    |
| ------------- | ------------------------- | ----------------------------------------------------------------------------- |
| **Primavera** | **Festival de les flors** | Competició de pintar ous, celebració del renaixament de la natura i les flors |
| **Estiu**     | **Nit de les Llums**      | Foguera a la platja, alliberació de fanalets, bany revitilitzador al mar      |
| **Tardor**    | **Vetlla als esperits**   | Foguera central on l'anciana explica històries, apareixen esperits amistosos  |
| **Hivern**    | **Solstici d'Hivern**     | Cerimònia al temple, regals entre NPCs, neu màgica, cristalls especials       |

### 9.2 Events Únics (Per Època)

- Cada canvi d'època té un event narratiu especial
- Transformació visible del món i del temple

---

## 10. CONTINGUT QUANTIFICAT

### 10.1 Resum Numèric

| Element                | Quantitat                            |
| ---------------------- | ------------------------------------ |
| Zones del mapa         | 7 biomes                             |
| Èpoques                | 5                                    |
| Estacions              | 4 (Primavera, Estiu, Tardor, Hivern) |
| Dies per estació       | 30                                   |
| Durada d'un dia (real) | ~25 min                              |
| Cultius                | 20 (5 per estació)                   |
| Peixos                 | 20 (5 per estació)                   |
| Animals domesticables  | 7-21 (1-3 per zona)                  |
| NPCs totals            | ~25-30                               |
| NPCs romançables       | ~8-10                                |
| Clans externs          | 4                                    |
| Coves                  | 7 (1 per bioma)                      |
| Guardians              | 7 (1 per cova/energia)               |
| Vehicles               | 6 (3 per època 4 + 3 per època 5)    |
| Events/Festivals       | 4 per any + 5 d'època                |
| Habilitats del jugador | 12 camps                             |
| Nivells per habilitat  | 10                                   |
| Receptes de cuina      | ~40-60                               |
| Objectes artesanals    | ~50-80                               |
| Missions principals    | ~20-30                               |
| Missions secundàries   | ~50-80                               |
| Arbres de tecnologia   | 12 branques                          |

---

## 11. PROPOSTA DE NOM

### Opcions:

| Nom                  | Significat                 | Per què funciona                                                       |
| -------------------- | -------------------------- | ---------------------------------------------------------------------- |
| **Albada**           | "Alba" en català poètic    | Evoca el començament, la primera llum, el naixement d'una civilització |
| **Arrels del Temps** | Roots of Time              | Joc de paraules amb Roots of Pacha, connecta amb l'evolució temporal   |
| **Llar Salvatge**    | Wild Home                  | El viatge de convertir la natura salvatge en llar                      |
| **Senderi**          | Derivat de "sender" (camí) | El camí del jugador, l'exploració, el viatge                           |
| **Despertar**        | Awakening                  | El despertar de la civilització i de les energies                      |
| **Orígens**          | Origins                    | Directe, evoca la prehistòria i el començament                         |

**Recomanació personal: "Albada"** — és curt, sonor, únic, en català, i captura perfectament
l'essència del joc (el començament d'una civilització, la primera llum, el despertar).

---

## 12. RUTA DE DESENVOLUPAMENT

### Fase 0 — PROTOTIP MÍNIM (MVP Hiper-Simple)

**Objectiu**: Un personatge es mou per un mapa, pot recollir coses i dormir.

- [ ] Finestra del joc amb Pygame
- [ ] Mapa d'una sola zona (Bosc, 20x20 tiles)
- [ ] Personatge amb moviment (8 direccions)
- [ ] Cicle dia/nit bàsic (visual)
- [ ] 3 objectes recol·lectables (fusta, pedra, baies)
- [ ] Inventari bàsic (10 slots)
- [ ] Sistema de temps (rellotge del dia)
- [ ] Poder dormir per avançar al dia següent
- [ ] Pantalla de resum del dia (PG guanyats, activitats, vendes, acumulats)
- [ ] Guardat automàtic en dormir
- [ ] Barra d'energia bàsica
- [ ] Interfície mínima (inventari, hora, energia)
- [ ] Sistema d'i18n bàsic (textos en fitxer extern, català)
- [ ] Arquitectura client-servidor bàsica (local)

**Resultat**: Pots caminar pel bosc, recollir coses, passa el temps, pots dormir.
**Temps estimat**: Primera fita jugable.

---

### Fase 1 — AGRICULTURA I ARTESANIA

**Objectiu**: El jugador pot plantar, cuidar i collir.

- [ ] Sistema de tiles editables (terra cultivable)
- [ ] Eines bàsiques (aixada, regadora)
- [ ] 5 cultius de primavera (plantar, créixer, collir)
- [ ] Artesania bàsica (3-5 receptes)
- [ ] Chest/Cofre per emmagatzemar
- [ ] Qualitat dels cultius (bàsic)
- [ ] Animacions de plantar/regar/collir
- [ ] Sistema de guardat (save/load)

---

### Fase 2 — ESTACIONS I ECONOMIA

**Objectiu**: El temps avança, les estacions canvien, es pot comerciar.

- [ ] 4 estacions amb canvis visuals
- [ ] 5 cultius per estació (20 totals)
- [ ] Efectes de clima per estació
- [ ] Calendari visual
- [ ] Primer NPC (comerciant bàsic)
- [ ] Sistema de trueque bàsic
- [ ] Menu de pausa i configuració

---

### Fase 3 — EXPLORACIÓ I MAPA

**Objectiu**: Món més gran amb múltiples zones.

- [ ] Transicions entre zones
- [ ] 3-4 zones del mapa (Bosc, Selva, Savana, Platja)
- [ ] Cada zona amb recursos únics
- [ ] Fog of war / zones per descobrir
- [ ] Mini-mapa
- [ ] Criatures fantàstiques bàsiques (orbes lluminosos)

---

### Fase 4 — NPCs I CLANS

**Objectiu**: Interacció social completa.

- [ ] 4 clans externs amb 4-5 NPCs cada un
- [ ] Diàlegs i sistema de conversa
- [ ] Sistema d'amistat (10 nivells)
- [ ] NPCs reclutables per al clan del jugador
- [ ] Rutines diàries dels NPCs
- [ ] Regals i preferències
- [ ] Missions principals bàsiques

---

### Fase 5 — PESCA, MINERIA I ANIMALS

**Objectiu**: Totes les activitats jugables.

- [ ] Mini-joc de pesca + 20 peixos
- [ ] Sistema de mines/coves (mapa d'habitacions, guardians, totems)
- [ ] Combat senzill temps real a les coves (armes cos a cos)
- [ ] Domesticació d'animals + productes
- [ ] Trampes de caça per obtenir carn
- [ ] Cuina (20+ receptes, donen energia i vida)
- [ ] Alquímia (infusions, unguents, pocions d'habilitats)
- [ ] Sistema de lluita (contra criatures d'energia fosca)
- [ ] Nivells d'habilitat funcionals (12 camps)

---

### Fase 6 — PROGRESSIÓ I TECNOLOGIA

**Objectiu**: L'arbre de tecnologia i les èpoques funcionen.

- [ ] Punts Globals complets
- [ ] Arbre de tecnologia visual i funcional
- [ ] 5 èpoques amb transicions
- [ ] Vehicles (carros, baixell, bicicleta per època 4 / furgoneta, tren, moto per època 5)
- [ ] Temple que creix
- [ ] Economia evolutiva completa (trueque → moneda)
- [ ] Missions principals completes

---

### Fase 7 — RELACIONS I EVENTS

**Objectiu**: Contingut social i festiu.

- [ ] Romances i matrimoni
- [ ] Fills
- [ ] Separació
- [ ] 4 festivals (1 per estació)
- [ ] Events d'època
- [ ] Missions secundàries

---

### Fase 8 — MULTIJUGADOR

**Objectiu**: Co-op funcional.

- [ ] Lobby i connexió entre jugadors
- [ ] Sincronització del món
- [ ] Tasques col·laboratives
- [ ] Test de xarxa i optimització
- [ ] Clan compartit funcional

---

### Fase 9 — PERSONALITZACIÓ I POLIMENT

**Objectiu**: Tot el sistema estètic.

- [ ] Editor d'avatar complet
- [ ] Sistema de pintura (pigments, colors)
- [ ] Personalització de construccions
- [ ] Decoració interior/exterior
- [ ] Zona final del mapa (Desert, Muntanya, Illa)
- [ ] Energies místiques completes
- [ ] Criatures fantàstiques completes
- [ ] Poliment visual, sons, música
- [ ] Equilibrat de joc (balancing)
- [ ] Testing complet

---

### Fase 10 — PUBLICACIÓ

- [ ] Més idiomes
- [ ] Pàgina de Steam / itch.io
- [ ] Trailer
- [ ] Beta testing
- [ ] Llançament

---

## 13. ARQUITECTURA TÈCNICA (Visió General)

### 13.1 Tecnologia

- **Motor**: Python + Pygame (prototip) — considerar migració a Godot per producció
- **Networking**: Socket-based / WebSocket per multijugador
- **Dades**: JSON per guardat de partides i definicions
- **i18n**: Fitxers de traducció externs (JSON/YAML)
- **Assets**: Pixel art 32x32 tiles, sprites animats

### 13.2 Estructura del Projecte (Prevista)

```
prova-joc/
├── GDD.md                  # Aquest document
├── requirements.txt        # Dependències Python
├── src/
│   ├── main.py             # Entry point
│   ├── settings.py         # Constants i configuració
│   ├── network/            # Client-servidor
│   ├── world/              # Mapa, zones, tiles
│   ├── entities/           # Jugador, NPCs, animals, criatures
│   ├── systems/            # Temps, clima, economia, missions
│   ├── ui/                 # Interfície, menús, HUD
│   ├── items/              # Objectes, eines, cultius
│   ├── combat/             # Sistema de lluita
│   ├── alchemy/            # Sistema d'alquímia
│   └── i18n/               # Traduccions
├── assets/
│   ├── sprites/            # Personatges, objectes
│   ├── tiles/              # Tiles del mapa
│   ├── ui/                 # Elements d'interfície
│   └── audio/              # Música i sons
└── data/
    ├── items.json           # Definició d'objectes
    ├── crops.json           # Definició de cultius
    ├── npcs.json            # Definició de NPCs
    ├── quests.json          # Missions
    ├── tech_tree.json       # Arbre de tecnologia
    ├── alchemy.json         # Receptes d'alquímia
    └── energies.json        # Definició de les 7 energies
```

### 13.3 Nota sobre Motor de Joc

> **Python + Pygame** és ideal per al prototip i les primeres fases. Si el joc creix
> en complexitat (especialment amb multijugador i molts assets), es recomanaria considerar
> migrar a **Godot Engine** (GDScript és similar a Python) per a la producció final,
> ja que ofereix millor rendiment, editor visual, i exportació nativa a Steam.
> Tanmateix, podem arribar molt lluny amb Pygame i és perfecte per validar el disseny.

---

_Document creat el 12/03/2026 — Versió 1.0_
_Actualitzat el 14/03/2026 — Versió 1.1_
_Pendent: Confirmació del nom, revisió de quantitats, definició detallada de NPCs_
