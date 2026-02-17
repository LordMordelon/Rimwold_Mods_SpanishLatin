# Descripción Detallada de Programas

## 📁 Referencia Rápida

| Programa | Tipo | Entrada | Salida | GUI | Crítico |
|----------|------|---------|--------|-----|---------|
| `extractor.py` | Python/GUI | Mod local o Steam | `Archivo Traducciones/` | ✓ Sí | ✅ Alto |
| `compilador.py` | Python/GUI | `Archivo Traducciones/` | `Pack Traducciones/` | ✓ Sí | ✅ Alto |
| `cli_compilador.py` | Python/CLI | `Archivo Traducciones/` | `Pack Traducciones/` | ✗ No | ✅ Alto |
| `extractor_metadatos.py` | Python/GUI | Steam Workshop | `Metadatos_Mods/` | ✓ Sí | 🟡 Medio |
| `generar_release_notes.py` | Python/GUI | Pack anterior + nuevo | `RELEASE_NOTES.md` | ✓ Sí | 🟡 Medio |

---

## 1️⃣ extractor.py - Extración de Traducciones

### 🎯 Propósito
Escanea un mod individual (desde Steam Workshop o carpeta local) y extrae **solo los textos traducibles** en estructura organizada para el repositorio.

### 📥 Entrada
- **Carpeta del Mod:** Ruta a carpeta que contiene `/Defs`
- **Archivo Traducciones:** Ruta opcional a repositorio local
- **Idioma:** Nombre del idioma (ej: `SpanishLatin (Español(Latinoamérica))`)
- **Opciones:**
  - `Mostrar aviso al finalizar` (popup al terminar)
  - `Crear archivo LEEME` (instrucciones de instalación)
  - `Combinar todo en versión destino` (fusiona versiones)
  - `Integrar contenido de Mods en raíz` (aplana estructura)
  - `Limpiar carpeta de salida` (borra salida previa)
  - `Recuperar líneas implícitas (Legacy)` (busca traducciones heredadas)
  - `Crear About.xml (Metadata)` (⭐ CRÍTICO para PackageID)

### 🔧 Configuración: extractor_config.json

```json
{
  "last_mod_path": "C:\\Program Files (x86)\\Steam\\steamapps\\workshop\\content\\294100\\2675937082",
  "archive_path": "C:/Users/amaro/Desktop/Proyectos/Archivo Traducciones",
  "target_version": "Todas",
  "show_popup": false,
  "create_readme": false,
  "merge_versions": true,
  "simplify_mods": true,
  "clean_output": true,
  "recover_implicit": false,
  "create_about": true,  ← ⭐ IMPORTANTE: Genera About.xml con PackageID
  "translatable_tags": [
    "label", "description", "jobString", "reportString", "pawnLabel",
    "graphLabel", "verb", "gerund", "deathMessage", "skillLabel",
    "labelNoun", "labelShort", "labelPlural", "adjective", "text",
    "rejectionMessage", "helpText", "labelShortAdj", "flavorText",
    "title", "titleShort", "baseDesc", "titleFemale", "titleShortFemale",
    "letterLabel", "letterText", "extraOutcomeDesc", "customLabel",
    "chargeNoun", "endMessage"
  ],
  "blacklisted_tags": [
    "verbClass", "commandTexture", "commandLabelKey", "texPath", "iconPath"
  ]
}
```

### 📊 Proceso Interno

#### Paso 1: Detecting Idiomas
```python
def detectar_idiomas(origen: str):
    """Busca todas carpetas de idioma en mods"""
    # Ignora: about, defs, assemblies, patches, textures, sounds, 1.0-1.5
    # Busca: SpanishLatin (Español...), English, German, etc.
```

#### Paso 2: Parsear XML del Mod
```python
def extract_translatable_tags(xml_file):
    """Para cada archivo en /Defs/"""
    for tag in translatable_tags:
        if tag not in blacklisted_tags:
            value = element.find(tag).text
            output.append((key, value))
```

