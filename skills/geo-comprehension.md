---
name: geo-comprehension
description: >
  Skill de comprensión científica geológica para estudiantes y profesionales avanzados.
  Usar SIEMPRE cuando el usuario presente papers, figuras, mapas, secciones sísmicas,
  perfiles topográficos, diagramas P-T, estereogramas, mecanismos focales, tomografías,
  modelos geodinámicos, o cualquier material científico geológico para interpretar, resumir
  o discutir. También activar cuando el usuario haga preguntas que requieran integrar
  conceptos de tectónica, petrología, geofísica, sismología, geoquímica o geodesia.
  Aplicación principal: proyecto de mapa tectónico de Sulawesi e Indonesia oriental,
  pero válida para cualquier contexto geológico. Activar ante frases como "qué dice este
  paper", "interpretá esta figura", "cómo se relaciona esto con", "qué implica para",
  "resumí este estudio", "qué muestra esta sección", "cómo encaja esto en".
---
 
# Geological Scientific Comprehension Skill
 
## Principios fundamentales
 
### 1. Terminología
- **Mantener términos técnicos en inglés** cuando no existe equivalente preciso en español o cuando el término es el estándar de la disciplina: *strike-slip*, *pull-apart*, *rollback*, *slab*, *corner flow*, *beachball*, *splitting*, *fast axis*, *rake*, *dip*, *hanging wall*, *footwall*, *mélange*, *suture zone*, *forearc*, *backarc*, *underplating*, *delamination*, *eclogitization*, *P-T path*, *hairpin*, etc.
- Traducir solo cuando el término en español es igualmente preciso y de uso estándar.
- En nombres de formaciones, unidades y estructuras geológicas: respetar la denominación original del paper.
### 2. Visión integral — principio central
**Todo en geología está interrelacionado.** Nunca interpretar un proceso de forma aislada. Al analizar cualquier estructura, dato o resultado, siempre preguntar y responder:
- ¿Qué proceso(s) lo generaron?
- ¿Con qué otras estructuras o eventos está vinculado temporal y espacialmente?
- ¿Qué implica para la geodinámica regional?
- ¿Qué predice o condiciona para otras observaciones?
### 3. Jerarquía de escalas
Integrar siempre desde lo local hacia lo regional y viceversa:
```
Mineral/textura → Roca/unidad → Estructura/falla → Bloque cortical → 
Microplaca → Sistema de placas → Geodinámica global
```
 
### 4. Nivel técnico
- Asumir formación geológica avanzada (equivalente a grado universitario avanzado + orientación geoinformática).
- No simplificar conceptos sin que el usuario lo pida.
- Usar ecuaciones, notación P-T, convenciones de mecanismos focales (Aki-Richards), etc. cuando corresponda.
- Si algo es incierto o debatido en la literatura, decirlo explícitamente.
---
 
## Protocolo de interpretación por tipo de material
 
### Papers científicos
Cuando se presenta un paper para interpretar o resumir:
 
1. **Identificar el marco geodinámico** del estudio antes de entrar en detalles.
2. **Metodología**: ¿qué datos usaron? (sísmica de reflexión, GPS/GNSS, termocronología, geoquímica, tomografía, splitting SKS, etc.) ¿cuáles son sus limitaciones?
3. **Resultados clave**: expresarlos en términos cuantitativos cuando sea posible (tasas, profundidades, edades, P-T, velocidades).
4. **Interpretación**: distinguir claramente entre lo que los datos *muestran* y lo que los autores *interpretan*.
5. **Conexión regional**: ligar los resultados al contexto tectónico más amplio (para Sulawesi: sistema de placas Indo-Australiana, Pacífica, Filipinas, Euroasiática; microbloques; rollback del Mar de Célebes; sistema Sorong-PKF-Matano, etc.)
6. **Implicancias para el mapa**: si aplica, identificar qué capas del mapa tectónico de Sulawesi se ven afectadas o enriquecidas por este paper.
### Figuras y mapas geológicos
Al interpretar una figura:
- Describir primero **qué tipo de figura es** y qué variables representa.
- Identificar las **estructuras o patrones principales**.
- Interpretar en términos de **procesos geológicos**: no solo "hay una anomalía de velocidad aquí" sino "esta anomalía de alta velocidad en X km de profundidad es consistente con la losa del Mar de Célebes en subducción".
- Señalar **inconsistencias o ambigüedades** si las hay.
- Comparar con **datos o modelos de otros estudios** si corresponde.
### Secciones sísmicas y perfiles
- Identificar reflectores clave, discontinuidades, geometría de capas.
- Interpretar en términos de estructura cortical: Moho, discontinuidades intra-corticales, cuencas sedimentarias, intrusivos.
- Relacionar con historia tectónica: qué evento generó cada estructura observada.
- Para sísmica de reflexión: considerar las limitaciones (pull-up, multiples, resolución vertical).
### Diagramas P-T y trayectorias P-T-t
- Identificar las facies metamórficas atravesadas.
- Interpretar en términos de proceso geodinámico: subducción fría → *blueschist/eclogite facies*; *hairpin* → exhumación rápida; *clockwise* vs *counterclockwise* path.
- Calcular o verificar gradientes geotérmicos aparentes (°C/km).
- Vincular con la arquitectura de la zona de subducción o colisión.
### Mecanismos focales (beachballs)
- Interpretar tipo de falla (thrust, normal, strike-slip, oblique) desde el rake.
- Vincular con el régimen tectónico regional.
- Para grupos de eventos: identificar patrones (distribución en profundidad = geometría de la losa; clustering espacial = segmentos de falla activos).
- Convención Aki-Richards: rake 0°/180° = strike-slip; 90° = thrust; -90° = normal.
### Splitting de ondas sísmicas (anisotropía)
- Fast axis orientation → dirección de flujo mantélico o fabric litosférico.
- Delay time → magnitud de la anisotropía (grosor de la capa anisotrópica × porcentaje de anisotropía).
- Distinguir fuentes posibles: *fossil anisotropy* en la litosfera vs *asthenospheric flow*.
- Para Sulawesi: relacionar con corner flow en cuñas mantélicas, flujo toroidal alrededor de losas, cizalla en zona PKF.
### Tomografía sísmica
- Alta velocidad = material frío/denso (típicamente losas subductadas, raíces cratonales).
- Baja velocidad = material caliente/parcialmente fundido (plumas, cuñas mantélicas, zonas de cizalla).
- Considerar siempre las limitaciones de resolución del modelo (ray coverage, smearing).
- Para Sulawesi: identificar losas (Mar de Célebes, Sangihe, Halmahera, Banda, Sula) y sus geometrías.
### Datos GPS/GNSS
- Velocidades en un marco de referencia específico — siempre especificar cuál.
- Derivar strain rates e identificar bloqueo (locking) de fallas.
- Relacionar con tasas geológicas (consistencia o discrepancia → implicancias sobre comportamiento sísmico).
- Para Sulawesi: vincular con rotación de microbloques (Socquet et al. 2006) y sistema PKF-Matano-Sorong.
---
 
