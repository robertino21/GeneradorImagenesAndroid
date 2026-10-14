import asyncio
import flet as ft
from PIL import Image, ImageDraw, ImageFont
import os

# ============================================================
# Configuración
# ============================================================
ANCHO = 1080
ALTO = 1080
CARPETA_SALIDA = "texto_imagenes"
RUTA_FUENTE_DEFAULT = "DejaVuSans.ttf"


def cargar_fuente(ruta, tam):
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
    img = Image.new("RGB", (ancho, alto), color_fondo)
    draw = ImageDraw.Draw(img)
    fuente = cargar_fuente(None, tam_fuente)

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

    interlineado = int(tam_fuente * 0.3)
    alturas = []
    for linea in lineas:
        try:
            bbox = draw.textbbox((0, 0), linea if linea else "Ay", font=fuente)
            alturas.append(bbox[3] - bbox[1])
        except Exception:
            alturas.append(tam_fuente)

    altura_total = sum(alturas) + interlineado * (len(lineas) - 1) if lineas else 0
    y = int((alto - altura_total) / 2)

    cur_y = y
    for i, linea in enumerate(lineas):
        if not linea:
            cur_y += alturas[i] + interlineado
            continue
        try:
            bbox = draw.textbbox((0, 0), linea, font=fuente)
            ancho_linea = bbox[2] - bbox[0]
        except Exception:
            ancho_linea = len(linea) * tam_fuente * 0.6
        x = int((ancho - ancho_linea) / 2)
        draw.text((x, cur_y), linea, font=fuente, fill=color_texto)
        cur_y += alturas[i] + interlineado

    os.makedirs(CARPETA_SALIDA, exist_ok=True)
    ruta_salida = os.path.join(CARPETA_SALIDA, "imagen_texto.jpg")
    img.save(ruta_salida, "JPEG", quality=95)
    return ruta_salida


# ============================================================
# Aplicación Flet
# ============================================================
def main(page: ft.Page):
    page.title = "Generador de Imagen"
    page.scroll = ft.ScrollMode.ADAPTIVE
    page.padding = 20

    async def hablar(texto: str):
        # ⚠️ Cambio importante: announce_tooltip en lugar de announce_message
        try:
            await page.semantics_service.announce_tooltip(texto)
        except Exception:
            pass

    campo_texto = ft.TextField(
        label="Texto a generar (multilínea)",
        multiline=True,
        min_lines=4,
        max_lines=8,
        autofocus=True,
        border_color=ft.Colors.BLUE_400,
    )

    slider_fuente = ft.Slider(
        min=20, max=200, value=80, divisions=18, label="Tamaño: {value}",
    )

    dropdown_color_texto = ft.Dropdown(
        label="Color del texto",
        value="Blanco",
        options=[
            ft.dropdown.Option("Blanco"),
            ft.dropdown.Option("Negro"),
            ft.dropdown.Option("Rojo"),
            ft.dropdown.Option("Amarillo"),
        ],
    )

    dropdown_color_fondo = ft.Dropdown(
        label="Color del fondo",
        value="Negro",
        options=[
            ft.dropdown.Option("Negro"),
            ft.dropdown.Option("Blanco"),
            ft.dropdown.Option("Azul marino"),
            ft.dropdown.Option("Gris oscuro"),
        ],
    )

    COLORES = {
        "Blanco": (255, 255, 255),
        "Negro": (0, 0, 0),
        "Rojo": (255, 0, 0),
        "Amarillo": (255, 255, 0),
        "Azul marino": (0, 0, 128),
        "Gris oscuro": (80, 80, 80),
    }

    ultima_imagen = {"ruta": None}

    async def on_generar(e):
        texto = campo_texto.value
        if not texto or not texto.strip():
            await hablar("Ingresa un texto primero")
            return

        await hablar("Generando imagen, por favor espera")

        tam_fuente = int(slider_fuente.value)
        color_texto = COLORES.get(dropdown_color_texto.value, (255, 255, 255))
        color_fondo = COLORES.get(dropdown_color_fondo.value, (0, 0, 0))

        try:
            ruta = await asyncio.to_thread(
                generar_imagen_texto,
                texto=texto, ancho=ANCHO, alto=ALTO,
                tam_fuente=tam_fuente,
                color_texto=color_texto, color_fondo=color_fondo,
            )
            ultima_imagen["ruta"] = ruta
            await hablar("Imagen guardada correctamente")
        except Exception as ex:
            await hablar("Error al generar la imagen")

    btn_generar = ft.Button(
        content="Generar imagen",
        on_click=on_generar,
        height=50,
    )

    async def on_describir(e):
        ruta = ultima_imagen.get("ruta")
        if ruta and os.path.exists(ruta):
            await hablar(f"La última imagen se encuentra en {ruta}")
        else:
            await hablar("Aún no has generado ninguna imagen")

    btn_describir = ft.Button(
        content="¿Dónde está la última imagen?",
        on_click=on_describir,
    )

    async def on_slider_change(e):
        await hablar(f"Tamaño de fuente: {int(slider_fuente.value)}")

    slider_fuente.on_change = on_slider_change

    page.add(
        ft.Text("Generador de Imagen con Texto", size=24, weight=ft.FontWeight.BOLD),
        ft.Text("Escribe tu texto, elige las opciones y genera la imagen.", size=14, italic=True),
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