#### Paso 3: Crear Estructura Salida
```
Archivo Traducciones/
└── NombreMod/
    ├── About/
    │   └── About.xml  ← Extraído del mod original
    │
    └── SpanishLatin (Español(Latinoamérica))/
        ├── DefInjected/
        │   ├── ThingDef/
        │   │   └── [NombreMod]_ThingDef.xml
        │   ├── HediffDef/
        │   └── ... (otras Defs que existan)
        │
        └── Keyed/
            └── [NombreMod]_Keys.xml
```

#### Paso 4: Generar About.xml (si `create_about:true`)
```xml
<?xml version="1.0" encoding="utf-8"?>
<ModMetaData>
  <name>NombreMod</name>
  <author>Autor Original</author>
  <packageId>ejemplo.packageid.aqui</packageId>
  <description>Metadatos extraído automáticamente</description>
  <supportedVersions>
    <li>1.6</li>
  </supportedVersions>
</ModMetaData>
```

### 🎮 GUI Elementos

```
┌───────────────────────────────────────────────────────────┐
│         RimWorld Translation Extractor                     │
├───────────────────────────────────────────────────────────┤
│                                                            │
│  Carpeta del Mod:  [            ] [Buscar...] [Abrir]   │
│  Archivo Traducciones: [      ] [Buscar...] [Abrir]    │
│  Lenguaje de salida:   [SpanishLatin] Versión: [Todas▼] │
│                                                            │
│  [Opciones ▼]  ← Desplegable con 7 opciones             │
│                                                            │
│  Etiquetas Traducibles:    │ Etiquetas Editables:       │
│  ├☑ label                  │ ├ label                     │
│  ├☑ description            │ ├ description               │
│  ├☑ jobString              │ └ ...                       │
│  └ ... (25 tags)           │                             │
│                                                            │
│  [Extractar Traducción]  [Limpiar]  [Ver Log]           │
│                                                            │
├───────────────────────────────────────────────────────────┤
│ LOG OUTPUT (3 líneas):                                    │
│ > Iniciando extracción...                                 │
│ > Encontrados 142 elementos traducibles                   │
│ > Proceso completado en 2.3s                              │
└───────────────────────────────────────────────────────────┘
```

### ⚠️ Casos de Uso Comunes

**Caso A: Extraer mod nuevo del Workshop**
1. Click "Buscar..." → Navega a `C:\Program Files (x86)\Steam\steamapps\workshop\content\294100\[ID]\`
2. Select idioma: `SpanishLatin (Español(Latinoamérica))`
3. Opciones: `create_about: true`, `clean_output: true`
4. Click "Extractar Traducción"
5. ✓ Resultado en `Archivo Traducciones/NombreMod/`

**Caso B: Recuperar traducciones obsoletas (legacy)**
1. Opciones: Activar **"Recuperar líneas implícitas (Legacy)"**
2. El programas buscará etiquetas heredadas XML

---

## 2️⃣ compilador.py - Compilación del Pack Completo

### 🎯 Propósito
Lee **TODAS** las traducciones en `Archivo Traducciones/`, las **combina en un único Pack** validado e integrado.

### 📥 Entrada
- **Origen:** `Archivo Traducciones/` (100+ mods)
- **Destino:** `Pack Traducciones [Español Latino]/` (install path RimWorld)

### 🔧 Configuración: compilador_config.json

```json
{
  "origen": "C:/Users/amaro/Desktop/Proyecto/Archivo Traducciones",
  "destino": "C:/Program Files (x86)/Steam/steamapps/common/RimWorld/Mods/Pack Traducciones [Español Latino]",
  "idioma_seleccionado": "SpanishLatin (Español(Latinoamérica))",
  "reporte_config": {
    "titulo": "Mods Procesados",
    "incluir_conteo": true,
    "incluir_lista_mods": true,
    "texto_adicional": "",
    "reporte_ruta_personalizada_enabled": false,
    "reporte_ruta_personalizada": ""
  },
  "opciones_default": {
    "limpiar_destino": true,        ← Borra Pack viejo
    "eliminar_comentarios": true,   ← Quita comments XML
    "comprimir": false              ← No usado
  }
}
```

### 🔧 Clase Principal: CopiadorThread (QThread)

```python
class CopiadorThread(QThread):
    """Thread que ejecuta copia/compilación en background"""
    
    def __init__(self, origen, destino, nombre_subcarpeta, 
                 limpiar_destino=False, eliminar_comentarios=False):
        self.origen = origen
        self.destino = destino
        self.nombre_destino = normalizar_nombre_idioma(nombre_subcarpeta)
        self._lock = Lock()  # Para thread-safety
    
    def run(self):
        """Ejecuta en thread separado"""
        # Step 1: Limpiar si se solicita
        # Step 2: Listar mods a procesar
        # Step 3: Procesar con ThreadPoolExecutor (máx 4 workers)
        # Step 4: Emitir señales de progreso
