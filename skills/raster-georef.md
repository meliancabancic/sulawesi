# SKILL: raster-georef

## Activación
Trigger: "extraé figura", "georreferenciá", "ImageStatic", "rasterio", "samplear TIF",
"CPD raster", "slice tomográfico", "PyMuPDF", "calibrar", "recortar figura".

---

## Directorios relevantes

```
mapa/
  fuentes/
    sulawesi_bouguer_completa.tif    ← WGM2012 Bouguer (rasterio)
    sulawesi_freeair_recortada.tif   ← WGM2012 Free-air (rasterio)
    height_anomaly.png               ← geoide EIGEN-6C4
    grav_bouguer.png / grav_freeair.png ← previews PNG
  data/
    georef_extents.json              ← extents calibrados (fuente de verdad)
    sections/                        ← figuras extraídas de papers + slices raster
      {paper_id}/
        {paper_id}_fig{N}_map.png    ← mapa de referencia para calibración
        slice_{depth}km.png          ← slices tomográficos individuales
```

---

## 1. Diagnóstico previo: tipo de figura de journal

Antes de extraer, identificar el layout de la figura en el PDF:

| Tipo | Descripción | Estrategia de crop |
|---|---|---|
| **Single panel** | Un mapa que ocupa la figura completa | Renderizar página + crop limpio |
| **Multi-panel columnas** | Panel izq = mapa (A), paneles der apilados (B, C) | Crop mitad izquierda: `(0, 0, w//2, h)` |
| **Multi-panel grilla 2×2** | Paneles A, B, C, D en grilla | Crop cuadrante: `(0, 0, w//2, h//2)` para panel A |
| **Multi-panel grilla 3×3** | 9 slices de profundidad | Crop por celda: `(col*pw, row*ph, (col+1)*pw, (row+1)*ph)` |
| **Figura con texto de página** | Map + caption + body text | Renderizar a DPI, crop manual por coordenadas pixel |

**Regla**: ver siempre el thumbnail del layout antes de extraer.

---

## 2. Extraer figuras con PyMuPDF

### Caso A — imagen embebida de alta resolución (preferido)
```python
import fitz, io
from PIL import Image

doc = fitz.open(pdf_path)
page = doc[page_num]  # 0-indexed
imgs = page.get_images(full=True)
# Seleccionar la imagen más grande de la página
main = sorted(imgs, key=lambda x: x[2]*x[3], reverse=True)[0]
img_data = doc.extract_image(main[0])
pil = Image.open(io.BytesIO(img_data['image']))
print(f'{pil.size}')  # verificar dimensiones antes de recortar
```

### Caso B — figura vectorial o multi-elemento (renderizar página)
```python
mat = fitz.Matrix(200/72, 200/72)  # 200 DPI (texto legible)
pix = page.get_pixmap(matrix=mat, alpha=False)
pil = Image.open(io.BytesIO(pix.tobytes()))
# Para thumbnail de diagnóstico: usar 50/72
```

### Thumbnail para diagnóstico de layout
```python
mat_thumb = fitz.Matrix(50/72, 50/72)
pix_thumb = page.get_pixmap(matrix=mat_thumb, alpha=False)
pix_thumb.save('thumb_p{}.png'.format(page_num+1))
# Leer con Read tool para ver el layout antes de decidir el crop
```

---

## 3. Recortes por tipo de layout

```python
from PIL import Image

# Multi-panel columnas: panel izquierdo (A)
pil = Image.open('full_figure.png')
w, h = pil.size
panel_a = pil.crop((0, 0, w//2, h))

# Grilla 2×2: cuadrante top-left (A)
panel_a = pil.crop((0, 0, w//2, h//2))

# Grilla 3×3: extraer los 9 slices
depths = [10, 20, 40, 60, 80, 100, 120, 150, 200]
pw, ph = w//3, h//3
for i, depth in enumerate(depths):
    row, col = i//3, i%3
    crop = pil.crop((col*pw, row*ph, (col+1)*pw, (row+1)*ph))
    crop.save(f'slice_{depth:03d}km.png')

# Página renderizada: crop manual (ajustar por visualización del thumbnail)
# top: fijar debajo del header de revista + título figura
# bottom: fijar encima del caption "Figure N."
# Ejemplo Di Leo 2012 p3 a 200 DPI (1694x2192):
crop = pil.crop((28, 215, 1668, 845))  # mapa sin header ni caption
```

**Remover siempre**: header de revista, DOI, caption de figura, panel labels (a)(b).
Si el panel incluye leyenda lateral: dejar — es parte del contexto cartográfico.

---

## 4. Sistema de georef interactivo en el mapa

El frontend tiene un sistema de calibración de capas de referencia con teclado.

### Estructura
- Cada paper tiene una capa `refXxxLayer` (ImageStatic) en el panel "Verificación"
- Los extents se persisten en `mapa/data/georef_extents.json`
- `_REF_DEFAULTS` en `index.html` define los valores de arranque
- El JSON tiene prioridad sobre `_REF_DEFAULTS` (se carga via fetch con cache:no-cache)

