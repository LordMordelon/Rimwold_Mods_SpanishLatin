import argparse
import os
import re
import shutil
import subprocess
import sys
import traceback
from datetime import datetime
from pathlib import Path
import xml.etree.ElementTree as ET
from xml.etree.ElementTree import ParseError

# Utilidades compartidas con compilador.py (GUI)
from compilador_utils import (
    MODS_A_IGNORAR,
    es_mod_ignorado,
    normalizar_nombre_idioma,
    normalizar_nombre_carpeta,
    indent_xml,
    obtener_package_id,
    obtener_published_file_id,
    leer_contribuidores,
    procesar_xml_a_destino,
    detectar_idiomas,
)


def run_git(args, cwd=None, text=True):
    return subprocess.check_output(
        ["git"] + args,
        cwd=cwd,
        text=text,
        encoding="utf-8" if text else None,
        errors="replace" if text else None,
    ).strip()


def get_repo_root(cwd):
    try:
        return Path(run_git(["rev-parse", "--show-toplevel"], cwd=cwd))
    except subprocess.CalledProcessError:
        return None


def get_last_tag(repo_root):
    try:
        return run_git(["describe", "--tags", "--abbrev=0"], cwd=repo_root)
    except subprocess.CalledProcessError:
        return ""


def bump_tag(last_tag):
    if not last_tag:
        return "v1.1.24"

    tag = last_tag.strip()
    if tag.startswith("v"):
        tag = tag[1:]

    parts = tag.split(".")
    if len(parts) != 3 or not all(p.isdigit() for p in parts):
        return "v1.1.24"

    major, minor, patch = [int(p) for p in parts]
    patch += 1
    return f"v{major}.{minor}.{patch}"


def get_repo_name(repo_root):
    """Obtiene el nombre del repositorio en formato user/repo desde git"""
    try:
        url = subprocess.check_output(
            ["git", "config", "--get", "remote.origin.url"],
            cwd=repo_root,
            text=True,
            encoding="utf-8",
        ).strip()
        
        # Parsear URLs tipo: https://github.com/user/repo.git o git@github.com:user/repo.git
        if "github.com" in url:
            if url.startswith("https://"):
                # https://github.com/user/repo.git -> user/repo
                parts = url.replace("https://github.com/", "").replace(".git", "")
            elif url.startswith("git@"):
                # git@github.com:user/repo.git -> user/repo
                parts = url.replace("git@github.com:", "").replace(".git", "")
            else:
                return ""
            return parts
        return ""
    except subprocess.CalledProcessError:
        return ""


def generar_release_notes(repo_root, tag):
    output_path = repo_root / "RELEASE_NOTES.md"
    script_path = repo_root / "Programas" / "generar_release_notes.py"
    if not script_path.is_file():
        return False, "No se encontró generar_release_notes.py"

    repo_name = get_repo_name(repo_root)
    args = [
        sys.executable,
        str(script_path),
        "--output",
        str(output_path),
        "--tag",
        tag,
    ]
    
    if repo_name:
        args.extend(["--repo", repo_name])

    try:
        subprocess.check_call(args, cwd=repo_root)
    except subprocess.CalledProcessError as e:
        return False, f"Error generando release notes: {e}"

    return True, f"Release notes generado en {output_path}"


def git_commit_and_tag(repo_root, tag):
    try:
        run_git(["add", "-A"], cwd=repo_root)
        status = run_git(["status", "--porcelain"], cwd=repo_root)
        if not status:
            return False, "No hay cambios para commitear"

        run_git(["commit", "-m", f"Release {tag}"] , cwd=repo_root)
        run_git(["tag", tag], cwd=repo_root)
    except subprocess.CalledProcessError as e:
        return False, f"Error en git: {e}"

    return True, f"Commit y tag creados: {tag}"


# indent_xml, detectar_idiomas, obtener_package_id, obtener_published_file_id
# estan en compilador_utils (importadas al inicio del archivo)