```

### 📊 Proceso Multihilo Detallado

```
Main Thread (GUI)
    └─→ CopiadorThread.run()
            └─→ ThreadPoolExecutor(max_workers=4)
                    ├─→ Worker 1: Procesa ModA
                    ├─→ Worker 2: Procesa ModB
                    ├─→ Worker 3: Procesa ModC
                    └─→ Worker 4: Procesa ModD
                    (Continue con el resto secuencialmente)
 
Cada Worker emite:
    • progreso(int)         ← % completado
    • log(str)              ← Mensaje de estado
    • error_log(str)        ← Errores (si ocurren)
    • archivos_count(int)   ← Archivos copiados
    • mods_count(int, int)  ← (procesados, total)
```

### 🔄 Función Crítica: _procesar_mod

```python
def _procesar_mod(self, mod: str, total_mods: int):
    """
    Procesa UN MOD completo
    
    1. Obtiene carpeta idioma (SpanishLatin/...)
    2. Para cada archivo .xml
       a) Si eliminar_comentarios: limpia comentarios
       b) Renombra a: [ModName]_FileName.xml
       c) Copia manteniendo jerarquía (DefInjected/Keyed/etc)
    3. Si existe About.xml
       a) Extrae packageId
       b) Devuelve para LoadFolders.xml
    """
```

### 📋 Señales Emitidas

```python
progreso = Signal(int)                  # 0-100 (para progress bar)
log = Signal(str)                       # "Iniciando..."
error_log = Signal(str)                 # "Error: ..."
terminado = Signal(int)                 # Total archivos copiados
mods_count = Signal(int, int)           # (5/100) mods
archivos_count = Signal(int)            # 1234 archivos
```

### 🎮 GUI Elementos

```
┌──────────────────────────────────────────────────────────┐
│       Compilador de Traducciones RimWorld                │
├──────────────────────────────────────────────────────────┤
│                                                           │
│  Ruta Origen:      [C:/Archivo Traducciones/      ]    │
│  Ruta Destino:     [C:/Mods/Pack Traducciones/     ]    │
│  Idioma:           [SpanishLatin (Español...)     ]    │
│                                                           │
│  Opciones:                                              │
│    ☑ Limpiar carpeta destino antes de compilar         │
│    ☑ Eliminar comentarios XML                          │
│    ☐ Generar comprimido .zip                           │
│                                                           │
│  [Compilar]  [Cancelar]  [Abrir Destino]               │
│                                                           │
├──────────────────────────────────────────────────────────┤
│ Progreso: [████████────────────────────────────] 35%    │
│ Mods: 35/127                                            │
│ Archivos: 3,847                                         │
│ Tiempo: 1m 23s                                          │
│                                                           │
├──────────────────────────────────────────────────────────┤
│ LOG:                                                     │
│ > Iniciando compilación...                              │
│ > Limpiando destino anterior...                         │
│ > Procesando: A RimWorld of Magic (1/127)               │
│ > Copiado: [Magic]_Faction.xml                          │
│ > Procesando: Achtung! (2/127)                          │
│ > Error en: LiquidityPumps - archivo corrupto           │
│ > Continuando...                                         │
│ > COMPILACIÓN COMPLETADA: 3,847 archivos copiados      │
└──────────────────────────────────────────────────────────┘
```

### ⚙️ Output del Compilador

```
Pack Traducciones [Español Latino]/
│
├── About/
│   ├── About.xml                ← Metadata del Pack
│   ├── ModIcon.png
│   ├── preview.png
│   └── PublishedFileId.txt
│
├── Languages/
│   └── SpanishLatin/
│       ├── DefInjected/
│       │   ├── ThingDef/
│       │   │   ├── [A RimWorld of Magic]_ThingDef.xml
│       │   │   ├── [Achtung]_ThingDef.xml
│       │   │   └── ... (150+ archivos)
│       │   │
│       │   ├── HediffDef/
│       │   │   ├── [Anima Bionics]_HediffDef.xml
│       │   │   └── ...
│       │   
│       │   └── ... (otros tipos de Def)
│       │
│       └── Keyed/
│           ├── [A RimWorld of Magic]_Keys.xml
│           ├── [Achtung]_Keys.xml
│           └── ... (100+ Keys)
│
└── LoadFolders.xml              ← ⭐ NUEVO: Controla carga condicional
```

### 🔗 Integración con LoadFolders.xml (PRÓXIMA FASE)

```xml
<?xml version="1.0" encoding="utf-8"?>
<loadFolders>
  <v1.6>
    <!-- Contenido siempre cargado -->
    <li>Common</li>
    
    <!-- Parches condicionales para mods que alteran Vanilla -->
    <li IfModActive="ludeon.rimworld.royalty">Mods/Royalty_Vanilla_Patches</li>
    <li IfModActive="oskarpotocki.vanillaexpanded.core">Mods/VFE_Core_Vanilla_Patches</li>
  </v1.6>
