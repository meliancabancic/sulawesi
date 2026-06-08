# Categorías GeoJSON — Referencia para paper-extractor

Leer solo las secciones necesarias para el paper en proceso.

---

## 1. fault

**Geometría**: LineString (traza discreta) | Polygon (zona de falla difusa)
**Usar LineString cuando**: se puede trazar el plano de falla en el mapa.
**Usar Polygon cuando**: el paper define una zona de deformación sin traza única.

```json
{
  "category": "fault",
  "layer_type": "fault",
  "kinematics": "sinistral|dextral|thrust|normal|oblique|reverse|unknown",
  "slip_rate_mmyr": null,
  "slip_rate_notes": "",
  "dip_deg": null,
  "dip_direction": "",
  "rake_deg": null,
  "max_magnitude": null,
  "seismic_coupling": null,
  "locking_depth_km": null,
  "last_rupture": "",
  "iugs_symbol": "strike_slip_sinistral|strike_slip_dextral|thrust|normal|unknown",
  "active": true
}
```

Casos especiales en el proyecto:
- PKF → `kinematics: "sinistral"`, `slip_rate_mmyr: 35-45`, `iugs_symbol: "strike_slip_sinistral"`
- Matano → `kinematics: "dextral"`, `iugs_symbol: "strike_slip_dextral"`
- Batui Thrust → `kinematics: "thrust"`, `iugs_symbol: "thrust"`
- MST → `kinematics: "thrust"`, segmentar en N/CN/Mamuju/Somba si el paper los distingue

---

## 2. subduction_zone

**Geometría**: LineString (frente de subducción en superficie) | Polygon (zona)
**layer_type**: `subduction_zone`

```json
{
  "category": "subduction_zone",
  "layer_type": "subduction_zone",
  "slab_name": "Celebes|Sangihe|Halmahera|Banda|Sula|Cotabato",
  "dip_direction": "S|N|E|W|NW|etc",
  "dip_deg": null,
  "convergence_rate_mmyr": null,
  "convergence_azimuth_deg": null,
  "max_depth_km": null,
  "coupling_coefficient": null,
  "trench_depth_m": null,
  "onset_ma": null,
  "megathrust": true
}
```

---

## 3. fold_thrust_belt

**Geometría**: LineString (frente de cabalgamiento) | Polygon (cinturón)
**layer_type**: `fold_thrust_belt`

```json
{
  "category": "fold_thrust_belt",
  "layer_type": "fold_thrust_belt",
  "vergence": "N|S|E|W|NE|etc",
  "shortening_rate_mmyr": null,
  "age_onset": ""
}
```

---

## 4. suture_zone

**Geometría**: LineString
**layer_type**: `fault` (en la DB, las suturas se cargan como fault)

```json
{
  "category": "suture_zone",
  "layer_type": "fault",
  "terranes_joined": ["terrane_A", "terrane_B"],
  "collision_age_ma": null,
  "ophiolite_present": false
}
```

---

## 5. deformation_zone / coupling_zone

**Geometría**: Polygon
**layer_type**: `deformation_zone`

```json
{
  "category": "deformation_zone",
  "layer_type": "deformation_zone",
  "regime": "compressional|extensional|transpressional|transtensional",
  "strain_rate": null,
  "locking_fraction": null
}
```

---

## 6. cross_section

**Geometría**: LineString (traza del perfil en el mapa)
**layer_type**: `structure`

```json
{
  "category": "cross_section",
  "layer_type": "structure",
  "section_label": "A-A'",
  "section_type": "tomography|seismic_reflection|geological|gravity|combined",
  "depth_range_km": [0, 700],
  "image_file": "autor_año_figN_seccionAA.png",
  "image_path": "mapa/data/sections/autor_año/autor_año_figN_seccionAA.png",
  "key_features_in_section": ["PKF", "Moho", "slab"]
}
```

La traza LineString va de inicio a fin del perfil en el mapa (en coordenadas del papel).
`image_file` se rellena después de extraer la figura con PyMuPDF (ver `skills/raster-georef.md`).

---

## 7. hazard_zone / seismicity_cluster

**Geometría**: Polygon
**layer_type**: `hazard_zone`

```json
{
  "category": "hazard_zone",
  "layer_type": "hazard_zone",
  "hazard_type": "seismic_gap|tsunami_source|liquefaction|landslide|volcanic",
  "return_period_yr": null,
  "max_expected_mw": null,
  "pga_g": null,
  "notes": ""
}
```

Regla: gaps sísmicos son zonas SIN sismos recientes = acumulación de stress.
No crear canonical propio — asociar al canonical de la falla/subducción contenedora.

---

## 8. basin

**Geometría**: Polygon
**layer_type**: `structure`

```json
{
  "category": "basin",
  "layer_type": "structure",
  "basin_type": "pull_apart|rift|foreland|forearc|backarc|failed_rift|passive_margin",
  "age_onset_ma": null,
  "max_depth_m": null,
  "fill_thickness_km": null,
  "hydrocarbon_potential": false
}
```

---

## 9. terrane

**Geometría**: Polygon
**layer_type**: `structure`

```json
{
  "category": "terrane",
  "layer_type": "structure",
  "affinity": "continental_australian|continental_sundaland|oceanic|arc|mixed",
  "collision_age_ma": null,
  "basement_age_ma": null,
  "key_lithologies": []
}
```