def copiar_traducciones(origen, destino_root, nombre_subcarpeta, limpiar_destino, eliminar_comentarios):
    destino_languages = os.path.join(destino_root, "Languages")
    os.makedirs(destino_languages, exist_ok=True)

    nombre_destino = normalizar_nombre_idioma(nombre_subcarpeta)
    ruta_destino_subcarpeta = os.path.join(destino_languages, nombre_destino)

    # Ya no limpiamos aquí, se hace al inicio del main()

    mods_a_procesar = [
        d for d in os.listdir(origen)
        if not es_mod_ignorado(d)
        and os.path.isdir(os.path.join(origen, d, nombre_subcarpeta))
    ]

    if not mods_a_procesar:
        return [], 0, []

    archivos_copiados = 0
    errores = []

    for mod in mods_a_procesar:
        ruta_mod = os.path.join(origen, mod)
        ruta_idioma = os.path.join(ruta_mod, nombre_subcarpeta)

        # Usar PublishedFileId (Steam ID) como prefijo; fallback al nombre de carpeta
        published_id = obtener_published_file_id(ruta_mod)
        prefijo_mod = published_id if published_id else mod

        archivos_del_mod = []
        for carpeta_raiz, _, archivos in os.walk(ruta_idioma):
            for archivo in archivos:
                if archivo.endswith(".xml"):
                    archivos_del_mod.append((carpeta_raiz, archivo))

        for carpeta_raiz, archivo in archivos_del_mod:
            ruta_origen = os.path.join(carpeta_raiz, archivo)
            ruta_relativa = os.path.relpath(carpeta_raiz, ruta_idioma)
            ruta_destino_base = os.path.join(destino_languages, nombre_destino)
            ruta_destino_carpeta = os.path.join(ruta_destino_base, ruta_relativa)
            os.makedirs(ruta_destino_carpeta, exist_ok=True)
            nuevo_nombre = f"{prefijo_mod}_{os.path.splitext(archivo)[0]}.xml"
            ruta_destino_archivo = os.path.join(ruta_destino_carpeta, nuevo_nombre)

            if eliminar_comentarios:
                try:
                    parser = ET.XMLParser(target=ET.TreeBuilder(insert_comments=False))
                    with open(ruta_origen, "rb") as f:
                        raw_data = f.read()

                    try:
                        content = raw_data.decode("utf-8-sig")
                    except UnicodeDecodeError:
                        content = raw_data.decode("utf-16")

                    content = content.strip()
                    if content.startswith("<?xml"):
                        content = content.split("?>", 1)[-1].strip()

                    content = re.sub(
                        r"<(/?(?:color|size|b|i)(?:\s+[^>]*?)?)>",
                        r"&lt;\1&gt;",
                        content,
                        flags=re.IGNORECASE,
                    )

                    root = ET.fromstring(content, parser=parser)
                    tree = ET.ElementTree(root)
                    root[:] = sorted(root, key=lambda child: child.tag)
                    indent_xml(root)
                    tree.write(ruta_destino_archivo, encoding="utf-8", xml_declaration=True)
                except ParseError as e:
                    errores.append({
                        "archivo": ruta_origen,
                        "motivo": f"XML invalido: {e}",
                        "trace": traceback.format_exc(),
                    })
                    shutil.copy2(ruta_origen, ruta_destino_archivo)
                except Exception as e:
                    errores.append({
                        "archivo": ruta_origen,
                        "motivo": f"Error procesando XML: {e}",
                        "trace": traceback.format_exc(),
                    })
                    shutil.copy2(ruta_origen, ruta_destino_archivo)
            else:
                try:
                    shutil.copy2(ruta_origen, ruta_destino_archivo)
                except Exception as e:
                    errores.append({
                        "archivo": ruta_origen,
                        "motivo": f"Error copiando archivo: {e}",
                        "trace": traceback.format_exc(),
                    })
                    continue

            archivos_copiados += 1

    return mods_a_procesar, archivos_copiados, errores


