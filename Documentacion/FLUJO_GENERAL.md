# Flujo General del Sistema de Traducciones

## 🔄 Pipeline Completo

```
┌─────────────────────────────────────────────────────────────────────┐
│                    CICLO DE VIDA DEL PACK                           │
└─────────────────────────────────────────────────────────────────────┘

FASE 1: EXTRACCIÓN DE MODS               │  FASE 2: COMPILACIÓN
─────────────────────────────────────────│──────────────────────────────
                                         │
Steam Workshop / RimWorld Mods           │
    ↓                                    │
 [extractor.py]                          │
 • Escanea carpetas de mods              │
 • Identifica archivos XML               │
 • Extrae textos traducibles             │
 • Genera estructura de salida           │
    ↓                                    │  Archivo Traducciones/
 Archivo Traducciones/                   │  (100+ carpetas de mods)
    ├── Mod A/                           │         ↓
    ├── Mod B/                           │   [compilador.py]
    ├── Mod C/                           │   o [cli_compilador.py]
    └── ... (100+ mods)                  │   • Lee ALL traducciones
                                         │   • Normaliza nombrados
                                         │   • Verifica integridad
                                         │   • Combina en único Pack
                                         │   • Genera LoadFolders.xml
                                         │         ↓
                                         │  Pack Traducciones [ES]
                                         │  (Ready para Steam)
                                         │
                                         │  [generar_release_notes.py]
                                         │  • Crea notas de versión
                                         │  • Documenta cambios
                                         │         ↓
                                         │  Release Notes & Package
```

---

## 📊 Diagrama de Flujo Detallado

### EXTRACCIÓN: extractor.py

**Entrada:** Carpeta de un mod (desde Steam Workshop o local)  
**Salida:** Estructura en `Archivo Traducciones/NombreMod/`

```
Step 1: Cargar Configuración
├── Lee extractor_config.json
├── Obtiene rutas de origen/destino
└── Carga lista de etiquetas "traducibles"

Step 2: Analizar Estructura del Mod
├── Busca carpeta /Defs
├── Identifica versiones (1.0, 1.1, 1.2, 1.3, 1.4, 1.5, 1.6, Base)
├── Detecta subcarpetas (ThingDef, HediffDef, etc.)
└── Valida estructura XML

Step 3: Parsear y Extraer
├── Para cada archivo .xml en /Defs
│   ├── Parse XML
│   ├── Identifica etiquetas traducibles
│   ├── Extrae keys → valores en inglés
│   ├── Valida contra blacklist (etiquetas técnicas)
│   └── Procesa heredadas (legacy) si aplica
│
└── Si opción "Crear About.xml"
    ├── Extrae metadata del mod original
    └── Genera About.xml en salida

Step 4: Generar Salida
├── Crea carpeta Archivo Traducciones/ModName/
├── Dentro: SpanishLatin (Español(Latinoamérica))/
│   ├── DefInjected/
│   │   ├── ThingDef/
│   │   ├── HediffDef/
│   │   └── ... (otros DefTypes)
│   │
│   └── Keyed/
│       └── <Language>Keys.xml
│
└── Crea LEEME.txt con instrucciones (opcional)
```

---

### COMPILACIÓN: compilador.py / cli_compilador.py

**Entrada:** Todo `Archivo Traducciones/` (100+ mods)  
**Salida:** `Pack Traducciones [Español Latino]/` (único pack unificado)

