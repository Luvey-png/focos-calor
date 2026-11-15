# Guía paso a paso

Esta guía explica cómo subir los cambios de la rama `armonizacion-sensores`, cómo
activar el asistente de IA y cómo probar todo antes de la demo. Seguí los pasos en
orden y no saltees ninguno.

> **Antes de empezar:** los comandos se escriben en una terminal (PowerShell,
> Git Bash o la terminal de VS Code), **dentro de la carpeta del proyecto**
> `focos-calor`. Para abrirla en VS Code: *Archivo → Abrir carpeta → focos-calor*,
> y después *Terminal → Nueva terminal*.

---

## Parte 1: Subir la rama a GitHub

La rama `armonizacion-sensores` tiene los cambios de la armonización, el asistente
y la documentación. Primero hay que subirla a GitHub y después unirla a `main`.

### Paso 1. Verificar en qué rama estás

```
git branch
```

La rama actual aparece con un asterisco (`*`). Tiene que decir
`* armonizacion-sensores`. Si no, cambiate a esa rama:

```
git checkout armonizacion-sensores
```

### Paso 2. Ver qué commits tiene la rama

```
git log --oneline -4
```

Arriba de todo tienen que aparecer estos tres commits:

```
Asistente de IA y respaldo NOAA-20/21 en la armonización
Documentación de la armonización entre satélites
Armonización de la serie entre satélites (equivalente VIIRS S-NPP)
```

### Paso 3. Revisar si hay archivos modificados

```
git status
```

Si aparecen archivos como `modified: data/oni.txt` o `modified: graficos.py`
**sin que nadie los haya tocado**, son solo diferencias en los finales de línea
(Windows guarda los saltos de línea distinto que Linux). **No los agregues ni los
commitees.** No afectan a la subida.

### Paso 4. Subir la rama

```
git push -u origin armonizacion-sensores
```

- La primera vez puede abrirse una ventana para iniciar sesión en GitHub. Iniciá
  sesión con tu cuenta.
- Si dice `Permission denied` o `403`, tu cuenta no tiene permiso en el repo. El
  dueño del repo (`Luvey-png`) tiene que agregarte como colaborador: *Settings →
  Collaborators → Add people*. Después repetí este paso.
- Si funcionó, al final aparece algo como
  `branch 'armonizacion-sensores' set up to track 'origin/armonizacion-sensores'`.

### Paso 5. Abrir un Pull Request

Un *Pull Request* (PR) es un pedido para unir los cambios de una rama a `main`,
para que el equipo los revise antes.

1. Entrá a <https://github.com/Luvey-png/focos-calor>.
2. Arriba va a aparecer un aviso amarillo con el botón **"Compare & pull
   request"**. Hacé clic.
   - Si no aparece: pestaña **Pull requests → New pull request**, y elegí
     `base: main` ← `compare: armonizacion-sensores`.
3. En el título poné: `Armonización entre satélites y asistente de IA`.
4. En la descripción podés pegar:
   ```
   - Pestaña "Armonización": serie en escala equivalente VIIRS S-NPP, con validación.
   - Pestaña "Asistente IA": preguntas en lenguaje simple con los datos de la app.
   - Documentación en docs/.
   Ver docs/armonizacion.md y docs/asistente.md.
   ```
5. Hacé clic en **"Create pull request"**.

### Paso 6. Unir la rama a `main`

Cuando alguien del equipo haya revisado el PR:

1. En la página del PR, hacé clic en **"Merge pull request"** y después en
   **"Confirm merge"**.
2. En tu computadora, volvé a `main` y bajá los cambios:
   ```
   git checkout main
   git pull
   ```

> Si GitHub dice **"This branch has conflicts"**, alguien cambió los mismos
> archivos en `main`. **No hagas merge todavía.** Pedile ayuda a quien haya hecho
> esos cambios para resolverlo juntos.

---

## Parte 2: Activar el asistente de IA

Sin una clave, el asistente funciona en "modo sin IA" (muestra un resumen
automático). Para que responda preguntas hace falta una **clave de API**. Esta
guía usa **Gemini** porque tiene un plan gratuito.

### Paso 7. Conseguir la clave de Gemini

1. Entrá a <https://aistudio.google.com> con una cuenta de Google.
2. Buscá la opción **"Get API key"** (o "Obtener clave de API").
3. Hacé clic en **"Create API key"** y copiá la clave.

> **La clave es como una contraseña.** No la pegues en el chat del equipo, en el
> código ni en GitHub. Si se publica por error, borrala desde la misma página y
> creá otra.