def copiar_vanilla_patches(origen_vanilla, destino_root, nombre_subcarpeta, eliminar_comentarios):
    """
    Procesa carpetas de 'Archivo Traducciones Vanilla' y las copia a Mods/NombreMod/
    Retorna lista de (nombre_carpeta_normalizado, packageId, nombre_carpeta_original).
    Los dos primeros valores alimentan LoadFolders.xml; el tercero se usa para
    mostrar el nombre legible (con espacios) en el README y el reporte.
    """
    if not os.path.isdir(origen_vanilla):
        return [], 0, []
    
    nombre_destino = normalizar_nombre_idioma(nombre_subcarpeta)
    mods_vanilla = []
    archivos_copiados = 0
    errores = []
    
    for mod_folder in os.listdir(origen_vanilla):
        if es_mod_ignorado(mod_folder):
            continue
        
        ruta_mod = os.path.join(origen_vanilla, mod_folder)
        if not os.path.isdir(ruta_mod):
            continue
        
        ruta_idioma = os.path.join(ruta_mod, nombre_subcarpeta)
        if not os.path.isdir(ruta_idioma):
            continue
        
        # Obtener packageId del About.xml
        package_id = obtener_package_id(ruta_mod)
        if not package_id:
            print(f"ADVERTENCIA: No se encontró packageId en {mod_folder}, se omitirá en LoadFolders.xml")
        
        # Normalizar nombre de carpeta (espacios → underscores)
        nombre_normalizado = normalizar_nombre_carpeta(mod_folder)
        
        # Crear ruta destino: Mods/NombreNormalizado/Languages/SpanishLatin/
        ruta_destino_mod = os.path.join(destino_root, "Mods", nombre_normalizado, "Languages", nombre_destino)
        os.makedirs(ruta_destino_mod, exist_ok=True)
        
        # Copiar archivos
        for carpeta_raiz, _, archivos in os.walk(ruta_idioma):
            for archivo in archivos:
                if archivo.endswith(".xml"):
                    ruta_origen = os.path.join(carpeta_raiz, archivo)
                    ruta_relativa = os.path.relpath(carpeta_raiz, ruta_idioma)
                    ruta_destino_carpeta = os.path.join(ruta_destino_mod, ruta_relativa)
                    os.makedirs(ruta_destino_carpeta, exist_ok=True)
                    
                    ruta_destino_archivo = os.path.join(ruta_destino_carpeta, archivo)
                    
                    if eliminar_comentarios:
                        try:
                            parser = ET.XMLParser(target=ET.TreeBuilder(insert_comments=False))
                            with open(ruta_origen, "rb") as f:
                                raw_data = f.read()
                            
                            try:
                                content = raw_data.decode("utf-8-sig")
                            except UnicodeDecodeError:
                                content = raw_data.decode("utf-16")
                            
                            content = content.strip()
                            if content.startswith("<?xml"):
                                content = content.split("?>", 1)[-1].strip()
                            
                            content = re.sub(
                                r"<(/?(?:color|size|b|i)(?:\s+[^>]*?)?)>",
                                r"&lt;\1&gt;",
                                content,
                                flags=re.IGNORECASE,
                            )
                            
                            root = ET.fromstring(content, parser=parser)
                            tree = ET.ElementTree(root)
                            root[:] = sorted(root, key=lambda child: child.tag)
                            indent_xml(root)
                            tree.write(ruta_destino_archivo, encoding="utf-8", xml_declaration=True)
                        except Exception as e:
                            errores.append({
                                "archivo": ruta_origen,
                                "motivo": f"Error procesando XML: {e}",
                                "trace": traceback.format_exc(),
                            })
                            shutil.copy2(ruta_origen, ruta_destino_archivo)
                    else:
                        try:
                            shutil.copy2(ruta_origen, ruta_destino_archivo)
                        except Exception as e:
                            errores.append({
                                "archivo": ruta_origen,
                                "motivo": f"Error copiando archivo: {e}",
                                "trace": traceback.format_exc(),
                            })
                            continue
                    
                    archivos_copiados += 1
        
        # Guardar para LoadFolders.xml (se conserva el nombre original para el README)
        if package_id:
            mods_vanilla.append((nombre_normalizado, package_id, mod_folder))
    
    return mods_vanilla, archivos_copiados, errores


