# SKILL: frontend-design

## Activación
Trigger: "CSS", "panel", "UI", "toggle", "checkbox", "Chart.js", "gráfico", "perfil",
"slider", "diseño del mapa", "html del mapa", "estilo", "popup", "panel lateral".

---

## Arquitectura actual

**Todo en un solo archivo**: `mapa/index.html` (~3600 líneas).
No hay `layers.js`, `ui.js`, `config.js` separados — esa es la versión anterior.

```
HTML (líneas 1–330)   ← estructura DOM + panel de capas
CSS  (líneas 11–120)  ← estilos (variables CSS, clases de panel)
JS   (líneas 330+)    ← datos hardcoded, layers, handlers, funciones
```

---

## Estructura del DOM

```
body
  #header          ← barra superior: título + botones S1-S8 + botones de acción
  #map             ← viewport OpenLayers (flex: 1)
    canvas         ← renderizado OL6
    #coords        ← coordenadas bajo el cursor (monospace, bottom-left)
    #tip           ← tooltip flotante (position:fixed, display:none por defecto)
    #georef-hud    ← HUD de calibración georef (position:fixed, bottom center)
    #lb            ← botón "⊞ Capas" (top-right)
    #lp            ← panel desplegable de capas (position:absolute, right:10px)
    #grav-modal    ← modal del perfil gravitatorio
    #deck-modal    ← (eliminado — Deck.gl descartado)
  #panel           ← panel lateral de info (right side, flex-shrink:0)
    #pb            ← cuerpo scrolleable del panel
```

---

## Variables CSS

```css
:root {
  --bg:     #0c0f14   /* fondo principal (negro azulado) */
  --bg2:    #13171f   /* fondo panel/modal */
  --bg3:    #1a1f2b   /* fondo elementos interactivos */
  --border: rgba(255,255,255,0.09)
  --accent: #d4a843   /* amarillo ocre — highlights, títulos */
  --text:   #cdd1dc   /* texto principal */
  --dim:    #5a6070   /* texto secundario/atenuado */
}
```

Usar siempre las variables CSS del proyecto. No hardcodear colores en nuevo código.

---

## Sistema de panel de capas (#lp)

El panel es un `<div id="lp">` con `overflow-y: scroll; max-height: calc(100vh - 48px)`.
Se abre/cierra con el botón `#lb` y click fuera.

### Elementos HTML del panel

```html
<!-- Separador de categoría -->
<div class="lcat">Nombre de sección</div>

<!-- Fila de capa (toggle) -->
<div class="lr" data-t="mi_key">
  <div class="lchk" id="chk-mi_key"></div>    <!-- vacío = OFF, con ✓ = ON -->
  <span>Nombre visible — Fuente (año)</span>
  <!-- Opcional: slider de opacidad -->
  <input type="range" min="0" max="100" value="65" class="op-slider"
    onclick="event.stopPropagation()"
    oninput="miLayer.setOpacity(this.value/100)">
  <!-- Opcional: botón ⓘ de fuente -->
  <span onclick="event.stopPropagation();openPanel('db_entry_id')"
    style="cursor:pointer;color:var(--dim);font-size:.65rem;flex-shrink:0"
    title="Fuente">ⓘ</span>
</div>

<!-- Separador visual -->
<div class="lsep"></div>
```

### Toggle handler (ya implementado en index.html)

El sistema usa `document.querySelectorAll('.lr').forEach(row => { row.addEventListener('click', ...) })`.
Para cada click:
1. Lee `key = row.dataset.t`
2. Busca `lyr = layerObjs[key]`
3. Si no existe → return (por eso SIEMPRE registrar en layerObjs)
4. Llama `lyr.setVisible(!lyr.getVisible())`
5. Actualiza `chk.classList.toggle('on')` y `chk.textContent`

**No hay switch/case** — el sistema es automático via `layerObjs`.

---

## Sistema de panel lateral (#panel)

Al hacer click en un feature del mapa, se llama `openPanel(id)` donde `id = feat.get('feat_id')`.

```javascript
// openPanel busca en el objeto DB (definido en index.html):
const DB = {
  'mi_feature_id': {
    type: 'Tipo visible',
    color: '#c87030',
    title: 'Título del feature',
    tags: ['tag1', 'tag2'],
    desc: 'Descripción en español.',
    papers: [
      {
        ref: 'Autor et al. (año)',
        title: 'Título del paper',
        journal: 'Journal, volumen, página. doi:...',
        find: 'Qué encontró este paper sobre esta estructura.'
      }
    ]
  }
};
```

Para que un feature sea clickeable:
1. Definir entrada en `DB['mi_feature_id']`
2. En el feature: `feat.setProperties({ feat_type: 'mi_tipo', feat_id: 'mi_feature_id' })`
3. En el click handler (`map.on('singleclick', ...)`): agregar el tipo al bloque correspondiente

---

## Tooltip (#tip)

```javascript
// El tooltip se muestra en map.on('pointermove', ...) con map.forEachFeatureAtPixel()
// Patrón HTML típico para el tooltip:
html = `<span style="color:${DB[id].color};font-size:.5rem">${DB[id].type}</span><br>${DB[id].title}`;
// El handler en index.html actualiza #tip.innerHTML y lo posiciona
```

