Verificar que todos los endpoints del backend responden correctamente.

Pasos:
1. Hacer GET a los siguientes endpoints y reportar status + datos clave de cada uno:
   - `http://localhost:8080/api/earthquakes?minMag=6.5&startYear=2000&endYear=2010` → mostrar `count`
   - `http://localhost:8080/api/annotations` → mostrar cantidad de anotaciones
   - `http://localhost:8080/api/catalog/live?minMag=5.5&days=30` → mostrar `count` y `with_mt`
2. Si algún endpoint falla (timeout, error 5xx, puerto cerrado), indicar cuál y sugerir si hay que reiniciar el servidor con `/restart-server`.
3. Mostrar un resumen final: ✓ OK / ✗ ERROR por endpoint.
