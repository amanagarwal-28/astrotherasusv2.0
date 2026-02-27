#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Fix Suggestions:
1. Remove pre-loaded suggestions that aren't orbital dynamics (black holes merging)
2. Update chatbot message to include "related to orbital dynamics"
3. Keep all orbital-related suggestions
"""

import os
import sys

def fix_html_suggestions():
    """Remove non-orbital suggestions from HTML"""
    
    filepath = "index_rebound.html"
    if not os.path.exists(filepath):
        print("✗ index_rebound.html not found")
        return False
    
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
    except:
        with open(filepath, 'r', encoding='latin-1') as f:
            content = f.read()
    
    changes = []
    
    # Remove black holes merging suggestion (not orbital dynamics)
    if "two black holes merging" in content:
        # Find and remove the entire line
        lines = content.split('\n')
        new_lines = []
        for line in lines:
            if "two black holes merging" in line and "onclick" in line:
                # Skip this line (remove it)
                changes.append("Removed 'black holes merging' suggestion")
                continue
            new_lines.append(line)
        
        content = '\n'.join(new_lines)
    
    # Replace with orbital-friendly suggestions
    # Find the suggestion area and add better examples
    if '<div class="wce"' in content and len(changes) > 0:
        # Add replacement suggestions after TRAPPIST-1
        old_section = '<div class="wce" onclick="fillSim(\'TRAPPIST-1 all 7 planets\')">⚡ Simulate TRAPPIST-1</div>'
        
        new_section = '''<div class="wce" onclick="fillSim('TRAPPIST-1 all 7 planets')">⚡ Simulate TRAPPIST-1</div>
            <div class="wce" onclick="fillSim('Earth Moon system')">⚡ Simulate Earth-Moon</div>
            <div class="wce" onclick="fillSim('Hot Jupiter with two planets')">⚡ Simulate Hot Jupiter</div>'''
        
        if old_section in content:
            content = content.replace(old_section, new_section)
            changes.append("Added Earth-Moon and Hot Jupiter suggestions")
    
    if changes:
        # Backup
        backup = filepath + ".backup"
        if not os.path.exists(backup):
            with open(backup, 'w', encoding='utf-8') as f:
                with open(filepath, 'r', encoding='utf-8') as src:
                    f.write(src.read())
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        
        return changes
    
    return []

def fix_chatbot_message():
    """Update chatbot rejection message"""
    
    # Find the file with the message
    for filepath in ['api_server.py', 'websocket_server.py']:
        if not os.path.exists(filepath):
            continue
        
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
        except:
            with open(filepath, 'r', encoding='latin-1') as f:
                content = f.read()
        
        changes = []
        
        # Find the current message
        old_messages = [
            "I specialize in orbital mechanics.",
            "I specialize in orbital mechanics and dynamics only.",
        ]
        
        new_message = "I specialize in orbital mechanics. Ask about planet orbits, transfers, Lagrange points, Kepler's laws related to orbital dynamics!"
        
        changed = False
        for old_msg in old_messages:
            if old_msg in content and "Ask about" not in content:
                content = content.replace(old_msg, new_message)
                changed = True
                changes.append(f"Updated message in {filepath}")
        
        if changed:
            # Backup
            backup = filepath + ".backup"
            if not os.path.exists(backup):
                with open(backup, 'w', encoding='utf-8') as f:
                    f.write(open(filepath, 'r', encoding='utf-8').read())
            
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(content)
            
            return changes
    
    return []

# === MAIN ===
print("=" * 70)
print("FIX SUGGESTIONS")
print("=" * 70)
print("\n1. Remove non-orbital suggestions (black holes merging)")
print("2. Add orbital suggestions (Earth-Moon, Hot Jupiter)")
print("3. Update chatbot message to include 'related to orbital dynamics'\n")

input("Press ENTER to apply fixes...")

all_changes = []

# Fix HTML suggestions
print("\n[Fixing] index_rebound.html...")
html_changes = fix_html_suggestions()
if html_changes:
    for change in html_changes:
        print(f"  ✓ {change}")
    all_changes.extend(html_changes)
else:
    print("  ℹ No changes needed or file not found")

# Fix chatbot message
print("\n[Fixing] Chatbot message...")
msg_changes = fix_chatbot_message()
if msg_changes:
    for change in msg_changes:
        print(f"  ✓ {change}")
    all_changes.extend(msg_changes)
else:
    print("  ℹ No changes needed or file not found")

print("\n" + "=" * 70)
if all_changes:
    print("COMPLETE!")
    print("=" * 70)
    print(f"\nChanges applied: {len(all_changes)}")
    print("\nNext steps:")
    print("  1. Restart servers")
    print("  2. Reload browser (Ctrl+Shift+R)")
    print("\nSuggestions now show:")
    print("  ✓ What is a Hohmann transfer?")
    print("  ✓ Explain Lagrange points")
    print("  ✓ Show Mars orbit plot")
    print("  ✓ Simulate TRAPPIST-1")
    print("  ✓ Simulate Earth-Moon (NEW)")
    print("  ✓ Simulate Hot Jupiter (NEW)")
    print("\nRemoved:")
    print("  ✗ Simulate black holes merging")
else:
    print("NO CHANGES NEEDED")
    print("=" * 70)
    print("\nFiles already fixed or not found")

print("\n" + "=" * 70)
