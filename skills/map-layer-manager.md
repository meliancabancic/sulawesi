# SKILL: map-layer-manager

## Activación
Trigger: "actualizá el mapa", "agregá la capa", "implementá el popup", "toggle",
"VectorLayer", "ImageStatic", "panel de capas", mapa OpenLayers.

---

## Arquitectura actual (2026-05-31)

**Un solo archivo**: `mapa/index.html` (~3500 líneas). Todo está inline: HTML, CSS, JS.
No hay `layers.js`, `ui.js`, `config.js` separados — eso es la versión anterior.

```
mapa/
  index.html          ← ÚNICO frontend. No usar versiones anteriores.
  backend/            ← FastAPI + SQLite
  fuentes/            ← GeoJSONs estáticos por paper
  data/
    sections/         ← imágenes de figuras de papers (referencia + capas raster)
    georef_extents.json ← extents calibrados de capas de referencia
  ol.js / ol.css      ← OpenLayers 6 (CDN local)
```

**Stack**: OpenLayers 6 como objeto global `ol`. No usar ES modules ni `import`.
**Backend**: FastAPI corriendo en `http://127.0.0.1:8000`. Ver endpoints en este skill.

---

## Sistema de capas (layerObjs)

Todas las capas del mapa se registran en el objeto `const layerObjs = {...}`.
El panel de capas usa `data-t` para identificar cada toggle — debe coincidir con la key en `layerObjs`.

```javascript
// Patrón estándar de registro
const layerObjs = {
  // key:  layer_variable (o multiLayer([a, b]) para grupos)
  mi_capa: miLayer,
  grupo_ab: multiLayer([layerA, layerB]),
};
```

`multiLayer([a,b])` devuelve un wrapper que llama `setVisible` en todos los sublayers.

---

## Checklist para agregar una capa nueva

### 1. Declarar el layer (antes de `const map = new ol.Map(...)`)

**VectorLayer desde GeoJSON estático:**
```javascript
const miLayer = new ol.layer.Vector({
  visible: false,
  source: new ol.source.Vector(),
  style: miStyleFn,
  zIndex: 50
});
fetch('fuentes/mi_paper.geojson')
  .then(r => r.json())
  .then(fc => {
    miLayer.getSource().addFeatures(fc.features.map(f => buildFeature(f)));
  }).catch(() => {});
```

**VectorLayer desde endpoint del backend:**
```javascript
const miLayer = new ol.layer.Vector({
  visible: false,
  source: new ol.source.Vector(),
  style: miStyleFn
});
fetch('/api/mi_endpoint?param=valor')
  .then(r => r.json())
  .then(data => {
    const feats = data.features.map(f => {
      const feat = new ol.Feature({
        geometry: buildGeometry(f.geometry),
        ...f.properties,
        feat_type: 'mi_tipo',
        feat_id: f.properties.id
      });
      return feat;
    });
    miLayer.getSource().addFeatures(feats);
  }).catch(() => {});
```

**ImageStatic (raster georreferenciado):**
```javascript
const miExtent = ol.proj.transformExtent([lon_min, lat_min, lon_max, lat_max], 'EPSG:4326', 'EPSG:3857');
const miRasterLayer = new ol.layer.Image({
  visible: false,
  opacity: 0.70,
  zIndex: 19,
  source: new ol.source.ImageStatic({
    url: 'data/sections/paper_id/imagen.png',
    imageExtent: miExtent,
    projection: 'EPSG:3857'
  })
});
```

**Helper `buildFeature(f)`**: ya definido en index.html, convierte un GeoJSON Feature a `ol.Feature` con `geometry` en EPSG:3857.

**Helper `fromLL([lon, lat])`**: convierte a EPSG:3857. `lc([[lon,lat],...])` convierte array de coordenadas.

### 2. Agregar al array `map.layers`
```javascript
const map = new ol.Map({
  layers: [
    // ... capas existentes ...
    miLayer,  // ← agregar aquí en el orden correcto
  ]
});
```
Orden: rasters base → polígonos → líneas → puntos → anotaciones.

