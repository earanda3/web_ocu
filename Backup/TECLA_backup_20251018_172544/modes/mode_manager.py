"""
ModeManager - Gestiona els diferents modes del TECLA i les transicions entre ells.
Utilitza ConfigManager per gestionar la configuració dels modes i els bancs.
"""
import time
import os
from core.config_manager import ConfigManager
from modes.base_mode import BaseMode

# Diccionari amb els modes disponibles i les seves classes
MODE_CLASSES = {
    'Silenci': ('mode_silenci', 'ModeSilenci'),
    'Riu': ('mode_rio', 'ModeRio'),
    'Tempesta': ('mode_tormenta', 'ModeTormenta'),
    'Matemàtic': ('mode_matematic_armonic', 'ModeMatematicArmonic'),
    'Mandelbrot': ('mode_mandelbrot', 'ModeMandelbrot'),
    'Jazz': ('mode_jazz_chords', 'ModeJazzChords'),
    'Ecos': ('mode_ecos_pasado', 'ModeEcosPasado'),
    'Rítmic': ('mode_ritmic_loop', 'ModeRitmicLoop'),
    'Sinusoidal': ('mode_ona_sinusoidal', 'ModeOnaSinusoidal'),
    'Dinamo': ('mode_dinamo', 'ModeDinamo'),
    'Cascada': ('mode_cascada', 'ModeCascada'),
    'Pèndol': ('mode_pendular', 'ModePendular'),
    'Caos': ('mode_caos_controlat', 'ModeCaosControlat'),
    'Vida': ('mode_vida', 'ModeVida'),
    'Ressonàncies': ('mode_resonancies', 'ModeResonancies'),
    'Acords': ('mode_acords_aleatoris', 'ModeAcordsAleatoris'),
    # Nous modes
    'Harmonia': ('mode_harmonia_celeste', 'ModeHarmoniaCeleste'),
    'Biomímesi': ('mode_biomimesi', 'ModeBiomimesi'),
    'Mirall': ('mode_mirall_quantic', 'ModeMirallQuantic'),
    # Mode Teclat MIDI
    'Teclat': ('mode_teclat_midi', 'ModeTeclatMIDI'),
    # Mode Ritme Fractal
    'Fractal': ('mode_ritme_fractal', 'ModeRitmeFractal'),
    # Mode Veus
    'Veus': ('mode_veus', 'ModeVeus')
}

