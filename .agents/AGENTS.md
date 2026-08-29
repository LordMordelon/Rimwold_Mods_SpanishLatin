# AGENTS.md — Proyecto Rimwold Mods SpanishLatin

Documentacion tecnica para agentes IA. Leer antes de modificar cualquier archivo.

---

## Proposito del Proyecto

Sistema de herramientas para crear y mantener un **pack de traduccion al Espanol Latino** para mods de RimWorld. El pack se distribuye como un unico mod en Steam Workshop que consolida las traducciones de 100+ mods.

---

## Estructura del Proyecto

`
Proyecto/
+-- Archivo Traducciones/          <- FUENTE: Traducciones de mods normales (100+ mods)
|   +-- NombreMod/
|       +-- About/
|       |   +-- About_<SteamID>.xml   <- packageId + PublishedFileId (comentario)
|       +-- SpanishLatin (Espanol...)/
|           +-- DefInjected/
|           +-- Keyed/
|
+-- Archivo Traducciones Vanilla/  <- FUENTE: Parches al contenido base de RimWorld
|   +-- NombreMod/
|       +-- About/About.xml           <- packageId OBLIGATORIO para LoadFolders.xml
|       +-- SpanishLatin (Espanol...)/
|
+-- Pack Traducciones [Espanol Latino]/   <- OUTPUT: el mod compilado
|   +-- About/About.xml
|   +-- Common/Languages/SpanishLatin/   <- Mods normales
|   +-- Mods/NombreMod/Languages/        <- Parches Vanilla (carga condicional)
|   +-- LoadFolders.xml
|
+-- Programas/                     <- Herramientas Python
    +-- compilador_utils.py        <- MODULO COMPARTIDO (leer primero)
    +-- compilador.py              <- GUI de compilacion (PySide6)
    +-- cli_compilador.py          <- CLI de compilacion (argparse)
    +-- extractor.py               <- GUI de extraccion (PySide6)
    +-- extractor_metadatos.py     <- GUI de metadatos (PySide6)
    +-- generar_release_notes.py   <- Script Git de release notes
`

---

## compilador_utils.py — Modulo compartido (LEER PRIMERO)

NO importa PySide6. Es Python estandar puro.
Tanto compilador.py como cli_compilador.py importan de aqui.

| Funcion | Descripcion |
|---|---|
| es_mod_ignorado(nombre) | Filtra mods de ejemplo/plantilla |
| normalizar_nombre_idioma(nombre) | "SpanishLatin (Espanol)" -> "SpanishLatin" |
| normalizar_nombre_carpeta(nombre) | "Mi Mod" -> "Mi_Mod" (para Mods/) |
| obtener_package_id(ruta_mod) | Lee packageId de About.xml -> usado en LoadFolders.xml |
| obtener_published_file_id(ruta_mod) | Lee Steam ID numerico -> usado como prefijo de archivos |
| procesar_xml_a_destino(src, dst, bool) | Copia XML con limpieza opcional de comentarios |
| indent_xml(elem) | Pretty-print de ElementTree en su lugar |
| detectar_idiomas(origen) | Lista carpetas de idioma disponibles en Archivo Traducciones/ |

REGLA: Si necesitas modificar alguna de estas funciones, hazlo SOLO en compilador_utils.py.

---

## compilador.py — Compilador con GUI

Clases principales:
- CopiadorThread(QThread): trabajo pesado en background
  - _procesar_mod_normal(mod): copia mods de Archivo Traducciones/ -> Common/Languages/
  - _procesar_mod_vanilla(mod): copia mods de Archivo Traducciones Vanilla/ -> Mods/
  - _reorganizar_a_common(): mueve Languages/ -> Common/Languages/
  - _generar_loadfolders_xml(): crea LoadFolders.xml con entradas IfModActive
- VentanaPrincipal(QMainWindow): UI principal con checkboxes de opciones
- DialogoPersonalizarReporte(QDialog): configura el reporte de mods

Opciones de compilacion (checkboxes en GUI, guardadas en compilador_config.json):
- limpiar_destino: borra Languages/, Common/, Mods/, LoadFolders.xml antes
- eliminar_comentarios: procesa XML quitando comentarios y ordenando tags
- fusionar_xml_por_carpeta: fusiona todos los XML de un mod en uno
- usar_steam_id: usa PublishedFileId como prefijo de archivo
- update_about: actualiza forceLoadAfter en About.xml del Pack

---

## cli_compilador.py — Compilador sin GUI

Funciones principales:
- copiar_traducciones(): procesa Archivo Traducciones/
- copiar_vanilla_patches(): procesa Archivo Traducciones Vanilla/
- reorganizar_a_common(): mueve Languages/ -> Common/Languages/
- generar_loadfolders_xml(): crea LoadFolders.xml
- actualizar_about_xml(): actualiza forceLoadAfter

