"""
ModeManager - Gestiona els diferents modes del TECLA i les transicions entre ells.
Utilitza ConfigManager per gestionar la configuració dels modes i els bancs.
Tots els modes (excepte Teclat) es carreguen del registre sota demanda.
"""
import time
import os
import json

from core.config_manager import ConfigManager
from core.layer_manager import LayerManager
from modes.base_mode import BaseMode
from adafruit_midi.control_change import ControlChange
from adafruit_midi.note_on import NoteOn
from effects.effect_manager import EffectManager

def _get_mode_info_from_registry(mode_name):
    """Obté la informació d'un mode del registre JSON.
    Tots els modes (excepte Teclat) estan registrats al custom_modes_registry.json.
    Això estalvia memòria: només es carreguen modes sota demanda.
    """
    try:
        # Construir path absolut basant-se en la ubicació d'aquest fitxer
        try:
            import os
            current_dir = os.path.dirname(os.path.abspath(__file__))
            registry_path = os.path.join(current_dir, 'custom_modes_registry.json')
        except:
            # Fallback per CircuitPython pur (sense os.path)
            registry_path = 'modes/custom_modes_registry.json'
        
        # Llegir el registre
        try:
            with open(registry_path, 'r') as f:
                registry = json.load(f)
            
            modes_data = registry.get('custom_modes', {})
            if mode_name in modes_data:
                mode_info = modes_data[mode_name]
                return (mode_info['file_name'], mode_info['class_name'])
        except OSError:
            pass
    except Exception as e:
        print(f"⚠️ Error consultant registre per {mode_name}: {e}")
    
    return None

def _count_registered_modes():
    """Compta els modes registrats al JSON (tots excepte Teclat)."""
    try:
        try:
            import os
            current_dir = os.path.dirname(os.path.abspath(__file__))
            registry_path = os.path.join(current_dir, 'custom_modes_registry.json')
        except:
            registry_path = 'modes/custom_modes_registry.json'
        
        try:
            with open(registry_path, 'r') as f:
                registry = json.load(f)
            return len(registry.get('custom_modes', {}))
        except OSError:
            return 0
    except:
        return 0

# MODE_CLASSES: Només el mode Teclat està SEMPRE carregat a la RAM
# Tots els altres modes es carreguen del registre JSON sota demanda
MODE_CLASSES = {
    'Teclat': ('mode_keyboard', 'KeyboardMode'),
}

_registered_count = _count_registered_modes()
# Silenciós - no mostrar missatges verbosos

