#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SMART RESTRICTION FIX
- Chatbot: Answers ANY question
- Simulations: ONLY orbital dynamics (shows error message for non-orbital)
"""

import os
import sys

def find_files():
    files = {}
    for name in ['ai_scenario_generator.py', 'ai_scenario_generator_final.py']:
        if os.path.exists(name):
            files['ai'] = name
            break
    if os.path.exists('websocket_server.py'):
        files['ws'] = 'websocket_server.py'
    if os.path.exists('index_rebound.html'):
        files['html'] = 'index_rebound.html'
    return files

def backup_once(filepath):
    backup = f"{filepath}.original"
    if not os.path.exists(backup):
        try:
            with open(filepath, 'r', encoding='utf-8') as src:
                with open(backup, 'w', encoding='utf-8') as dst:
                    dst.write(src.read())
        except:
            with open(filepath, 'r', encoding='latin-1') as src:
                with open(backup, 'w', encoding='utf-8') as dst:
                    dst.write(src.read())
        return True
    return False

def fix_ai_generator(filepath):
    """Add orbital-only restriction to AI scenario generator"""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
    except:
        with open(filepath, 'r', encoding='latin-1') as f:
            content = f.read()
    
    changes = []
    
    # Fix velocity if needed
    if '"vy": 6.396' in content:
        content = content.replace('"vy": 6.396', '"vy": 0.2148')
        changes.append("velocity")
    
    # Add validator
    if 'scenario_validator' not in content:
        pos = content.find('import json')
        if pos != -1:
            nl = content.find('\n', pos) + 1
            content = content[:nl] + '\ntry:\n    from scenario_validator import fix_scenario_velocities\nexcept:\n    def fix_scenario_velocities(s): return s\n\n' + content[nl:]
            changes.append("validator")
    
    # Add orbital-only validation function
    if 'def is_orbital_simulation' not in content:
        validation_code = '''
def is_orbital_simulation(prompt):
    """Check if request is for orbital dynamics simulation"""
    prompt_lower = prompt.lower()
    
    # Orbital keywords (ALLOWED)
    orbital_keywords = [
        'orbit', 'planet', 'moon', 'star', 'sun', 'earth', 'mars', 'venus', 
        'mercury', 'jupiter', 'saturn', 'uranus', 'neptune', 'pluto',
        'asteroid', 'comet', 'spacecraft', 'satellite', 'binary', 'exoplanet',
        'solar system', 'black hole', 'neutron star', 'lagrange', 'hohmann',
        'transfer', 'kepler', 'celestial', 'gravity', 'orbital', 'ellipse',
        'perihelion', 'aphelion', 'trojan', 'kuiper', 'oort'
    ]
    
    # Non-orbital keywords (REJECTED)
    non_orbital_keywords = [
        'weather', 'climate', 'temperature', 'rain', 'wind', 'storm', 'hurricane',
        'atmosphere', 'chemical', 'molecule', 'reaction', 'biology', 'cell',
        'DNA', 'protein', 'quantum', 'electron', 'atom', 'particle',
        'spring', 'pendulum', 'wave', 'sound', 'light diffraction',
        'electric', 'magnetic field', 'circuit', 'current', 'voltage'
    ]
    
    # Check for non-orbital keywords
    for keyword in non_orbital_keywords:
        if keyword in prompt_lower:
            return False
    
    # Check for orbital keywords
    for keyword in orbital_keywords:
        if keyword in prompt_lower:
            return True
    
    # If contains "simulate" but no clear orbital context, be cautious
    if 'simulate' in prompt_lower or 'show' in prompt_lower:
        # Default to allowing if ambiguous (user can try)
        return True
    
    return True  # Default allow

'''
        # Insert before get_scenario function
        pos = content.find('def get_scenario(')
        if pos != -1:
            content = content[:pos] + validation_code + content[pos:]
            changes.append("validation_function")
    
    # Modify get_scenario to check if orbital
    if 'def get_scenario(' in content and 'is_orbital_simulation' in content:
        # Find get_scenario function
        start = content.find('def get_scenario(')
        if start != -1:
            # Find the beginning of function body
            body_start = content.find(':', start) + 1
            next_line = content.find('\n', body_start) + 1
            
            # Add validation check
            validation_check = '''
    # Check if request is for orbital dynamics
    if not is_orbital_simulation(request):
        return {
            "ok": False,
            "error": "non_orbital",
            "message": "⚠️ This simulator is specialized for ORBITAL DYNAMICS only.\\n\\nI can simulate:\\n  • Planets, moons, asteroids, comets\\n  • Binary/multiple star systems\\n  • Black holes with orbiting objects\\n  • Spacecraft trajectories\\n  • Exoplanet systems\\n\\nTry: 'hot jupiter system' or 'earth moon' or 'binary stars'"
        }
    
'''
            content = content[:next_line] + validation_check + content[next_line:]
            changes.append("orbital_check")
    
    # Add auto-scaling
    if 'def auto_scale(' not in content:
        scale_code = '''
def auto_scale(bodies):
    """Auto-adjust scale to prevent off-screen issues"""
    if not bodies:
        return 180
    max_r = 0
    for b in bodies:
        r = (b.get('x', 0)**2 + b.get('y', 0)**2)**0.5
        if r > max_r:
            max_r = r
    if max_r < 0.1:
        return 600
    elif max_r < 1:
        return 300
    elif max_r < 5:
        return 100
    elif max_r < 15:
        return 40
    else:
        return 20

'''
        pos = content.find('def get_scenario(')
        if pos != -1:
            content = content[:pos] + scale_code + content[pos:]
            changes.append("auto_scale")
            
            # Use auto_scale
            if 'scenario.setdefault("scale"' in content:
                content = content.replace(
                    'scenario.setdefault("scale", 180.0)',
                    'scenario.setdefault("scale", auto_scale(scenario.get("bodies", [])))'
                )
    
    if changes:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
    
    return changes

def fix_websocket(filepath):
    """Add error handling in WebSocket server for non-orbital requests"""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
    except:
        try:
            with open(filepath, 'r', encoding='latin-1') as f:
                content = f.read()
        except:
            return []
    
    changes = []
    
    # Add error handling for non-orbital simulations
    if 'if not result["ok"]' in content and 'non_orbital' not in content:
        # Find error handling section
        pattern = 'if not result["ok"]:'
        pos = content.find(pattern)
        if pos != -1:
            # Find the error message send
            error_section_start = pos
            error_section_end = content.find('continue', pos)
            
            if error_section_end != -1:
                # Check if it's the WebSocket section
                if 'await send' in content[error_section_start:error_section_end]:
                    # Add special handling for non_orbital error
                    insert_pos = content.find('await send({"type": "error"', pos)
                    if insert_pos != -1:
                        # Add check before generic error
                        check_code = '''
                    # Check if non-orbital rejection
                    if result.get("error") == "non_orbital":
                        await send({
                            "type": "error", 
                            "message": result.get("message", "Simulations restricted to orbital dynamics only")
                        })
                        continue
                    
                    '''
                        # Insert before the generic error send
                        indent = ' ' * 20
                        content = content[:insert_pos] + check_code + content[insert_pos:]
                        changes.append("ws_error_handling")
    
    if changes:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
    
    return changes

def fix_overlap(filepath):
    """Fix overlap with z-ordering"""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
    except:
        with open(filepath, 'r', encoding='latin-1') as f:
            content = f.read()
    
    if 'sortedBodies' in content:
        return []
    
    lines = content.split('\n')
    for i, line in enumerate(lines):
        if 'bodies.forEach(function (b) {' in line:
            indent = ' ' * (len(line) - len(line.lstrip()))
            sorting = [
                f"{indent}var sortedBodies = bodies.slice().sort(function(a, b) {{",
                f"{indent}  if (a.type === 'star' && b.type !== 'star') return -1;",
                f"{indent}  if (b.type === 'star' && a.type !== 'star') return 1;",
                f"{indent}  var distA = a.x * a.x + a.y * a.y;",
                f"{indent}  var distB = b.x * b.x + b.y * b.y;",
                f"{indent}  return distB - distA;",
                f"{indent}}});",
                line.replace('bodies.forEach', 'sortedBodies.forEach')
            ]
            lines[i:i+1] = sorting
            break
    
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write('\n'.join(lines))
    
    return ['z-order']

# === MAIN ===
print("=" * 70)
print("SMART RESTRICTION FIX")
print("=" * 70)
print("\n✓ Chatbot: Answers ANY question (orbital, physics, anything)")
print("✓ Simulations: ONLY orbital dynamics")
print("✓ Shows user-friendly error for non-orbital simulation requests")
print("✓ Auto-scales to prevent off-screen issues")
print("✓ One-time backup (no repeated .backup files)\n")

files = find_files()

if not files.get('ai'):
    print("✗ AI generator not found!")
    sys.exit(1)

print("Found files:")
for key, val in files.items():
    print(f"  - {val}")

input("\nPress ENTER to apply fixes...")

all_changes = []

# Fix AI generator
print(f"\n[Fixing] {files['ai']}...")
if backup_once(files['ai']):
    print("  ✓ Created backup (.original)")
changes = fix_ai_generator(files['ai'])
if changes:
    print(f"  ✓ Applied: {', '.join(changes)}")
    all_changes.extend(changes)

# Fix WebSocket if exists
if files.get('ws'):
    print(f"\n[Fixing] {files['ws']}...")
    if backup_once(files['ws']):
        print("  ✓ Created backup (.original)")
    changes = fix_websocket(files['ws'])
    if changes:
        print(f"  ✓ Applied: {', '.join(changes)}")
        all_changes.extend(changes)

# Fix overlap if HTML exists
if files.get('html'):
    print(f"\n[Fixing] {files['html']}...")
    if backup_once(files['html']):
        print("  ✓ Created backup (.original)")
    changes = fix_overlap(files['html'])
    if changes:
        print(f"  ✓ Applied: {', '.join(changes)}")
        all_changes.extend(changes)

print("\n" + "=" * 70)
print("COMPLETE!")
print("=" * 70)

if all_changes:
    print(f"\nFixed: {', '.join(set(all_changes))}")
    print("\nNext steps:")
    print("  1. Restart servers (python websocket_server.py & node server_v2.js)")
    print("  2. Reload browser (Ctrl+Shift+R)")
    print("\nTesting:")
    print("  ✓ Chatbot: Ask anything (works)")
    print("  ✓ Simulation: 'earth moon system' (works)")
    print("  ✓ Simulation: 'weather in 2030' (shows error message)")
else:
    print("\nAlready fixed! Restart servers if needed.")

print("\n" + "=" * 70)
