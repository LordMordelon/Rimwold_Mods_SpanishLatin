# Diagramas Visuales del Flujo de Datos

## 📊 Diagrama General del Pipeline

```
FUENTE DE DATOS          PROCESAMIENTO            SALIDA FINAL
═════════════════════════════════════════════════════════════════════

Steam Workshop    extractor.py     Archivo Traducciones    compilador.py
    │─────────────┤  GUI/Python    └────────────┬──────────│
    │               • Parse XML       • 127 mods │           │
    │               • Extract texto   • 3.8k arcs│           │
    │               • Crear About.xml • PackageID│           │
    │                                            │           │
Local Mods ───────┘                             │     Pack Traducción
                                                │      [Español Latino]
                                                │
                                              ✓ Ready para:
                                              • Steam Workshop
                                              • GitHub Releases
                                              • Instalación local
```

---

## 📋 Flujo Paso a Paso de Compilación

```
START: compilador.py
  │
  ├─ [1. CARGAR CONFIG]
  │   └─ Lee compilador_config.json
  │       ├─ origen: C:/Archivo Traducciones
  │       ├─ destino: C:/RimWorld/Mods/Pack Traducciones
  │       ├─ idioma: SpanishLatin (Español...)
  │       └─ opciones: limpiar, eliminar_comentarios
  │
  ├─ [2. PREPARAR DESTINO]
  │   └─ Si limpiar_destino==true
  │       └─ Borra: C:/RimWorld/Mods/Pack Traducciones/*
  │
  ├─ [3. CREAR ESTRUCTURA BASE]
  │   └─ Crea:
  │       Pack Traducciones/
  │       ├── About/
  │       │   └── About.xml (metadata del Pack)
  │       ├── Languages/
  │       │   └── SpanishLatin/
  │       │       ├── DefInjected/
  │       │       └── Keyed/
  │       └── LoadFolders.xml (vacío, se llena en [7])
  │
  ├─ [4. ESCANEAR MODS]
  │   ├─ Lee: C:/Archivo Traducciones/
  │   └─ Encuentra:
  │       ├─ A RimWorld of Magic/ ← incluir
  │       ├─ Achtung! ← incluir
  │       ├─ [Estructura Ejemplo]/ ← IGNORAR (config)
  │       └─ ... (125 más)
  │       │
  │       Total: 127 mods a procesar
  │
  ├─ [5. COPIAR EM PARALELO]
  │   ├─ ThreadPoolExecutor(max_workers=4)
  │   │   ├─ Worker 1: Procesa A RimWorld of Magic
  │   │   ├─ Worker 2: Procesa Achtung!
  │   │   ├─ Worker 3: Procesa Adaptive Storage
  │   │   └─ Worker 4: Procesa Advanced Moisture
  │   │       (Sigue con el resto secuencialmente)
  │   │
  │   ├─ Por cada mod:
  │   │   ├─ Localiza: Archivo Traducciones/ModA/SpanishLatin/
  │   │   ├─ Para cada archivo .xml:
  │   │   │   ├─ Si eliminar_comentarios: limpia comments
  │   │   │   ├─ Renombra: [ModA]_NombreArchivo.xml
  │   │   │   ├─ Mantiene ruta: DefInjected/ThingDef/
  │   │   │   └─ Copia a destino
  │   │   │
  │   │   └─ Si existe About.xml:
  │   │       ├─ Parse XML
  │   │       ├─ Extrae: name, author, packageId
  │   │       └─ Almacena packageId para [7]
  │   │
  │   └─ Emite señales:
  │       ├─ log("Procesando Mod X...")
  │       ├─ mods_count(50, 127)
  │       ├─ archivos_count(2345)
  │       └─ progreso(39)
  │
  ├─ [6. VALIDAR INTEGRIDAD]
  │   ├─ Verifica:
  │   │   ├─ Todos los archivos fueron copiados
  │   │   ├─ Estructura de carpetas es correcta
  │   │   ├─ No hay archivos duplicados
  │   │   └─ PackageIDs son únicos
  │   │
  │   └─ Si error: log("Error: archivo corrupto")
  │
  ├─ [7. GENERAR LoadFolders.xml] ⭐ NUEVA FUNCIONALIDAD
  │   └─ Para cada mod con About.xml:
  │       ├─ Si packageId contiene "vanilla_patch":
  │       │   └─ Crea entrada condicional:
  │       │       <li IfModActive="packageid.exacto">
  │       │           Mods/NombreMod/
  │       │       </li>
  │       │
  │       └─ Si es mod normal:
  │           └─ Crea entrada:
  │               <li>Common</li>
  │
  ├─ [8. GENERAR REPORTE]
  │   ├─ Calcula estadísticas:
  │   │   ├─ Archivos totales copiados: 3,847
  │   │   ├─ Mods procesados: 127
  │   │   ├─ Tiempo total: 2m 15s
  │   │   └─ Errors: 0
  │   │
  │   └─ Emite: terminado(3847)
  │
  └─ END: Compilación exitosa
      └─ Pack ready en: C:/RimWorld/Mods/Pack Traducciones [ES]
```

