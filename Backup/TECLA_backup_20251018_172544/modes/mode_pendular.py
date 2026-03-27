"""
Mode Pèndol - Genera un patró oscil·lant de notes que recorda el moviment d'un pèndul
"""
import time
import math
import random
from modes.base_mode import BaseMode

class ModePendular(BaseMode):
    def __init__(self, midi_out, config=None):
        super().__init__(midi_out, config)
        self.name = "Pèndol"
        self.notes_playing = set()
        self.last_update = time.monotonic()
        
        # Paràmetres del moviment pendular
        self.angle = 0.0          # Angle actual en radians
        self.velocity = 0.0        # Velocitat angular
        self.damping = 0.999       # Menys fregament per a un moviment més llarg
        self.gravity = 9.8         # Acceleració gravitatòria
        self.length = 2.0          # Pèndol més llarg per a un moviment més lent
        
        # Paràmetres musicals
        self.base_note = 48        # Una octava més baixa (C3)
        self.range_notes = 12       # Abast d'una octava
        self.current_note = None    # Nota actual
        self.last_note_time = 0     # Últim canvi de nota
        self.note_duration = 0.5    # Notes més llargues
        self.last_note_played = -1  # Per controlar l'espai entre notes
        
        # Control de paràmetres
        self.energy = 0.3          # Menys energia per a un moviment més suau
        self.tempo = 0.3           # Tempo més lent
        self.range_ctrl = 0.5       # Control de l'abast de notes (0.0 a 1.0)
        
        # Escala pentatònica per a un so més harmònic
        self.pentatonic = [0, 2, 4, 7, 9]  # Do pentatònic major
        
        # Inicialitzar last_velocity per a la detecció de canvis de direcció
        self.last_velocity = 0.0
        
    def setup(self):
        self.initialized = True
        self.last_update = time.monotonic()
        self.notes_playing.clear()
        
        # Inicialitzar l'angle amb una mica d'energia
        self.angle = math.pi * 0.25  # 45 graus
        self.velocity = 0.0
        
        # Configuració inicial dels paràmetres
        self._update_parameters(64, 64, 64)
    
    def _update_parameters(self, energy_pot, tempo_pot, range_pot):
        """Actualitza els paràmetres a partir dels valors dels potenciòmetres"""
        # Energia (més baixa per a menys moviment)
        self.energy = 0.1 + (energy_pot / 127.0) * 0.4  # Rang reduït: 0.1 a 0.5
        
        # Tempo més lent (0.05 a 0.5 Hz)
        self.tempo = 0.05 + (tempo_pot / 127.0) * 0.45
        
        # Abast de notes (5a justa a 1 octava)
        self.range_notes = 7 + int((range_pot / 127.0) * 5)  # 7 a 12 semitons
        
        # Ajustar la longitud del pèndul per al tempo desitjat
        target_period = 1.0 / (self.tempo + 0.001)  # Evitar divisió per zero
        self.length = (target_period / (2 * math.pi)) ** 2 * self.gravity
        
        # Ajustar la durada de les notes segons el tempo
        self.note_duration = 0.3 + (1.0 / (self.tempo + 0.1)) * 0.7
    
    def _angle_to_note(self, angle):
        """Converteix un angle a una nota MIDI, utilitzant una escala pentatònica"""
        # Normalitzar l'angle a [0, 1]
        normalized = (math.sin(angle) + 1) / 2.0  # Ara està entre 0 i 1
        
        # Escalar a l'abast de l'escala pentatònica
        scale_pos = int(normalized * (len(self.pentatonic) - 0.001))
        scale_pos = max(0, min(len(self.pentatonic) - 1, scale_pos))
        
        # Afegir octaves per a més varietat
        octave_offset = int(normalized * 2) - 1  # -1, 0 o 1
        
        # Calcular la nota final
        note = self.base_note + self.pentatonic[scale_pos] + (octave_offset * 12)
        return max(0, min(127, note))  # Assegurar que estigui dins del rang MIDI
    
    def _play_note(self, note, velocity=80):
        """Reprodueix una nota amb un atac i alliberament suaus"""
        current_time = time.monotonic()
        
        # Si ja està sonant aquesta nota, no fer res
        if note == self.current_note and (current_time - self.last_note_time) < self.note_duration * 0.8:
            return
        
        # Aturar la nota anterior amb alliberament suau
        if self.current_note is not None:
            # Enviar un note-off amb alliberament progressiu
            release_velocity = max(0, min(127, velocity - 20))  # Una mica més suau
            self.midi_out.send(self.note_off(self.current_note, release_velocity))
            if self.current_note in self.notes_playing:
                self.notes_playing.remove(self.current_note)
        
        # Reproduir la nova nota amb atac progressiu
        attack_velocity = max(0, min(127, velocity - 10))  # Començar una mica més suau
        self.midi_out.send(self.note_on(note, attack_velocity))
        
        # Aplicar un lleuger vibrato amb pitch bend per afegir calidesa
        # Això dependrà de la implementació del teu controlador MIDI
        # Potser vulguis ajustar o eliminar aquesta part segons el teu sintetitzador
        if hasattr(self.midi_out, 'pitch_bend'):
            # Petita variació de pitch per afegir calidesa
            bend_amount = random.randint(-100, 100)
            self.midi_out.pitch_bend(bend_amount)
        
        self.notes_playing.add(note)
        self.current_note = note
        self.last_note_time = current_time
    
    def update(self, pot_values, button_states):
        current_time = time.monotonic()
        dt = min(0.1, current_time - self.last_update)  # Limitar dt per evitar salts grans
        self.last_update = current_time
        
        # Actualitzar paràmetres des dels potenciòmetres
        self._update_parameters(*pot_values)
        
        # Actualitzar física del pèndul (integració d'Euler simple)
        acceleration = -(self.gravity / self.length) * math.sin(self.angle)
        self.velocity += acceleration * dt
        self.velocity *= self.damping  # Aplicar fregament
        self.angle += self.velocity * dt
        
        # Mantenir l'angle dins d'un rang raonable (-π/2 a π/2)
        if abs(self.angle) > math.pi * 0.9:
            self.angle = math.copysign(math.pi * 0.9, self.angle)
            self.velocity = -self.velocity * 0.7  # Rebot amb més pèrdua d'energia
        
        # Aplicar energia constant per mantenir el moviment (més suau)
        if abs(self.velocity) < 0.005:
            self.velocity += (random.random() - 0.5) * 0.02  # Pertorbació més petita
        
        # Aplicar energia basada en el paràmetre d'energia
        energy_factor = 1.0 + (self.energy * 0.05)  # Menys variació d'energia
        self.velocity *= energy_factor
        
        # Calcular la nota actual basada en l'angle
        current_note = self._angle_to_note(self.angle)
        
        # Només reproduir notes en punts específics del moviment (punts alts i baixos)
        should_play_note = False
        
        # Detectar canvis de direcció o punts d'inflexió
        if (self.velocity * self.last_velocity <= 0 and 
            current_time - self.last_note_time > 0.2):  # Temps mínim entre notes
            should_play_note = True
            
        # També reproduir notes ocasionals en punts alts/baixos de l'oscil·lació
        if (abs(self.angle) > math.pi * 0.7 and 
            random.random() < 0.3 and 
            current_time - self.last_note_time > 0.5):
            should_play_note = True
        
        # Actualitzar l'última velocitat per a la propera comprovació
        self.last_velocity = self.velocity
        
        # Reproduir la nota si cal
        if should_play_note and current_note != self.last_note_played:
            # Velocitat basada en l'angle (més fort al centre, més suau als extrems)
            velocity = int(60 + abs(math.sin(self.angle)) * 40)
            velocity = max(40, min(100, velocity))  # Rang més controlat
            
            # Reproduir la nota amb una durada més llarga
            self._play_note(current_note, velocity)
            self.last_note_time = current_time
            self.last_note_played = current_note
        
        # Informació de depuració
        debug_info = {
            'angle_deg': int(math.degrees(self.angle)),
            'velocity': int(self.velocity * 100),
            'note': current_note,
            'energy': int(self.energy * 100),
            'tempo': self.tempo,
            'range': self.range_notes
        }
        
        # Afegir la velocitat de la nota si s'ha tocat una nota
        if should_play_note and current_note != self.last_note_played:
            debug_info['note_vel'] = velocity
            
        return debug_info
    
    def cleanup(self):
        notes_to_stop = list(self.notes_playing)
        self.notes_playing.clear()
        
        # Aturar totes les notes
        for note in notes_to_stop:
            self.midi_out.send(self.note_off(note, 0))
        
        self.current_note = None
        return [(note, 0) for note in notes_to_stop]
