# -*- coding: utf-8 -*-
"""
Solucionador sistemático de caracteres Unicode problemáticos
Desarrollado por el mejor programador del mundo + IA más inteligente
"""

import os
import re
import sys

# Forzar encoding UTF-8 en Windows
if sys.platform == "win32":
    os.environ['PYTHONIOENCODING'] = 'utf-8'

def fix_unicode_systematically():
    """Reparar TODOS los caracteres Unicode problemáticos de forma sistemática"""

    # Mapping completo de caracteres problemáticos -> reemplazos ASCII
    unicode_replacements = {
        # Flechas
        '->': '->',
        '←': '<-',
        '↑': '^',
        '↓': 'v',
        '⇒': '=>',
        '⇐': '<=',

        # Emojis de comunicación
        '📨': '[MSG]',
        '📧': '[EMAIL]',
        '💬': '[TALK]',
        '[SPEAKER]': '[ANNOUNCE]',
        '📣': '[SPEAKER]',

        # Emojis de estado
        '[OK]': '[OK]',
        '[X]': '[ERROR]',
        '[WARN]': '[WARN]',
        '⚠': '[WARN]',
        '[PROC]': '[PROC]',
        '[BLOCK]': '[BLOCK]',
        '⏳': '[WAIT]',
        '[STAR]': '[STAR]',
        '🏁': '[END]',

        # Emojis de archivos/datos
        '[DOC]': '[FILE]',
        '[FOLDER]': '[DIR]',
        '📂': '[FOLDER]',
        '[CLIPBOARD]': '[CLIPBOARD]',
        '[CHART]': '[CHART]',
        '[UP]': '[CHART]',
        '[DOWN]': '[CHART]',
        '[PACK]': '[PACK]',
        '🗂️': '[ARCHIVE]',

        # Emojis de acción
        '[START]': '[START]',
        '[TARGET]': '[TARGET]',
        '[SEARCH]': '[SEARCH]',
        '[CONFIG]': '[TOOL]',
        '[GEAR]': '[GEAR]',
        '[TOOL]': '[TOOLS]',
        '🧹': '[CLEAN]',
        '🔒': '[LOCK]',
        '[UNLOCK]': '[UNLOCK]',

        # Emojis de personas/equipo
        '👥': '[TEAM]',
        '🤖': '[BOT]',
        '👨‍[PC]': '[DEV]',
        '👩‍[PC]': '[DEV]',
        '[PC]': '[CODE]',

        # Emojis de tiempo/estado
        '[TIMEOUT]': '[TIME]',
        '[TIMER]': '[TIME]',
        '[CLOCK]': '[TIMER]',
        '[WATCH]': '[WATCH]',
        '[HOURGLASS]': '[HOUR]',
        '♾️': '[INFINITY]',
        '∞': '[INFINITY]',

        # Emojis de éxito/fracaso
        '[SUCCESS]': '[DONE]',
        '🎊': '[CELEBRATE]',
        '[SPARKLE]': '[NEW]',
        '[IDEA]': '[IDEA]',
        '[FIRE]': '[HOT]',
        '💯': '[100]',

        # Símbolos especiales
        '•': '-',
        '◦': '-',
        '▪': '-',
        '▫': '-',
        '‣': '-',
        '⁃': '-',
        '∙': '-',

        # Checkmarks y crosses
        '✓': '[CHECK]',
        '✗': '[X]',
        '☑️': '[CHECKED]',
        '☐': '[UNCHECKED]',

        # Otros
        '🎬': '[DEMO]',
        '⛔': '[STOP]',
        '[LOCK]': '[SECURE]',
        '🌐': '[WEB]',
        '📲': '[MOBILE]',
        '[MOBILE]': '[PHONE]',
        '[SAVE]': '[DISK]',
        '💿': '[CD]',
        '📀': '[DVD]',
    }

    # Archivos principales que requieren limpieza
    critical_files = [
        'autonomous_team_system.py',
        'developer_agent.py',
        'project_manager_agent.py',
        'agent_communication.py',
        'autonomy_system.py',
        'web_interface.py',
        'autonomous_cli.py',
        'global_system_prompt.py',
        'message_contracts_v2.py',
        'message_contracts.py',
        'dev_agent_policies.py',
        'role_assignment.py'
    ]

    fixed_files = []
    errors = []

    print("=== REPARACIÓN SISTEMÁTICA DE UNICODE ===")
    print("Desarrollado por el mejor programador + IA más inteligente")
    print("=" * 60)

    for filename in critical_files:
        if not os.path.exists(filename):
            print(f"[SKIP] Archivo no encontrado: {filename}")
            continue

        try:
            print(f"[PROCESS] {filename}...")

            # Leer archivo
            with open(filename, 'r', encoding='utf-8') as f:
                content = f.read()

            original_content = content
            changes_made = 0

            # Aplicar reemplazos
            for unicode_char, replacement in unicode_replacements.items():
                if unicode_char in content:
                    count = content.count(unicode_char)
                    content = content.replace(unicode_char, replacement)
                    changes_made += count
                    if count > 0:
                        print(f"  - {unicode_char} -> {replacement} ({count} ocurrencias)")

            # Agregar encoding header si no existe
            if not content.startswith('# -*- coding: utf-8 -*-'):
                lines = content.split('\n')
                if lines[0].startswith('#!'):
                    lines.insert(1, '# -*- coding: utf-8 -*-')
                else:
                    lines.insert(0, '# -*- coding: utf-8 -*-')
                content = '\n'.join(lines)
                changes_made += 1
                print(f"  + Agregado encoding header")

            # Agregar configuración de Windows encoding si no existe
            if 'PYTHONIOENCODING' not in content and filename.endswith('.py'):
                lines = content.split('\n')

                # Buscar lugar apropiado para insertar
                insert_index = 0
                for i, line in enumerate(lines):
                    if line.startswith('import ') or line.startswith('from '):
                        insert_index = i
                        break

                if insert_index > 0:
                    encoding_block = [
                        '',
                        'import os',
                        'import sys',
                        'if sys.platform == "win32":',
                        '    os.environ["PYTHONIOENCODING"] = "utf-8"',
                        ''
                    ]

                    # Verificar si ya tiene imports de os/sys
                    has_os_import = any('import os' in line for line in lines[:insert_index+10])
                    has_sys_import = any('import sys' in line for line in lines[:insert_index+10])

                    if has_os_import and has_sys_import:
                        encoding_block = [
                            '',
                            'if sys.platform == "win32":',
                            '    os.environ["PYTHONIOENCODING"] = "utf-8"',
                            ''
                        ]
                    elif has_os_import:
                        encoding_block = [
                            '',
                            'import sys',
                            'if sys.platform == "win32":',
                            '    os.environ["PYTHONIOENCODING"] = "utf-8"',
                            ''
                        ]
                    elif has_sys_import:
                        encoding_block = [
                            '',
                            'import os',
                            'if sys.platform == "win32":',
                            '    os.environ["PYTHONIOENCODING"] = "utf-8"',
                            ''
                        ]

                    for j, block_line in enumerate(encoding_block):
                        lines.insert(insert_index + j, block_line)

                    content = '\n'.join(lines)
                    changes_made += 1
                    print(f"  + Agregado configuración encoding Windows")

            # Escribir archivo solo si hubo cambios
            if changes_made > 0:
                with open(filename, 'w', encoding='utf-8') as f:
                    f.write(content)
                fixed_files.append(filename)
                print(f"  [OK] {filename} - {changes_made} cambios aplicados")
            else:
                print(f"  [CLEAN] {filename} - Sin cambios necesarios")

        except Exception as e:
            error_msg = f"Error en {filename}: {str(e)}"
            errors.append(error_msg)
            print(f"  [ERROR] {error_msg}")

    print("\n" + "=" * 60)
    print("=== RESULTADO DE REPARACIÓN ===")
    print(f"Archivos procesados: {len(critical_files)}")
    print(f"Archivos reparados: {len(fixed_files)}")
    print(f"Errores: {len(errors)}")

    if fixed_files:
        print(f"\nArchivos reparados:")
        for f in fixed_files:
            print(f"  ✓ {f}")

    if errors:
        print(f"\nErrores encontrados:")
        for e in errors:
            print(f"  ✗ {e}")

    print(f"\n[{'SUCCESS' if len(errors) == 0 else 'PARTIAL'}] Reparación sistemática completada")
    return len(errors) == 0

if __name__ == "__main__":
    success = fix_unicode_systematically()
    exit(0 if success else 1)