</loadFolders>
```

---

## 3️⃣ cli_compilador.py - Versión CLI del Compilador

### 🎯 Propósito
Exactamente lo mismo que `compilador.py` pero sin GUI. Para **automatización** y **scripts batch**.

### 💻 Uso

```bash
# Compilación básica con defaults
python cli_compilador.py

# Con parámetros personalizados
python cli_compilador.py --origen "C:/Archivo Traducciones" \
                          --destino "C:/Mods/Pack Traducciones" \
                          --limpiar --no-comentarios
```

### 📋 Parámetros

| Parámetro | Tipo | Default | Descripción |
|-----------|------|---------|-------------|
| `--origen` | str | compilador_config.json | Ruta `Archivo Traducciones/` |
| `--destino` | str | compilador_config.json | Ruta destino Pack |
| `--idioma` | str | compilador_config.json | `SpanishLatin (Español...)` |
| `--limpiar` | flag | true | Borra Pack anterior |
| `--no-comentarios` | flag | true | Elimina comentarios XML |
| `--verbose` | flag | false | Output detallado |
| `--config` | str | compilador_config.json | Custom config file |

### 📤 Output CLI

```
[INFO] Cargando configuración: compilador_config.json
[INFO] Origen: /Archivo Traducciones
[INFO] Destino: /Pack Traducciones [Español Latino]
[INFO] Idioma: SpanishLatin (Español(Latinoamérica))
[INFO] Opción limpiar_destino: TRUE
[INFO] Opción eliminar_comentarios: TRUE
-------
[START] Compilación iniciada: 2:34:15 PM
[SCAN] Escaneando /Archivo Traducciones...
[FOUND] 127 mods detectados
[CLEAN] Limpiando directorio destino...
[PROCESS] Iniciando compilación multihilo (4 workers)...
[1/127] A RimWorld of Magic → 234 archivos
[2/127] Achtung! → 18 archivos
[3/127] Adaptive Storage → 45 archivos
...
[COMPLETE] ✓ Compilación exitosa en 2m 15s
[STATS] Total: 3,847 archivos copiados de 127 mods
[OUTPUT] Ubicación: C:\Program Files (x86)\Steam\steamapps\common\RimWorld\Mods\Pack Traducciones [Español Latino]
```

---

## 4️⃣ extractor_metadatos.py - Extración de Metadatos

### 🎯 Propósito
Escanea **toda la librería de Steam Workshop** y extrae metadatos (nombre, autor, packageId) de cada mod. Útil para generar **tabla de referencia de PackageIDs**.

### 📥 Entrada
- **Carpeta de Workshop:** `C:\Program Files (x86)\Steam\steamapps\workshop\content\294100\`

### 📤 Salida
```
Metadatos_Mods/
├── Mod A.txt          ← nombre, packageId, autor, etc.
├── Mod B.txt
└── ... (1000+ mods)
```

### 🔧 Proceso

```python
def run(self):
    """
    1. Escanea todas carpetas numéricas en Workshop
    2. Para cada carpeta:
       a) Busca About/About.xml
       b) Parse XML → extrae name, packageId, author
       c) Valida y sanitiza
    3. Guarda en Metadatos_Mods/NombreMod.txt
    """