---

## 🔄 Ciclo Completo (Semana Típica)

```
LUNES               MARTES-VIERNES            VIERNES              SÁBADO
═════════════════════════════════════════════════════════════════════════════

User extrae      Traductores             Compilación          Release
nuevo mod        editan archivos         final                
                                                               
[extractor.py]   [Manual editing]        [compilador.py]      [Upload]
  │                 │                      │                    │
  ├─ Steam WS        ├─ Archivo Trad/     ├─ Lee 127 mods      ├─ GitHub
  ├─ Scan mod        │   ModA/            ├─ Combina           ├─ Workshop
  ├─ Parse XML       │   └─ .../Keyed/    ├─ Valida            └─ SSite
  ├─ Extract         │       ├─ Key 1     ├─ Genera Pack
  └─ Store           │       ├─ Key 2     └─ Crea ZIP
                     │       └─ Key 3
                     │
                     ├─ ModB/
                     │   └─ .../DefInj/
                     │       ├─ [ModB]_T1.xml
                     │       ├─ [ModB]_T2.xml
                     └─ ...
                
        ↓                   ↓                ↓
   Archivo Trad/      (127 mods en repo)   Pack Final
   crece               (listo para compile) (3.8k archivos)
                                            
                                           [generar_release_notes.py]
                                           ├─ Compara versiones
                                           ├─ Genera RELEASE_NOTES.md
                                           └─ Versionado
```

---

## 🎯 Estructura de Carpetas: Entrada → Salida

### Entrada (Archivo Traducciones/)

```
Archivo Traducciones/
│
├─ A RimWorld of Magic/
│  └─ About/
│     └─ About.xml ← packageId = "ejemplo.rimworld.magic"
│  └─ SpanishLatin (Español(Latinoamérica))/
│     ├─ DefInjected/
│     │  ├─ ThingDef/
│     │  │  └─ [A RimWorld of Magic]_ThingDef.xml
│     │  ├─ HediffDef/
│     │  │  └─ [A RimWorld of Magic]_HediffDef.xml
│     │  └─ SkillDef/
│     │     └─ [A RimWorld of Magic]_SkillDef.xml
│     └─ Keyed/
│        ├─ [A RimWorld of Magic]_Keys.xml
│        └─ [A RimWorld of Magic]_Dialogs.xml
│
├─ Achtung!/
│  ├─ About/
│  │  └─ About.xml ← packageId = "brrainz.achtung"
│  └─ SpanishLatin (Español(Latinoamérica))/
│     └─ Keyed/
│        └─ [Achtung]_Keys.xml
│
└─ ... (125 más en mismo formato)
```

### Salida (Pack Traducciones [Español Latino]/)

```
Pack Traducciones [Español Latino]/
│
├─ About/
│  ├─ About.xml
│  │  ├─ name: Traducciones [Español Latino]
│  │  ├─ packageId: Mordelon.ModPack.SpanishLatin
│  │  └─ version: 2.5.3
│  ├─ ModIcon.png
│  ├── preview.png
│  └─ PublishedFileId.txt
│
├─ Languages/
│  └─ SpanishLatin/
│     ├─ DefInjected/
│     │  ├─ ThingDef/
│     │  │  ├─ [A RimWorld of Magic]_ThingDef.xml ← copiado
│     │  │  └─ [Achtung]_ThingDef.xml ← (si existe)
│     │  │  ...
│     │  ├─ HediffDef/
│     │  │  └─ [A RimWorld of Magic]_HediffDef.xml ← copiado
│     │  ...
│     │
│     └─ Keyed/
│        ├─ [A RimWorld of Magic]_Keys.xml ← copiado
│        ├─ [Achtung]_Keys.xml ← copiado
│        └─ [Adaptive Storage]_Keys.xml ← copiado
│        ... (100+ Keys combinados)
│
├─ LoadFolders.xml ⭐ AUTOINGENERADO
│  ├─ <v1.6>
│  │  ├─ <li>Common</li>
│  │  ├─ <li IfModActive="ludeon.rimworld.royalty">Mods/Royalty_Patch</li>
│  │  └─ <li IfModActive="other.mod">Mods/Mod_Patch</li>
│  └─ </v1.6>
│
└─ RELEASE_NOTES.md ⭐ AUTOINGENERADO
   ├─ Versión 2.5.3 - 17/02/2026
   ├─ Nuevas traducciones: 4 mods
   ├─ Actualizaciones: 12 mods
   └─ Estadísticas: 127 mods, 3847 archivos
```

