import flet as ft
from PIL import Image, ImageDraw, ImageFont
import os

# ============================================================
# Configuración
# ============================================================
ANCHO = 1080
ALTO = 1080
CARPETA_SALIDA = "texto_imagenes"

# Fuente por defecto (en Android, DejaVuSans suele estar disponible)
RUTA_FUENTE_DEFAULT = "DejaVuSans.ttf"


def cargar_fuente(ruta, tam):
    """Carga una fuente TrueType, con fallback si falla."""
    try:
        if ruta and os.path.exists(ruta):
            return ImageFont.truetype(ruta, tam)
        return ImageFont.truetype(RUTA_FUENTE_DEFAULT, tam)
    except Exception:
        try:
            return ImageFont.truetype("arial.ttf", tam)
        except Exception:
            return ImageFont.load_default()


def generar_imagen_texto(texto, ancho, alto, tam_fuente, color_texto, color_fondo):
    """
    Lógica de Pillow (idéntica a la del escritorio).
    Devuelve la ruta donde se guardó la imagen.
    """
    # Crear imagen de fondo
    img = Image.new("RGB", (ancho, alto), color_fondo)
    draw = ImageDraw.Draw(img)

    # Cargar fuente
    fuente = cargar_fuente(None, tam_fuente)

    # Partir texto en líneas (ajuste simple por ancho)
    max_ancho = int(ancho * 0.85)
    lineas = []
    for parrafo in texto.split("\n"):
        palabras = parrafo.split(" ")
        linea_actual = ""
        for palabra in palabras:
            prueba = (linea_actual + " " + palabra).strip() if linea_actual else palabra
            try:
                bbox = draw.textbbox((0, 0), prueba, font=fuente)
                ancho_texto = bbox[2] - bbox[0]
            except Exception:
                ancho_texto = len(prueba) * tam_fuente * 0.6

            if ancho_texto <= max_ancho or not linea_actual:
                linea_actual = prueba
            else:
                if linea_actual:
                    lineas.append(linea_actual)
                linea_actual = palabra
        if linea_actual:
            lineas.append(linea_actual)

    # Calcular altura total
    interlineado = int(tam_fuente * 0.3)
    alturas = []
    for linea in lineas:
        try:
            bbox = draw.textbbox((0, 0), linea if linea else "Ay", font=fuente)
            alturas.append(bbox[3] - bbox[1])
        except Exception:
            alturas.append(tam_fuente)

    altura_total = sum(alturas) + interlineado * (len(lineas) - 1) if lineas else 0

    # Posición vertical centrada
    y = int((alto - altura_total) / 2)

    # Dibujar cada línea
    cur_y = y
    for i, linea in enumerate(lineas):
        if not linea:
            cur_y += alturas[i] + interlineado
            continue

        # Centrar horizontalmente
        try:
            bbox = draw.textbbox((0, 0), linea, font=fuente)
            ancho_linea = bbox[2] - bbox[0]
        except Exception:
            ancho_linea = len(linea) * tam_fuente * 0.6

        x = int((ancho - ancho_linea) / 2)
        draw.text((x, cur_y), linea, font=fuente, fill=color_texto)
        cur_y += alturas[i] + interlineado

    # Guardar
    os.makedirs(CARPETA_SALIDA, exist_ok=True)
    ruta_salida = os.path.join(CARPETA_SALIDA, "imagen_texto.jpg")
    img.save(ruta_salida, "JPEG", quality=95)
    return ruta_salida


