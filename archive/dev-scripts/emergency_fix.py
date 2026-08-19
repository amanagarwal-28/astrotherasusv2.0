#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
EMERGENCY FIX - Windows Compatible
"""

import os
import sys
from datetime import datetime

def find_ai_generator():
    candidates = ['ai_scenario_generator.py', 'ai_scenario_generator_final.py', 'ai_scenario_generator_fixed.py']
    for name in candidates:
        if os.path.exists(name):
            return name
    for f in os.listdir('.'):
        if f.startswith('ai_scenario') and f.endswith('.py'):
            return f
    return None

def backup_file(filepath):
    backup = f"{filepath}.backup.{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    try:
        with open(filepath, 'r', encoding='utf-8') as src:
            with open(backup, 'w', encoding='utf-8') as dst:
                dst.write(src.read())
    except:
        with open(filepath, 'r', encoding='latin-1') as src:
            with open(backup, 'w', encoding='utf-8') as dst:
                dst.write(src.read())
    print(f"  ✓ Backed up {filepath}")
    return True

def fix_moon_velocity(filepath):
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
    except:
        with open(filepath, 'r', encoding='latin-1') as f:
            content = f.read()
    
    changes = 0
    if '"vy": 6.396' in content:
        content = content.replace('"vy": 6.396', '"vy": 0.2148')
        changes += 1
        print("  ✓ Fixed Moon velocity: 6.396 → 0.2148")
    
    if 'scenario_validator' not in content:
        pos = content.find('import json')
        if pos != -1:
            nl = content.find('\n', pos) + 1
            content = content[:nl] + '\ntry:\n    from scenario_validator import fix_scenario_velocities\n    VALIDATOR_AVAILABLE = True\nexcept:\n    VALIDATOR_AVAILABLE = False\n    def fix_scenario_velocities(s): return s\n\n' + content[nl:]
            changes += 1
            print("  ✓ Added validator")
    
    if changes:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
    return changes > 0

print("=" * 70)
print("ASTRO THESAURUS - VELOCITY FIX")
print("=" * 70)

ai_file = find_ai_generator()
if not ai_file:
    print("\n✗ AI generator not found!")
    sys.exit(1)

print(f"\n✓ Found: {ai_file}")
input("\nPress ENTER to fix...")

backup_file(ai_file)
fix_moon_velocity(ai_file)

print("\n" + "=" * 70)
print("DONE! Restart servers and test 'earth moon system'")
print("=" * 70)
