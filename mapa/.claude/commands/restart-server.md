Reiniciar el servidor de desarrollo del mapa.

Pasos:
1. Usar PowerShell para encontrar y matar cualquier proceso que esté usando el puerto 8080: `Get-NetTCPConnection -LocalPort 8080 -ErrorAction SilentlyContinue | ForEach-Object { Stop-Process -Id $_.OwningProcess -Force -ErrorAction SilentlyContinue }`
2. Esperar 1 segundo.
3. Lanzar uvicorn en background desde el directorio del proyecto: `uvicorn backend.main:app --host 0.0.0.0 --port 8080 --reload`
4. Confirmar que el servidor levantó haciendo GET a `http://localhost:8080/api/annotations` y reportar el resultado.