# ============================================================
# App Flet
# ============================================================
def main(page: ft.Page):
    page.title = "Generador de Imagen"
    page.scroll = ft.ScrollMode.ADAPTIVE
    page.padding = 20

    # --- Función de anuncio para TalkBack ---
    async def hablar(texto: str):
        """
        Envía un anuncio al servicio de accesibilidad del sistema.
        TalkBack lo leerá en voz alta si está activado.
        """
        try:
            await page.semantics_service.announce_message(texto)
        except Exception:
            # Si falla (ej: en escritorio sin TalkBack), no rompe la app
            pass

    # --- Campo de texto multilínea ---
    campo_texto = ft.TextField(
        label="Texto a generar (multilínea)",
        multiline=True,
        min_lines=4,
        max_lines=8,
        autofocus=True,
        border_color=ft.Colors.BLUE_400,
    )

    # --- Controles de tamaño de fuente ---
    slider_fuente = ft.Slider(
        min=20,
        max=200,
        value=80,
        divisions=18,
        label="Tamaño: {value}",
    )

    # --- Color del texto ---
    dropdown_color_texto = ft.Dropdown(
        label="Color del texto",
        value="Blanco",
        options=[
            ft.dropdown.Option("Blanco", text="Blanco"),
            ft.dropdown.Option("Negro", text="Negro"),
            ft.dropdown.Option("Rojo", text="Rojo"),
            ft.dropdown.Option("Amarillo", text="Amarillo"),
        ],
    )

    # --- Color del fondo ---
    dropdown_color_fondo = ft.Dropdown(
        label="Color del fondo",
        value="Negro",
        options=[
            ft.dropdown.Option("Negro", text="Negro"),
            ft.dropdown.Option("Blanco", text="Blanco"),
            ft.dropdown.Option("Azul marino", text="Azul marino"),
            ft.dropdown.Option("Gris oscuro", text="Gris oscuro"),
        ],
    )

    # Mapeo de nombres a colores RGB
    COLORES = {
        "Blanco": (255, 255, 255),
        "Negro": (0, 0, 0),
        "Rojo": (255, 0, 0),
        "Amarillo": (255, 255, 0),
        "Azul marino": (0, 0, 128),
        "Gris oscuro": (80, 80, 80),
    }

    # --- Estado de la última imagen generada ---
    ultima_imagen = {"ruta": None}

    # --- Botón de generar ---
    async def on_generar(e):
        texto = campo_texto.value
        if not texto or not texto.strip():
            await hablar("Ingresá un texto primero")
            return

        await hablar("Generando imagen, por favor esperá")

        # Leer controles
        tam_fuente = int(slider_fuente.value)
        nombre_color_texto = dropdown_color_texto.value
        nombre_color_fondo = dropdown_color_fondo.value
        color_texto = COLORES.get(nombre_color_texto, (255, 255, 255))
        color_fondo = COLORES.get(nombre_color_fondo, (0, 0, 0))

        # Generar (esto es síncrono pero rápido para 1080x1080)
        try:
            ruta = generar_imagen_texto(
                texto=texto,
                ancho=ANCHO,
                alto=ALTO,
                tam_fuente=tam_fuente,
                color_texto=color_texto,
                color_fondo=color_fondo,
            )
            ultima_imagen["ruta"] = ruta
            await hablar(f"Imagen guardada en {ruta}")
        except Exception as ex:
            await hablar(f"Error al generar: {ex}")

    btn_generar = ft.ElevatedButton(
        content="Generar imagen",
        on_click=on_generar,
        height=50,
    )

    # --- Botón de describir última imagen ---
    async def on_describir(e):
        ruta = ultima_imagen.get("ruta")
        if ruta and os.path.exists(ruta):
            await hablar(f"La última imagen está en {ruta}")
        else:
            await hablar("Todavía no generaste ninguna imagen")

    btn_describir = ft.OutlinedButton(
        content="¿Dónde está la última imagen?",
        on_click=on_describir,
    )

    # --- Anunciar al cambiar el slider (accesibilidad) ---
    async def on_slider_change(e):
        await hablar(f"Tamaño de fuente: {int(slider_fuente.value)}")

    slider_fuente.on_change = on_slider_change

    # --- Layout ---
    page.add(
        ft.Text(
            "Generador de Imagen con Texto",
            size=24,
            weight=ft.FontWeight.BOLD,
        ),
        ft.Text(
            "Escribí tu texto, elegí opciones y generá la imagen.",
            size=14,
            italic=True,
        ),
        ft.Divider(),
        campo_texto,
        ft.Text("Tamaño de fuente:", weight=ft.FontWeight.BOLD),
        slider_fuente,
        dropdown_color_texto,
        dropdown_color_fondo,
        ft.Divider(),
        btn_generar,
        btn_describir,
    )


if __name__ == "__main__":
    ft.run(main)
