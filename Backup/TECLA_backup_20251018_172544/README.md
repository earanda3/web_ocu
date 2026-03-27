# TECLA - Sintetitzador MIDI Modular

TECLA és un sintetitzador MIDI modular desenvolupat per a plataformes embegudes amb CircuitPython. Aquest projecte permet crear sons i seqüències musicals mitjançant diferents modes d'operació, cadascun amb les seves pròpies característiques i comportaments.

## Característiques

- Múltiples modes d'operació (batec, harmonic, melodic, etc.)
- Control mitjançant potenciòmetres i botons
- Sortida MIDI per a controlar sintetitzadors externs
- Arquitectura modular per a fàcil expansió

## Estructura del Projecte

- `/config`: Configuració de l'aplicació
- `/modes`: Modes d'operació del sintetitzador
- `/core`: Mòduls principals del sistema
- `main.py`: Punt d'entrada principal de l'aplicació

## Requisits

- CircuitPython 7.0 o superior
- Mòduls necessaris:
  - adafruit_midi
  - Altres mòduls estàndard de CircuitPython

## Instal·lació

1. Copia el contingut d'aquest directori a la teva placa amb CircuitPython
2. Assegura't que tots els mòduls necessaris estan instal·lats
3. Connecta els potenciòmetres i botons segons la configuració a `config/settings.py`

## Ús

1. Connecta la placa al teu sintetitzador MIDI
2. Selecciona el mode d'operació amb els botons
3. Ajusta els paràmetres amb els potenciòmetres

## Llicència

Aquest projecte està sota la llicència MIT. Consulta el fitxer `LICENSE` per a més informació.
