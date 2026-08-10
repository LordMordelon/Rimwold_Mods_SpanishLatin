"""
compilador_utils.py
===================
Funciones de utilidad compartidas entre compilador.py (GUI) y cli_compilador.py (CLI).

IMPORTANTE PARA AGENTES IA:
  - Este modulo NO importa PySide6. Es puro Python estandar.
  - Cualquier funcion que se necesite en AMBOS compiladores debe vivir aqui.
  - compilador.py     importa: from compilador_utils import <nombres>
  - cli_compilador.py importa: from compilador_utils import <nombres>

Funciones disponibles:
  - es_mod_ignorado(nombre)              -> bool
  - normalizar_nombre_idioma(nombre)     -> str
  - normalizar_nombre_carpeta(nombre)    -> str
  - indent_xml(elem, level, space)       -> None  (modifica en su lugar)
  - obtener_package_id(ruta_mod)         -> str | None
  - obtener_published_file_id(ruta_mod)  -> str | None
  - procesar_xml_a_destino(src, dst, eliminar_comentarios) -> None
  - detectar_idiomas(origen)             -> list[str]
"""

import os
import re
import shutil
import xml.etree.ElementTree as ET
from xml.etree.ElementTree import ParseError


# ==============================================================================
# Constantes
# ==============================================================================

MODS_A_IGNORAR = {
    "estructura ejemplo",
    "[estructura ejemplo]",
}

# Regex para etiquetas HTML inline que RimWorld usa dentro del texto
# Ejemplo: <color=#FF0000>texto</color>, <b>texto</b>
_HTML_TAG_PATTERN = re.compile(
    r"<(/?(?:color|size|b|i)(?:\s+[^>]*?)?)>",
    flags=re.IGNORECASE,
)

_CARPETAS_NO_IDIOMA = {
    "about", "defs", "assemblies", "patches", "textures", "sounds", "common",
    "ideasshared", "licenses", "source", "src", "docs", "examples", ".git",
    ".vs", "1.0", "1.1", "1.2", "1.3", "1.4", "1.5", "1.6",
}


# ==============================================================================
# Filtros de mods
# ==============================================================================

def es_mod_ignorado(nombre: str) -> bool:
    """Retorna True si el nombre del mod esta en la lista negra de ignorados."""
    return nombre.strip().lower() in MODS_A_IGNORAR


# ==============================================================================
# Normalizacion de nombres
# ==============================================================================

def normalizar_nombre_idioma(nombre: str) -> str:
    """
    Extrae el codigo de idioma de un nombre de carpeta con parentesis.

    Ejemplos:
      "SpanishLatin (Espanol(Latinoamerica))" -> "SpanishLatin"
      "English (United Kingdom)"              -> "English"
      "SpanishLatin"                          -> "SpanishLatin"

    Estrategia:
      1. Si hay " (" -> corta antes del parentesis.
      2. Si no -> elimina cualquier segmento final entre parentesis.
    """
    if not isinstance(nombre, str):
        return ""
    nombre = nombre.strip()
    corte = nombre.find(" (")
    if corte != -1:
        return nombre[:corte].strip()
    s = nombre
    while True:
        open_idx = s.rfind("(")
        close_idx = s.rfind(")")
        if open_idx != -1 and close_idx != -1 and close_idx > open_idx:
            s = s[:open_idx].rstrip()
        else:
            break
    return s.strip()


def normalizar_nombre_carpeta(nombre: str) -> str:
    """
    Convierte un nombre de carpeta para usarlo como subcarpeta en Mods/.
    Reemplaza espacios por underscores.

    Ejemplo: "Vanilla Gravship Expanded" -> "Vanilla_Gravship_Expanded"
    """
    if not isinstance(nombre, str):
        return ""
    return nombre.strip().replace(" ", "_")


# ==============================================================================
# XML: indentacion (pretty-print)
# ==============================================================================

