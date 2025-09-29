#!/usr/bin/env python3
import os

def aggressive_unicode_fix():
    """Fix unicode agresivo - reemplazar CUALQUIER caracter no ASCII"""

    # Archivos críticos que están causando problemas
    files_to_fix = [
        'autonomous_team_system.py',
        'developer_agent.py',
        'project_manager_agent.py',
        'web_interface.py',
        'autonomous_cli.py',
        'global_system_prompt.py'
    ]

    for filename in files_to_fix:
        if os.path.exists(filename):
            print(f"Procesando {filename}...")

            try:
                # Leer archivo
                with open(filename, 'r', encoding='utf-8') as f:
                    content = f.read()

                # Convertir todo a ASCII, reemplazando caracteres problemáticos
                ascii_content = ""
                changes = 0

                for char in content:
                    try:
                        char.encode('ascii')
                        ascii_content += char
                    except UnicodeEncodeError:
                        # Reemplazos específicos
                        replacements = {
                            '✅': '[OK]',
                            '❌': '[ERROR]',
                            '🎉': '[SUCCESS]',
                            '🚀': '[START]',
                            '📁': '[FOLDER]',
                            '🔧': '[CONFIG]',
                            '→': '->',
                            '⏰': '[TIMEOUT]',
                            '📤': '[SEND]',
                            '🚫': '[BLOCK]',
                            '📋': '[CLIPBOARD]',
                            '📊': '[CHART]',
                            '🔍': '[SEARCH]',
                            '📈': '[GRAPH]',
                            '💾': '[SAVE]',
                            '⚡': '[FAST]',
                            '🎯': '[TARGET]',
                            '📝': '[EDIT]',
                            '🔄': '[PROC]',
                            '📦': '[PACK]',
                            '🌟': '[NEW]',
                            'ó': 'o',
                            'í': 'i',
                            'á': 'a',
                            'é': 'e',
                            'ú': 'u',
                            'ñ': 'n',
                            'ü': 'u',
                            'Ó': 'O',
                            'Í': 'I',
                            'Á': 'A',
                            'É': 'E',
                            'Ú': 'U',
                            'Ñ': 'N',
                            'Ü': 'U'
                        }

                        if char in replacements:
                            ascii_content += replacements[char]
                            changes += 1
                        else:
                            # Si no está en la lista, usar código hex como comentario
                            ascii_content += f"[U{ord(char):04X}]"
                            changes += 1

                # Escribir archivo solo si hubo cambios
                if changes > 0:
                    with open(filename, 'w', encoding='utf-8') as f:
                        f.write(ascii_content)
                    print(f"  -> {changes} caracteres reemplazados")
                else:
                    print(f"  -> Sin cambios necesarios")

            except Exception as e:
                print(f"  -> ERROR: {e}")

if __name__ == "__main__":
    print("=== REPARACION AGRESIVA DE UNICODE ===")
    aggressive_unicode_fix()
    print("=== COMPLETADO ===")