> Las pantallas de Google pueden cambiar. Si no encontrás el botón, buscá
> "Google AI Studio API key" en internet.

### Paso 8. Crear el archivo de secretos

1. En la carpeta `.streamlit` del proyecto hay un archivo llamado
   `secrets.toml.example`.
2. Hacé una copia en la misma carpeta y llamala **`secrets.toml`** (sin el
   `.example`).
   - En VS Code: clic derecho sobre el archivo → *Copiar*, clic derecho en la
     carpeta → *Pegar*, y después clic derecho → *Cambiar nombre*.
3. Abrí `secrets.toml` y dejalo así, con tu clave entre comillas:
   ```toml
   IA_PROVEEDOR = "gemini"
   IA_API_KEY = "acá-va-tu-clave"
   ```
4. Guardá el archivo.

`secrets.toml` ya está en `.gitignore`, así que **git no lo sube**. Para
comprobarlo, corré `git status`: **no** tiene que aparecer en la lista. Si
aparece, no hagas commit y avisale al equipo.

### Paso 9. Correr la app en tu computadora

Si es la primera vez, creá un entorno virtual e instalá las dependencias:

```
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
```

> En Mac o Linux, el segundo comando es `source venv/bin/activate`.

Para abrir la app:

```
streamlit run app.py
```

Se abre el navegador en `http://localhost:8501`. La próxima vez solo hace falta
`venv\Scripts\activate` y `streamlit run app.py`.

### Paso 10. Probar el asistente

1. Abrí la pestaña **"Asistente IA"**.
2. El aviso amarillo de "Modo sin IA" **ya no tiene que aparecer**. Si sigue,
   revisá el Paso 8 (nombre del archivo, comillas y que esté dentro de
   `.streamlit`) y reiniciá la app (`Ctrl + C` en la terminal y de nuevo
   `streamlit run app.py`).
3. Hacé clic en una pregunta de ejemplo. Debería aparecer una respuesta en unos
   segundos.
4. Probá el botón **"Informe semanal para brigadas"**.
5. Abrí **"Ver los datos que usa el asistente"** y comprobá que las cifras de la
   respuesta coincidan con esos datos.

---

## Parte 3: Publicar en Streamlit Cloud (si la app está publicada)

El archivo `secrets.toml` **no se sube** a GitHub, así que en la nube la clave se
carga aparte.

### Paso 11. Cargar la clave en Streamlit Cloud

1. Entrá a <https://share.streamlit.io> y buscá la app.
2. Hacé clic en los tres puntos (**⋮**) → **Settings → Secrets**.
3. Pegá lo mismo que en el Paso 8:
   ```toml
   IA_PROVEEDOR = "gemini"
   IA_API_KEY = "acá-va-tu-clave"
   ```
4. Hacé clic en **Save**. La app se reinicia sola.

### Paso 12. Verificar qué rama publica la app

Streamlit Cloud publica una rama en particular, normalmente `main`. Los cambios
van a aparecer recién después del Paso 6 (merge a `main`). Para ver o cambiar la
rama: **⋮ → Settings → General**.

---

## Problemas comunes

| Qué pasa | Qué hacer |
|---|---|
| `git push` dice `rejected` o `fetch first` | Alguien subió cambios a la misma rama. Corré `git pull` y después de nuevo `git push`. |
| `git` dice `index.lock: File exists` | Cerrá VS Code y cualquier otra terminal que esté usando git, borrá el archivo `.git/index.lock` y repetí el comando. |
| El asistente dice "No se pudo consultar al modelo" | La clave está mal copiada, el modelo cambió de nombre o no hay internet. Revisá la clave y probá agregar en `secrets.toml` la línea `IA_MODELO = "gemini-2.5-flash"` u otro modelo disponible en AI Studio. |
| La pestaña "Armonización" tarda en abrir | La primera vez calcula todo (unos segundos). Después queda guardado en caché. |
| `ModuleNotFoundError` al correr la app | Falta activar el entorno virtual (`venv\Scripts\activate`) o instalar las dependencias (`pip install -r requirements.txt`). |
| Aparecen archivos modificados que nadie tocó | Son finales de línea de Windows. No los commitees. |

---

## Lista final antes de la demo

- [ ] La rama está subida y unida a `main` (Partes 1 y 3).
- [ ] La app abre sin errores.
- [ ] El asistente responde con la clave real.
- [ ] Las pestañas "Armonización" y "Asistente IA" se ven bien.
- [ ] La clave **no** está en GitHub.
- [ ] En la entrega a Space Apps se declara el uso de IA (ver la sección final de
      `docs/asistente.md`).
