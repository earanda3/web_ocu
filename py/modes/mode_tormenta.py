"""
Mode Tempesta - Versió optimitzada per memòria
"""
import time
import math
import random
from modes.base_mode import BaseMode
from adafruit_midi.note_on import NoteOn
from adafruit_midi.note_off import NoteOff

class ModeTormenta(BaseMode):
    def __init__(self, midi_out, config=None):
        super().__init__(midi_out, config)
        self.name = "Tempesta"
        self.background_intensity = 0.0
        self.thunder_intensity = 0.0
        self.lightning_intensity = 0.0
        self.background_notes = {
            'deep_hum': {'note': 24, 'velocity': 0, 'active': False},
            'low_rumble': {'note': 28, 'velocity': 0, 'active': False},
            'mid_rumble': {'note': 32, 'velocity': 0, 'active': False},
            'vibration': {'note': 36, 'velocity': 0, 'active': False}
        }
        self.last_lightning = 0
        self.last_thunder = 0
        self.notes_playing = set()
        self.last_update = time.monotonic()

    def generate_storm_sounds(self, x, y, z):
        current_time = time.monotonic()
        self.thunder_intensity = x / 127.0
        self.lightning_intensity = y / 127.0
        self.background_intensity = z / 127.0
        storm_sounds = []
        self._update_background(current_time)
        if (current_time - self.last_thunder) > (3.0 - (self.thunder_intensity * 2.5)) and random.random() < (self.thunder_intensity * 0.7):
            self._add_thunder_sound(current_time, storm_sounds)
            self.last_thunder = current_time
        lightning_wait = max(0.1, 2.0 - (self.lightning_intensity * 1.9))
        if (current_time - self.last_lightning) > lightning_wait:
            num = 1 + int(self.lightning_intensity * 5) if self.lightning_intensity > 0.3 else 1
            for i in range(num):
                self._add_lightning_sound(current_time + (i * 0.2), storm_sounds, i)
            self.last_lightning = current_time
        self.last_update = current_time
        return storm_sounds

    def _update_background(self, current_time):
        for key, note_info in self.background_notes.items():
            target = int(self.background_intensity * 60)
            if note_info['velocity'] < target:
                note_info['velocity'] = min(note_info['velocity'] + 2, target)
            elif note_info['velocity'] > target:
                note_info['velocity'] = max(note_info['velocity'] - 2, target)
            if note_info['velocity'] > 0 and not note_info['active']:
                self.midi_out.send(NoteOn(note_info['note'], note_info['velocity']))
                note_info['active'] = True
                self.notes_playing.add(note_info['note'])  # Rastrejar nota
            elif note_info['velocity'] == 0 and note_info['active']:
                self.midi_out.send(NoteOff(note_info['note'], 0))
                note_info['active'] = False
                self.notes_playing.discard(note_info['note'])  # Deixar de rastrejar
            elif note_info['active']:
                self.midi_out.send(NoteOn(note_info['note'], note_info['velocity']))

    def _add_thunder_sound(self, current_time, sounds):
        note = random.randint(25, 35)
        velocity = int(50 + self.thunder_intensity * 70)
        sounds.append({'type': 'thunder', 'note': note, 'velocity': velocity, 'duration': 1.5 + random.random() * 1.5, 'time': current_time})

    def _add_lightning_sound(self, current_time, sounds, index):
        note = random.randint(90, 110)
        velocity = int(80 + random.random() * 40)
        sounds.append({'type': 'lightning', 'note': note, 'velocity': velocity, 'duration': 0.05 + random.random() * 0.1, 'time': current_time})
        if index == 0:
            delay = 0.1 + random.random() * 0.3
            thunder_note = random.randint(25, 35)
            thunder_vel = int(60 + self.thunder_intensity * 50)
            sounds.append({'type': 'thunder_echo', 'note': thunder_note, 'velocity': thunder_vel, 'duration': 1.0 + random.random() * 1.5, 'time': current_time + delay})

    def play_storm_sounds(self, storm_sounds, current_time):
        for sound in storm_sounds:
            if sound['time'] <= current_time:
                if sound['note'] not in self.notes_playing:
                    self.midi_out.send(NoteOn(sound['note'], sound['velocity']))
                    self.notes_playing.add(sound['note'])

    def update(self, pot_values, button_states=None):
        x, y, z = pot_values
        current_time = time.monotonic()
        storm_sounds = self.generate_storm_sounds(x, y, z)
        self.play_storm_sounds(storm_sounds, current_time)
        to_stop = []
        for note in self.notes_playing:
            if random.random() < 0.1:
                to_stop.append(note)
        for note in to_stop:
            self.midi_out.send(NoteOff(note, 0))
            self.notes_playing.discard(note)

    def stop(self):
        from adafruit_midi.control_change import ControlChange
        
        # CRÍTIC: Sustain OFF PRIMER per alliberar notes enganxades
        try:
            for channel in range(3):  # Canals 0-2
                self.midi_out.send(ControlChange(64, 0, channel=channel))
        except:
            pass
        
        # Aturar background_notes (supergreus) amb NoteOff TRIPLE per assegurar parada
        for note_info in self.background_notes.values():
            if note_info['active'] or note_info['velocity'] > 0:
                # Enviar NoteOff 3 vegades per garantir que el sintetitzador ho processa
                for _ in range(3):
                    try:
                        self.midi_out.send(NoteOff(note_info['note'], 0))
                    except:
                        pass
                note_info['active'] = False
                note_info['velocity'] = 0
        
        # Aturar totes les altres notes (llamps, trons)
        for note in list(self.notes_playing):
            try:
                self.midi_out.send(NoteOff(note, 0))
            except:
                pass
        self.notes_playing.clear()
    
    def cleanup(self):
        """Neteja en sortir del mode - Sistema Mandelbrot"""
        # 1. Aturar TOTES les notes individualment (com Mandelbrot)
        for note in list(self.notes_playing):
            try:
                self.midi_out.send(NoteOff(note, 0))
            except:
                pass
        self.notes_playing.clear()
        
        # 2. Aturar background_notes explícitament
        for note_info in self.background_notes.values():
            if note_info['active']:
                try:
                    self.midi_out.send(NoteOff(note_info['note'], 0))
                except:
                    pass
                note_info['active'] = False
                note_info['velocity'] = 0
        
        # 3. Reset COMPLET: All Notes Off (només canals necessaris per reduir latència)
        from adafruit_midi.control_change import ControlChange
        try:
            # All Notes Off i All Sound Off només als canals 0-2 (redueix latència)
            for channel in range(3):  # Reduir de 16 a 3 canals per evitar latència
                self.midi_out.send(ControlChange(123, 0, channel=channel))  # All Notes Off
                self.midi_out.send(ControlChange(120, 0, channel=channel))  # All Sound Off
            
            # Reset controls
            self.midi_out.send(ControlChange(64, 0))  # Sustain OFF
        except Exception:
            pass
