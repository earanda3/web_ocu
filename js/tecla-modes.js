/**
 * TECLAModes — Gestió de modes TECLA
 * Port de mode_importer.py i custom_modes_manager.py a JavaScript
 * 
 * Registre: modes/custom_modes_registry.json
 *   { "custom_modes": { "ModeName": { "file_name": "mode_x", "class_name": "ModeX", ... } } }
 */
export class TECLAModes {
    constructor(device) {
        this.device = device;
        this.REGISTRY_PATH = 'modes/custom_modes_registry.json';
        this.MANAGER_PATH = 'modes/mode_manager.py';
    }

    // ─── Llegir modes ────────────────────────────────────────────────

    async getInstalledModes() {
        const modes = {};

        // 1. Modes originals de mode_manager.py
        try {
            const content = await this.device.readFile(this.MANAGER_PATH);
            const match = content.match(/MODE_CLASSES\s*=\s*\{([^}]+)\}/s);
            if (match) {
                const pattern = /'([^']+)':\s*\('([^']+)',\s*'([^']+)'\)/g;
                let m;
                while ((m = pattern.exec(match[1])) !== null) {
                    modes[m[1]] = {
                        file_name: m[2],
                        class_name: m[3],
                        source: 'original'
                    };
                }
            }
        } catch (e) {
            console.warn('[TECLA] No s\'ha pogut llegir mode_manager.py:', e);
        }

        // 2. Modes personalitzats del registre
        try {
            const content = await this.device.readFile(this.REGISTRY_PATH);
            const registry = JSON.parse(content);
            const customModes = registry.custom_modes || {};
            for (const [name, info] of Object.entries(customModes)) {
                modes[name] = { ...info, source: 'custom' };
            }
        } catch (e) {
            // El registre pot no existir encara — és normal
        }

        return modes;
    }

    // ─── Validació ───────────────────────────────────────────────────

    validateModeFile(content, fileName) {
        if (!fileName.endsWith('.py')) {
            return { valid: false, error: 'El fitxer ha de ser .py' };
        }

        const baseName = fileName.replace('.py', '');
        if (!baseName.startsWith('mode_')) {
            return { valid: false, error: `El fitxer ha de seguir la convenció 'mode_nom.py' (ara: ${fileName})` };
        }

        // Buscar classe que hereti de BaseMode
        const classMatch = content.match(/class\s+(\w+)\s*\(\s*BaseMode\s*\)/);
        if (!classMatch) {
            return { valid: false, error: 'No s\'ha trobat cap classe que hereti de BaseMode' };
        }

        // Verificar mètode update (obligatori)
        if (!content.includes('def update')) {
            return { valid: false, error: `La classe ${classMatch[1]} no té el mètode update() (obligatori)` };
        }

        const className = classMatch[1];
        let modeName = className;
        if (modeName.startsWith('Mode')) modeName = modeName.slice(4);

        const hasClanup = content.includes('def cleanup');
        const hasSetup = content.includes('def setup');

        return {
            valid: true,
            className,
            modeName,
            baseName,
            hasSetup,
            hasClanup
        };
    }

    // ─── Instal·lar mode ─────────────────────────────────────────────

    async installMode(fileContent, fileName) {
        const v = this.validateModeFile(fileContent, fileName);
        if (!v.valid) {
            return { success: false, error: v.error };
        }

        const { className, modeName, baseName } = v;

        // Duplicats
        const installed = await this.getInstalledModes();
        if (modeName in installed) {
            return { success: false, error: `Mode '${modeName}' ja instal·lat` };
        }
        if (await this.device.fileExists(`modes/${baseName}.py`)) {
            return { success: false, error: `Fitxer '${baseName}.py' ja existent al dispositiu` };
        }

        // Escriure el fitxer
        try {
            await this.device.writeFile(`modes/${baseName}.py`, fileContent);
        } catch (e) {
            return { success: false, error: `No s'ha pogut escriure al dispositiu: ${e.message}` };
        }

        // Actualitzar el registre
        let registry = { custom_modes: {} };
        try {
            const existing = await this.device.readFile(this.REGISTRY_PATH);
            registry = JSON.parse(existing);
            if (!registry.custom_modes) registry.custom_modes = {};
        } catch { }

        registry.custom_modes[modeName] = {
            file_name: baseName,
            class_name: className,
            added_date: new Date().toISOString()
        };

        try {
            await this.device.writeFile(this.REGISTRY_PATH, JSON.stringify(registry, null, 2));
        } catch (e) {
            // El fitxer s'ha copiat però el registre ha fallat — avisar però no error crític
            console.warn('[TECLA] Registre no actualitzat:', e);
            return { success: true, modeName, warning: 'Mode copiat però el registre no s\'ha pogut actualitzar' };
        }

        return { success: true, modeName };
    }

    // ─── Eliminar mode ───────────────────────────────────────────────

    async removeMode(modeName, modeInfo) {
        // Eliminar el fitxer
        try {
            await this.device.deleteFile(`modes/${modeInfo.file_name}.py`);
        } catch (e) {
            return { success: false, error: `No s'ha pogut eliminar el fitxer: ${e.message}` };
        }

        // Actualitzar el registre (només per modes custom)
        if (modeInfo.source === 'custom') {
            try {
                const content = await this.device.readFile(this.REGISTRY_PATH);
                const registry = JSON.parse(content);
                if (registry.custom_modes) {
                    delete registry.custom_modes[modeName];
                    await this.device.writeFile(this.REGISTRY_PATH, JSON.stringify(registry, null, 2));
                }
            } catch (e) {
                console.warn('[TECLA] No s\'ha pogut actualitzar el registre:', e);
            }
        }

        return { success: true };
    }
}