def indent_xml(elem, level: int = 0, space: str = "  ") -> None:
    """
    Indenta un arbol ElementTree en su lugar para mejor legibilidad.
    Modifica el arbol directamente (sin retornar nada).

    Uso tipico:
      root = ET.fromstring(content)
      indent_xml(root)
      ET.ElementTree(root).write(path, encoding="utf-8", xml_declaration=True)
    """
    i = "\n" + level * space
    if len(elem):
        if not elem.text or not elem.text.strip():
            elem.text = i + space
        if not elem.tail or not elem.tail.strip():
            elem.tail = i
        for subelem in elem:
            indent_xml(subelem, level + 1, space)
        if not subelem.tail or not subelem.tail.strip():
            subelem.tail = i
    else:
        if level and (not elem.tail or not elem.tail.strip()):
            elem.tail = i


# ==============================================================================
# XML: procesado de archivos (copia + limpieza opcional de comentarios)
# ==============================================================================

def _leer_xml_raw(ruta_origen: str) -> str:
    """
    Lee un archivo XML manejando BOM UTF-8 y UTF-16.
    Retorna el contenido como str limpio (sin BOM).
    """
    with open(ruta_origen, "rb") as f:
        raw_data = f.read()
    try:
        content = raw_data.decode("utf-8-sig")
    except UnicodeDecodeError:
        content = raw_data.decode("utf-16")
    return content.strip()


def procesar_xml_a_destino(
    ruta_origen: str,
    ruta_destino: str,
    eliminar_comentarios: bool,
) -> None:
    """
    Copia un archivo XML de origen a destino.

    SIEMPRE escapa etiquetas HTML inline de RimWorld (<color>, <b>, <i>, <size>)
    porque son XML invalido que RimWorld interpreta como texto enriquecido.

    Si eliminar_comentarios=True ademas:
      - Elimina comentarios XML
      - Ordena etiquetas alfabeticamente dentro del root
      - Aplica pretty-print con indent_xml()

    Si hay error de parseo -> copia el archivo tal cual (fallback silencioso).

    Parametros:
      ruta_origen          : str  - Ruta absoluta del XML fuente
      ruta_destino         : str  - Ruta absoluta donde escribir el resultado
      eliminar_comentarios : bool - True para limpiar y ordenar, False para copia minima
    """
    try:
        content = _leer_xml_raw(ruta_origen)

        # Quitar declaracion XML para parsear solo el cuerpo
        declaracion = ""
        if content.startswith("<?xml"):
            partes = content.split("?>", 1)
            declaracion = partes[0] + "?>"
            content = partes[1].strip()

        # Escapar SIEMPRE las tags HTML inline de RimWorld (<color>, <b>, <i>, <size>)
        # que son XML invalido pero RimWorld las interpreta como texto enriquecido
        content = _HTML_TAG_PATTERN.sub(r"&lt;\1&gt;", content)

        if not eliminar_comentarios:
            # Modo minimo: solo escapar las tags HTML, conservar todo lo demas
            os.makedirs(os.path.dirname(ruta_destino), exist_ok=True)
            with open(ruta_destino, "w", encoding="utf-8") as fh:
                if declaracion:
                    fh.write(declaracion + "\n")
                fh.write(content)
            return

        # Modo limpieza completa: parsear, eliminar comentarios, ordenar y pretty-print
        parser = ET.XMLParser(target=ET.TreeBuilder(insert_comments=False))
        root = ET.fromstring(content, parser=parser)
        root[:] = sorted(root, key=lambda child: child.tag)
        indent_xml(root)
        ET.ElementTree(root).write(ruta_destino, encoding="utf-8", xml_declaration=True)

    except (ParseError, Exception):
        # Fallback: copiar tal cual si hay error de parseo
        shutil.copy2(ruta_origen, ruta_destino)


# ==============================================================================
# Metadatos de mods: packageId y PublishedFileId
# ==============================================================================

