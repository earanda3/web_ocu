"""
ConfigManager - Gestiona la configuració i els temes del TECLA
"""
import json
import os

class ConfigManager:
    def __init__(self, config_path='config/tecla_config.json'):
        """Inicialitza el gestor de configuració"""
        self.config_path = config_path
        self.config = self._load_config()
        self.current_bank_index = self.config.get('current_bank', 0)
        self.theme = self.config.get('theme_name', 'default')
        self.button_actions = self.config.get('button_actions', {})
        
    def _load_config(self):
        """Carrega la configuració des del fitxer JSON"""
        try:
            with open(self.config_path, 'r') as f:
                config = json.load(f)
                # Validació bàsica de l'estructura
                if not isinstance(config, dict) or 'banks' not in config:
                    print("Avís: Format de configuració invàlid, utilitzant valors per defecte")
                    return self._get_default_config()
                return config
        except (OSError, ValueError) as e:  # ValueError atrapa errors de JSON en CircuitPython
            # Retorna una configuració per defecte si hi ha algun error
            print(f"Error carregant la configuració: {e}. Utilitzant valors per defecte.")
            return self._get_default_config()
    
    def _get_default_config(self):
        """Retorna una configuració per defecte"""
        return {
            'theme_name': 'default',
            'banks': [{
                'name': 'Default Bank',
                'modes': ['Silenci'] + ['Mode ' + str(i) for i in range(1, 16)]
            }],
            'current_bank': 0,
            'button_actions': {}
        }
    
    def save_config(self):
        """Guarda la configuració actual al fitxer"""
        try:
            # Validació bàsica abans de desar
            if not isinstance(self.config, dict) or 'banks' not in self.config:
                print("Error: La configuració no és vàlida i no es pot desar")
                return False
                
            # Assegurar que el directori existeix
            os.makedirs(os.path.dirname(self.config_path), exist_ok=True)
            
            # Desar la configuració en un fitxer temporal primer
            temp_path = self.config_path + '.tmp'
            with open(temp_path, 'w') as f:
                json.dump(self.config, f, indent=2, ensure_ascii=False)
                
            # Reanomenar el fitxer temporal al fitxer final
            # Això ajuda a prevenir la corrupció del fitxer en cas d'error
            try:
                os.rename(temp_path, self.config_path)
            except OSError:
                # Si el rename falla, intentar copiar i eliminar
                with open(temp_path, 'r') as src:
                    with open(self.config_path, 'w') as dst:
                        dst.write(src.read())
                try:
                    os.remove(temp_path)
                except Exception:
                    pass  # Ignorar si no es pot eliminar el temporal
                    
            return True
            
        except OSError as e:
            print(f"Error en desar la configuració: {e}")
            return False
        except Exception as e:
            print(f"Error inesperat en desar la configuració: {e}")
            return False
    
    def get_current_bank(self):
        """Retorna el banc actual"""
        if 0 <= self.current_bank_index < len(self.config['banks']):
            return self.config['banks'][self.current_bank_index]
        return None
    
    def get_available_banks(self):
        """Retorna la llista de tots els bancs disponibles"""
        return [bank['name'] for bank in self.config.get('banks', [])]
    
    def set_current_bank(self, bank_index):
        """Canvia al banc especificat"""
        if 0 <= bank_index < len(self.config['banks']):
            self.current_bank_index = bank_index
            self.config['current_bank'] = bank_index
            self.save_config()
            return True
        return False
    
    def next_bank(self):
        """Canvia al següent banc"""
        new_index = (self.current_bank_index + 1) % len(self.config['banks'])
        return self.set_current_bank(new_index)
    
    def get_mode_for_button(self, button_index, bank_index=None):
        """Retorna el mode assignat a un botó específic"""
        bank = self.get_current_bank() if bank_index is None else \
               self.config['banks'][bank_index]
        if bank and 0 <= button_index < len(bank['modes']):
            return bank['modes'][button_index]
        return None
    
    def set_mode_for_button(self, button_index, mode_name, bank_index=None):
        """Assigna un mode a un botó específic"""
        bank_idx = self.current_bank_index if bank_index is None else bank_index
        if 0 <= bank_idx < len(self.config['banks']):
            bank = self.config['banks'][bank_idx]
            if 0 <= button_index < len(bank['modes']):
                bank['modes'][button_index] = mode_name
                return self.save_config()
        return False
    
    def get_button_action(self, button_index, action_type='long_press'):
        """Retorna l'acció configurada per un botó"""
        return self.button_actions.get(action_type, {}).get(str(button_index))
