# Plataforma de PDFs

Una plataforma web senzilla per compartir i descarregar arxius PDF.

## Característiques

- Interfície neta amb fons blanc
- Visualització automàtica de tots els PDFs disponibles
- Descàrrega directa dels arxius
- Responsive design
- Servidor Python integrat

## Com utilitzar-la

1. **Iniciar el servidor:**
   ```bash
   python3 server.py
   ```

2. **Obrir el navegador:**
   - Ves a `http://localhost:8000`

3. **Afegir nous PDFs:**
   - Simplement copia els arxius PDF a la carpeta del projecte
   - Es mostraran automàticament a la web

## Estructura del projecte

```
pdf-platform/
├── server.py              # Servidor Python
├── index.html             # Interfície web
├── README.md              # Aquesta documentació
└── *.pdf                  # Els teus arxius PDF
```

## Funcionalitats

- **Llistat automàtic**: Tots els PDFs de la carpeta es mostren automàticament
- **Descàrrega segura**: Els arxius es serveixen amb els headers correctes
- **Informació dels arxius**: Es mostra la mida de cada PDF
- **Interfície moderna**: Disseny net i fàcil d'utilitzar

## Notes tècniques

- El servidor funciona per defecte al port 8000
- Si el port està ocupat, automàticament prova el següent
- Compatible amb tots els navegadors moderns
- Suporta arxius PDF de qualsevol mida
