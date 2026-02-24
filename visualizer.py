import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
import numpy as np
import io
import base64

# Dark theme matching your existing UI
plt.rcParams.update({
    'figure.facecolor':  '#02030a',
    'axes.facecolor':    '#030510',
    'axes.edgecolor':    '#1a2550',
    'axes.labelcolor':   '#8899cc',
    'text.color':        '#e8eeff',
    'xtick.color':       '#4a5a88',
    'ytick.color':       '#4a5a88',
    'grid.color':        '#0d1530',
    'grid.linewidth':    0.5,
    'font.family':       'monospace',
    'axes.titlecolor':   '#e8eeff',
    'legend.facecolor':  '#030510',
    'legend.edgecolor':  '#1a2550',
    'legend.labelcolor': '#e8eeff',
})

def fig_to_base64(fig):
    """Convert matplotlib figure to base64 string for sending to browser"""
    buf = io.BytesIO()
    fig.savefig(buf, format='png', dpi=150,
                bbox_inches='tight',
                facecolor=fig.get_facecolor())
    buf.seek(0)
    b64 = base64.b64encode(buf.read()).decode('utf-8')
    plt.close(fig)
    return b64

def plot_orbit(orbit_data, title=None):
    """
    Publication-ready orbital trajectory plot
    Left panel: XY orbit path colored by velocity
    Right panel: Distance and speed vs time
    """
    fig, axes = plt.subplots(1, 2, figsize=(14, 6))
    fig.suptitle(
        title or f"{orbit_data['body'].title()} Orbital Trajectory",
        fontsize=14, fontweight='bold', y=1.02
    )

    x = np.array(orbit_data['x'])
    y = np.array(orbit_data['y'])
    r = np.array(orbit_data['r'])
    v = np.array(orbit_data['v'])
    t = np.array(orbit_data['t'])
    color = orbit_data.get('color', '#4f7cff')
    body = orbit_data['body'].title()

    # ── LEFT: Orbital Path ──────────────────────────────────
    ax = axes[0]
    ax.grid(True, alpha=0.3)

    # Normalize velocity for color mapping
    v_norm = (v - v.min()) / (v.max() - v.min() + 1e-10)

    # Draw orbit segments colored by velocity
    for i in range(len(x) - 1):
        c = plt.cm.plasma(v_norm[i])
        ax.plot([x[i], x[i+1]], [y[i], y[i+1]],
                color=c, linewidth=2.0, alpha=0.9, solid_capstyle='round')

    # Sun at origin
    ax.scatter([0], [0], s=300, c='#fff200', zorder=10,
               edgecolors='#ffaa00', linewidth=2, label='Sun')

    # Planet starting position
    ax.scatter([x[0]], [y[0]], s=100, c=color,
               zorder=10, edgecolors='white',
               linewidth=1, label=body)

    # Perihelion marker
    peri_idx = np.argmin(r)
    ax.scatter([x[peri_idx]], [y[peri_idx]], s=80,
               c='#ff9900', zorder=9, marker='^',
               edgecolors='white', linewidth=0.5)
    ax.annotate('Perihelion',
                (x[peri_idx], y[peri_idx]),
                xytext=(8, 8), textcoords='offset points',
                fontsize=7, color='#ff9900', alpha=0.9)

    # Aphelion marker
    aph_idx = np.argmax(r)
    ax.scatter([x[aph_idx]], [y[aph_idx]], s=80,
               c='#4f7cff', zorder=9, marker='v',
               edgecolors='white', linewidth=0.5)
    ax.annotate('Aphelion',
                (x[aph_idx], y[aph_idx]),
                xytext=(8, -12), textcoords='offset points',
                fontsize=7, color='#4f7cff', alpha=0.9)

    # Colorbar for velocity
    sm = plt.cm.ScalarMappable(
        cmap='plasma',
        norm=mcolors.Normalize(vmin=v.min(), vmax=v.max())
    )
    sm.set_array([])
    cbar = plt.colorbar(sm, ax=ax, shrink=0.6, pad=0.02)
    cbar.set_label('Orbital Speed', fontsize=8, color='#8899cc')
    cbar.ax.yaxis.set_tick_params(color='#4a5a88')

    ax.set_xlabel('X (AU)')
    ax.set_ylabel('Y (AU)')
    ax.set_title(f'{body} — Orbital Path', fontsize=11)
    ax.legend(fontsize=8, loc='upper right')
    ax.set_aspect('equal')

    # ── RIGHT: Distance & Speed vs Time ─────────────────────
    ax2 = axes[1]
    ax2.grid(True, alpha=0.3)

    # Distance line
    ax2.plot(t, r, color=color, linewidth=2,
             label='Distance (AU)', alpha=0.9)
    ax2.set_xlabel('Time (days)')
    ax2.set_ylabel('Distance from Sun (AU)', color=color)
    ax2.tick_params(axis='y', labelcolor=color)

    # Speed on twin axis
    ax2b = ax2.twinx()
    ax2b.plot(t, v, color='#ff4f9a', linewidth=1.5,
              alpha=0.8, linestyle='--', label='Speed')
    ax2b.set_ylabel('Orbital Speed (AU/day)', color='#ff4f9a')
    ax2b.tick_params(axis='y', labelcolor='#ff4f9a')

    # Add orbital elements as text box
    elems = orbit_data.get('elements', {})
    info = (f"a = {elems.get('semi_major_axis_au','?')} AU\n"
            f"e = {elems.get('eccentricity','?')}\n"
            f"T = {elems.get('period_days','?')} days\n"
            f"q = {elems.get('perihelion_au','?')} AU\n"
            f"Q = {elems.get('aphelion_au','?')} AU")
    ax2.text(0.02, 0.97, info,
             transform=ax2.transAxes,
             fontsize=8, verticalalignment='top',
             bbox=dict(boxstyle='round', facecolor='#02030a',
                      alpha=0.8, edgecolor='#1a2550'),
             color='#e8eeff', family='monospace')

    ax2.set_title('Distance & Speed vs Time', fontsize=11)
    lines1, labs1 = ax2.get_legend_handles_labels()
    lines2, labs2 = ax2b.get_legend_handles_labels()
    ax2.legend(lines1 + lines2, labs1 + labs2,
               fontsize=8, loc='lower right')

    plt.tight_layout()
    return fig_to_base64(fig)