def generar_loadfolders_xml(destino_root, mods_vanilla_info):
    """
    Genera LoadFolders.xml en la raíz del pack con entradas condicionales
    mods_vanilla_info: lista de tuplas (nombre_carpeta_normalizado, packageId, ...)
    """
    if not mods_vanilla_info:
        return False, "No hay mods vanilla para generar LoadFolders.xml"
    
    ruta_loadfolders = os.path.join(destino_root, "LoadFolders.xml")
    
    # Crear estructura XML
    root = ET.Element("loadFolders")
    version_node = ET.SubElement(root, "v1.6")
    
    # Primero la carpeta Common (todo el contenido normal)
    common_li = ET.SubElement(version_node, "li")
    common_li.text = "Common"
    
    # Luego las carpetas condicionales de Mods
    for entrada in sorted(mods_vanilla_info, key=lambda x: x[0]):
        nombre_carpeta, package_id = entrada[0], entrada[1]
        mod_li = ET.SubElement(version_node, "li")
        mod_li.set("IfModActive", package_id)
        mod_li.text = f"Mods/{nombre_carpeta}"
    
    # Indentar y guardar
    indent_xml(root)
    tree = ET.ElementTree(root)
    tree.write(ruta_loadfolders, encoding="utf-8", xml_declaration=True)
    
    return True, f"LoadFolders.xml generado con {len(mods_vanilla_info)} entradas condicionales"


def reorganizar_a_common(destino_root, nombre_subcarpeta):
    """
    Mueve Languages/ a Common/Languages/ para la nueva estructura
    """
    nombre_destino = normalizar_nombre_idioma(nombre_subcarpeta)
    ruta_languages_actual = os.path.join(destino_root, "Languages")
    ruta_common = os.path.join(destino_root, "Common")
    ruta_languages_nueva = os.path.join(ruta_common, "Languages")
    
    if not os.path.isdir(ruta_languages_actual):
        return False, "No se encontró Languages/ para mover"
    
    # Si Common/ ya existe, eliminarlo primero
    if os.path.exists(ruta_common):
        shutil.rmtree(ruta_common)
    
    # Crear Common/ y mover Languages/
    os.makedirs(ruta_common, exist_ok=True)
    shutil.move(ruta_languages_actual, ruta_languages_nueva)
    return True, f"Contenido movido a Common/Languages/"


def _localizar_about_xml(destino_root):
    rutas_posibles = [
        os.path.join(destino_root, "About", "about.xml"),
        os.path.join(destino_root, "About", "About.xml"),
        os.path.join(os.path.dirname(destino_root), "About", "about.xml"),
        os.path.join(os.path.dirname(destino_root), "About", "About.xml"),
    ]

    for r in rutas_posibles:
        if os.path.isfile(r):
            return r

    return None


def actualizar_about_xml(destino_root, origen, mods_procesados):
    ruta_about = _localizar_about_xml(destino_root)

    if not ruta_about:
        return False, "No se encontro About/about.xml (o About/About.xml) para actualizar."

    tree = ET.parse(ruta_about)
    root = tree.getroot()

    force_load = root.find("forceLoadAfter")
    if force_load is None:
        force_load = ET.SubElement(root, "forceLoadAfter")

    force_load.clear()

    ids_mods = []
    for mod_name in mods_procesados:
        ruta_mod = os.path.join(origen, mod_name)
        pid = obtener_package_id(ruta_mod)

        has_published_id = False
        for p in [
            os.path.join(ruta_mod, "PublishedFileId.txt"),
            os.path.join(ruta_mod, "About", "PublishedFileId.txt"),
        ]:
            if os.path.isfile(p):
                has_published_id = True
                break

        if pid and has_published_id:
            ids_mods.append(pid)

    ids_mods = sorted(list(set(ids_mods)))

    for pid in ids_mods:
        li = ET.SubElement(force_load, "li")
        li.text = pid

    indent_xml(root)
    tree.write(ruta_about, encoding="utf-8", xml_declaration=True)

    return True, f"About.xml actualizado con {len(ids_mods)} entradas."