```
Step 1: Cargar Configuración
├── Lee compilador_config.json
├── Obtiene ruta origen (Archivo Traducciones/)
├── Obtiene ruta destino (Pack final)
├── Define idioma de salida (ej: SpanishLatin)
└── Lee opciones (limpiar_destino, eliminar_comentarios, etc.)

Step 2: Preparar Salida
├── Si limpiar_destino = true
│   └── Borra Pack anterior (limpia completamente)
│
├── Crea estructura base
│   ├── Pack Traducciones [Español Latino]/
│   ├── ├── About/
│   ├── │   └── About.xml
│   ├── ├── Languages/
│   ├── │   └── SpanishLatin/
│   ├── │       ├── DefInjected/
│   ├── │       └── Keyed/
│   └── └── LoadFolders.xml ⭐ (NUEVO)

Step 3: Escanear Mods Disponibles
├── Lee todas las carpetas en Archivo Traducciones/
├── Ignora carpetas configuradas (ej: [Estructura Ejemplo])
├── Para cada carpeta mod
│   ├── Busca subcarpeta idioma (ej: SpanishLatin...)
│   └── Si existe → añade a lista de procesamiento

Step 4: Procesar Traducciones en Paralelo
├── Abre ThreadPool con 4 workers simultáneos
│
├── Para cada mod
│   ├── Lee carpeta idioma
│   ├── Para cada archivo .xml
│   │   ├── Si eliminar_comentarios = true
│   │   │   └── Parse y elimina comentarios XML
│   │   │
│   │   ├── Copia a destino renombrando: [ModName]_Nombre.xml
│   │   ├── Mantiene jerarquía: DefInjected/Keyed/etc.
│   │   └── Formatea XML (indenta correctamente)
│   │
│   └── Emite señal de progreso
│
└── Obtiene PackageID si existe About.xml local

Step 5: Generar LoadFolders.xml (PRÓXIMA FASE)
├── Lee lista de mods procesados
├── Para cada mod (si es "Vanilla Patch")
│   ├── Obtiene PackageID
│   ├── Crea entrada: <li IfModActive="packageid">Mods/NombreMod</li>
│   └── Mantiene orden por prioridad
│
├── Para mods normales
│   └── <li>Common</li> (o carpeta de contenido original)
│
└── Genera XML válido con indentación

Step 6: Finalizar
├── Genera reporte de archivos copiados
├── Calcula estadísticas
│   ├── Total mods procesados
│   ├── Total archivos copiados
│   └── Tiempo transcurrido
│
├── Si generar_release_notes = true
│   └── Llamará a generar_release_notes.py
│
└── Emite señal de finalización
```

---

### METADATOS: extractor_metadatos.py

**Entrada:** Carpetas numéricas de Steam Workshop  
**Salida:** `Metadatos_Mods/` con info formateada

```
Step 1: Detectar Mods en Workshop
├── Escanea C:\Program Files (x86)\Steam\steamapps\workshop\content\294100\
├── Identifica carpetas numéricas (WorkshopID)
└── Obtiene lista de mods (conteo total)

Step 2: Extraer About.xml
├── Para cada WorkshopID
│   ├── Busca About/About.xml
│   ├── Parse XML
│   └── Extrae:
│       ├── name (nombre del mod)
│       ├── author (autor)
│       ├── packageId (ID único - CRÍTICO para LoadFolders)
│       ├── description
│       └── supportedVersions

Step 3: Procesar y Formatear
├── Sanitiza nombres (quita caracteres inválidos)
├── Crea carpeta en Metadatos_Mods/NombreMod
├── Genera archivo formateado con metadatos
└── Documenta errors (mods sin About.xml)

Step 4: Salida
└── Metadatos_Mods/
    ├── Mod A.txt (nombre, packageId, etc.)
    ├── Mod B.txt
    └── ... (todos los mods)
```

---

### NOTAS DE VERSIÓN: generar_release_notes.py

**Entrada:** Pack compilado + cambios recientes  
**Salida:** RELEASE_NOTES.md + versión en About.xml

```
Step 1: Detectar Cambios
├── Compara Pack anterior vs actual
├── Identifica mods nuevos
├── Identifica mods actualizados
└── Calcula estadísticas

Step 2: Genera Archivo Release Notes
├── Encabezado con versión y fecha
├── Lista mods nuevos
├── Lista mods modificados
├── Estadísticas totales
└── Links a commits/issues (si integrado con Git)

Step 3: Actualiza About.xml
└── Incrementa version number
    └── Usa formato semver (X.Y.Z)
```

---

## 🔗 Conexiones e Interdependencias

### Relación: extractor.py → Archivo Traducciones

```
Input: Mod en Steam/Local
         ↓
extractor.py analiza
         ↓
Output: Archivo Traducciones/ModName/SpanishLatin/.../
         ├── DefInjected/[ModName]_archivo.xml
         ├── Keyed/[ModName]_Keys.xml
         └── About.xml (opcional, pero IMPORTANTE)
```

**Nota:** El About.xml local en la subcarpeta traducción es CRUCIAL para que el compilador extraiga el PackageID.

---

### Relación: compilador.py → Pack Traducciones

