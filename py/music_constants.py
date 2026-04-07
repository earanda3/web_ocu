"""
Constants musicals compartides per estalviar RAM
Utilitzar tuples (immutables) en lloc de llistes per reduir memòria
"""

# Escales: només intervals (sense noms per estalviar RAM)
# Accés: SCALES[scale_id]
SCALES = (
    (0, 2, 4, 5, 7, 9, 11),      # 0: Jònic (Major)
    (0, 2, 3, 5, 7, 9, 10),      # 1: Dòric
    (0, 1, 3, 5, 7, 8, 10),      # 2: Frigi
    (0, 2, 4, 6, 7, 9, 11),      # 3: Lidi
    (0, 2, 4, 5, 7, 9, 10),      # 4: Mixolidi
    (0, 2, 3, 5, 7, 8, 10),      # 5: Eòlic (Minor)
    (0, 1, 3, 5, 6, 8, 10),      # 6: Locri
    (0, 2, 4, 7, 9),             # 7: Pentatònica Major
    (0, 3, 5, 7, 10),            # 8: Pentatònica Menor
    (0, 1, 4, 6, 7),             # 9: Japonesa
    (0, 2, 5, 7, 9),             # 10: Egípcia
    (0, 1, 4, 5, 7, 8, 11),      # 11: Aràbiga
    (0, 2, 3, 6, 7, 9, 10),      # 12: Hongaresa Menor
    (0, 2, 4, 6, 7, 9, 10),      # 13: Lídia Dominant
    (0, 1, 3, 4, 6, 8, 10),      # 14: Alterada
    (0, 2, 3, 5, 7, 9, 11),      # 15: Menor Melòdica
    (0, 1, 4, 5, 7, 8, 11),      # 16: Raga Bhairav
    (0, 1, 3, 6, 7, 8, 11),      # 17: Raga Todi
    (0, 1, 4, 5, 7, 8, 10),      # 18: Flamenca
    (0, 1, 4, 5, 7, 9, 11),      # 19: Catalana
    (0, 1, 3, 5, 7, 8, 10),      # 20: Frígia
    (0, 1, 4, 5, 7, 8, 11),      # 21: Balcànica
    (0, 2, 4, 6, 8, 10),         # 22: Tons Sencers
    (0, 2, 4, 5, 7, 8, 11),      # 23: Harmònica Major
)

# Noms de les escales (per mostrar en prints)
SCALE_NAMES = (
    'Jònic (Major)',        # 0
    'Dòric',                # 1
    'Frigi',                # 2
    'Lidi',                 # 3
    'Mixolidi',             # 4
    'Eòlic (Minor)',        # 5
    'Locri',                # 6
    'Pentatònica Major',    # 7
    'Pentatònica Menor',    # 8
    'Japonesa',             # 9
    'Egípcia',              # 10
    'Aràbiga',              # 11
    'Hongaresa Menor',      # 12
    'Lídia Dominant',       # 13
    'Alterada',             # 14
    'Menor Melòdica',       # 15
    'Raga Bhairav',         # 16
    'Raga Todi',            # 17
    'Flamenca',             # 18
    'Catalana',             # 19
    'Frígia',               # 20
    'Balcànica',            # 21
    'Tons Sencers',         # 22
    'Harmònica Major',      # 23
)

# Modes d'arpegiador: només direcció (sense noms)
# Strings curts per estalviar memòria
ARP_DIRS = (
    'up', 'down', 'pingpong', 'random', 'order',
    'alberti', 'alberti_alt', 'waltz', 'broken', 'tremolo',
    'zigzag', 'block', 'rolled', 'octaves', 'contrary', 'spread'
)

# Tonalitats
KEYS = (0, 7, 2, 9, 4, 11, 6, 1, 8, 3, 10, 5)  # Offsets en semitons

# Notes musicals
NOTES = ('C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B')

# Acords: només intervals
CHORDS = {
    'Major': (0, 4, 7),
    'm': (0, 3, 7),
    '7': (0, 4, 7, 10),
    'maj7': (0, 4, 7, 11),
    'm7': (0, 3, 7, 10),
    'dim': (0, 3, 6),
    'aug': (0, 4, 8),
    'sus4': (0, 5, 7),
    'sus2': (0, 2, 7),
}

# Mapatge notes → offset (generat dinàmicament per estalviar RAM)
def note_offset(note_name):
    """Retorna l'offset MIDI d'una nota"""
    try:
        return NOTES.index(note_name)
    except ValueError:
        return 0
