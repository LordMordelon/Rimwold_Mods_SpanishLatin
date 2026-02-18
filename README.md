# Rimwold Mods Español Latino

Paquete de traducciones al español latino para mods de RimWorld.

## Contribuciones / ¿Como ayudar?

Lo mas rapido es informar errores, terminos o elementos que no se entiendan; tambien descripciones o nombres de historia que resulten raros o vagos, o que necesiten un poco mas de contexto. Se agradecen sugerencias.

Explico cómo trabajo actualmente: mientras juego, uso el mod Extract Translation. Si veo algo que me gusta, lo uso. Extract Translation genera una carpeta "SpanishLatin (Español (Latinoamérica))" dentro del mod, que traduzco por completo con el asistente de Gemini, dándole indicaciones sobre términos y preferencias para adecuar algunas cosas.

Luego pruebo la traducción para ver qué tal va mientras ajusto irregularidades y detalles. Una vez revisado el mod, lo muevo de la carpeta de Steam Workshop a la carpeta de Archivo Traducciones. Acumulo algunos otros mods y uso el archivo compilador.py de la carpeta de Programas: lo ejecuto para meter todas las traducciones dentro de una carpeta SpanishLatin, que es con la que actualizo el mod.

Requisitos para usar compilador.py (GUI):
- Python 3 instalado.
- Paquete PySide6 instalado (para la interfaz gráfica).

Flujo general de trabajo:
1. Traduzco mods y los guardo en Archivo Traducciones (cada mod con su carpeta de idioma).
2. Compilo todas las traducciones en el pack final (carpeta SpanishLatin dentro de Languages).
3. Actualizo About/About.xml con la lista de dependencias.

Herramientas:
- compilador.py (GUI): uso local con interfaz.
- cli_compilador.py (CLI): uso automatizado sin interfaz, genera reportes de mods y errores.
	- Modo `--git`: genera release notes y crea commit/tag automaticamente.

Automatizacion:
- GitHub Actions ejecuta el CLI en cada push a main.
- Se publica una pre-release (beta) con el pack completo.

## Glosario (por añadir)
- chemfuel > quimbustible
- astrofuel > astrobustible
- ghoul > necrófago