def obtener_package_id(ruta_mod: str) -> "str | None":
    """
    Lee el <packageId> del About.xml de un mod.

    Busca en ruta_mod/About/ cualquier archivo About*.xml.
    Prioriza About.xml (nombre mas corto) sobre About_123456.xml.

    Retorna el packageId en minusculas, o None si no se encuentra.

    Uso en el sistema:
      - LoadFolders.xml: atributo IfModActive="<packageId>"
      - NO se usa para prefijos de archivo (para eso ver obtener_published_file_id)
    """
    about_dir = os.path.join(ruta_mod, "About")
    if not os.path.isdir(about_dir):
        return None

    candidatos = [
        f for f in os.listdir(about_dir)
        if f.lower().startswith("about") and f.lower().endswith(".xml")
    ]
    candidatos.sort(key=len)

    for nombre in candidatos:
        ruta = os.path.join(about_dir, nombre)
        try:
            tree = ET.parse(ruta)
            root = tree.getroot()
            pid = root.find("packageId")
            if pid is not None and pid.text:
                return pid.text.strip().lower()
        except Exception:
            continue

    return None


def obtener_published_file_id(ruta_mod: str) -> "str | None":
    """
    Obtiene el PublishedFileId (Steam Workshop ID numerico) de un mod.

    Estrategia de busqueda (en orden de prioridad):
      1. Nombre de archivo: About_<digitos>.xml -> extrae el numero del nombre.
         Ejemplo: "About_3033901359.xml" -> "3033901359"
      2. Comentario XML: <!-- PublishedFileId: <digitos> --> dentro del XML.
         Ejemplo: <!-- PublishedFileId: 3033901359 -->

    Retorna el ID como string (ej. "3033901359"), o None si no se encuentra.

    Uso en el sistema:
      - Prefijo de archivos compilados cuando la opcion "Usar Steam ID" esta activa.
      - Ejemplo: "3033901359_Abilities_Base.xml" en vez de "[A RimWorld of Magic]_Abilities_Base.xml"
    """
    about_dir = os.path.join(ruta_mod, "About")
    if not os.path.isdir(about_dir):
        return None

    # 1. Buscar por nombre de archivo: About_<digitos>.xml
    for f in os.listdir(about_dir):
        m = re.match(r"About_(\d+)\.xml", f, re.IGNORECASE)
        if m:
            return m.group(1)

    # 2. Fallback: buscar comentario PublishedFileId dentro del XML
    candidatos = [
        f for f in os.listdir(about_dir)
        if f.lower().startswith("about") and f.lower().endswith(".xml")
    ]
    for nombre in candidatos:
        ruta = os.path.join(about_dir, nombre)
        try:
            with open(ruta, "r", encoding="utf-8-sig", errors="replace") as fh:
                contenido = fh.read()
            m = re.search(r"PublishedFileId:\s*(\d+)", contenido)
            if m:
                return m.group(1)
        except Exception:
            continue

    return None


# ==============================================================================
# Deteccion de idiomas disponibles
# ==============================================================================

def detectar_idiomas(origen: str) -> list:
    """
    Detecta los idiomas de traduccion disponibles escaneando todos los mods.

    Recorre cada subcarpeta de 'origen' (un mod) y busca subcarpetas que
    no sean carpetas tecnicas conocidas (Defs, About, Assemblies, etc.).
    Las carpetas restantes se consideran idiomas.

    Parametros:
      origen : str - Ruta a "Archivo Traducciones/"

    Retorna:
      list[str] - Lista ordenada de nombres de carpeta de idioma.
      Ejemplo: ["English", "SpanishLatin (Espanol(Latinoamerica))"]
    """
    idiomas_encontrados = set()

    for mod_folder in os.listdir(origen):
        if es_mod_ignorado(mod_folder):
            continue
        ruta_mod = os.path.join(origen, mod_folder)
        if not os.path.isdir(ruta_mod):
            continue
        try:
            for subfolder in os.listdir(ruta_mod):
                ruta_subfolder = os.path.join(ruta_mod, subfolder)
                if (
                    os.path.isdir(ruta_subfolder)
                    and subfolder.lower() not in _CARPETAS_NO_IDIOMA
                ):
                    idiomas_encontrados.add(subfolder)
        except OSError:
            continue

    return sorted(idiomas_encontrados)
