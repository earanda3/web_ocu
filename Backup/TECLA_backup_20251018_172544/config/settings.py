# Configuració bàsica del projecte TECLA

# Pins dels botons digitals
DIGITAL_PINS = [
    'GP1', 'GP0', 'GP3', 'GP2', 'GP5', 'GP4', 'GP7', 'GP6',
    'GP9', 'GP8', 'GP11', 'GP10', 'GP13', 'GP12', 'GP15', 'GP14'
]

# Pins dels potenciòmetres analògics
POT_PINS = ['A1', 'A0', 'A2']

# Configuració MIDI
MIDI_CHANNEL = 0
DEFAULT_VELOCITY = 100
DEFAULT_OCTAVE = 0

# Configuració de modes
AVAILABLE_MODES = {
    0: 'mode_estandard',
    1: 'mode_harmonic',
    2: 'mode_ritmic',
    3: 'mode_melodic',
    4: 'mode_aleatori',
    5: 'mode_batec',
    6: 'mode_jazz',
    7: 'mode_perlin',
    8: 'mode_math',
    9: 'mode_ecos',
    10: 'mode_tormenta',
    11: 'mode_vibrato',
    12: 'mode_math_avancat',
    13: 'mode_math_pro',
    23: 'mode_math_harmonic'
}

# Altres constants
SAMPLE_RATE = 30  # Hz, freqüència de mostreig dels potenciòmetres
DEBOUNCE_TIME = 0.05  # segons, temps de rebot dels botons