### 3. Registrar en `layerObjs`
```javascript
const layerObjs = {
  // ... existentes ...
  mi_key: miLayer,
};
```

### 4. Agregar toggle en el panel HTML
En `<div id="lp">`, dentro de la sección temática correcta (S1–S8):
```html
<div class="lr" data-t="mi_key">
  <div class="lchk" id="chk-mi_key"></div>
  <span>Nombre descriptivo — Autor et al. (año)</span>
</div>
```

Si tiene slider de opacidad:
```html
<input type="range" min="0" max="100" value="65" class="op-slider"
  onclick="event.stopPropagation()"
  oninput="miLayer.setOpacity(this.value/100)">
```

### 5. Si la capa es temática (default OFF) — agregar a THEMATIC_KEYS
```javascript
const THEMATIC_KEYS = [
  // ... existentes ...
  'mi_key',
];
```

### 6. Agregar a la sección correcta en SECTION_KEYS
```javascript
const SECTION_KEYS = {
  '3': ['slab_layer', 'hua_layer', ..., 'mi_key'],  // ← agregar a S3 si es mantélico
};
```

### 7. Si tiene features clickeables — agregar al click handler
En `map.on('singleclick', ...)`, dentro del loop `map.forEachFeatureAtPixel(...)`:
```javascript
} else if (type === 'mi_tipo') {
  // type = feat.get('feat_type')
  openPanel(feat.get('feat_id'));  // si tiene entrada en DB[]
  // o: mostrar tooltip directo
}
```

### 8. Agregar a LEGEND_DEF (si tiene ícono en leyenda)
```javascript
const LEGEND_DEF = {
  // ...
  mi_key: { svg: '<circle ...>', label: 'Mi capa' },
};
```

### 9. Actualizar mapa_plan.json
Marcar la tarea como `"estado": "implementado"` con `"nota_completado"` y fecha.

---

## Sistema de fondos (base layers) — mutex obligatorio

El fondo del mapa tiene tres opciones mutuamente exclusivas:
- **Sentinel-2** (EOX, default ON): `satellite` / `esriSat`
- **ESRI Hybrid** (satélite + fronteras): `esri_hybrid` / `esriHybridBase + esriHybridLabels`
- **GEBCO** (batimetría): `gebco_color` + `gebco_relief`

Reglas del mutex (ya implementadas en el click handler de `.lr`):
- Sentinel solo se puede apagar si hay otro fondo activo
- Al activar ESRI Hybrid → Sentinel se apaga automáticamente
- Al desactivar ESRI Hybrid → si no hay GEBCO, Sentinel vuelve a ON
- Al desactivar GEBCO → si no hay otro fondo, Sentinel vuelve a ON

**Para agregar un nuevo fondo**: extender estas reglas en el mismo bloque del click handler y en `updateSentinelLock()`.

---

## Sistema de capas de referencia (calibración georef)

Las capas `ref_*` son ImageStatic que se superponen sobre el mapa para calibrar la posición de datos digitalizados. Ver `skills/raster-georef.md` para el workflow completo.

```javascript
// Patrón para agregar una capa de referencia nueva:
const refMiPaperLayer = makeRefLayer(
  'data/sections/mi_paper/mi_paper_fig1_map.png',
  D.ref_mi_paper   // extent desde _REF_DEFAULTS
);
// D = _REF_DEFAULTS (alias corto ya definido)
```

El sistema guarda extents en `data/georef_extents.json` y los carga automáticamente.

---

## zIndex de referencia

| Rango | Tipo de capa |
|-------|-------------|
| 10–20 | Rasters (gravedad, CPD, height anomaly) — ImageStatic |
| 22 | Capas de referencia (calibración) — makeRefLayer |
| 25–40 | Polígonos temáticos (Jibran clusters, hazard zones, unidades geológicas) |
| 50–80 | Líneas secundarias (fallas B, GEM, Hikmy, Husein) |
| 100–150 | Líneas principales (tectKeyLayer, tectSubLayer, newFaultLayer) |
| 200–310 | Puntos y símbolos (volcanes, CMT, GPS, estaciones, manifestaciones) |
| 500+ | Anotaciones |