def _clave_mod(nombre):
    """
    Clave de comparacion para detectar el mismo mod escrito de dos formas
    (por ejemplo "Vanilla_Gravship_Expanded_-_Chapter_1" y
    "Vanilla Gravship Expanded - Chapter 1", que aparecen cuando un mod tiene
    traduccion normal y ademas un parche en 'Archivo Traducciones Vanilla').
    """
    clave = re.sub(r"[\s_]+", " ", nombre or "")
    clave = clave.replace("—", "-").replace("–", "-")
    clave = re.sub(r"\s*-\s*", " - ", clave)
    return clave.strip().casefold()


def _formatear_colaboradores(contribuidores):
    """
    Devuelve el sufijo de credito para la linea del README, o "" si no hay
    colaboradores. Los nombres con URL se enlazan.
    """
    if not contribuidores:
        return ""

    partes = []
    for nombre, url in contribuidores:
        partes.append(f"[{nombre}]({url})" if url else nombre)

    if len(partes) == 1:
        listado = partes[0]
    else:
        listado = ", ".join(partes[:-1]) + " y " + partes[-1]

    # Se usan parentesis (y no un guion largo) porque varios nombres de mod ya
    # contienen "—", p. ej. "Vanilla Animals Expanded — Waste Animals".
    return f" *(colaboración de {listado})*"


def _consolidar_mods(mods):
    """
    Normaliza la entrada de generar_readme a una lista ordenada de
    (nombre_visible, ruta_mod), eliminando duplicados entre traducciones
    normales y parches Vanilla.

    'mods' acepta strings (solo nombre) o tuplas (nombre, ruta_mod).
    Ante un duplicado se conserva el nombre mas legible (el que tiene espacios
    en vez de underscores) y la primera ruta disponible.
    """
    entradas = {}

    for item in mods:
        if isinstance(item, (tuple, list)):
            nombre = item[0] if item else ""
            ruta_mod = item[1] if len(item) > 1 else None
        else:
            nombre, ruta_mod = item, None

        nombre = (nombre or "").strip()
        if not nombre:
            continue

        clave = _clave_mod(nombre)
        previo = entradas.get(clave)

        if previo is None:
            entradas[clave] = (nombre, ruta_mod)
            continue

        nombre_previo, ruta_previa = previo
        if nombre.count("_") < nombre_previo.count("_"):
            nombre_previo = nombre
        entradas[clave] = (nombre_previo, ruta_previa or ruta_mod)

    return sorted(entradas.values(), key=lambda x: x[0].casefold())


def generar_readme(repo_root, destino_root, mods, fecha=None):
    """
    Genera/actualiza README.md en la raiz del repo con la lista total de mods
    traducidos. Se regenera en cada compilacion para que GitHub siempre
    muestre el listado actualizado.

    'mods' puede ser una lista de nombres o de tuplas (nombre, ruta_mod).
    Cuando se pasa la ruta, se lee About/Contributors.xml para acreditar a los
    colaboradores de esa traduccion.
    """
    if not mods:
        return False, "No hay mods para generar README.md"

    nombre_pack = "Traducciones RimWorld [Español Latino]"
    descripcion = ""

    ruta_about = _localizar_about_xml(destino_root)
    if ruta_about:
        try:
            root = ET.parse(ruta_about).getroot()
            name_node = root.find("name")
            if name_node is not None and name_node.text:
                nombre_pack = name_node.text.strip()
            desc_node = root.find("description")
            if desc_node is not None and desc_node.text:
                descripcion = desc_node.text.strip()
        except Exception:
            pass

    fecha = fecha or datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    mods_ordenados = _consolidar_mods(mods)

    lineas_mods = []
    total_con_colaboradores = 0
    for nombre, ruta_mod in mods_ordenados:
        contribuidores = leer_contribuidores(ruta_mod) if ruta_mod else []
        if contribuidores:
            total_con_colaboradores += 1
        lineas_mods.append(f"- {nombre}{_formatear_colaboradores(contribuidores)}")

    lineas = [f"# {nombre_pack}", ""]
    if descripcion:
        lineas.extend([descripcion, ""])
    lineas.extend([
        f"**Última compilación:** {fecha}  ",
        f"**Total de mods traducidos:** {len(mods_ordenados)}",
        "",
        "## Lista de mods traducidos",
        "",
    ])
    lineas.extend(lineas_mods)
    lineas.append("")
    lineas.append("---")
    lineas.append("*Este README se genera y actualiza automáticamente en cada compilación. No editar manualmente.*")

    ruta_readme = os.path.join(repo_root, "README.md")
    with open(ruta_readme, "w", encoding="utf-8") as f:
        f.write("\n".join(lineas) + "\n")

    detalle = f"README.md actualizado con {len(mods_ordenados)} mods en {ruta_readme}"
    if total_con_colaboradores:
        detalle += f" ({total_con_colaboradores} con colaboradores acreditados)"
    return True, detalle