### Flujo de calibración
1. Abrir panel de capas → sección "Verificación" (al final)
2. Click en el toggle de la capa → la capa se activa y el georef se inicia (HUD visible)
3. Controles de teclado:
   - `↑↓←→` — traslación 5 km/paso
   - `Shift+↑↓←→` — traslación 50 km/paso
   - `Ctrl+↑↓←→` — traslación 100 m/paso (fino)
   - `Alt+↑↓` — escalar vertical (expandir/achicar)
   - `Alt+←→` — escalar horizontal
   - `+` / `-` — escala uniforme
   - `C` — copiar extent actual al clipboard
   - `Esc` — desactivar georef
4. El HUD muestra: `[lon_min, lat_min, lon_max, lat_max]` actualizado en tiempo real
5. Al terminar: botón "⬇ Exportar extents" → descarga `georef_extents.json`
6. Reemplazar `mapa/data/georef_extents.json` con el archivo descargado
7. Actualizar los valores en `_REF_DEFAULTS` de `index.html` para que coincidan

### Añadir una nueva capa de referencia

```javascript
// En _REF_DEFAULTS:
ref_nuevo:  [lon_min, lat_min, lon_max, lat_max],

// Declaración de la capa:
const refNuevoLayer = makeRefLayer(
  'data/sections/paper_id/paper_id_figN_map.png',
  D.ref_nuevo
);

// En map.layers[]:
refNuevoLayer,

// En layerObjs:
ref_nuevo: refNuevoLayer,

// En REF_LAYERS_DATA:
ref_nuevo: {url:'data/sections/.../fig.png', ext:[...D.ref_nuevo], label:'Paper Año'},

// En panel HTML (sección Verificación correspondiente):
// <div class="lr" data-t="ref_nuevo">...
```

### Extents de arranque recomendados por tipo de figura

| Tipo de mapa | Extent inicial típico |
|---|---|
| Sulawesi solamente | `[118, -6, 126, 2]` |
| Sulawesi + entorno regional | `[117, -9, 130, 5]` |
| Indonesia/SE Asia | `[110, -10, 135, 10]` |
| Indonesia completa + contexto | `[95, -15, 145, 15]` |
| Grilla Supendi (116-128°E) | `[116, -4, 128, 8]` |

---

## 5. Georreferenciar para ImageStatic (capa de mapa real)

Diferente del sistema de calibración: aquí la imagen es una **capa de mapa** visible, no una referencia.

```javascript
// En index.html — patrón para capa raster de mapa:
const myExtent = ol.proj.transformExtent([lon_min, lat_min, lon_max, lat_max], 'EPSG:4326', 'EPSG:3857');
const myLayer = new ol.layer.Image({
  visible: false,
  opacity: 0.70,
  zIndex: 19,  // encima de vectores base, debajo de puntos
  source: new ol.source.ImageStatic({
    url: 'data/sections/paper_id/imagen_recortada.png',
    imageExtent: myExtent,
    projection: 'EPSG:3857'
  })
});
```

Para determinar el extent de una capa de mapa: usar la capa de referencia calibrada
como guía, luego ajustar hasta que coincida con features vectoriales conocidos.

---

## 6. Samplear GeoTIFF con rasterio

```python
import rasterio

def sample_tif(tif_path: str, coords: list) -> list:
    """coords: lista de (lon, lat) en EPSG:4326"""
    with rasterio.open(tif_path) as src:
        values = list(src.sample(coords))
    nodata = src.nodata
    return [None if (nodata and v[0]==nodata) else round(float(v[0]),2) for v in values]
```

TIFFs disponibles:
- `fuentes/sulawesi_bouguer_completa.tif` — WGM2012 Bouguer anomaly (mGal)
- `fuentes/sulawesi_freeair_recortada.tif` — WGM2012 Free-air (mGal)

---

## 7. Slices tomográficos como capas de mapa (s3_fe3)

Estado actual (2026-05-31): Supendi 2024 tiene 9 slices extraídos y calibrados.
Pendiente convertirlos a ImageStatic layers reales con slider de profundidad.

Patrón para implementar:
```javascript
const TOMO_SLICES = [
  {depth: 10,  url: 'data/sections/supendi_2024_sulawesi_tomo/slice_010km.png', ext:[114.96,-11.32,130.14,6.82]},
  {depth: 20,  url: 'data/sections/supendi_2024_sulawesi_tomo/slice_020km.png', ext:[114.83,-11.33,130.17,6.86]},
  // ... resto de slices con extents calibrados de georef_extents.json
];
// Slider activa setVisible(true) en el slice de profundidad seleccionada
```

Extents calibrados disponibles en `mapa/data/georef_extents.json` bajo keys `ref_sup_010` a `ref_sup_200`.

---

## Notas

- DPI: 200 dpi para figuras de texto/mapa; basta para calibración visual
- Siempre ver el thumbnail antes de recortar (evitar re-trabajo)
- El extent en `georef_extents.json` tiene prioridad sobre `_REF_DEFAULTS` en index.html
- Después de exportar extents calibrados: actualizar también `_REF_DEFAULTS` para coherencia
- Multi-panel grilla: verificar que el crop no incluya fracciones del panel adyacente (usar thumbnail de diagnóstico)