Terrenos del proyecto: Banggai-Sula (australiana, ~5-6 Ma), Buton-TK (australiana),
West Sulawesi Province (sundaland), Sula Spur (australiana).

---

## 10. ophiolite

**Geometría**: Polygon
**layer_type**: `structure`

```json
{
  "category": "ophiolite",
  "layer_type": "structure",
  "formation_age_ma": null,
  "obduction_age_ma": null,
  "completeness": "complete|partial|dismembered",
  "preserved_units": []
}
```

ESO: `formation_age_ma: 123`, `obduction_age_ma: ~15` (Neógeno).

---

## 11. metamorphic_complex

**Geometría**: Polygon
**layer_type**: `structure`

```json
{
  "category": "metamorphic_complex",
  "layer_type": "structure",
  "complex_type": "core_complex|UHP|HP|amphibolite|greenschist|blueschist",
  "P_GPa_min": null,
  "P_GPa_max": null,
  "T_C_min": null,
  "T_C_max": null,
  "age_ma": null,
  "exhumation_mechanism": ""
}
```

Bantimala: `complex_type: "UHP"`, `P_GPa_min: 2.7`, `P_GPa_max: 2.85`,
`T_C_min: 615`, `T_C_max: 640`, `age_ma: 119`.

---

## 12. volcanic_complex / volcanic_arc

**Geometría**: Polygon (área del complejo/arco) | LineString (lineal)
**layer_type**: `structure`

```json
{
  "category": "volcanic_complex",
  "layer_type": "structure",
  "arc_type": "continental|oceanic|island",
  "age_range": "",
  "geochemistry": "tholeiitic|calc_alkaline|alkaline|adakitic",
  "active": false
}
```

---

## 13. volcano

**Geometría**: Point
**layer_type**: `structure`

```json
{
  "category": "volcano",
  "layer_type": "structure",
  "volcano_type": "stratovolcano|caldera|shield|maar|lava_dome",
  "pvmbg_type": "A|B|C",
  "elev_m": null,
  "last_eruption": "",
  "gvp_id": "",
  "geothermal_field": false
}
```

---

## 14. anisotropy

**Geometría**: Point (estación SKS)
**layer_type**: `structure`
**depth_class**: siempre `"mantélica"`

```json
{
  "category": "anisotropy",
  "layer_type": "structure",
  "depth_class": "mantélica",
  "fast_axis_deg": null,
  "delay_time_s": null,
  "measurement_type": "SKS|SKKS|PKS|combined",
  "anisotropy_source": "asthenospheric_flow|lithospheric_fabric|fossil|uncertain",
  "station_code": ""
}
```

---

## 15. gps_vector

**Geometría**: Point (estación GPS)
**layer_type**: `structure`

```json
{
  "category": "gps_vector",
  "layer_type": "structure",
  "Ve_mmyr": null,
  "Vn_mmyr": null,
  "Vu_mmyr": null,
  "ref_frame": "ITRF2014|ITRF2008|Sundaland|Eurasia",
  "station_code": "",
  "observation_period": ""
}
```

---

## 16. earthquake

**Geometría**: Point (epicentro)
**layer_type**: `structure`

```json
{
  "category": "earthquake",
  "layer_type": "structure",
  "magnitude": null,
  "magnitude_type": "Mw|Ms|mb",
  "depth_km": null,
  "fault_type": "T|N|S|O",
  "strike1": null, "dip1": null, "rake1": null,
  "year": null,
  "rupture_length_km": null,
  "rupture_velocity_kms": null,
  "event_notes": ""
}
```

---

## 17. geophysical_point

**Geometría**: Point
**layer_type**: `structure`

Para: estaciones sismológicas, perfiles OBS, puntos de flujo calórico, puntos de CPD.

```json
{
  "category": "geophysical_point",
  "layer_type": "structure",
  "point_type": "seismic_station|OBS|heat_flow|gravity_station|CPD",
  "value": null,
  "units": "",
  "network": "",
  "station_code": ""
}
```

---

## 18. structure (genérico)

Para estructuras que no encajan en categorías anteriores.
**layer_type**: `structure`

```json
{
  "category": "structure",
  "layer_type": "structure",
  "structure_type": "descripción libre",
  "notes": ""
}
```

---

## Decision tree — categoría ambigua

```
¿Es una traza de falla activa con cinemática definida?
  → fault

¿Es el frente de una zona de subducción?
  → subduction_zone

¿Es un cinturón de pliegues y cabalgamientos?
  → fold_thrust_belt

¿Es una zona de colisión entre dos terrenos (límite fósil)?
  → suture_zone (layer_type: fault)

¿Es una anomalía de velocidad en el manto o vector de anisotropía?
  → anisotropy o geophysical_point (depth_class: mantélica)

¿Es un polígono de terreno geológico, ofiolita o complejo metamórfico?
  → terrane | ophiolite | metamorphic_complex

¿Es una cuenca sedimentaria?
  → basin

¿Es una zona de amenaza sísmica o gap?
  → hazard_zone (asociar al canonical de la falla, no crear canonical propio)

¿No encaja en ninguna de las anteriores?
  → structure con structure_type descriptivo
```
