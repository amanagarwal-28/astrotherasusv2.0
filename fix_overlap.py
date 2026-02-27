#!/usr/bin/env python3
"""
Fix planets overlapping Sun in the frontend.
Windows-compatible version with proper UTF-8 encoding.
"""

import os
import sys
from datetime import datetime

def backup_file(filepath):
    """Create timestamped backup with UTF-8 encoding."""
    if os.path.exists(filepath):
        backup = f"{filepath}.backup.{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        try:
            with open(filepath, 'r', encoding='utf-8') as src:
                with open(backup, 'w', encoding='utf-8') as dst:
                    dst.write(src.read())
            print(f"  ✓ Backed up: {backup}")
            return True
        except UnicodeDecodeError:
            # Try with different encoding
            with open(filepath, 'r', encoding='latin-1') as src:
                with open(backup, 'w', encoding='utf-8') as dst:
                    dst.write(src.read())
            print(f"  ✓ Backed up: {backup} (converted to UTF-8)")
            return True
    return False

def fix_html_rendering():
    """Add z-ordering to body rendering."""
    filepath = "index_rebound.html"
    
    if not os.path.exists(filepath):
        print(f"  ✗ {filepath} not found")
        print("     Make sure you're in the correct directory")
        return False
    
    backup_file(filepath)
    
    # Read file with UTF-8
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
    except UnicodeDecodeError:
        # Fallback to latin-1
        with open(filepath, 'r', encoding='latin-1') as f:
            content = f.read()
    
    # Find the renderFrame function and bodies.forEach
    target = "var bodies = data.bodies || []; simState.currentBodies = bodies;\n      bodies.forEach(function (b) {"
    
    if target not in content:
        # Try without exact spacing
        target_alt1 = "var bodies = data.bodies || []"
        target_alt2 = "bodies.forEach(function (b) {"
        
        if target_alt1 in content and target_alt2 in content:
            # Find the section between these two
            start = content.find(target_alt1)
            end = content.find(target_alt2, start)
            
            if start != -1 and end != -1:
                # Extract the full section
                section = content[start:end + len(target_alt2)]
                
                # Create replacement
                replacement = """var bodies = data.bodies || []; simState.currentBodies = bodies;

      // Z-ORDER FIX: Render stars first (background), then planets by distance
      var sortedBodies = bodies.slice().sort(function(a, b) {
        // Stars always in back
        if (a.type === 'star' && b.type !== 'star') return -1;
        if (b.type === 'star' && a.type !== 'star') return 1;
        // Render farther bodies first (they go behind)
        var distA = a.x * a.x + a.y * a.y;
        var distB = b.x * b.x + b.y * b.y;
        return distB - distA;
      });

      sortedBodies.forEach(function (b) {"""
                
                content = content.replace(section, replacement)
                
                # Write back with UTF-8
                with open(filepath, 'w', encoding='utf-8') as f:
                    f.write(content)
                
                print("  ✓ Added z-ordering to body rendering")
                print("     Sun will now always render behind planets")
                return True
        
        print("  ✗ Could not find rendering code to patch")
        print("     Manual fix needed - see instructions below")
        return False
    
    # Original exact match found
    replacement = """var bodies = data.bodies || []; simState.currentBodies = bodies;

      // Z-ORDER FIX: Render stars first (background), then planets by distance
      var sortedBodies = bodies.slice().sort(function(a, b) {
        // Stars always in back
        if (a.type === 'star' && b.type !== 'star') return -1;
        if (b.type === 'star' && a.type !== 'star') return 1;
        // Render farther bodies first (they go behind)
        var distA = a.x * a.x + a.y * a.y;
        var distB = b.x * b.x + b.y * b.y;
        return distB - distA;
      });

      sortedBodies.forEach(function (b) {"""
    
    content = content.replace(target, replacement)
    
    # Write back with UTF-8
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print("  ✓ Added z-ordering to body rendering")
    print("     Sun will now always render behind planets")
    return True

def main():
    print("=" * 70)
    print("OVERLAP FIX - Planets Overlapping Sun")
    print("=" * 70)
    print("\nThis patches index_rebound.html to fix visual overlapping.")
    print("Bodies will be rendered in correct z-order (Sun in back).\n")
    
    if not os.path.exists('index_rebound.html'):
        print("ERROR: index_rebound.html not found!")
        print("Please run this script from your Astro Thesaurus directory.")
        sys.exit(1)
    
    input("Press ENTER to continue (or Ctrl+C to cancel)...")
    
    print("\n[Patching] index_rebound.html...")
    success = fix_html_rendering()
    
    if success:
        print("\n" + "=" * 70)
        print("FIX COMPLETE!")
        print("=" * 70)
        print("\n✓ index_rebound.html patched successfully")
        print("✓ Backup created")
        print("\nNext steps:")
        print("  1. Reload the page in your browser (Ctrl+Shift+R)")
        print("  2. Test with: 'hot jupiter system'")
        print("  3. Planet should now be visually separate from star!")
    else:
        print("\n" + "=" * 70)
        print("MANUAL FIX NEEDED")
        print("=" * 70)
        print("\nOpen index_rebound.html and find this line (~1528):")
        print("  bodies.forEach(function (b) {")
        print("\nReplace it with:")
        print("""
      var sortedBodies = bodies.slice().sort(function(a, b) {
        if (a.type === 'star' && b.type !== 'star') return -1;
        if (b.type === 'star' && a.type !== 'star') return 1;
        var distA = a.x * a.x + a.y * a.y;
        var distB = b.x * b.x + b.y * b.y;
        return distB - distA;
      });
      
      sortedBodies.forEach(function (b) {
""")
        print("\nThen reload browser.")
    
    print("\n" + "=" * 70)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nCancelled by user.")
        sys.exit(0)
    except Exception as e:
        print(f"\n\nERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