def plot_hohmann(transfer_data):
    """Plot Hohmann transfer orbit between two planets"""
    fig, ax = plt.subplots(figsize=(9, 9))
    ax.grid(True, alpha=0.3)
    ax.set_facecolor('#030510')

    r1 = transfer_data['r1_au']
    r2 = transfer_data['r2_au']
    body1 = transfer_data['from'].title()
    body2 = transfer_data['to'].title()

    # Draw circular orbits
    theta = np.linspace(0, 2*np.pi, 300)
    ax.plot(r1*np.cos(theta), r1*np.sin(theta),
            color='#4fffb0', linewidth=1.2,
            alpha=0.5, linestyle=':', label=f'{body1} orbit')
    ax.plot(r2*np.cos(theta), r2*np.sin(theta),
            color='#ff6b35', linewidth=1.2,
            alpha=0.5, linestyle=':', label=f'{body2} orbit')

    # Transfer ellipse
    tx = transfer_data['transfer_x']
    ty = transfer_data['transfer_y']
    ax.plot(tx, ty, color='#fff200', linewidth=2.5,
            alpha=0.9, label='Transfer orbit')

    # Sun
    ax.scatter([0], [0], s=300, c='#fff200',
               zorder=10, edgecolors='#ffaa00', linewidth=2)
    ax.annotate('Sun', (0, 0), xytext=(0.05, 0.05),
                fontsize=9, color='#fff200')

    # Departure point
    ax.scatter([tx[0]], [ty[0]], s=120, c='#4fffb0',
               zorder=10, edgecolors='white', linewidth=1)
    ax.annotate(f'{body1}\n(Departure)',
                (tx[0], ty[0]), xytext=(8, 8),
                textcoords='offset points',
                fontsize=8, color='#4fffb0')

    # Arrival point
    ax.scatter([tx[-1]], [ty[-1]], s=120, c='#ff6b35',
               zorder=10, edgecolors='white', linewidth=1)
    ax.annotate(f'{body2}\n(Arrival)',
                (tx[-1], ty[-1]), xytext=(8, -16),
                textcoords='offset points',
                fontsize=8, color='#ff6b35')

    # Transfer info box
    info = (f"Transfer: {body1} → {body2}\n"
            f"Duration: {transfer_data['transfer_days']} days\n"
            f"Δv₁: {transfer_data['delta_v1']} AU/yr\n"
            f"Δv₂: {transfer_data['delta_v2']} AU/yr\n"
            f"Total Δv: {transfer_data['total_delta_v']} AU/yr")
    ax.text(0.02, 0.98, info,
            transform=ax.transAxes,
            fontsize=9, verticalalignment='top',
            bbox=dict(boxstyle='round', facecolor='#02030a',
                     alpha=0.9, edgecolor='#fff200'),
            color='#e8eeff', family='monospace')

    ax.set_xlabel('X (AU)')
    ax.set_ylabel('Y (AU)')
    ax.set_title(f'Hohmann Transfer: {body1} → {body2}',
                 fontsize=13, fontweight='bold')
    ax.legend(fontsize=9, loc='lower right')
    ax.set_aspect('equal')

    plt.tight_layout()
    return fig_to_base64(fig)