```

### 💡 Caso de Uso

**Para llenar LoadFolders.xml:**
1. Ejecutar `extractor_metadatos.py`
2. Genera `Metadatos_Mods/` con todos los PackageIDs
3. **Desarrollador revisa** cuáles mods alteran Vanilla
4. **Manualmente** crea carpetas en `/Mods/` para esos PackageIDs específicos
5. Usa el nombre exacto del PackageID en `LoadFolders.xml`

---

## 5️⃣ generar_release_notes.py - Release Notes Automáticas

### 🎯 Propósito
Compara Pack anterior vs nuevo, **detecta cambios**, genera **RELEASE_NOTES.md** y actualiza **versión** en About.xml.

### 📥 Entrada
- Pack anterior (backup)
- Pack actual (recientemente compilado)

### 📤 Salida
```
Pack Traducciones [Español Latino]/
├── RELEASE_NOTES.md          ← Nuevo archivo
└── About/About.xml           ← Versión actualizada a X.Y.Z
```

### 🔄 Proceso

```python
def generate_release_notes(old_pack, new_pack):
    """
    1. Escanea directorios viejo/nuevo
    2. Compara lista de mods
       - Mods nuevos: agregar a "Nueva traducciones"
       - Mods actualizados: agregar a "Actualizaciones"
       - Mods removidos: opcional (normalmente no)
    3. Calcula estadísticas:
       - Total archivos nuevos
       - Total líneas traducidas
       - Mods modificados
    4. Incrementa versión semver
       - Patch (Z) si cambios menores
       - Minor (Y) si mods nuevos
       - Major (X) si cambio importante
    """
```

### 📋 Ejemplo de RELEASE_NOTES.md

```markdown
# Release Notes - Pack Traducciones [Español Latino]

## Versión 2.5.3 - 17 de febrero de 2026

### 🎉 Nuevas Traducciones (4 mods)
- A RimWorld of Magic - Traducción completa
- GravTech - Big Cannons - Traducción inicial
- Mechanoid Upgrades - Archotech - Traducción inicial
- Integrated Implants - Traducción inicial

### 🔄 Actualizaciones (12 mods)
- Achtung! - Actualizado a v1.6 compatible
- Vanilla Expanded Framework - 45 líneas nuevas
- Elite Bionics Framework - Correcciones ortográficas
- ... (9 más)

### 📊 Estadísticas
- Total de mods soportados: 127
- Total de archivos de traducción: 3,847
- Líneas de texto traducidas: +45,000

### 🐛 Fixes
- [Fixed] Caracteres especiales en Keyed/
- [Fixed] Nombres de mods con corchetes

### 📝 Notas del Traductor
Esfuerzo de localización basado en expresiones naturales del español latino...

Version anterior: 2.5.2 - 10/02/2026
```

---

## 🎛️ Matriz de Dependencias

```
extractor.py
    ↓ Genera
Archivo Traducciones/ (repoLocal)
    ↓ Consume
compilador.py / cli_compilador.py
    ├─→ Requiere (About.xml con PackageID)
    │       ↓
    │   extractor_metadatos.py (genera PackageID reference)
    │
    └─→ Genera
        Pack Traducciones [Español Latino]/
            ↓ Consume
            generar_release_notes.py
                ↓ Genera
                + RELEASE_NOTES.md
                + About.xml (versión actualizada)
```

---

## 🔐 Validaciones Críticas

| Validación | Dónde | Impacto |
|-----------|-------|--------|
| PackageID exacto | compilador.py | ❌ LoadFolders.xml incorrecto |
| About.xml presente | extractor.py | ❌ No se extrae PackageID |
| Nombre idioma normalizado | normalizar_nombre_idioma() | ⚠️ Archivos no se copian |
| Etiqueta en whitelist | extractor.py | ⚠️ Texto ignorado |
| Archivo XML válido | todos | ❌ Crash al parsear |
| Thread-safety | compilador.py | ⚠️ Race conditions |

---

**Siguiente:** [FLUJO_VISUAL.md](FLUJO_VISUAL.md) para ver diagramas
