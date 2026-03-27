"""
Mocks de CircuitPython per al simulador web TECLA (Pyodide).
Port de core/simulator_mocks.py per a l'execució al navegador.

_js_midi_send ha d'estar definida com a global Python abans de cridar install_mocks():
  la injecta tecla-simulator.js via pyodide.globals.set()
"""
import sys
import types
import time


# ── Estat compartit (llegit/escrit des de JS via Pyodide proxy) ──────────────

class _SharedState:
    def __init__(self):
        self.buttons = [False] * 16
        self.pots    = [0, 0, 0]   # valors 0-127

    def set_button(self, i, v):
        if 0 <= i < 16:
            self.buttons[i] = bool(v)

    def set_pot(self, i, v):
        if 0 <= i < 3:
            self.pots[i] = int(v)

_state = _SharedState()


# ── Helpers ──────────────────────────────────────────────────────────────────

def _create_mod(name):
    m = types.ModuleType(name)
    sys.modules[name] = m
    return m


# ── Mock classes ─────────────────────────────────────────────────────────────

class _MockPin:
    def __init__(self, name): self.name = name
    def __repr__(self): return f"board.{self.name}"

class _MockDigitalInOut:
    def __init__(self, pin):
        self.pin = pin
        self.direction = None
        self.pull = None
        self._v = False
        self.bi = -1
        if hasattr(pin, 'name') and pin.name.startswith('GP'):
            try: self.bi = int(pin.name[2:])
            except: pass

    @property
    def value(self):
        return _state.buttons[self.bi] if 0 <= self.bi < 16 else self._v

    @value.setter
    def value(self, v): self._v = v

class _MockAnalogIn:
    def __init__(self, pin):
        self.pi = -1
        if hasattr(pin, 'name') and pin.name.startswith('A'):
            try: self.pi = int(pin.name[1:])
            except: pass

    @property
    def value(self):
        # Retorna valors 0-65535 (rang analogic CircuitPython)
        return (_state.pots[self.pi] * 516) if 0 <= self.pi < 3 else 0

class _MockPWMOut:
    def __init__(self, pin, **kw):
        self.duty_cycle = 0
        self.frequency = 440
    def deinit(self): pass

class _NoteOn:
    def __init__(self, note, velocity, channel=None):
        self.note = note & 0x7F
        self.velocity = velocity & 0x7F
        self.channel = channel or 0
    def __repr__(self): return f"NoteOn {self.note} vel={self.velocity} ch={self.channel}"

class _NoteOff:
    def __init__(self, note, velocity=0, channel=None):
        self.note = note & 0x7F
        self.velocity = (velocity or 0) & 0x7F
        self.channel = channel or 0
    def __repr__(self): return f"NoteOff {self.note} ch={self.channel}"

class _ControlChange:
    def __init__(self, control, value, channel=None):
        self.control = control
        self.value = value
        self.channel = channel or 0
    def __repr__(self): return f"CC {self.control}={self.value} ch={self.channel}"

class _PitchBend:
    def __init__(self, pitch_bend, channel=None):
        self.pitch_bend = pitch_bend
        self.channel = channel or 0
    def __repr__(self): return f"PitchBend {self.pitch_bend} ch={self.channel}"

class _MockMIDI:
    def __init__(self, midi_out=None, *a, **kw): pass

    def send(self, msg, channel=None):
        t = type(msg).__name__
        ch = int(getattr(msg, 'channel', 0) or 0)
        if t in ('_NoteOn', 'NoteOn'):
            _js_midi_send('note_on', int(msg.note), int(msg.velocity), ch)
        elif t in ('_NoteOff', 'NoteOff'):
            _js_midi_send('note_off', int(msg.note), int(getattr(msg, 'velocity', 0) or 0), ch)
        elif t in ('_ControlChange', 'ControlChange'):
            _js_midi_send('control_change', int(msg.control), int(msg.value), ch)
        elif t in ('_PitchBend', 'PitchBend'):
            _js_midi_send('pitchwheel', int(msg.pitch_bend), 0, ch)


# ── Instal·lar tots els mocks ─────────────────────────────────────────────────

def install_mocks():
    # board
    b = _create_mod('board')
    for i in range(29): setattr(b, f'GP{i}', _MockPin(f'GP{i}'))
    for i in range(4):  setattr(b, f'A{i}',  _MockPin(f'A{i}'))
    setattr(b, 'LED', _MockPin('LED'))

    # digitalio
    di = _create_mod('digitalio')
    di.DigitalInOut = _MockDigitalInOut
    di.Direction = type('Direction', (), {'INPUT': 0, 'OUTPUT': 1})
    di.Pull = type('Pull', (), {'UP': 0, 'DOWN': 1})

    # analogio
    ai = _create_mod('analogio')
    ai.AnalogIn = _MockAnalogIn

    # pwmio
    pw = _create_mod('pwmio')
    pw.PWMOut = _MockPWMOut

    # usb_midi
    um = _create_mod('usb_midi')
    um.ports = [None, "MOCK_PORT"]

    # adafruit_midi + submòduls
    am = _create_mod('adafruit_midi')
    am.MIDI = _MockMIDI
    no_m = _create_mod('adafruit_midi.note_on');         no_m.NoteOn = _NoteOn
    noff_m = _create_mod('adafruit_midi.note_off');      noff_m.NoteOff = _NoteOff
    cc_m = _create_mod('adafruit_midi.control_change');  cc_m.ControlChange = _ControlChange
    pb_m = _create_mod('adafruit_midi.pitch_bend');      pb_m.PitchBend = _PitchBend

    # supervisor
    sv = _create_mod('supervisor')
    sv.reload = lambda: None

    # main (per compatibilitat amb base_mode.py que fa "import main")
    mn = _create_mod('main')
    mn.pwm = _MockPWMOut(None)
    mn.midi_to_frequency = lambda n: round(440 * (2 ** ((n - 69) / 12)))

    # gc compat (CircuitPython té gc.mem_free)
    import gc
    if not hasattr(gc, 'mem_free'):
        gc.mem_free = lambda: 100000

    # time.monotonic compat
    if not hasattr(time, 'monotonic'):
        time.monotonic = time.time

    print("✓ Mocks TECLA instal·lats al Pyodide")


# Funció per accedir a l'estat des de JS
def get_state():
    return _state
