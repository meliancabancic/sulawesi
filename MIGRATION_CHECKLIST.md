# MIGRATION_CHECKLIST.md — Claude.ai → Claude Code

## Prerequisitos
- [ ] Claude Code instalado: `npm install -g @anthropic-ai/claude-code`
- [ ] Directorio del proyecto creado: `mkdir sulawesi-geotect && cd sulawesi-geotect`

---

## Paso 1 — Ejecutar setup
```bash
bash setup.sh
```
Verifica dependencias, crea estructura de directorios, instala paquetes Python/Node.

---

## Paso 2 — Copiar PDFs de papers
Copiar todos los archivos de `/mnt/project/` al directorio `papers/`:
```
papers/
  2011_IAGI_Makassar_TectonicEvolutionofSulawesi.pdf
  socquet_jgr_2006.pdf
  Geochem_Geophys_Geosyst__2012__Di_Leo__*.pdf
  JGR_Solid_Earth__2024__Cao__*.pdf
  Geochem_Geophys_Geosyst__2024__Yuan__*.pdf
  Geophysical_Research_Letters__2023__Hua__*.pdf
  Natawidjaja_et_al2020.pdf
  2016LukmanetalUnderstandingMatanoFault.pdf
  hussein_etal_2014_*.pdf
  Tectonics__2021__Greenfield__*.pdf
  Geophysical_Research_Letters__2025__Kesumastuti__*.pdf
  cipta_etal_2016_PSHA_sulawesi.pdf
  Walpersdorf_etal_EPSL_1998.pdf
  The_2018_Mw75_Palu_supershear_earthquake_rupture.pdf
  adminjurnal02_Surono.pdf
  Jayadi_2023_*.pdf
  Jibran_2025_*.pdf
  Baillie_Decker2022.pdf
  satyana_ipa11g219.pdf
  egusphere20253105.pdf
  ggae085.pdf
  s44195025001194.pdf
  [+ cualquier paper adicional]
```

---

## Paso 3 — Copiar skills
Copiar los skills desde el entorno claude.ai (ya actualizados con los paths correctos):

```
skills/
  geo-comprehension.md          ← /mnt/skills/user/geo-comprehension/SKILL.md
  paper-extractor.md            ← /mnt/skills/user/paper-extractor/SKILL.md
  references/
    categories.md               ← /mnt/skills/user/paper-extractor/references/categories.md
  monograph-writer.md           ← /mnt/skills/user/monograph-writer/SKILL.md
  map-layer-manager.md          ← /mnt/skills/user/map-layer-manager/SKILL.md
  bibliography-compiler.md      ← /mnt/skills/user/bibliography-compiler/SKILL.md
  docx.md                       ← /mnt/skills/user/docx/SKILL.md
  pdf.md                        ← /mnt/skills/user/pdf/SKILL.md
  pdf-reading.md                ← /mnt/skills/user/pdf-reading/SKILL.md
  frontend-design.md            ← /mnt/skills/user/frontend-design/SKILL.md
  scripts/
    unpack.py                   ← generado por setup.sh
    pack.py                     ← generado por setup.sh
    validate.py                 ← generado por setup.sh
```

---

## Paso 4 — Verificar CLAUDE.md y project_state.json
- [ ] `CLAUDE.md` está en la raíz del proyecto
- [ ] `project_state.json` está en la raíz del proyecto
- [ ] Los nombres de archivo en `project_state.json` coinciden con los PDFs copiados en `papers/`

---

## Paso 5 — Definir enfoque de Sección 6
Antes de empezar a trabajar, resolver la única decisión pendiente:
- [ ] Confirmar enfoque de Sección 6 con usuario
- [ ] Actualizar `project_state.json` → `monografia.seccion_6_enfoque`
- [ ] Cambiar status de `"bloqueada"` a `"pendiente"`

---

## Paso 6 — Relevamiento bibliográfico de secciones 4 y 5
Antes de redactar, verificar cobertura de papers para gravimetría y flujo calórico:
```bash
# En Claude Code:
# "Revisá los papers del proyecto e identificá cuáles tienen datos de
#  gravimetría y flujo calórico para las secciones 4 y 5"
```
- [ ] Papers con gravimetría identificados
- [ ] Papers con flujo calórico identificados
- [ ] Si hay gap: decidir si agregar papers o replantear alcance de las secciones

---

## Paso 7 — Iniciar Claude Code
```bash
cd sulawesi-geotect
claude
```

Claude Code leerá `CLAUDE.md` automáticamente al inicio de cada sesión.

---

## Lo que NO migra (no es necesario)
- El system prompt de claude.ai → reemplazado por `CLAUDE.md`
- Los archivos en `/mnt/skills/public/` → no se usan, los skills locales los reemplazan
- El project knowledge de claude.ai → los PDFs están en `papers/`

---

## Verificación final
```bash
# Estructura esperada
ls -la
# CLAUDE.md  MIGRATION_CHECKLIST.md  project_state.json  setup.sh
# mapa/  monografia/  node_modules/  papers/  skills/  tmp/

ls papers/*.pdf | wc -l
# debe mostrar ≥ 22 (número de papers del proyecto)

ls skills/*.md
# debe mostrar los 10 skills

node -e "require('./node_modules/docx')" && echo "docx OK"
python3 -c "import pypdf, pdfplumber, pyproj; print('Python deps OK')"
libreoffice --version
pdfinfo --version
```