---

## 🔗 Dependencies Graph

```
                    GITHUB REPOSITORY
                    ┌─────────────────┐
                    │ Archivo Traduc. │
                    │  (100+ mods)    │
                    └────────┬────────┘
                             │
                    Read by (compilador.py)
                             │
        ┌────────────────────┼────────────────────┐
        │                    │                    │
        ▼                    ▼                    ▼
    [Config]         [Normalize]           [Thread Pool]
    JSON file         idioma/path           (max 4)
        │                    │                    │
        │                    │                    │
        └────────────────────┼────────────────────┘
                             │
                             ▼
                    PACK GENERATION
                    ┌─────────────────────────┐
                    │ Pack Traducciones [ES]  │
                    │  • About.xml            │
                    │  • Languages/Spanish    │
                    │  • LoadFolders.xml      │
                    │  • 3,847 archivos       │
                    └────────────┬────────────┘
                                 │
                 ┌───────────────┼───────────────┐
                 │               │               │
                 ▼               ▼               ▼
            [Compress]     [Upload]       [Release Notes]
              .zip        Steam/Github      Markdown
                           Release          Version
```

---

## 🧪 Flujo de Testing/Validación

```
POST-COMPILACIÓN
═════════════════

[CHECK] Pack generado
  └─ ¿Existe Pack?                  → SI ✓
     └─ ¿Tiene About.xml?           → SI ✓
        └─ ¿Tiene Languages/?       → SI ✓
           └─ ¿Tiene LoadFolders?   → SI ✓

[CHECK] Contenido
  └─ ¿127 mods procesados?          → SI (log muestra mods_count)
     └─ ¿3,847 archivos copiados?   → SI (archivos_count)
        └─ ¿DefInjected/Keyed OK?   → SI (estructura intacta)

[CHECK] Metadatos
  └─ ¿About.xml valido XML?         → SI (parser lo valida)
     └─ ¿PackageIDs únicos?         → SI (verificación en [6])
        └─ ¿Versión actualizada?    → SI (generar_release_notes)

[CHECK] Calidad
  └─ ¿Comentarios XML eliminados?   → if enabled ✓
     └─ ¿Normalización correcta?    → SI (idioma "SpanishLatin")
        └─ ¿Errores en log?         → ANALIZAR

RESULTADO FINAL
═════════════════
✓ PASS: Pack listo para compresión/upload
✗ FAIL: Revisar logs, corregir About.xml, recompilar
```

---

## 📊 Matriz de Transformación

```
INPUT: Archivo Traducciones/ModA/SpanishLatin/.../Key1.xml
   └─ <label>Sombrero rojo</label>

PROCESAR EN compilador.py
   ├─ [Leer] Archivo desde INPUT path
   ├─ [Parse] XML válido?
   ├─ [Rename] Key1.xml → [ModA]_Key1.xml
   ├─ [Maintain] ruta: DefInjected/ThingDef/
   ├─ [Clean] si eliminar_comentarios

SALIDA: Pack Traducciones/.../DefInjected/ThingDef/[ModA]_Key1.xml
   └─ <label>Sombrero rojo</label>
   
RESULTADO FINAL (en RimWorld)
   └─ Cuando jugador installa Pack + ModA
      └─ RimWorld carga [ModA]_Key1.xml
      └─ Sombrero en juego dice: "Sombrero rojo"
```

---

## 🔄 Rollback/Recovery Flow

```
   Problema detectado
          │
          ▼
   Existe backup viejo?
    │          │
   SI          NO
    │          └─→ (Imposible restaurar)
    │              (Usar último commit Git)
    │
    ▼
   Restaurar Pack anterior
    ├─ cp backup/ actual/
    │
    ├─ Actualizar About.xml
    │   └─ Version ← versión backup
    │
    └─ RELEASE_NOTES.md
        └─ Documenta rollback
```

---

**Siguiente:** Consulta [MANTENIMIENTO.md](MANTENIMIENTO.md) para instrucciones de actualización
