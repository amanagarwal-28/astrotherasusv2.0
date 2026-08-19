"""
Integrator accuracy/performance benchmark for the paper's validation section.

Builds a reproducible 9-body Sun + 8-planets scenario purely from the
analytic Keplerian elements already in physics_engine.SOLAR_SYSTEM (each
planet placed at perihelion with its vis-viva perihelion speed) — no network
access required, so this benchmark is fully offline and deterministic.

For each REBOUND integrator (ias15, whfast, leapfrog) it integrates the
system forward, sampling the fractional energy drift |ΔE/E| at regular
intervals, and produces:
  - benchmarks/results/energy_drift_comparison.png  (log-scale drift vs time)
  - benchmarks/results/energy_drift_data.csv          (raw sampled data)
  - benchmarks/results/summary.md                      (final drift + runtime table)

Run: python benchmarks/integrator_comparison.py
"""
import csv
import math
import os
import sys
import time

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import rebound

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from physics_engine import SOLAR_SYSTEM  # noqa: E402

RESULTS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "results")
G_SOLAR = 4 * math.pi ** 2
M_SUN = 1.0
EARTH_MASSES_TO_MSUN = 3.003e-6  # SOLAR_SYSTEM["mass"] is in Earth masses

INTEGRATORS = ["ias15", "whfast", "leapfrog"]
# dataviz palette — categorical slots 1/2/3 (light mode), fixed order
COLORS = {"ias15": "#2a78d6", "whfast": "#eb6834", "leapfrog": "#1baf7a"}

INTEGRATION_YEARS = 50.0
SAMPLE_INTERVAL_YEARS = 0.5
# Fixed-step integrators need dt well below Mercury's ~0.24 yr period.
FIXED_DT_YEARS = SOLAR_SYSTEM["mercury"]["period"] / 365.25 / 50.0


def build_solar_system(integrator: str) -> rebound.Simulation:
    """Sun + 8 planets, each placed at perihelion with the vis-viva perihelion speed."""
    sim = rebound.Simulation()
    sim.units = ("AU", "yr", "Msun")
    sim.integrator = integrator
    if integrator in ("whfast", "leapfrog"):
        sim.dt = FIXED_DT_YEARS

    sim.add(m=M_SUN)  # Sun at origin
    for name, body in SOLAR_SYSTEM.items():
        a, e = body["a"], body["e"]
        r_peri = a * (1 - e)
        v_peri = math.sqrt(G_SOLAR * M_SUN * (2 / r_peri - 1 / a))
        sim.add(m=body["mass"] * EARTH_MASSES_TO_MSUN, x=r_peri, y=0.0, vx=0.0, vy=v_peri)

    sim.move_to_com()
    return sim


def run_benchmark(integrator: str) -> dict:
    sim = build_solar_system(integrator)
    E0 = sim.energy()

    times, drifts = [], []
    # Start at the first sample interval, not t=0: energy drift is trivially
    # zero at t=0 by definition, which would otherwise plot as a spurious
    # vertical spike down to the log-scale floor.
    t = SAMPLE_INTERVAL_YEARS
    wall_start = time.perf_counter()
    while t <= INTEGRATION_YEARS + 1e-9:
        sim.integrate(t)
        drift = abs((sim.energy() - E0) / E0) if E0 != 0 else 0.0
        times.append(t)
        drifts.append(max(drift, 1e-16))  # floor for log-scale plotting
        t += SAMPLE_INTERVAL_YEARS
    wall_elapsed = time.perf_counter() - wall_start

    return {
        "integrator": integrator,
        "times": times,
        "drifts": drifts,
        "final_drift": drifts[-1],
        "max_drift": max(drifts),
        "wall_seconds": wall_elapsed,
    }


def write_csv(results: list, path: str) -> None:
    with open(path, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["integrator", "t_years", "energy_drift_abs"])
        for r in results:
            for t, d in zip(r["times"], r["drifts"]):
                writer.writerow([r["integrator"], round(t, 4), f"{d:.6e}"])


def write_summary(results: list, path: str) -> None:
    lines = [
        "# Integrator Benchmark Summary",
        "",
        f"9-body Sun + 8-planets system, integrated for {INTEGRATION_YEARS:.0f} years.",
        "Initial conditions: each planet at perihelion with vis-viva perihelion speed,",
        "derived analytically from physics_engine.SOLAR_SYSTEM (a, e, period). No network access used.",
        "",
        "| Integrator | Final \\|ΔE/E\\| | Max \\|ΔE/E\\| | Wall time (s) |",
        "|---|---|---|---|",
    ]
    for r in results:
        lines.append(
            f"| {r['integrator']} | {r['final_drift']:.2e} | {r['max_drift']:.2e} | {r['wall_seconds']:.3f} |"
        )
    lines.append("")
    with open(path, "w") as f:
        f.write("\n".join(lines))


def plot_comparison(results: list, path: str) -> None:
    fig, ax = plt.subplots(figsize=(7, 4.5), dpi=150)
    fig.patch.set_facecolor("#fcfcfb")
    ax.set_facecolor("#fcfcfb")

    for r in results:
        ax.plot(
            r["times"], r["drifts"],
            color=COLORS[r["integrator"]], linewidth=2,
            label=r["integrator"],
        )

    ax.set_yscale("log")
    ax.set_xlabel("Simulation time (years)", color="#0b0b0b")
    ax.set_ylabel("Fractional energy drift  |ΔE / E₀|", color="#0b0b0b")
    ax.set_title(
        f"Energy conservation: REBOUND integrators on a {len(SOLAR_SYSTEM) + 1}-body solar system",
        color="#0b0b0b", fontsize=11,
    )
    ax.tick_params(colors="#52514e")
    for spine in ("top", "right"):
        ax.spines[spine].set_visible(False)
    for spine in ("left", "bottom"):
        ax.spines[spine].set_color("#c3c2b7")
    ax.grid(True, which="major", axis="y", color="#e1e0d9", linewidth=0.8)
    legend = ax.legend(frameon=False, loc="upper left")
    for text in legend.get_texts():
        text.set_color("#0b0b0b")

    fig.tight_layout()
    fig.savefig(path, facecolor=fig.get_facecolor())
    plt.close(fig)


def main():
    os.makedirs(RESULTS_DIR, exist_ok=True)
    results = [run_benchmark(integrator) for integrator in INTEGRATORS]

    plot_comparison(results, os.path.join(RESULTS_DIR, "energy_drift_comparison.png"))
    write_csv(results, os.path.join(RESULTS_DIR, "energy_drift_data.csv"))
    write_summary(results, os.path.join(RESULTS_DIR, "summary.md"))

    print(f"{'Integrator':<10} {'Final |dE/E|':>14} {'Max |dE/E|':>14} {'Wall (s)':>10}")
    for r in results:
        print(f"{r['integrator']:<10} {r['final_drift']:>14.2e} {r['max_drift']:>14.2e} {r['wall_seconds']:>10.3f}")
    print(f"\nWrote figures/data to {RESULTS_DIR}/")


if __name__ == "__main__":
    main()