class ModeManager:
    """Gestiona tots els modes d'operació i les transicions entre ells."""
    
    def __init__(self, midi_out, config_path='config/tecla_config.json'):
        self.midi_out = midi_out
        self.modes = {}
        self.current_mode = None
        self.current_mode_name = None
        self.last_mode_change = time.monotonic()
        
        # Carregar tots els modes disponibles
        self._load_all_modes()
        
        # Iniciar amb el mode Silenci per defecte si està disponible
        if 'Silenci' in self.modes:
            self.set_mode('Silenci')
    
    def _load_all_modes(self):
        """Carrega tots els modes definits a MODE_CLASSES."""
        for mode_name, (module_name, class_name) in MODE_CLASSES.items():
            try:
                # Carregar el mòdul i la classe dinàmicament
                module = __import__(f'modes.{module_name}')
                module = getattr(module, module_name)
                mode_class = getattr(module, class_name)
                
                # Crear i inicialitzar la instància del mode
                self.modes[mode_name] = mode_class(self.midi_out, {})
                print(f"✓ Mode carregat: {mode_name}")
                
            except Exception as e:
                print(f"✗ Error carregant el mode {mode_name}: {e}")
    
    def set_mode(self, mode_name):
        """Canvia al mode especificat."""
        current_time = time.monotonic()
        
        # Evitar canvis massa ràpids
        if current_time - self.last_mode_change < 0.5:  # 500ms entre canvis
            return False
            
        # Verificar que el mode existeix
        if mode_name not in self.modes:
            print(f"✗ Mode no trobat: {mode_name}")
            return False
            
        self.last_mode_change = current_time
        
        # Aturar el mode actual
        if self.current_mode:
            self._stop_current_mode()
        
        # Iniciar el nou mode
        self.current_mode = self.modes[mode_name]
        self.current_mode_name = mode_name
        
        # Inicialitzar el nou mode si cal
        if hasattr(self.current_mode, 'setup'):
            self.current_mode.setup()
            
        print(f"Mode canviat a: {mode_name}")
        return True
        
    def get_available_modes(self):
        """Retorna una llista amb els noms dels modes disponibles."""
        return list(self.modes.keys())
        
    def _stop_current_mode(self):
        """Atura el mode actual i neteja els seus recursos."""
        if not self.current_mode:
            return
            
        try:
            notes_to_stop = self.current_mode.cleanup()
            if notes_to_stop:
                self._stop_notes(notes_to_stop)
        except Exception as e:
            print(f"Error en aturar el mode {self.current_mode_name}: {e}")
    
    def _stop_notes(self, notes_info):
        """Atura les notes especificades."""
        from adafruit_midi.note_off import NoteOff
        
        for note_info in notes_info:
            try:
                if len(note_info) >= 2:  # Mínim (note, velocity)
                    note, velocity = note_info[0], note_info[1]
                    channel = note_info[2] if len(note_info) > 2 else 0
                    
                    # Crear mensaje Note Off sin usar self.note_off
                    note_off_msg = NoteOff(note & 0x7F, velocity & 0x7F)
                    note_off_msg.channel = channel
                    self.midi_out.send(note_off_msg)
            except Exception as e:
                print(f"Error aturant nota {note_info}: {e}")
    
    def update(self, pot_values, button_states):
        """Actualitza l'estat actual del mode."""
        if not self.current_mode:
            return {'mode': 'Cap mode actiu'}
        
        try:
            # Actualitzar el mode actual amb nous valors
            status = self.current_mode.update(pot_values, button_states)
            
            # Assegurar que status és un diccionari
            if not isinstance(status, dict):
                status = {'status': str(status)}
                
            status['mode'] = self.current_mode_name
            return status
            
        except Exception as e:
            print(f"Error en l'actualització del mode: {e}")
            return {'mode': 'Error'}
    
    def cleanup(self):
        """Neteja tots els recursos utilitzats pels modes."""
        # Aturar el mode actual
        self._stop_current_mode()
        
        # Enviar senyals MIDI per aturar totes les notes
        self._panic()
        
        return []
    
    def _panic(self):
        """Atura totes les notes MIDI en tots els canals."""
        try:
            # Enviar All Notes Off i All Sound Off a tots els canals
            for channel in range(16):
                self.midi_out.send(self.control_change(123, 0, channel))  # All Notes Off
                self.midi_out.send(self.control_change(120, 0, channel))  # All Sound Off
                
            # Petita pausa per assegurar que s'envien les dades
            time.sleep(0.1)
            
        except Exception as e:
            print(f"Error en el panic MIDI: {e}")
    
    def note_on(self, note, velocity=127, channel=0):
        """Retorna un missatge de nota ON MIDI."""
        from adafruit_midi.note_on import NoteOn
        note_on_msg = NoteOn(note & 0x7F, velocity & 0x7F)
        note_on_msg.channel = channel
        return note_on_msg
        
    def note_off(self, note, velocity=0, channel=0):
        """Retorna un missatge de nota OFF MIDI."""
        from adafruit_midi.note_off import NoteOff
        note_off_msg = NoteOff(note & 0x7F, velocity & 0x7F)
        note_off_msg.channel = channel
        return note_off_msg
        
    def control_change(self, control, value, channel=0):
        """Retorna un missatge de control canvi MIDI."""
        from adafruit_midi.control_change import ControlChange
        return ControlChange(control, value, channel=channel)
        