def comprimir_resultado(destino_root, nombre_subcarpeta):
    destino_languages = os.path.join(destino_root, "Languages")
    nombre_destino = normalizar_nombre_idioma(nombre_subcarpeta)
    ruta_carpeta_origen = os.path.join(destino_languages, nombre_destino)

    if not os.path.isdir(ruta_carpeta_origen):
        return False, f"La carpeta a comprimir no existe: {ruta_carpeta_origen}"

    nombre_archivo_salida = os.path.join(destino_languages, nombre_destino)
    archivo_comprimido = shutil.make_archive(
        base_name=nombre_archivo_salida,
        format="tar",
        root_dir=destino_languages,
        base_dir=nombre_destino,
    )

    shutil.rmtree(ruta_carpeta_origen)

    return True, archivo_comprimido


def generar_reporte(destino_root, mods_procesados, errores=None, titulo="Reporte de Mods Procesados"):
    if not mods_procesados:
        return False, "No hay mods procesados para generar reporte."

    errores = errores or []

    ruta_reportes = os.path.join(destino_root, "Reportes")
    os.makedirs(ruta_reportes, exist_ok=True)

    nombre_archivo = "reporte_mods.txt"
    ruta_archivo = os.path.join(ruta_reportes, nombre_archivo)

    with open(ruta_archivo, "w", encoding="utf-8") as f:
        f.write(f"{titulo} - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write("=" * 50 + "\n\n")
        f.write(f"Total de mods encontrados: {len(mods_procesados)}\n\n")
        f.write("Lista de mods:\n")
        for mod in sorted(mods_procesados):
            f.write(f"- {mod}\n")

        if errores:
            f.write("\n" + "=" * 50 + "\n")
            f.write("Errores de compilacion:\n\n")
            for idx, err in enumerate(errores, start=1):
                f.write(f"{idx}. Archivo: {err.get('archivo', 'N/A')}\n")
                f.write(f"   Motivo: {err.get('motivo', 'N/A')}\n")
                f.write("   Trace:\n")
                f.write(err.get("trace", "") + "\n")

    return True, f"Reporte generado en: {ruta_archivo}"


def generar_reporte_errores(destino_root, errores):
    if not errores:
        return False, "No hay errores para generar reporte."

    ruta_reportes = os.path.join(destino_root, "Reportes")
    os.makedirs(ruta_reportes, exist_ok=True)

    nombre_archivo = "errores_compilacion.txt"
    ruta_archivo = os.path.join(ruta_reportes, nombre_archivo)

    with open(ruta_archivo, "w", encoding="utf-8") as f:
        f.write(f"Errores de compilacion - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write("=" * 50 + "\n\n")
        for idx, err in enumerate(errores, start=1):
            f.write(f"{idx}. Archivo: {err.get('archivo', 'N/A')}\n")
            f.write(f"   Motivo: {err.get('motivo', 'N/A')}\n")
            f.write("   Trace:\n")
            f.write(err.get("trace", "") + "\n")

    return True, f"Reporte de errores generado en: {ruta_archivo}"


def main():
    parser = argparse.ArgumentParser(description="Compilador CLI de traducciones RimWorld")
    parser.add_argument("--origen", required=True, help="Ruta a 'Archivo Traducciones'")
    parser.add_argument("--destino", required=True, help="Ruta a la carpeta del pack de traducciones")
    parser.add_argument("--idioma", default="", help="Nombre exacto de la carpeta de idioma a procesar")
    parser.add_argument("--limpiar-destino", action="store_true", help="Elimina la carpeta de idioma antes de copiar")
    parser.add_argument("--eliminar-comentarios", action="store_true", help="Elimina comentarios XML y ordena tags")
    parser.add_argument("--comprimir", action="store_true", help="Comprime la carpeta resultante en .tar")
    parser.add_argument("--update-about", action="store_true", help="Actualiza About/about.xml con forceLoadAfter")
    parser.add_argument("--reporte", action="store_true", help="Genera un reporte de mods compilados (default)")
    parser.add_argument("--sin-reporte", action="store_true", help="No generar reporte de mods compilados")
    parser.add_argument("--reporte-titulo", default="Reporte de Mods Procesados", help="Titulo del reporte")
    parser.add_argument("--sin-readme", action="store_true", help="No actualizar README.md con la lista total de mods")
    parser.add_argument("--git", action="store_true", help="Genera release notes y hace commit+tag automaticamente")

    args = parser.parse_args()

    origen = args.origen
    destino = args.destino

    if not os.path.isdir(origen):
        print(f"Origen no valido: {origen}")
        return 2

    if not os.path.isdir(destino):
        print(f"Destino no valido: {destino}")
        return 2

    idioma = args.idioma.strip()
    if not idioma:
        idiomas = detectar_idiomas(origen)
        if len(idiomas) == 1:
            idioma = idiomas[0]
        else:
            print("No se especifico idioma y se encontraron multiples opciones:")
            for item in idiomas:
                print(f"- {item}")
            return 2

    # Limpiar destino si se especifica (excepto About/ y Reportes/)
    if args.limpiar_destino:
        carpetas_a_eliminar = ["Languages", "Common", "Mods"]
        archivos_a_eliminar = ["LoadFolders.xml"]
        
        for carpeta in carpetas_a_eliminar:
            ruta_carpeta = os.path.join(destino, carpeta)
            if os.path.isdir(ruta_carpeta):
                print(f"Limpiando: {carpeta}/")
                shutil.rmtree(ruta_carpeta)
        
        for archivo in archivos_a_eliminar:
            ruta_archivo = os.path.join(destino, archivo)
            if os.path.isfile(ruta_archivo):
                print(f"Eliminando: {archivo}")
                os.remove(ruta_archivo)

    # Procesar traducciones normales (Archivo Traducciones)
    print(f"\n[1/4] Procesando traducciones normales desde: {origen}")
    mods_procesados, archivos_copiados, errores = copiar_traducciones(
        origen,
        destino,
        idioma,
        limpiar_destino=args.limpiar_destino,
        eliminar_comentarios=args.eliminar_comentarios,
    )

    print(f"  → Mods procesados: {len(mods_procesados)}")
    print(f"  → Archivos copiados: {archivos_copiados}")
    if errores:
        print(f"  → Errores detectados: {len(errores)}")

    # Detectar y procesar Archivo Traducciones Vanilla
    origen_vanilla = os.path.join(os.path.dirname(origen), "Archivo Traducciones Vanilla")
    mods_vanilla_info = []
    archivos_vanilla_copiados = 0
    
    if os.path.isdir(origen_vanilla):
        print(f"\n[2/4] Procesando parches Vanilla desde: {origen_vanilla}")
        mods_vanilla_info, archivos_vanilla_copiados, errores_vanilla = copiar_vanilla_patches(
            origen_vanilla,
            destino,
            idioma,
            eliminar_comentarios=args.eliminar_comentarios,
        )
        
        print(f"  → Mods Vanilla procesados: {len(mods_vanilla_info)}")
        print(f"  → Archivos copiados: {archivos_vanilla_copiados}")
        if errores_vanilla:
            print(f"  → Errores detectados: {len(errores_vanilla)}")
            errores.extend(errores_vanilla)
    else:
        print(f"\n[2/4] No se encontró carpeta 'Archivo Traducciones Vanilla', omitiendo parches Vanilla")

    # Reorganizar a estructura Common/
    print(f"\n[3/4] Reorganizando estructura a Common/")
    ok_common, msg_common = reorganizar_a_common(destino, idioma)
    print(f"  → {msg_common}")

    # Generar LoadFolders.xml si hay mods vanilla
    if mods_vanilla_info:
        print(f"\n[4/4] Generando LoadFolders.xml")
        ok_lf, msg_lf = generar_loadfolders_xml(destino, mods_vanilla_info)
        print(f"  → {msg_lf}")
    else:
        print(f"\n[4/4] No hay mods Vanilla, omitiendo LoadFolders.xml")

    # Resumen final
    total_archivos = archivos_copiados + archivos_vanilla_copiados
    print(f"\n{'='*60}")
    print(f"RESUMEN:")
    print(f"  Total mods normales: {len(mods_procesados)}")
    print(f"  Total mods Vanilla: {len(mods_vanilla_info)}")
    print(f"  Total archivos copiados: {total_archivos}")
    print(f"  Errores: {len(errores)}")
    print(f"{'='*60}\n")

    if total_archivos == 0:
        print("No se encontraron archivos XML para copiar.")
        return 1

    if args.update_about:
        ok, mensaje = actualizar_about_xml(destino, origen, mods_procesados)
        if ok:
            print(mensaje)
        else:
            print(f"ADVERTENCIA: {mensaje}")

    if args.comprimir:
        ok, mensaje = comprimir_resultado(destino, idioma)
        print(mensaje)
        if not ok:
            return 1

    # Combinar mods normales y vanilla para el reporte y el README.
    # Se usa el nombre original de carpeta (con espacios), no el normalizado con
    # underscores que va a Mods/, para no duplicar entradas en el README.
    mods_info = [(nombre, os.path.join(origen, nombre)) for nombre in mods_procesados]
    mods_info += [
        (entrada[2] if len(entrada) > 2 else entrada[0],
         os.path.join(origen_vanilla, entrada[2] if len(entrada) > 2 else entrada[0]))
        for entrada in mods_vanilla_info
    ]
    todos_los_mods = [nombre for nombre, _ in mods_info]

    if not args.sin_reporte:
        ok, mensaje = generar_reporte(destino, todos_los_mods, errores=errores, titulo=args.reporte_titulo)
        print(mensaje)
        if not ok:
            return 1

        if errores:
            ok_err, mensaje_err = generar_reporte_errores(destino, errores)
            print(mensaje_err)
            if not ok_err:
                return 1
        else:
            ruta_errores = os.path.join(destino, "Reportes", "errores_compilacion.txt")
            if os.path.isfile(ruta_errores):
                os.remove(ruta_errores)

    if not args.sin_readme:
        repo_root_readme = get_repo_root(os.getcwd())
        if repo_root_readme:
            ok_readme, msg_readme = generar_readme(repo_root_readme, destino, mods_info)
            print(msg_readme)
        else:
            print("ADVERTENCIA: No se detecto repositorio git, omitiendo actualizacion de README.md")

    if args.git:
        repo_root = get_repo_root(os.getcwd())
        if not repo_root:
            print("ADVERTENCIA: No se detecto repositorio git, omitiendo git/release notes")
            print(f"Finalizado: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            return 0

        nuevo_tag = bump_tag(get_last_tag(repo_root))
        ok_notes, msg_notes = generar_release_notes(repo_root, nuevo_tag)
        print(msg_notes)
        if not ok_notes:
            return 1

        ok_git, msg_git = git_commit_and_tag(repo_root, nuevo_tag)
        print(msg_git)
        if not ok_git:
            return 1

    print(f"Finalizado: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