---

## Funciones de estilo disponibles

| Función / Objeto | Uso |
|---|---|
| `keyFaultStyle(f, resolution)` | Estilo fallas clave: sinistral/dextral/thrust con flechas/dientes |
| `newFaultStyleFn(f, resolution)` | Fallas de newFaultLayer (mismo patrón) |
| `makeBeachballCanvas(s1,d1,r1,sz,col)` | Renderiza beachball en canvas para CMT |
| `toothPolygon(p1,p2,size,flip)` | Triángulo perpendicular al segmento (thrust) |
| `strikeslipArrows(coords,res,sinistral)` | Flechas apareadas para strike-slip |
| `depthColorArr(depth)` | `[r,g,b,a]` por profundidad (verde→amarillo→rojo→violeta) |
| `faultType(rake)` | `'T'|'N'|'S'|'O'` desde ángulo de rake |
| `fromLL([lon,lat])` | EPSG:4326 → EPSG:3857 |
| `lc([[lon,lat],...])` | Array de coords → EPSG:3857 |
| `buildFeature(geojsonFeature)` | GeoJSON Feature → ol.Feature en EPSG:3857 |
| `multiLayer([l1,l2])` | Wrapper que agrupa layers para layerObjs |

---

## Backend — endpoints disponibles

| Endpoint | Método | Params principales | Descripción |
|---|---|---|---|
| `/api/earthquakes` | GET | `minMag`, `maxMag`, `startYear`, `endYear`, `minDepth`, `maxDepth`, `faultTypes`, `sources` | Catálogo sísmico DB (GCMT + USGS) |
| `/api/catalog/live` | GET | `minMag`, `days` | Eventos recientes USGS FDSN |
| `/api/catalog/isc` | GET | `minMag`, `maxMag`, `days`, `minDepth`, `maxDepth` | Catálogo ISC (proxy) |
| `/api/stations` | GET | — | Estaciones BMKG/GEOFON (IRIS FDSN proxy + fallback) |
| `/api/volcanoes` | GET | — | Volcanes GVP + clasificación PVMBG |
| `/api/slabs/slab2` | GET | — | Contornos Slab2 (GeoJSON) |
| `/api/faults/gem` | GET | `faultType` | Fallas GEM por tipo cinemático |
| `/api/gravity/profile` | POST | body: `{coords, n_points}` | Perfil Bouguer + Free-air desde TIFFs WGM2012 |
| `/api/annotations` | GET/POST/DELETE | — | Anotaciones del usuario |
| `/api/geodata/features` | GET | `source`, `layerType`, `unmatched` | Features de geo_features DB |
| `/api/geodata/canonical` | GET | `layerType` | Canonicals con merged_geom |
| `/api/geodata/canonical-groups` | GET | — | Grupos para definir merged_geom |
| `/api/geodata/canonical-groups/{id}/resolve` | POST | `chosenId` | Asignar merged_geom a canonical |
| `/api/geodata/clusters` | GET | `minSim` | Clusters de proposals pendientes |
| `/api/geodata/matches` | GET | `status` | Match proposals |
| `/api/geodata/matches/run` | POST | `threshold` | Ejecutar algoritmo de matching |
| `/api/geodata/features/{id}` | PATCH | body: `{geometry}` | Actualizar geometría de un feature |
| `/api/docs` | GET | — | Swagger UI (documentación interactiva) |

---

## Convenciones obligatorias

- `feat_type` en properties: identifica el tipo para el click/hover handler
- `feat_id`: ID único del feature (para `openPanel(id)`)
- Todo layer nuevo: `visible: false` por defecto (excepto límites de placa base)
- Todo layer nuevo: registrar en `layerObjs` + panel HTML + `SECTION_KEYS` + `THEMATIC_KEYS`
- Todo layer nuevo: actualizar `mapa_plan.json` → `"estado": "implementado"` con fecha
- Todo elemento visual: debe tener cita APA en `DB[id]` — sin cita no va al mapa