Flag especial --git: auto-commit + tag de version + release notes.

---

## extractor.py — Extractor de plantillas

GUI que lee un mod de Steam y genera archivos XML con placeholders TODO.
Clase: RimWorldTranslatorGUI(QMainWindow)

Metodos de extraccion:
- run_extraction(): orquesta todo (Defs -> Keyed -> Patches)
- process_file(): procesa un archivo de Defs
- extract_recursive(): traversal recursivo del arbol XML
- process_keyed_file(): procesa archivos Keyed
- process_patches_file(): procesa archivos Patches

NOTA: La logica de calculo de rutas de salida esta duplicada 3 veces (Defs, Keyed, Patches).
Es deuda tecnica conocida. Si modificas esa logica, busca los 3 bloques y editalos consistentemente.

---

## extractor_metadatos.py — Extractor de metadatos de Workshop

Genera los About_<SteamID>.xml necesarios para el sistema (paso de bootstrap).
Escanea Steam/steamapps/workshop/content/294100/ y genera:

  About_3033901359.xml:
    <ModMetaData>
      <name>Adaptive Storage Framework</name>
      <packageId>adaptive.storage.framework</packageId>
      <!-- PublishedFileId: 3033901359 -->
    </ModMetaData>

---

## generar_release_notes.py — Notas de version

Analiza git diff y clasifica mods en Anadidos/Actualizaciones/Correcciones.
Regla: si un mod esta en Correcciones, se excluye de Actualizaciones (modified -= deleted).

---

## Flujo de Trabajo Completo

1. extractor_metadatos.py
   Steam/workshop/294100/ -> Archivo Traducciones/ModName/About/About_<id>.xml

2. extractor.py (por cada mod nuevo)
   Mod de Steam -> Archivo Traducciones/ModName/SpanishLatin/DefInjected/*.xml (TODO)
   [Traductor rellena los TODO manualmente]

3. compilador.py / cli_compilador.py
   Archivo Traducciones/ + Archivo Traducciones Vanilla/
   -> Pack Traducciones [Espanol Latino]/
      +-- Common/Languages/SpanishLatin/   (mods normales)
      +-- Mods/*/Languages/SpanishLatin/   (parches vanilla)
      +-- LoadFolders.xml

4. generar_release_notes.py (via --git)
   git diff -> RELEASE_NOTES.md + git tag

---

## Convenciones de Nomenclatura

PublishedFileId vs packageId:
  - packageId -> para LoadFolders.xml (IfModActive="packageid.del.mod")
  - PublishedFileId -> para prefijos de nombres de archivos compilados
    Con Steam ID activo:    3033901359_Storage.xml
    Sin Steam ID:           [Adaptive Storage Framework]_Storage.xml

Carpetas de salida:
  - Mods normales: Common/Languages/SpanishLatin/DefInjected/TipoDeTag/
  - Mods vanilla: Mods/Nombre_Con_Underscores/Languages/SpanishLatin/

---

## Reglas para Agentes IA

1. No duplicar funciones. Si existe en compilador_utils.py, importar. No copiar.
2. Cambios en logica compartida -> solo editar compilador_utils.py.
3. No romper compatibilidad de JSON. Usar get(key, default) para nuevas claves.
4. Mods Vanilla requieren packageId en About.xml para aparecer en LoadFolders.xml.
5. La carpeta de origen siempre es "Archivo Traducciones/", nunca el Pack de salida.
6. Tests: verificar con python -c "from compilador_utils import *; print('OK')" despues de cambios.
7. Ver sección "Preferencia de Edición y Traducción de Archivos XML" (más abajo).

## Preferencia de Edición y Traducción de Archivos XML

- **Edición directa, sin excepción:** Toda modificación o traducción de archivos XML de RimWorld se realiza directamente sobre los archivos con las herramientas nativas de edición (`replace_file_content` / `multi_replace_file_content`). No se ejecutan scripts intermedios ni comandos de PowerShell/consola para editar contenido, sin importar el tamaño del archivo.
- **Búsqueda (única excepción):** Se permite el uso de herramientas de búsqueda (`grep_search`) exclusivamente para localizar etiquetas `TODO` o verificar términos pendientes en el proyecto. `grep_search` es solo lectura — nunca modifica archivos.
- **Preservación de estructura:** Mantén intacta la estructura XML, las etiquetas, los comentarios originales en inglés (`<!-- EN: ... -->`) y la codificación `UTF-8`.
- **Reemplazo exacto:** Sustituye únicamente los placeholders (`TODO`) por la traducción correspondiente en Español Latino, cuidando la coherencia terminológica del juego.