class ModeManager:
    """Gestiona tots els modes d'operació i les transicions entre ells."""
    
    # Configuració de memòria: Màxim de modes carregats simultàniament
    # El mode Teclat sempre està carregat, així que només podem tenir 2 modes més
    MAX_LOADED_MODES = 3  # Teclat + 2 modes addicionals màxim
    
    def __init__(self, midi_out=None):
        """Inicialitza el ModeManager."""
        self.midi_out = midi_out
        self.modes = {}
        self.current_mode = None
        self.current_mode_name = None
        self.banks = {}
        self.current_bank = None
        self.button_mappings = {}
        self.loaded_modes_history = []  # Tracking dels modes carregats (per LRU)
        
        # Efectes temporals: botons 14–15 (índex 13–14)
        self.effect_buttons = [13, 14]
        # Diccionari per gestionar els efectes temporals (per botó)
        default_effects = {
            13: 'Sustain',  # Botó 14
            14: 'Sustain',  # Botó 15
        }
        self.efectes_temporals = {}
        for btn in self.effect_buttons:
            self.efectes_temporals[btn] = {
                'active': False,
                'last_state': False,
                'press_time': 0,
                'last_release_time': 0,  # Per detectar doble clic
                'mode_instance': None,
                'pre_mode': None,
                'pre_mode_instance': None,
                'tipus': default_effects.get(btn, 'Sustain')
            }
        # Umbral per diferenciar toc curt (octava) vs mantenir (efecte)
        self.effect_hold_threshold = 0.35
        # Umbral per detectar doble clic
        self.double_click_threshold = 0.3  # segons (reduït per més agilitat)
        
        # Llista d'efectes disponibles per ciclar (s'actualitzarà des del config)
        self.available_effects = []
        # Octava global per a modes (no teclat)
        self.mode_octave = 0  # rang recomanat: -4..+4
        
        # Per compatibilitat amb codi existent (a eliminar més endavant)
        self.sustain_active = False
        self.sustain_press_time = 0
        self.sustain_last_state = False
        self.pre_sustain_mode = None
        self.pre_sustain_mode_instance = None
        self.sustain_mode = None
        
        self.pausa_active = False
        self.pausa_press_time = 0
        self.pausa_last_state = False
        self.pre_pausa_mode = None
        self.pre_pausa_mode_instance = None
        self.pausa_mode = None
        
        self.debounce_time = 0.2  # 200ms per a debounce en els canvis de botó
        
        # Inicialitzar el gestor de configuració
        self.config_manager = ConfigManager()
        
        # Inicialitzar el gestor de capes (després de les variables d'efectes)
        self.layer_manager = LayerManager(self)
        
        # Gestor d'efectes
        self.effect_manager = EffectManager(self.midi_out)
        
        # Control d'errors
        self.last_mode_error = None
        
        # Variables de "hold" (no utilitzades actualment, definides per evitar errors)
        self.hold_active = False
        self.hold_mode = None
        
        # Control de canvis de mode
        self.last_mode_change = time.monotonic()
        self.previous_mode_name = None
        
        # Carregar tots els modes disponibles
        self._load_all_modes()
        
        # Carregar la configuració
        self.load_config()
        
        # NO iniciar amb cap mode per defecte - es carregarà quan es premi un botó
        # Això estalvia més RAM al boot
        print("✓ ModeManager inicialitzat amb lazy loading - esperant selecció de mode")
    
    def load_config(self):
        """Carrega la configuració de bancs i modes"""
        # PRESERVAR efectes temporals actius abans del canvi
        efectes_preservats = {}
        for btn in self.effect_buttons:
            if self.efectes_temporals[btn]['active']:
                efectes_preservats[btn] = {
                    'tipus': self.efectes_temporals[btn]['tipus'],
                    'pre_mode': self.efectes_temporals[btn]['pre_mode'],
                    'pre_mode_instance': self.efectes_temporals[btn]['pre_mode_instance']
                }
                print(f"[PRESERVAR] Efecte {self.efectes_temporals[btn]['tipus']} al botó {btn+1} preservat")
        
        # IMPORTANT: Si hi ha un mode actiu (no teclat), aturar-lo abans de canviar la configuració
        # Això força que el proper botó premut carregui el mode correcte del nou banc
        if self.current_mode and self.current_mode_name and self.current_mode_name != 'Teclat':
            print(f"[CANVI BANC] Aturant mode actual: {self.current_mode_name}")
            previous_mode_name = self.current_mode_name
            
            # Aturar tot el so immediatament abans de fer cleanup
            self.stop_all_sound()
            
            self._stop_current_mode()
            
            # CRÍTIC: Alliberar memòria del mode anterior abans de continuar
            if previous_mode_name and previous_mode_name != 'Teclat':
                self._unload_mode(previous_mode_name)
            
            self.current_mode = None
            self.current_mode_name = None
            
            # Forçar garbage collection després d'alliberar el mode
            import gc
            gc.collect()
            mem_free = gc.mem_free() if hasattr(gc, 'mem_free') else 'N/A'
            print(f"[MEMÒRIA] RAM lliure després de descarregar mode: {mem_free} bytes")
        
        # Intentar carregar la configuració
        try:
            # Obtenim el banc actual
            current_bank = self.config_manager.get_current_bank()
            if not current_bank:
                print("Error carregant el banc actual. Utilitzant valors per defecte.")
                return False
            
            # === PART 1: Carregar la configuració dels modes per botons 1-12 ===
            disabled_modes = current_bank.get('disabled_modes', []) if isinstance(current_bank, dict) else []
            for button_idx in range(12):  # Només els primers 12 botons per a modes
                mode_name = None
                if 'modes' in current_bank and button_idx < len(current_bank['modes']):
                    mode_name = current_bank['modes'][button_idx]
                
                # Assignar el mode al botó si existeix
                if mode_name and mode_name in MODE_CLASSES and mode_name not in disabled_modes:
                    self.button_mappings[button_idx] = mode_name
                    print(f"Botó {button_idx+1} assignat al mode '{mode_name}'")
                else:
                    # Si no està configurat o no existeix, assignar Silenci
                    if 'Silenci' in MODE_CLASSES:
                        self.button_mappings[button_idx] = 'Silenci'
                        print(f"Botó {button_idx+1} assignat a 'Silenci' (per defecte)")
            
            # === PART 2: Reservar els botons especials ===
            # Botó 13 (12): Canvi de banc / Mode Teclat curt
            self.button_mappings[12] = 'RESERVADO_BANCS'
            
            # === PART 3: Carregar la configuració d'efectes temporals pels botons 14–15 (13–14) ===
            # NOTE: Els efectes temporals ara són GLOBALS (no per banc)
            # Només es carreguen a l'inici, NO es modifiquen al canviar de banc
            global_efectos = self.config_manager.config.get('efectos_temporales', {})
            
            # NOMÉS actualitzar si és la primera càrrega o si hi ha canvis a la config global
            if global_efectos:
                for btn in self.effect_buttons:
                    key = str(btn)
                    if key in global_efectos:
                        efecte_tipus_nou = global_efectos[key]
                        efecte_tipus_actual = self.efectes_temporals[btn]['tipus']
                        
                        # Només actualitzar si és diferent
                        if efecte_tipus_nou != efecte_tipus_actual:
                            # Si l'efecte està actiu, desactivar-lo abans de canviar el tipus
                            if self.efectes_temporals[btn]['active']:
                                print(f"[GLOBAL] Botó {btn+1}: {efecte_tipus_actual} -> {efecte_tipus_nou} (desactivant efecte actiu)")
                                self._deactivate_efecte_temporal(btn)
                            
                            # Actualitzar el tipus d'efecte
                            self.efectes_temporals[btn]['tipus'] = efecte_tipus_nou
                            print(f"Botó {btn+1} configurat amb efecte temporal GLOBAL: {efecte_tipus_nou}")
            
            # RESTAURAR efectes preservats després de recarregar la config
            if efectes_preservats:
                print("[RESTAURAR] Reactivant efectes temporals preservats...")
                for btn, efecte_data in efectes_preservats.items():
                    # Verificar que el tipus d'efecte no ha canviat
                    if self.efectes_temporals[btn]['tipus'] == efecte_data['tipus']:
                        # Reactivar l'efecte
                        activat = self.effect_manager.activate(efecte_data['tipus'])
                        if activat:
                            self.efectes_temporals[btn]['active'] = True
                            self.efectes_temporals[btn]['pre_mode'] = efecte_data['pre_mode']
                            self.efectes_temporals[btn]['pre_mode_instance'] = efecte_data['pre_mode_instance']
                            print(f"[RESTAURAR] Efecte {efecte_data['tipus']} reactivat al botó {btn+1}")
                        else:
                            print(f"[ERROR] No s'ha pogut reactivar efecte {efecte_data['tipus']}")
                    else:
                        print(f"[AVÍS] Efecte al botó {btn+1} ha canviat: {efecte_data['tipus']} -> {self.efectes_temporals[btn]['tipus']}")
            
            # === PART 4: Carregar els efectes disponibles per ciclar ===
            if self.config_manager:
                self.available_effects = self.config_manager.get_available_effects()
                print(f"[EFECTES] Disponibles: {', '.join(self.available_effects)}")
            
            # Marcar els botons 14–15 (13–14) amb el seu tipus d'efecte al mapping
            for btn in self.effect_buttons:
                self.button_mappings[btn] = f"RESERVADO_EFECTO_{self.efectes_temporals[btn]['tipus']}"
            
            # Botó 16 (15): Tornar
            self.button_mappings[15] = 'RESERVADO_TORNAR'
            
            return True
        except Exception as e:
            print(f"Error carregant la configuració: {e}")
            return False
    
    def _load_all_modes(self):
        """Carrega tots els modes disponibles dinàmicament"""
        print("Inicialitzant modes (càrrega sota demanda - LAZY LOADING)...")
        # Només precarregar el mode Teclat (essencial per botó 13)
        try:
            self._load_mode('Teclat')
            print("✓ Mode Teclat precarregat")
        except Exception as e:
            print(f"⚠ Error pre-carregant mode Teclat: {e}")
        
        # NOTA: Tots els altres modes es carregaran sota demanda quan es necessitin
        print("✓ Sistema de lazy loading activat - modes es carregaran quan es necessitin")
    
    def _get_memory_info(self):
        """Retorna informació de memòria disponible."""
        try:
            import gc
            gc.collect()
            import micropython
            # CircuitPython/MicroPython té mem_info()
            return micropython.mem_info()
        except:
            return None
    
    def _load_mode(self, mode_name):
        """Carrega un mode individual. Comprova primer MODE_CLASSES, després el registre personalitzat."""
        # Primer comprovar si és el mode Teclat (únic mode permanent)
        if mode_name in MODE_CLASSES:
            module_name, class_name = MODE_CLASSES[mode_name]
        else:
            # Tots els altres modes es consulten del registre JSON
            mode_info = _get_mode_info_from_registry(mode_name)
            if mode_info:
                module_name, class_name = mode_info
            else:
                return False
        
        # Si ja està carregat, actualitzar l'historial i retornar
        if mode_name in self.modes:
            if mode_name in self.loaded_modes_history:
                self.loaded_modes_history.remove(mode_name)
            self.loaded_modes_history.append(mode_name)
            return True
            
        try:
            # GESTIÓ DE MEMÒRIA: Comprovar límit de modes carregats
            # Si hem arribat al límit, descarregar el mode menys usat recentment (LRU)
            if len(self.modes) >= self.MAX_LOADED_MODES:
                # Trobar el mode menys usat recentment (que no sigen Teclat ni l'actual)
                for old_mode in self.loaded_modes_history:
                    if (old_mode in self.modes and 
                        old_mode != 'Teclat' and 
                        old_mode != self.current_mode_name and
                        old_mode != mode_name):
                        print(f"[MEMÒRIA] Límit assolit ({self.MAX_LOADED_MODES} modes). Descarregant: {old_mode}")
                        self._unload_mode(old_mode)
                        if old_mode in self.loaded_modes_history:
                            self.loaded_modes_history.remove(old_mode)
                        break
            
            # Forçar garbage collection ABANS de carregar el nou mode
            import gc
            gc.collect()
            mem_before = gc.mem_free() if hasattr(gc, 'mem_free') else None
            
            print(f"[CÀRREGA] Carregant mode: {mode_name}...")
            
            # Carregar el mòdul i la classe dinàmicament
            module = __import__(f'modes.{module_name}')
            module = getattr(module, module_name)
            mode_class = getattr(module, class_name)
            
            # Crear i inicialitzar la instància del mode
            self.modes[mode_name] = mode_class(self.midi_out, {})
            
            # Afegir a l'historial de modes carregats
            self.loaded_modes_history.append(mode_name)
            
            # Garbage collection DESPRÉS de carregar
            gc.collect()
            mem_after = gc.mem_free() if hasattr(gc, 'mem_free') else None
            
            if mem_before and mem_after:
                mem_used = mem_before - mem_after
                print(f"\u2713 Mode {mode_name} carregat | RAM usada: {mem_used} bytes | RAM lliure: {mem_after} bytes")
                print(f"[MEMÒRIA] Modes en RAM ({len(self.modes)}/{self.MAX_LOADED_MODES}): {list(self.modes.keys())}")
            else:
                print(f"\u2713 Mode {mode_name} carregat")
            
            return True
            
        except Exception as e:
            print(f"\u2717 Error carregant el mode {mode_name}: {e}")
            import sys
            sys.print_exception(e)
            return False
    
    def set_mode(self, mode_name, force_reload=False, capture_state=True):
        """Canvia al mode especificat."""
        try:
            # Lazy loading: carregar el mode si no està ja carregat
            if not mode_name in self.modes:
                # Intentar carregar el mode si no existeix
                self._load_mode(mode_name)
                if not mode_name in self.modes:
                    print(f"No s'ha pogut carregar el mode '{mode_name}'")
                    return False
            
            # Aturar mode actual
            if self.current_mode and self.current_mode_name != mode_name:
                if capture_state and hasattr(self.current_mode, 'capture_state'):
                    # Get active notes before stopping the current mode
                    captured_notes = self.current_mode.capture_state()
                    if self.current_mode_name:
                        print(f"Estat capturat de {self.current_mode_name}: {len(captured_notes) if isinstance(captured_notes, dict) else '-'}")
                captured_notes = None
                
            # Si és el mateix mode i no es força el reinici, no fer res
            if self.current_mode_name == mode_name and not force_reload:
                return True

            # Netejar i DESCARREGAR el mode anterior si és diferent
            if self.current_mode and (self.current_mode_name != mode_name or force_reload):
                previous_mode = self.current_mode_name
                print(f"Aturant el mode anterior: {previous_mode}")
                
                # ORDRE CORRECTE: 
                # 1. Primer cleanup del mode (atura notes del tracking intern)
                self._stop_current_mode()
                
                # 2. Després aturar TOT el so MIDI per assegurar silenci total
                self.stop_all_sound()
                
                # 3. LAZY LOADING: Descarregar el mode anterior per alliberar RAM
                # NO descarregar el mode Teclat (sempre necessari)
                if previous_mode and previous_mode != 'Teclat':
                    self._unload_mode(previous_mode)
            
            # Activar nou mode
            print(f"Mode canviat a: {mode_name}")
            self.current_mode = self.modes[mode_name]
            self.current_mode_name = mode_name
            self.last_mode_change = time.monotonic()
            
            # Inicialment guardar mode anterior
            if self.previous_mode_name != mode_name and self.current_mode_name != self.previous_mode_name:
                self.previous_mode_name = mode_name
            
            # Inicialitzar nou mode
            if hasattr(self.current_mode, 'setup'):
                try:
                    if capture_state and 'captured_notes' in locals() and captured_notes:
                        self.current_mode.setup(captured_notes=captured_notes)
                    else:
                        self.current_mode.setup()
                except Exception as e:
                    print(f"Error a l'inicialitzar el mode {mode_name}: {e}")
            
            return True
            
        except Exception as e:
            print(f"Error canviant al mode {mode_name}: {e}")
            self.last_mode_error = str(e)
            return False
    
    def reload_current_mode(self):
        """Reinicia el modo actual para aplicar cambios en la configuración."""
        if self.current_mode_name:
            return self.set_mode(self.current_mode_name, force_reload=True)
        return False
        
    def get_available_modes(self):
        """Retorna una llista amb els noms dels modes disponibles.
        Inclou el mode Teclat + tots els modes del registre JSON.
        """
        all_modes = list(MODE_CLASSES.keys())  # Teclat
        
        # Afegir tots els modes del registre
        try:
            try:
                import os
                current_dir = os.path.dirname(os.path.abspath(__file__))
                registry_path = os.path.join(current_dir, 'custom_modes_registry.json')
            except:
                registry_path = 'modes/custom_modes_registry.json'
            
            try:
                with open(registry_path, 'r') as f:
                    registry = json.load(f)
                registered_modes = registry.get('custom_modes', {})
                all_modes.extend(registered_modes.keys())
            except OSError:
                pass
        except:
            pass
        
        return sorted(all_modes)
        
    def _stop_current_mode(self):
        """Atura el mode actual i neteja els seus recursos."""
        if not self.current_mode:
            return
            
        try:
            # PRIORITAT 1: Cridar mètode stop() si existeix (per drones, background_notes, etc.)
            if hasattr(self.current_mode, 'stop'):
                try:
                    self.current_mode.stop()
                except Exception as e:
                    print(f"Error cridant stop() de {self.current_mode_name}: {e}")
            
            # PRIORITAT 2: Aturar tracking intern de notes actives
            from adafruit_midi.note_off import NoteOff
            
            # Aturar active_notes
            if hasattr(self.current_mode, 'active_notes'):
                for note in list(self.current_mode.active_notes):
                    try:
                        self.midi_out.send(NoteOff(note, 0))
                    except:
                        pass
                self.current_mode.active_notes.clear()
            
            # Aturar notes_playing
            if hasattr(self.current_mode, 'notes_playing'):
                for note in list(self.current_mode.notes_playing):
                    try:
                        self.midi_out.send(NoteOff(note, 0))
                    except:
                        pass
                self.current_mode.notes_playing.clear()
            
            # Aturar current_chord (Jazz)
            if hasattr(self.current_mode, 'current_chord'):
                for note in list(self.current_mode.current_chord):
                    try:
                        self.midi_out.send(NoteOff(note, 0))
                    except:
                        pass
                self.current_mode.current_chord.clear()
            
            # Aturar background_notes (Tempesta)
            if hasattr(self.current_mode, 'background_notes'):
                for note_info in self.current_mode.background_notes.values():
                    if isinstance(note_info, dict) and 'note' in note_info:
                        try:
                            self.midi_out.send(NoteOff(note_info['note'], 0))
                            note_info['active'] = False
                            note_info['velocity'] = 0
                        except:
                            pass
            
            # Aturar active_drones (PedalG, PedalTension, etc.)
            if hasattr(self.current_mode, 'active_drones'):
                for drone_info in list(self.current_mode.active_drones):
                    if isinstance(drone_info, tuple) and len(drone_info) >= 1:
                        try:
                            self.midi_out.send(NoteOff(drone_info[0], 0))
                        except:
                            pass
                self.current_mode.active_drones.clear()
            
            # Aturar active_layers (Drone)
            if hasattr(self.current_mode, 'active_layers'):
                for layer_info in list(self.current_mode.active_layers):
                    if isinstance(layer_info, tuple) and len(layer_info) >= 1:
                        try:
                            self.midi_out.send(NoteOff(layer_info[0], 0))
                        except:
                            pass
                self.current_mode.active_layers.clear()
            
            # PRIORITAT 3: Cridar cleanup del mode
            notes_to_stop = None
            if hasattr(self.current_mode, 'cleanup'):
                notes_to_stop = self.current_mode.cleanup()
            
            # Si el mode retorna notes per aturar, aturar-les explícitament
            if notes_to_stop:
                self._stop_notes(notes_to_stop)
                
        except Exception as e:
            print(f"Error en aturar el mode {self.current_mode_name}: {e}")
    
    def _unload_mode(self, mode_name):
        """Descarrega un mode de la memòria per alliberar RAM.
        NOTA: També elimina el mòdul de sys.modules per alliberar la RAM completament.
        """
        if mode_name in self.modes:
            try:
                import gc
                import sys
                mem_before = gc.mem_free() if hasattr(gc, 'mem_free') else None
                
                # Netejar el mode abans de descarregar-lo
                if hasattr(self.modes[mode_name], 'cleanup'):
                    self.modes[mode_name].cleanup()
                
                # Obtenir el nom del mòdul ABANS d'eliminar la instància
                module_name = None
                if mode_name in MODE_CLASSES:
                    module_name, _ = MODE_CLASSES[mode_name]
                else:
                    # Consultar registre
                    mode_info = _get_mode_info_from_registry(mode_name)
                    if mode_info:
                        module_name, _ = mode_info
                
                full_module_name = f'modes.{module_name}' if module_name else None
                
                # Eliminar la referència de la instància del mode
                del self.modes[mode_name]
                
                # CRÍTIC: Eliminar el mòdul de sys.modules per alliberar RAM real
                if full_module_name and full_module_name in sys.modules:
                    del sys.modules[full_module_name]
                
                # Eliminar de l'historial
                if mode_name in self.loaded_modes_history:
                    self.loaded_modes_history.remove(mode_name)
                
                # Forçar garbage collection per alliberar RAM immediatament
                gc.collect()
                mem_after = gc.mem_free() if hasattr(gc, 'mem_free') else None
                
                # Silenciós per no entorpir la fluïdesa
                pass
                
                return True
            except Exception as e:
                print(f"⚠ Error descarregant mode {mode_name}: {e}")
                import sys
                sys.print_exception(e)
                return False
        return False
    
    def stop_all_sound(self):
        """
        PANIC BUTTON - Atura TOT el so MIDI immediatament amb múltiples estratègies agressives.
        Envia els missatges DUES vegades per garantir que arriben als sintetitzadors.
        """
        if not self.midi_out:
            return
            
        from adafruit_midi.control_change import ControlChange
        from adafruit_midi.note_off import NoteOff
        
        # Repetir tot el procés DUES vegades per màxima seguretat
        for iteration in range(2):
            try:
                # PASSADA 1: Silenciar canals crítics ràpidament (0-2)
                for channel in range(3):
                    self.midi_out.send(ControlChange(64, 0, channel=channel))  # Sustain OFF
                    self.midi_out.send(ControlChange(120, 0, channel=channel)) # All Sound Off
                    self.midi_out.send(ControlChange(123, 0, channel=channel)) # All Notes Off
                
                # PASSADA 2: NoteOff explícit per TOTES les notes en el canal principal (0)
                for note in range(128):
                    try:
                        self.midi_out.send(NoteOff(note, 0, channel=0))
                    except:
                        pass
                
                # PASSADA 3: Reset complet de tots els canals
                for channel in range(16):
                    self.midi_out.send(ControlChange(64, 0, channel=channel))  # Sustain OFF
                    self.midi_out.send(ControlChange(120, 0, channel=channel)) # All Sound Off
                    self.midi_out.send(ControlChange(123, 0, channel=channel)) # All Notes Off
                    # Pitch Bend a neutral
                    try:
                        from adafruit_midi.pitch_bend import PitchBend
                        self.midi_out.send(PitchBend(8192, channel=channel))
                    except:
                        pass
                    # Reset controladors
                    self.midi_out.send(ControlChange(1, 0, channel=channel))   # Modulation OFF
                    self.midi_out.send(ControlChange(11, 127, channel=channel)) # Expression MAX
                    self.midi_out.send(ControlChange(91, 0, channel=channel))  # Reverb OFF
                    self.midi_out.send(ControlChange(93, 0, channel=channel))  # Chorus OFF
                    
            except Exception as e:
                print(f"Error en panic (iter {iteration}): {e}")
            
            # Micro-pausa entre iteracions per assegurar que els missatges arriben
            if iteration == 0:
                try:
                    time.sleep(0.01)  # 10ms
                except:
                    pass
        
        # Silenciar PWM local
        try:
            import main
            if hasattr(main, 'pwm') and main.pwm is not None:
                main.pwm.duty_cycle = 0
        except:
            pass

    
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

    def change_layer(self, layer_name):
        """Canvia a la capa especificada (main o teclat) utilitzant el LayerManager."""
        return self.layer_manager.change_layer(layer_name)
    
    def update(self, pot_values, button_states):
        """
        Actualitza el mode actual amb els valors dels potenciòmetres i l'estat dels botons
        
        Args:
            pot_values: Valors dels potenciòmetres (0-127)
            button_states: Estat dels botons (True/False)
            
        Returns:
            Dict amb l'estat del mode
        """
        change_mode = None
        try:
            # Inicialitzar estat per defecte
            status = {'change_mode': None}
            change_mode = None
            current_time = time.monotonic()
            
            # === PRIORITAT 1: Gestió de canvis de capa (botons 13 i 16) ===
            # Si es produeix un canvi de capa, això té preferència sobre qualsevol altra acció
            if isinstance(button_states, list) and len(button_states) > 15:
                # Processar els botons relacionats amb el canvi de capa
                layer_changed = self.layer_manager.process_layer_buttons(button_states)
                
                # Si s'ha canviat de capa, actualitzem el estat i continuem
                if layer_changed:
                    current_layer = self.layer_manager.current_layer
                    print(f"S'ha canviat a la capa: {current_layer}")
                    status['layer'] = current_layer
            
            # === PRIORITAT 2: Gestió dels botons d'efecte (14 i 15) amb funció dual ===
            if isinstance(button_states, list) and len(button_states) > 14:
                # Convertir a llista per poder modificar-la si cal (doble clic)
                button_states_modified = False
                button_states_list = list(button_states)
                
                for efecte_button in self.effect_buttons:
                    if len(button_states) <= efecte_button:
                        continue
                    efecte_info = self.efectes_temporals[efecte_button]
                    efecte_tipus = efecte_info['tipus']
                    current_state = bool(button_states[efecte_button])
                    
                    # Calcular temps transcorregut des de l'última pulsació
                    # FIX: Si press_time és 0 (inicial), elapsed serà 0
                    if efecte_info['press_time'] > 0:
                        elapsed = current_time - efecte_info['press_time']
                    else:
                        elapsed = 0
                    
                    # Comprovar debounce només si hi ha hagut una pulsació prèvia
                    time_since_press = current_time - efecte_info['press_time'] if efecte_info['press_time'] > 0 else 999
                    
                    if time_since_press > self.debounce_time or efecte_info['press_time'] == 0:
                        if current_state != efecte_info['last_state']:
                            # Transició d'estat
                            efecte_info['last_state'] = current_state
                            if current_state:
                                # Botó premut: marcar temps
                                efecte_info['press_time'] = current_time
                            else:
                                # Botó alliberat
                                release_time = current_time
                                time_since_last_release = release_time - efecte_info.get('last_release_time', 0)
                                
                                # Detectar doble clic: dos releases ràpids
                                # FIX: Permetre doble clic fins i tot amb efecte actiu per permetre ciclat
                                is_double_click = (time_since_last_release < self.double_click_threshold and 
                                                  time_since_last_release > 0.05)  # Evitar bouncing
                                
                                if is_double_click:
                                    # DOBLE CLIC: Ciclar efecte
                                    print(f"Doble clic detectat al botó {efecte_button+1}")
                                    
                                    # Desactivar efecte si estava actiu
                                    if efecte_info['active']:
                                        self._deactivate_efecte_temporal(efecte_button)
                                    
                                    # Ciclar al següent efecte
                                    self._cycle_effect(efecte_button)
                                    efecte_info['last_release_time'] = 0  # Reset per evitar triple clic
                                    
                                    # FIX: Consumir l'event modificant button_states per evitar interferències
                                    button_states_list[efecte_button] = False
                                    button_states_modified = True
                                else:
                                    # Release normal: desactivar efecte si estava actiu
                                    if efecte_info['active']:
                                        # Desactivar efecte si estava actiu
                                        print(f"{efecte_tipus} OFF - Tornant al mode: {efecte_info['pre_mode']}")
                                        self._deactivate_efecte_temporal(efecte_button)
                                        if efecte_tipus == 'Sustain':
                                            self.sustain_active = False
                                        elif efecte_tipus == 'Pausa':
                                            self.pausa_active = False
                                    
                                    # Marcar temps del release per detectar doble clic
                                    efecte_info['last_release_time'] = release_time
                        else:
                            # Sense canvi d'estat: comprovar si s'ha de activar l'efecte per manteniment
                            # BLINDAT: Permetre activació d'efectes en qualsevol capa
                            if (current_state and not efecte_info['active'] and 
                                elapsed >= self.effect_hold_threshold):
                                # Només ignorar si el mode actual és un efecte temporal
                                if self.current_mode_name in ['Sustain', 'Pausa']:
                                    print(f"Ignorant activació de {efecte_tipus} sobre mode {self.current_mode_name}")
                                else:
                                    print(f"{efecte_tipus} ON - Aplicant efecte sobre mode: {self.current_mode_name}")
                                    # Desactivar altre efecte si l'altre botó també l'ha activat
                                    for altre_button, altre_info in self.efectes_temporals.items():
                                        if altre_button != efecte_button and altre_info['active']:
                                            self._deactivate_efecte_temporal(altre_button)
                                    efecte_info['pre_mode'] = self.current_mode_name
                                    efecte_info['pre_mode_instance'] = self.current_mode
                                    # Activar l'efecte
                                    activat = self.effect_manager.activate(efecte_tipus)
                                    if activat:
                                        efecte_info['active'] = True
                                        efecte_info['mode_instance'] = None
                                        if efecte_tipus == 'Sustain':
                                            self.sustain_active = True
                                        elif efecte_tipus == 'Pausa':
                                            self.pausa_active = True
                                    else:
                                        print(f"No s'ha pogut activar l'efecte {efecte_tipus}")
                
                # FIX: Si s'han consumit events de doble clic, actualitzar button_states
                if button_states_modified:
                    button_states = button_states_list
            
            # === PRIORITAT 3: Actualitzar el mode actual si no hi ha efectes actius ===
            # Comprovar si hi ha algun efecte temporal actiu
            algun_efecte_actiu = False
            efecte_actiu_nom = None
            
            # Verificar tots els efectes configurables
            for efecte_button, efecte_info in self.efectes_temporals.items():
                if efecte_info['active']:
                    # Actualitzar paràmetres de l'efecte actiu en temps real segons potenciòmetres
                    try:
                        self.effect_manager.update_active_params(pot_values)
                    except Exception as e:
                        print(f"Error actualitzant paràmetres d'efecte {efecte_info['tipus']}: {e}")
                    algun_efecte_actiu = True
                    efecte_actiu_nom = efecte_info['tipus']
                    break
                    
            # Per compatibilitat amb codi antic, també comprovem les variables directes
            if not algun_efecte_actiu and (self.sustain_active or self.pausa_active):
                algun_efecte_actiu = True
                efecte_actiu_nom = 'sustain' if self.sustain_active else 'pausa'
                
            if not algun_efecte_actiu:
                # Actualitzar el mode actual només si no hi ha efectes actius
                if self.current_mode:
                    # Filtrar els botons 14-15 (índexs 13-14) abans de passar-los als modes
                    # Aquests botons estan reservats per efectes temporals i no haurien d'interferir amb els modes
                    filtered_button_states = list(button_states) if isinstance(button_states, (list, tuple)) else button_states
                    if isinstance(filtered_button_states, list) and len(filtered_button_states) > 14:
                        filtered_button_states[13] = False  # Botó 14
                        filtered_button_states[14] = False  # Botó 15
                    
                    # La funció update del mode actual determina si cal canviar de mode
                    mode_status = self.current_mode.update(pot_values, filtered_button_states)
                    
                    # Processar l'estat retornat pel mode
                    if isinstance(mode_status, dict):
                        status.update(mode_status)
                        if 'change_mode' in mode_status and mode_status['change_mode']:
                            change_mode = mode_status['change_mode']
                    else:
                        status = {'status': str(mode_status)}
            else:
                # Si hi ha un efecte actiu, evitem actualitzar el mode actual per mantenir les notes
                status['effect_active'] = efecte_actiu_nom
            
            # === PRIORITAT 4: Gestió de canvis de mode ===
            # Si cal canviar de mode i existeix
            if change_mode and change_mode in self.modes:
                self.set_mode(change_mode)
                
            # Informació d'estat per a la resposta
            status['mode'] = self.current_mode_name
            status['layer'] = self.layer_manager.current_layer
            status['pausa_active'] = self.pausa_active
            status['sustain_active'] = self.sustain_active
            status['mode_octave'] = self.mode_octave
            
            return status
            
        except Exception as e:
            print(f"Error en l'actualització del mode '{self.current_mode_name}': {e}")
            import sys
            sys.print_exception(e)
            return {'mode': 'Error'}

    def _update_effect_params(self, efecte_tipus, pot_values):
        """Actualitza en temps real els paràmetres dels efectes basats en potenciòmetres.
        Mapatge bàsic:
          - Pausa: CC7 (volum) amb X; CC11 (expressió) amb Y
          - Sustain: CC11 (expressió) amb X (opcional)
          - Reverb: CC91 amb X
          - Chorus: CC93 amb X
          - Delay: CC94 amb X
          - Filter: CC74 (cutoff) amb X, CC71 (resonància) amb Y
          - Scratch: CC74 (cutoff) amb X, CC1 (mod) amb Y, CC71 (res) amb Z
        """
        if not pot_values or len(pot_values) < 1:
            return
        x = pot_values[0]
        y = pot_values[1] if len(pot_values) > 1 else 0
        z = pot_values[2] if len(pot_values) > 2 else 0
        
        try:
            if efecte_tipus == 'Pausa':
                # Volum i expressió
                vol = max(1, min(127, int(x)))
                expr = max(1, min(127, int(y)))
                for channel in range(16):
                    self.midi_out.send(ControlChange(7, vol, channel=channel))
                    self.midi_out.send(ControlChange(11, expr, channel=channel))
            elif efecte_tipus == 'Sustain':
                # Expressió com a dinàmica
                expr = max(0, min(127, int(x)))
                for channel in range(16):
                    self.midi_out.send(ControlChange(11, expr, channel=channel))
            elif efecte_tipus == 'Reverb':
                rev = max(0, min(127, int(x)))
                for channel in range(16):
                    self.midi_out.send(ControlChange(91, rev, channel=channel))
            elif efecte_tipus == 'Chorus':
                cho = max(0, min(127, int(x)))
                for channel in range(16):
                    self.midi_out.send(ControlChange(93, cho, channel=channel))
            elif efecte_tipus == 'Delay':
                dly = max(0, min(127, int(x)))
                for channel in range(16):
                    self.midi_out.send(ControlChange(94, dly, channel=channel))
            elif efecte_tipus == 'Filter':
                cutoff = max(0, min(127, int(x)))
                res = max(0, min(127, int(y)))
                for channel in range(16):
                    self.midi_out.send(ControlChange(74, cutoff, channel=channel))
                    self.midi_out.send(ControlChange(71, res, channel=channel))
            elif efecte_tipus == 'Scratch':
                cutoff = max(0, min(127, int(x)))
                mod = max(0, min(127, int(y)))
                res = max(0, min(127, int(z)))
                for channel in range(16):
                    self.midi_out.send(ControlChange(74, cutoff, channel=channel))
                    self.midi_out.send(ControlChange(1, mod, channel=channel))
                    self.midi_out.send(ControlChange(71, res, channel=channel))
        except Exception as e:
            print(f"Error enviant CC per a efecte {efecte_tipus}: {e}")
    
    def _deactivate_efecte_temporal(self, efecte_button):
        """Desactiva un efecte temporal configurable i restaura l'estat anterior.
        
        Args:
            efecte_button: L'índex del botó d'efecte a desactivar
        """
        if efecte_button not in self.efectes_temporals or not self.efectes_temporals[efecte_button]['active']:
            return
            
        efecte_info = self.efectes_temporals[efecte_button]
        efecte_tipus = efecte_info['tipus']
        print(f"Desactivant efecte {efecte_tipus}")
        
        # Accions específiques segons el tipus d'efecte
        # Delegar desactivació a l'EffectManager
        try:
            self.effect_manager.deactivate()
        except Exception as e:
            print(f"Error desactivant efecte {efecte_tipus}: {e}")
        
        # Resetear variables
        efecte_info['active'] = False
        efecte_info['mode_instance'] = None
        efecte_info['pre_mode_instance'] = None
        efecte_info['pre_mode'] = None
        
    def _deactivate_pausa(self):
        """Desactiva l'efecte de pausa sense canviar de mode."""
        print("Desactivant efecte de pausa (mètode antic)")
        try:
            self.effect_manager.deactivate()
        except Exception:
            pass
        # Mantenir compatibilitat amb codi antic
        self.pausa_active = False
        self.pausa_mode = None
        self.pre_pausa_mode_instance = None
        self.pre_pausa_mode = None
        # No cal restaurar cap mode ja que el mode actual no ha canviat
    
    def _silent_current_mode_controls(self):
        """
        Silencia els controls MIDI del mode actual per evitar interferències
        Això millora la transició entre modes i evita comportaments estranys
        """
        try:
            # Resetear només els controls que podrien interferir
            for channel in range(16):
                # No resetegem volum per no trencar efectes fade
                # Només silenciem controls d'expressió i modulació
                self.midi_out.send(ControlChange(11, 127, channel=channel))  # Expression
                self.midi_out.send(ControlChange(1, 0, channel=channel))     # Modulation
            print("  > Controls silenciats per facilitar transició")
        except Exception as e:
            print(f"Error silenciant controls: {e}")
    
    def _deactivate_sustain(self):
        """Desactiva l'efecte de sustain sense canviar de mode."""
        print("Desactivant efecte de sustain (mètode antic)")
        try:
            self.effect_manager.deactivate()
        except Exception:
            pass
        # Mantenir compatibilitat
        self.sustain_active = False
        self.sustain_mode = None
        self.pre_sustain_mode_instance = None
        self.pre_sustain_mode = None

    def _change_mode_octave(self, delta):
        """Canvia l'octava global dels modes (no teclat)."""
        try:
            self.mode_octave = max(-4, min(4, self.mode_octave + (1 if delta > 0 else -1)))
            print(f"Octava modes: {self.mode_octave}")
            # Notificar al mode actual si disposa d'un mètode específic
            if self.current_mode:
                if hasattr(self.current_mode, 'set_octave_shift'):
                    try:
                        self.current_mode.set_octave_shift(self.mode_octave)
                    except Exception as e:
                        print(f"Error aplicant octave al mode: {e}")
                elif hasattr(self.current_mode, 'set_octave'):
                    try:
                        self.current_mode.set_octave(self.mode_octave)
                    except Exception:
                        pass
        except Exception as e:
            print(f"Error canviant octava dels modes: {e}")
    
    def _activate_mode(self, mode_name, captured_state=None):
        """
        Activa un mode existent sense fer neteja del mode anterior
        Útil per transicions temporals entre mode original i efectes
        
        Args:
            mode_name: Nom del mode a activar
            captured_state: Estat capturat del mode anterior (opcional)
        
        Returns:
            True si s'ha activat correctament, False en cas contrari
        """
        if mode_name not in self.modes:
            print(f"No es pot activar {mode_name}: mode no trobat")
            return False
            
        print(f"Activant mode: {mode_name} (amb captured_state: {captured_state is not None})")
            
        # Canviar al nou mode sense aturar l'anterior
        self.current_mode = self.modes[mode_name]
        self.current_mode_name = mode_name
        
        # Forçar reinici del mode per assegurar estat net
        if hasattr(self.current_mode, 'cleanup'):
            try:
                self.current_mode.cleanup()
            except Exception as e:
                print(f"Error netejant mode abans de reiniciar-lo: {e}")
        
        # Inicialitzar el mode
        if hasattr(self.current_mode, 'setup'):
            try:
                self.current_mode.setup()
            except Exception as e:
                print(f"Error inicialitzant {mode_name}: {e}")
            
        print(f"Mode activat: {mode_name}")
        return True
    
    def _cycle_effect(self, button_index):
        """Cicla l'efecte assignat a un botó d'efecte temporal"""
        efecte_info = self.efectes_temporals[button_index]
        current_effect = efecte_info['tipus']
        
        # Si no hi ha efectes disponibles, no fer res
        if not self.available_effects:
            print(f"[AVIS] Cap efecte disponible per ciclar")
            return
        
        # Si hi ha un efecte actiu, desactivar-lo primer
        if efecte_info['active']:
            self._deactivate_efecte_temporal(button_index)
        
        # Trobar l'índex de l'efecte actual
        try:
            current_index = self.available_effects.index(current_effect)
        except ValueError:
            # Si l'efecte actual no està a la llista, començar pel primer
            current_index = -1
        
        # Passar al següent efecte (circular)
        next_index = (current_index + 1) % len(self.available_effects)
        new_effect = self.available_effects[next_index]
        
        # Actualitzar l'efecte assignat
        efecte_info['tipus'] = new_effect
        
        # Ciclar entre efectes disponibles i guardar a la configuració GLOBAL
        if self.config_manager:
            try:
                # IMPORTANT: Guardar a nivell GLOBAL, no per banc
                if 'efectos_temporales' not in self.config_manager.config:
                    self.config_manager.config['efectos_temporales'] = {}
                
                self.config_manager.config['efectos_temporales'][str(button_index)] = new_effect
                print(f"[GLOBAL] Efecte temporal del botó {button_index+1} canviat a: {new_effect}")
            except Exception as e:
                print(f"Error guardant efecte temporal: {e}")
        
        print(f"[EFECTE] Botó {button_index+1}: {current_effect} -> {new_effect}")
    
    def cleanup(self):
        """Neteja tots els recursos utilitzats pels modes."""
        # Aturar el mode Hold si està actiu
        if self.hold_active and self.hold_mode:
            print("Netejant el mode Hold...")
            if hasattr(self.hold_mode, 'cleanup'):
                self.hold_mode.cleanup()
            self.hold_active = False
        
        # Desactivar Sustain i Pausa si estan actius
        if self.sustain_active:
            self._deactivate_sustain()
        
        if self.pausa_active:
            self._deactivate_pausa()
        
        # Aturar totes les notes MIDI actives en tots els canals
        if self.midi_out:
            # Per cada canal, enviem All Notes Off (CC 123 valor 0)
            for channel in range(16):
                try:
                    self.midi_out.send(ControlChange(123, 0, channel=channel))
                except Exception as e:
                    print(f"Error a cleanup del canal {channel}: {e}")
        
        # Cridar el mètode cleanup de tots els modes que en tinguin
        for mode_name, mode_instance in self.modes.items():
            if hasattr(mode_instance, 'cleanup'):
                try:
                    mode_instance.cleanup()
                except Exception as e:
                    print(f"Error a cleanup de {mode_name}: {e}")
        
        return True
    
    def emergency_stop_and_cleanup(self):
        """Atura COMPLETAMENT el so i DESCARREGA TOTS els modes de la memòria.
        Aquesta funció fa un refresh complet del sistema (Botó 16).
        També neteja sys.modules per alliberar RAM completament.
        """
        import gc
        import sys
        
        mem_inicial = gc.mem_free() if hasattr(gc, 'mem_free') else None
        
        # 1. CRÍTIC: Aturar TOT el so IMMEDIATAMENT amb stop_all_sound()
        # (Això ja inclou NoteOff per totes les notes, CC120, CC123, reset de controladors i PWM)
        self.stop_all_sound()
        
        # 2. Cleanup del mode actual
        if self.current_mode:
            try:
                if hasattr(self.current_mode, 'cleanup'):
                    self.current_mode.cleanup()
            except:
                pass
        
        # 3. Cridar stop_all_sound una segona vegada per màxima seguretat
        self.stop_all_sound()
        
        # 4. DESCARREGAR TOTS ELS MODES (excepte Teclat si es vol mantenir)
        modes_to_unload = [name for name in list(self.modes.keys()) if name != 'Teclat']
        for mode_name in modes_to_unload:
            try:
                self._unload_mode(mode_name)
            except:
                pass
        
        # 4. Netejar referències internes
        self.current_mode = None
        self.current_mode_name = None
        self.previous_mode_name = None
        
        # 5. Neteja d'efectes temporals
        for btn in self.effect_buttons:
            self.efectes_temporals[btn]['active'] = False
            self.efectes_temporals[btn]['mode_instance'] = None
            self.efectes_temporals[btn]['pre_mode'] = None
            self.efectes_temporals[btn]['pre_mode_instance'] = None
        
        # 6. Netejar variables d'estat legacy
        self.sustain_mode = None
        self.pre_sustain_mode = None
        self.pre_sustain_mode_instance = None
        self.pausa_mode = None
        self.pre_pausa_mode = None
        self.pre_pausa_mode_instance = None
        self.hold_mode = None
        
        # 7. NETEJA AGRESSIVA DE sys.modules - eliminar mòduls de modes no utilitzats
        # Això permet recuperar RAM dels mòduls importats
        modules_to_remove = []
        for module_name in list(sys.modules.keys()):
            # Eliminar mòduls de modes (excepte Teclat, base_mode, mode_manager)
            if (module_name.startswith('modes.mode_') and 
                module_name not in ['modes.mode_keyboard', 'modes.base_mode', 'modes.mode_manager']):
                modules_to_remove.append(module_name)
        
        for module_name in modules_to_remove:
            try:
                del sys.modules[module_name]
            except:
                pass
        
        # Silenciós
        
        # 8. Garbage collection ULTRA-AGRESSIU
        gc.collect()
        gc.collect()
        gc.collect()  # Triple passada per màxima neteja
        mem_final = gc.mem_free() if hasattr(gc, 'mem_free') else None
        
        # Neteja completa sense missatges per no entorpir la fluïdesa
        
        return True
    
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
            
            
    # Funció definida a main.py
    # Ens estalviem definir-la aquí també
  
    
    def note_on(self, note, velocity=127, channel=0):
        """Retorna un missatge de nota ON MIDI i actualitza el PWM."""
        from adafruit_midi.note_on import NoteOn
        note_on_msg = NoteOn(note & 0x7F, velocity & 0x7F)
        note_on_msg.channel = channel

        return note_on_msg 
        
    def note_off(self, note, velocity=0, channel=0):
        """Retorna un missatge de nota OFF MIDI i silencia el PWM."""
        from adafruit_midi.note_off import NoteOff
        note_off_msg = NoteOff(note & 0x7F, velocity & 0x7F)
        note_off_msg.channel = channel
        
        # Silenciar PWM - solució directa i garantida
        try:
            # Importar directament main per assegurar que no hi hagi problemes d'accés
            import main
            # Verificar que els objectes existeixen abans d'utilitzar-los
            if hasattr(main, 'pwm'):
                # Calcular freqüència per la nota
                freq = main.midi_to_frequency(note)
                # Mantenir freqüència pero silenciar (duty_cycle = 0)
                main.pwm.frequency = freq
                main.pwm.duty_cycle = 0  # Silenci
        except ImportError:
            print("Error: No s'ha pogut importar el mòdul main")
        except AttributeError as e:
            print(f"Error: L'objecte no té l'atribut: {e}")
        except Exception as e:
            print(f"Error PWM note_off: {e}")
        return note_off_msg
        
    def control_change(self, control, value, channel=0):
        """Retorna un missatge de control canvi MIDI."""
        from adafruit_midi.control_change import ControlChange
        return ControlChange(control, value, channel=channel)