def plot_multi_orbit(orbits_data, title="Solar System Orbits"):
    """Plot multiple planet orbits on same figure"""
    fig, ax = plt.subplots(figsize=(10, 10))
    ax.grid(True, alpha=0.2)

    for orbit in orbits_data:
        x = np.array(orbit['x'])
        y = np.array(orbit['y'])
        color = orbit.get('color', '#ffffff')
        body = orbit['body'].title()
        a = orbit['elements']['semi_major_axis_au']

        ax.plot(x, y, color=color, linewidth=1.8,
                alpha=0.8, label=f"{body} (a={a} AU)")
        ax.scatter([x[0]], [y[0]], s=60, c=color,
                   zorder=5, edgecolors='white', linewidth=0.5)

    # Sun
    ax.scatter([0], [0], s=400, c='#fff200',
               zorder=10, edgecolors='#ffaa00',
               linewidth=2, label='Sun')

    ax.set_xlabel('X (AU)')
    ax.set_ylabel('Y (AU)')
    ax.set_title(title, fontsize=13, fontweight='bold')
    ax.legend(fontsize=8, loc='upper right')
    ax.set_aspect('equal')

    plt.tight_layout()
    return fig_to_base64(fig)

# ── TEST ──────────────────────────────────────────────────────
if __name__ == "__main__":
    import sys
    sys.path.append('.')
    from physics_engine import compute_orbit, compute_hohmann

    print("Testing orbit plot...")
    orbit = compute_orbit("mars", duration_days=687)
    b64 = plot_orbit(orbit, "Mars — One Full Orbit")
    with open("test_mars_orbit.png", "wb") as f:
        f.write(base64.b64decode(b64))
    print("Saved test_mars_orbit.png")

    print("Testing Hohmann transfer plot...")
    transfer = compute_hohmann("earth", "mars")
    b64 = plot_hohmann(transfer)
    with open("test_hohmann.png", "wb") as f:
        f.write(base64.b64decode(b64))
    print("Saved test_hohmann.png")

    print("Testing multi-orbit plot...")
    from physics_engine import compute_multi_orbit
    orbits = compute_multi_orbit(
        ["mercury","venus","earth","mars"],
        duration_days=687
    )
    b64 = plot_multi_orbit(orbits, "Inner Solar System")
    with open("test_multi_orbit.png", "wb") as f:
        f.write(base64.b64decode(b64))
    print("Saved test_multi_orbit.png")

    print("\nAll plots generated successfully!")
    print("Check test_mars_orbit.png, test_hohmann.png, test_multi_orbit.png")