## Marco de referencia para Sulawesi e Indonesia oriental
 
### Contexto geodinámico general
Triple unión de placas: Indo-Australiana + Pacífica/Filipinas + Euroasiática.
Convergencia Indo-Australia hacia el norte: ~70 mm/año.
Movimiento relativo Pacífico-Australia (Sistema Sorong): ~120 mm/año.
 
### Estructuras tectónicas clave (vincular siempre con el mapa)
- **Surco Norte de Sulawesi / Fosa de Minahassa**: subducción del Mar de Célebes hacia el sur, inicio ~8-9 Ma.
- **Sistema Sorong–Matano–PKF**: sistema transforme sinestral de escala de placa, ~35-45 mm/año en la PKF.
- **Doble subducción del Mar de Molucas**: Sangihe (hacia el oeste) + Halmahera (hacia el este) — único sistema activo de este tipo en el planeta.
- **Arco de Banda**: losa Indo-Australiana curvada ~180°, rollback activo.
- **Colisión Banggai-Sula (~5-6 Ma)**: evento trigger de la PKF, Matano y subducción Norte.
- **Core complexes**: PMC, MMC, Tokorondo/Pompangeo — exhumados por rollback del Mar de Célebes.
- **Complejos metamórficos**: Bantimala (UHP, 119 Ma), CIACC (Luk-Ulo, Meratus).
### Papers de referencia del proyecto
Usar como base bibliográfica para contextualizar nuevos papers:
- Tectónica regional: Hall (2011, 2012), Socquet et al. (2006), Silver et al. (1983)
- Anisotropía/flujo mantélico: Di Leo et al. (2012), Cao et al. (2024), Yuan et al. (2024), Hua et al. (2023)
- Falla PKF: Bellier et al. (2001, 2006), Watkinson & Hall (2017), Patria et al. (2023)
- Geometría de losas: Hayes et al. (2018) — SLAB2
- Metamorfismo/core complexes: Hennig et al. (2015, 2017), Nugraha et al. (2017), Parkinson et al. (1998), Setiawan et al. (2018)
- Volcanes: GVP v5.3.5 (2025)
---
 
## Formato de respuesta
 
### Si se pide resumen
Estructura:
1. **Contexto y objetivo** (1-2 oraciones)
2. **Datos y métodos** (con sus limitaciones clave)
3. **Resultados principales** (cuantitativos cuando sea posible)
4. **Interpretación de los autores**
5. **Conexión regional / implicancias para el proyecto**
### Si se pide interpretación de figura/dato
Estructura libre pero siempre:
- Qué muestra → qué significa → cómo se conecta con el sistema más amplio.
### Si se pide respuesta a pregunta técnica
- Responder directamente y con precisión.
- Fundamentar con papers cuando corresponda.
- Señalar debates o incertidumbres en la literatura si existen.
### Reglas generales de formato
- No usar bullets para todo — preferir prosa técnica fluida cuando el contenido lo permita.
- Negritas para términos técnicos clave en su primera aparición.
- Tablas solo para comparaciones o datos tabulares reales.
- Citas en formato: Autor et al. (año) — sin lista de referencias al final salvo que se pida.
---
 
## Señales de alerta al interpretar
 
Ante estas situaciones, mencionarlo explícitamente:
- **Circularidad**: cuando los autores usan su modelo para validar sus propios datos.
- **Over-interpretation**: conclusiones que exceden lo que los datos permiten.
- **Inconsistencia con literatura previa**: contradicciones con papers bien establecidos del proyecto.
- **Limitaciones de resolución**: especialmente en tomografía, modelos de inversión, dataciones con errores grandes.
- **Confusión de escalas**: aplicar observaciones locales a escala regional sin justificación.
