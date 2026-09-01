# Glosario de traducción — Persona Mechanoid Pawns 2 (Español Latinoamérica)

Terminología fija para mantener consistencia en toda la traducción del mod.
Ante un término nuevo del juego que no esté aquí, consultar antes de fijarlo.

## Términos del mod / RimWorld

| Inglés | Español (LatAm) | Notas |
|---|---|---|
| mech | **meca** (pl. mecas) | Forma corta de "mecanoide" |
| mechanoid | mecanoide | |
| persona / personae (el ser con IA, y el concepto) | **IA** | Femenino invariable: "las IA", "una IA", "IA vengativas". Sustituye a "persona" salvo excepciones abajo |
| persona mech | **meca IA** | |
| persona mechanoid | **mecanoide IA** | |
| persona core / AI persona core / persona-grade AI core | **núcleo de IA** | Término oficial de RimWorld (item vanilla `AIPersonaCore`) |
| persona data | datos de IA | |
| persona engram | engrama de IA | |
| persona interface | interfaz de IA | |
| persona-grade / persona-level (intelligence) | IA avanzada / de nivel avanzado | Evitar "IA de nivel IA" |
| anti-persona | anti-IA | |
| subcore | subnúcleo | |
| subpersona (assistant, tier) | **sub-IA** | "subpersona assistant" → asistente sub-IA; "sub persona grade" → de nivel sub-IA |
| "persona" = humano real | persona | Se mantiene (p. ej. "esta persona", "la persona objetivo") |
| hyper-advanced computer core | núcleo de computadora hiperavanzado | |
| mechlink | **mecaenlace** | NO "mecoenlace" ni "mechlink" |
| mechanitor | **mecanizador** | NO "mecanitor" |
| war mech | meca de guerra | |
| labor mech | meca de trabajo | |
| mech gestator | gestador de mecas | |
| (mech) recharger / charger | **cargador** (de mecas) | NO "recargador"; el proceso/verbo sí es "recarga"/"recargar" |
| mech cluster | clúster mecanoide | |
| tipos de meca vanilla (nombres ES oficiales) | agricoide (agrihand), transportoide (lifter), fabricoide (fabricor), diabolus, tunelador, abrasador, termita, apocritón, lancero, paramédico… | En medio de frase van en minúscula: "mecas termita y transportoide", "un mecanoide fabricoide" |
| persona mech gestator | gestador de mecas IA | (plural) |
| psylink | **psicoenlace** | NO "psienlace" |
| psylink neuroformer / psychic amplifier | neuroformador de psicoenlace | |
| archotech | **arqueotéc** | Femenino: "la arqueotéc", "las arqueotéc". Como adjetivo, invariable: "brazo arqueotéc". NO "archotec" ni "arcotecnológico" |
| (toxic) waste pack | pack de residuos (tóxicos) | NO "paquete" |
| hauler | transportista | NO "acarreador" |
| pawn / colonist | colono | NO "colonista" |
| ship chunk | escombro de nave | |
| casing (carcasa exterior del meca) | **chasis** | Etiquetas cortas: "chasis blanco", "chasis dorado", "chasis reforzado"… |
| frame (estructura del meca) | estructura | "frame stabilizer" → estabilizador de estructura |
| ghoul | necrófago | NO "caminante" |
| shambler | caminante | |
| devilstrand | hilodiablo | |
| synthread | tela sintética | |
| hyperweave | hipertejido | |
| deepchem | quimiofango | |
| chemfuel | quimbustible | |
| drop pod | cápsula de descenso | |

## Tipos de trabajo (nombres oficiales RimWorld ES)

Bombero · Médico · Cuidar niños · Vigilante · Entretener · Cazar · Cultivar ·
Cortar plantas · Sastrería · Fabricar · Transporte · Ocultismo · Paciente ·
Descansar · Básico · Adiestrar · Cocinar · Construir · Minar · **Forjar** (=Smithing,
NO "herrería") · Arte · Pescar · Limpiar · Investigar

## Convenciones de estilo

- `Warning:` → `Advertencia:` · `Note:` → `Nota:`
- "Input a value" → "Introduce un valor"
- Mantener sin traducir: nombres de mods, placeholders `{...}`, secuencias `\n` literales, `Vanilla`.

## Reglas de XML

- Los tags de color en el **texto traducido** deben ir escapados:
  `&lt;color=#f1ce02&gt;...&lt;/color&gt;` (NO `<color=...>` literal — rompe el parseo XML).
- Dentro de comentarios `<!-- EN: ... -->` se dejan literales.
- No modificar los nombres de def en las etiquetas (p. ej. `PMP_CivilMechhive_Mechanitor`).

## Descripciones oficiales de referencia

**Núcleo de IA (persona core):**
> Un núcleo de computadora hiperavanzado que alberga una inteligencia artificial (IA)
> sobrehumana. De forma aislada el núcleo se encuentra en estado inactivo, pero si es
> instalado sobre un soporte adecuado puede convertirse en una mente de aterradoras
> capacidades.

**Neuroformador de psicoenlace (psylink neuroformer):**
> Un dispositivo consumible creado por la arqueotéc que forma o actualiza un psicoenlace
> en la mente del usuario. El usuario presiona el dispositivo sobre los ojos, donde se
> conecta directamente al cerebro y reestructura parte de este. Después, el dispositivo
> se desintegra en cenizas sin valor.

**Gestador de mecas (mech gestator):**
> Un tanque de fluido rico en mecanitas con tubos de soporte para introducir materiales
> y nutrientes. Los mecanizadores pueden utilizarlo para producir nuevos mecanoides o
> para resucitar mecanoides muertos. Este tipo básico de gestador de mecas solo es capaz
> de generar mecas ligeros. El proceso utiliza productos químicos agresivos que se
> almacenan en packs de residuos tóxicos. Los transportistas deben retirar los packs de
> residuos de vez en cuando.

**Mecaenlace (mechlink):**
> Un implante biónico que permite controlar directamente a los mecanoides. Los soldados
> utilizan los mecaenlaces para controlar a los mecas de guerra y los trabajadores para
> controlar a los mecas de trabajo. Una persona con un mecaenlace se conoce como
> mecanizador.
