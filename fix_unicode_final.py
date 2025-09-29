#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Reparacion final y definitiva de caracteres Unicode
"""

import os
import re

# Mapeo completo de caracteres Unicode a ASCII
UNICODE_MAP = {
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
    '📢': '[ANNOUNCE]',
    '📄': '[DOC]',
    '🔁': '[REPEAT]',
    '🏃': '[RUN]',
    '⚙️': '[GEAR]',
    '💻': '[PC]',
    '🖥️': '[DESKTOP]',
    '📱': '[MOBILE]',
    '🔗': '[LINK]',
    '⭐': '[STAR]',
    '💡': '[IDEA]',
    '🔥': '[HOT]',
    '🚨': '[ALERT]',
    '✔️': '[CHECK]',
    '❗': '[WARNING]',
    '⚠️': '[WARN]',
    '🛠️': '[TOOL]',
    '🎨': '[ART]',
    '📐': '[RULE]',
    '🔐': '[LOCK]',
    '🗝️': '[KEY]',
    '🔓': '[UNLOCK]',
    '📊': '[STATS]',
    '🎲': '[DICE]',
    '🧩': '[PUZZLE]',
    '⚽': '[BALL]',
    '🏆': '[TROPHY]',
    '🎖️': '[MEDAL]',
    '🏅': '[AWARD]',
    '📅': '[CALENDAR]',
    '⏱️': '[TIMER]',
    '⏲️': '[CLOCK]',
    '⌛': '[HOURGLASS]',
    '⌚': '[WATCH]',
    '📊': '[CHART]',
    '📈': '[UP]',
    '📉': '[DOWN]',
    '🔥': '[FIRE]',
    '💦': '[WATER]',
    '🌊': '[WAVE]',
    '🌟': '[SHINE]',
    '✨': '[SPARKLE]',
    '⭐': '[STAR]',
    '🔆': '[BRIGHT]',
    '🔅': '[DIM]',
    '\u2192': '->',  # Flecha derecha específica
    '\u2705': '[OK]',  # Check mark
    '\u274c': '[X]',   # Cross mark
    '\U0001f4cb': '[CLIPBOARD]',  # Clipboard
    '\U0001f50d': '[SEARCH]',     # Magnifying glass
    '\U0001f4e2': '[SPEAKER]',    # Loudspeaker
    '\U0001f6ab': '[BLOCK]',      # No entry sign
    '\U0001f4c4': '[DOC]'         # Page facing up
}

def fix_file_unicode(file_path):
    """Fix unicode characters in a single file"""
    try:
        # Read with UTF-8
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        original_content = content
        changes = 0

        # Replace all unicode characters
        for unicode_char, ascii_replacement in UNICODE_MAP.items():
            if unicode_char in content:
                count = content.count(unicode_char)
                content = content.replace(unicode_char, ascii_replacement)
                changes += count

        # Only write if changes were made
        if changes > 0:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            print(f"[OK] {file_path}: {changes} caracteres reparados")
            return True
        else:
            return False

    except Exception as e:
        print(f"[ERROR] {file_path}: {e}")
        return False

def main():
    """Main function"""
    print("=== REPARACION FINAL DE UNICODE ===")

    files_processed = 0
    files_fixed = 0

    # Process only critical files that are causing issues
    critical_files = [
        'test_global_prompt_v1.py',
        'fix_unicode_systematic.py',
        'backend_client.py',
        'discovery_cli.py',
        'excel_parser.py',
        'output_manager.py',
        'report_generator.py',
        'extraction.py'
    ]

    for file_name in critical_files:
        if os.path.exists(file_name):
            files_processed += 1
            if fix_file_unicode(file_name):
                files_fixed += 1

        # Also check in subdirectories
        for root, dirs, files in os.walk('.'):
            for file in files:
                if file == file_name:
                    file_path = os.path.join(root, file)
                    if file_path != file_name:  # Avoid duplicates
                        files_processed += 1
                        if fix_file_unicode(file_path):
                            files_fixed += 1

    print(f"\n=== RESULTADO ===")
    print(f"Archivos procesados: {files_processed}")
    print(f"Archivos reparados: {files_fixed}")
    print(f"[OK] Reparacion completa")

if __name__ == "__main__":
    main()