```
Input: Archivo Traducciones/*/ (todo contenido)
         ↓
compilador.py itera
         ↓
Output: Pack Traducciones [Español Latino]/
         ├── Languages/SpanishLatin/
         │   ├── DefInjected/
         │   │   └── [ModA]_file.xml
         │   │   └── [ModB]_file.xml
         │   │   └── ... (combinado)
         │   
         │   └── Keyed/
         │       └── [ModA]_Keys.xml
         │       └── [ModB]_Keys.xml
         │       └── ... (combinado)
         │
         └── LoadFolders.xml (NUEVO - mapea PackageIDs)
```

---

## ⚖️ Precedencia y Validación

### Normalizacion de Idiomas

- Input: `"SpanishLatin (Español(Latinoamérica))"`
- Output: `"SpanishLatin"` ← Quita información entre paréntesis

```python
def normalizar_nombre_idioma(nombre: str):
    # "Idioma (Native Name)" → "Idioma"
    corte = nombre.find(" (")
    if corte != -1:
        return nombre[:corte].strip()  # ← Esto
```

### Prioridad de Carpetas en Pack

Si dos mods usan el mismo nombre de archivo:
```xml
<li>Common</li>                    ← Carga primero
<li IfModActive="mod.a">Mods/ModA</li>
<li IfModActive="mod.b">Mods/ModB</li>
```
**RimWorld prioriza ÚLTIMA en lista** → ModB prevalece si ambos activos

---

## 📋 Configuración Central

### compilador_config.json

```json
{
  "origen": "C:/Users/amaro/Desktop/Proyecto/Archivo Traducciones",
  "destino": "C:/Program Files (x86)/Steam/steamapps/common/RimWorld/Mods/Pack Traducciones [Español Latino]",
  "idioma_seleccionado": "SpanishLatin (Español(Latinoamérica))",
  "opciones_default": {
    "limpiar_destino": true,        ← Borra Pack viejo antes de compilar
    "eliminar_comentarios": true,   ← Reduce tamaño
    "comprimir": false              ← No usado actualmente
  }
}
```

### extractor_config.json

```json
{
  "create_about": true,             ← IMPORTANTE para PackageIDs
  "merge_versions": true,           ← Combina 1.5+1.6 en carpeta 1.6
  "clean_output": true,             ← Limpia destino primero
  "translatable_tags": [...]        ← Etiquetas que busca (label, description, etc.)
  "blacklisted_tags": [...]         ← Etiquetas a IGNORAR (técnicas)
}
```

---

## 🚀 Flujo Temporal Típico

```bash
# Día 1: Extraer nuevo mod del Workshop
python extractor.py
  → Escanea Steam Workshop
  → Genera Archivo Traducciones/NuevoMod/...

# Día 2-7: Traductor regresa
  → Traduce archivos XML en Archivo Traducciones/

# Día 8: Compilar Pack actualizado
python compilador.py
  o
python cli_compilador.py  # CLI version

  → Lee TODO Archivo Traducciones/
  → Genera Pack final (toma ~2 min por 100+ mods)
  → Crea LoadFolders.xml automáticamente

# Día 9: Generar Release Notes
python generar_release_notes.py
  → Compara versión anterior
  → Crea RELEASE_NOTES.md
  → Actualiza versión en About.xml

# Día 10: Empaquetar y publicar
  → Comprime Pack Traducciones [Español Latino]/
  → Sube a Steam Workshop
```

---

## ⚠️ Puntos Críticos

1. **About.xml en subcarpetas** 
   - SIN About.xml → No se extrae PackageID
   - NO PackageID → LoadFolders.xml incompleto
   - RESULTADO: Traducciones de Vanilla aparecen siempre (Bug)

2. **Normalización de Idiomas**
   - Naming inconsistente → Archivos no se copian
   - SIEMPRE nombrar: `SpanishLatin (Español(Latinoamérica))`

3. **Paralelismo en compilador.py**
   - Usa 4 threads simultáneos
   - NO es thread-safe para modificaciones compartidas
   - Pero OK porque cada mod es independiente

4. **LoadFolders.xml (NUEVA FUNCIONALIDAD)**
   - CRÍTICO para separar Vanilla patches
   - Debe validarse que PackageIDs sean exactos
   - RimWorld versión 1.6+ requerido

---

**Próximo paso:** Consulta [PROGRAMAS.md](PROGRAMAS.md) para detalles de cada módulo.
