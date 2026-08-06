# ocu — univers interactiu

Web experimental i creativa publicada a **[ocu.cat](https://ocu.cat)**. Un llenç
(canvas) infinit on cada paraula és un món: tipografies que giren com una
màquina escurabutxaques, jocs, visors de contingut i eines interactives.

## Què hi ha

- **Llenç interactiu** — paraules arrossegables amb efectes tipogràfics i de color.
- **Jocs** — Snake (amb galetes "Kuki" que fan la serp més ampla i un boost del
  conill), Pong i un laberint.
- **Visor 3D (STL)** — models a `content/ocu3D/` renderitzats amb three.js.
- **Visor de PDF** — zines i documents (`content/zines/`), amb pdf.js (`lib/`).
- **Tecla** — teclat/simulador MIDI (WebMIDI).
- **Temes** — color de fons i d'elements personalitzables en directe.

Idioma per defecte: català.

## Estructura

```
index.html          # App principal (canvas, jocs, lògica — actualment monolítica)
css/style.css       # Estils extrets
js/                 # Mòduls (stl-viewer, info-viewer, tecla-viewer s'usen;
                    #   la resta és una refactorització en curs, encara no carregada)
lib/                # pdf.js + visor de PDF (vendored)
content/            # Contingut: ocu3D/ (STL), zines/ (PDF), newtro/, kuki/ ...
assets/             # Imatges de la interfície (kuki, sinte, ...)
fonts/              # Tipografies (Minecraft, O-Regular)
.github/workflows/  # Desplegament automàtic per FTP
```

## Desenvolupament local

```bash
python3 server.py       # servidor estàtic senzill
# o
python3 -m http.server 8000
```

Obre `http://localhost:8000`.

## Desplegament

Cada `push` a `main` desplega automàticament a ocu.cat via FTPS
(`.github/workflows/deploy.yml`). Requereix els secrets de repositori
`FTP_SERVER`, `FTP_USERNAME`, `FTP_PASSWORD` i `FTP_DIR`.

> ⚠️ El mètode antic (`github_deploy.php` + token públic) s'ha retirat per
> raons de seguretat. No el tornis a pujar al servidor.

## Notes tècniques

- Fitxers `.stl` grans (arrel del repo) **no** es versionen ni es despleguen;
  serveix els models des de `content/ocu3D/` o emmagatzematge extern.
- `three.js` i `pdf.js` es carreguen des de CDN; `lib/` en manté una còpia local.