---

## Botones de sección S1–S8

La barra superior tiene botones `.sec-btn` con `data-s="1"` a `data-s="8"` más "Todo".
Al hacer click activan solo las capas de `SECTION_KEYS[s]` y desactivan el resto.

```javascript
const SECTION_KEYS = {
  '1': ['gps_vel', 'plate_vel'],
  '2': ['seismicity', 'gaps', 'clusters', 'stations'],
  '3': ['slab_layer', 'hua_layer', ...],
  // ...
};
```

Al agregar una capa nueva: **siempre** agregarla a `SECTION_KEYS[s]` y a `THEMATIC_KEYS`.

---

## Capas base — sistema de fondos

Tres opciones mutuamente exclusivas (ver mutex en `mapa/CLAUDE.md` principio 4):

| Key | Layer | Por defecto |
|---|---|---|
| `satellite` | Sentinel-2 EOX | ON |
| `esri_hybrid` | ESRI WorldImagery + Labels | OFF |
| `gebco_color` | GEBCO batimetría color | OFF |
| `gebco_relief` | GEBCO hillshade | OFF |

El mutex garantiza que siempre hay al menos un fondo visible.

---

## Chart.js — perfil gravitatorio

```javascript
// El modal #grav-modal contiene el canvas #grav-chart
// Ya implementado — el botón ⏥ Perfil activa OL Draw LineString
// Al completar la línea llama fetch('/api/gravity/profile', {method:'POST', ...})
// El response tiene: {dist_km:[], bouguer:[], freeair:[], lon:[], lat:[], n, total_km}

const chart = new Chart(ctx, {
  type: 'line',
  data: {
    labels: distKm.map(d => d.toFixed(0)),
    datasets: [
      { label:'Bouguer (mGal)', data: bouguer, borderColor:'#3088dc', ... },
      { label:'Aire Libre (mGal)', data: freeair, borderColor:'#dc3c3c', ... }
    ]
  }
});
```

---

## Slider para z-slices tomográficos (s3_fe3 — pendiente)

Los slices de Supendi 2024 están extraídos y calibrados. Patrón a implementar:

```javascript
// Datos disponibles en georef_extents.json (keys ref_sup_010 a ref_sup_200)
const SUPENDI_SLICES = [
  {depth: 10,  url: 'data/sections/supendi_2024_sulawesi_tomo/slice_010km.png'},
  {depth: 20,  url: '...slice_020km.png'},
  // ... hasta 200km
];

// Un ImageLayer por slice, visible: false por defecto
const supSliceLayers = SUPENDI_SLICES.map(s => {
  const ext = ol.proj.transformExtent(
    georef_extents['ref_sup_' + String(s.depth).padStart(3,'0') + 'km'].ext,
    'EPSG:4326', 'EPSG:3857'
  );
  return new ol.layer.Image({
    visible: false, opacity: 0.70,
    source: new ol.source.ImageStatic({ url: s.url, imageExtent: ext })
  });
});

// Slider en el panel S3
document.getElementById('sup-depth-slider').addEventListener('input', e => {
  const idx = +e.target.value;
  supSliceLayers.forEach((l, i) => l.setVisible(i === idx));
  document.getElementById('sup-depth-val').textContent = SUPENDI_SLICES[idx].depth + ' km';
});
```

---

## CSS — clases del proyecto

| Clase | Uso |
|---|---|
| `.lcat` | Encabezado de categoría en panel de capas |
| `.lr` | Fila de layer en el panel — tiene `data-t` y click handler |
| `.lchk` / `.lchk.on` | Checkbox cuadrado (vacío=OFF, `✓`=ON) |
| `.lsep` | Separador horizontal entre grupos |
| `.op-slider` | Slider de opacidad inline en `.lr` |
| `.op-val` | Span que muestra el % del slider |
| `.sec-btn` / `.sec-btn.active` | Botones S1-S8 en el header |
| `.leg` | Fila de leyenda flotante |
| `.lr[data-t^="ref_"]` | Capas de referencia (calibración) |
| `#tip` | Tooltip flotante (`position:fixed`) |
| `#georef-hud` | HUD de calibración georef |
| `#pb` | Cuerpo del panel lateral (overflow-y:auto) |
| `.psec` / `.ptag` / `.pt` | Elementos del panel lateral de info |
| `.bbl-title` / `.bbl-canvas` | Elementos del panel de beachball CMT |

---

## Convenciones

- Colores: usar variables CSS (`var(--accent)`, `var(--dim)`, etc.) — no hardcodear
- Font: `font-family: monospace` en todos los elementos del panel y UI
- Tamaño de texto UI: `.5rem` a `.6rem` (muy compacto — el mapa es pequeño)
- Todo nuevo elemento interactivo: `event.stopPropagation()` en sliders/botones dentro de `.lr`
- Nunca `innerHTML` con datos no controlados — usar `textContent` para valores del usuario
- Cache: el `<meta http-equiv="Cache-Control" content="no-cache...">` ya está — no agregar versiones `?v=N`
