"""
Diode Rectifier Simulator
=========================
Simulates half-wave and full-wave (bridge) rectifiers with an optional
filter capacitor, using the constant-voltage-drop diode model
(as in Neamen, *Electronic Circuit Analysis and Design*).

Diode model:
    conducts when v_anode - v_cathode > V_gamma, then drops exactly V_gamma
    (V_gamma ~ 0.7 V for silicon).

Usage:
    python rectifier.py                 # run default demo and save plots
    python rectifier.py --vm 12 --f 60 --r 1000 --c 100e-6
"""

import argparse
import os
from dataclasses import dataclass

import numpy as np
import matplotlib

matplotlib.use("Agg")  # save figures without needing a display
import matplotlib.pyplot as plt


# --------------------------------------------------------------------------
# Circuit parameters
# --------------------------------------------------------------------------
@dataclass
class Circuit:
    vm: float = 12.0        # peak of the AC source (V)
    f: float = 60.0         # frequency (Hz) - 60 Hz in Saudi Arabia
    r: float = 1000.0       # load resistance (ohm)
    c: float = 100e-6       # filter capacitor (F); 0 = no filter
    v_gamma: float = 0.7    # diode turn-on voltage (V), silicon
    cycles: int = 10        # number of cycles to simulate
    dt: float = 1e-5        # time step (s)


# --------------------------------------------------------------------------
# Source
# --------------------------------------------------------------------------
def source(circ: Circuit):
    """Return time array and sine-wave input: Vin = Vm * sin(2*pi*f*t)."""
    t = np.arange(0, circ.cycles / circ.f, circ.dt)
    vin = circ.vm * np.sin(2 * np.pi * circ.f * t)
    return t, vin


# --------------------------------------------------------------------------
# Rectifiers WITHOUT filter
# --------------------------------------------------------------------------
def half_wave(vin, v_gamma):
    """Single diode: passes only the positive half, minus one diode drop."""
    return np.maximum(vin - v_gamma, 0.0)


def full_wave_bridge(vin, v_gamma):
    """Bridge: two diodes conduct at any time, so we lose 2 * V_gamma."""
    return np.maximum(np.abs(vin) - 2 * v_gamma, 0.0)


# --------------------------------------------------------------------------
# Rectifiers WITH filter capacitor
# --------------------------------------------------------------------------
def with_filter(vin, circ: Circuit, kind: str):
    """
    Add a capacitor in parallel with the load R.

    Each time step:
      - If the rectified source is higher than the capacitor voltage,
        the diode conducts and the capacitor follows the source.
      - Otherwise the diode is off and the capacitor discharges through R:
            v(t + dt) = v(t) * exp(-dt / (R*C))
    """
    if kind == "half":
        rectified = half_wave(vin, circ.v_gamma)
    elif kind == "full":
        rectified = full_wave_bridge(vin, circ.v_gamma)
    else:
        raise ValueError("kind must be 'half' or 'full'")

    decay = np.exp(-circ.dt / (circ.r * circ.c))
    vout = np.zeros_like(rectified)
    v_cap = 0.0
    for i, v_src in enumerate(rectified):
        if v_src > v_cap:
            v_cap = v_src            # diode ON: capacitor charges
        else:
            v_cap = v_cap * decay    # diode OFF: capacitor discharges
        vout[i] = v_cap
    return vout


# --------------------------------------------------------------------------
# Measurements
# --------------------------------------------------------------------------
def steady_state(t, vout, circ: Circuit, last_cycles=2):
    """Return the part of the waveform from the last few cycles."""
    t_start = (circ.cycles - last_cycles) / circ.f
    return vout[t >= t_start]


def measure(t, vout, circ: Circuit):
    """Peak, minimum, peak-to-peak ripple, DC average, and ripple factor."""
    v = steady_state(t, vout, circ)
    v_max, v_min = v.max(), v.min()
    v_ripple = v_max - v_min
    v_dc = v.mean()
    # ripple factor = Vr(rms) / Vdc, with the triangular-wave approximation
    ripple_factor = (v_ripple / (2 * np.sqrt(3))) / v_dc
    return {
        "v_max": v_max,
        "v_min": v_min,
        "v_ripple": v_ripple,
        "v_dc": v_dc,
        "ripple_factor": ripple_factor,
    }


def ripple_formula(v_peak_out, circ: Circuit, kind: str):
    """
    Textbook approximation:
        half-wave: Vr ~ VM / (f * R * C)
        full-wave: Vr ~ VM / (2 * f * R * C)
    """
    factor = 1 if kind == "half" else 2
    return v_peak_out / (factor * circ.f * circ.r * circ.c)


# --------------------------------------------------------------------------
# Plots
# --------------------------------------------------------------------------
def plot_unfiltered(circ: Circuit, outdir: str):
    t, vin = source(circ)
    one_cycle = t < 3 / circ.f  # show 3 cycles only

    fig, axes = plt.subplots(2, 1, figsize=(9, 7), sharex=True)
    for ax, (name, vout) in zip(
        axes,
        [
            ("Half-wave rectifier", half_wave(vin, circ.v_gamma)),
            ("Full-wave bridge rectifier", full_wave_bridge(vin, circ.v_gamma)),
        ],
    ):
        ax.plot(t[one_cycle] * 1e3, vin[one_cycle], "--", color="gray", label="Input")
        ax.plot(t[one_cycle] * 1e3, vout[one_cycle], color="tab:blue", lw=2, label="Output")
        ax.set_title(name + " (no filter)")
        ax.set_ylabel("Voltage (V)")
        ax.grid(alpha=0.3)
        ax.legend(loc="upper right")
    axes[-1].set_xlabel("Time (ms)")
    fig.tight_layout()
    path = os.path.join(outdir, "rectifiers_no_filter.png")
    fig.savefig(path, dpi=150)
    plt.close(fig)
    return path


def plot_filtered(circ: Circuit, outdir: str):
    t, vin = source(circ)
    fig, axes = plt.subplots(2, 1, figsize=(9, 7), sharex=True)
    results = {}
    for ax, kind, name in zip(
        axes, ["half", "full"], ["Half-wave", "Full-wave bridge"]
    ):
        vout = with_filter(vin, circ, kind)
        m = measure(t, vout, circ)
        results[kind] = m
        ax.plot(t * 1e3, np.abs(vin) if kind == "full" else np.maximum(vin, 0),
                color="lightgray", label="Rectified input (|Vin| or positive half)")
        ax.plot(t * 1e3, vout, color="tab:red", lw=2, label="Output with filter")
        ax.set_title(
            f"{name} + filter capacitor "
            f"(C = {circ.c * 1e6:.0f} uF, R = {circ.r:.0f} ohm)  |  "
            f"Ripple = {m['v_ripple']:.2f} V"
        )
        ax.set_ylabel("Voltage (V)")
        ax.grid(alpha=0.3)
        ax.legend(loc="lower right")
    axes[-1].set_xlabel("Time (ms)")
    fig.tight_layout()
    path = os.path.join(outdir, "rectifiers_with_filter.png")
    fig.savefig(path, dpi=150)
    plt.close(fig)
    return path, results


def plot_ripple_sweep(circ: Circuit, outdir: str):
    """Ripple vs. capacitor value: simulation vs. textbook formula."""
    caps = np.array([22, 47, 100, 220, 470, 1000]) * 1e-6
    fig, ax = plt.subplots(figsize=(8, 5))
    table = []
    for kind, color in [("half", "tab:orange"), ("full", "tab:green")]:
        sim, formula = [], []
        for c in caps:
            cc = Circuit(**{**circ.__dict__, "c": c})
            t, vin = source(cc)
            vout = with_filter(vin, cc, kind)
            m = measure(t, vout, cc)
            sim.append(m["v_ripple"])
            formula.append(ripple_formula(m["v_max"], cc, kind))
            table.append((kind, c * 1e6, m["v_ripple"], formula[-1]))
        ax.plot(caps * 1e6, sim, "o-", color=color, label=f"{kind}-wave (simulation)")
        ax.plot(caps * 1e6, formula, "x--", color=color, alpha=0.7,
                label=f"{kind}-wave (formula)")
    ax.set_xscale("log")
    ax.set_xlabel("Filter capacitor C (uF)")
    ax.set_ylabel("Ripple voltage (V)")
    ax.set_title("Ripple voltage vs. filter capacitor")
    ax.grid(alpha=0.3, which="both")
    ax.legend()
    fig.tight_layout()
    path = os.path.join(outdir, "ripple_vs_capacitor.png")
    fig.savefig(path, dpi=150)
    plt.close(fig)
    return path, table


# --------------------------------------------------------------------------
# Main
# --------------------------------------------------------------------------
def main():
    p = argparse.ArgumentParser(description="Diode rectifier simulator")
    p.add_argument("--vm", type=float, default=12.0, help="source peak voltage (V)")
    p.add_argument("--f", type=float, default=60.0, help="frequency (Hz)")
    p.add_argument("--r", type=float, default=1000.0, help="load resistance (ohm)")
    p.add_argument("--c", type=float, default=100e-6, help="filter capacitor (F)")
    p.add_argument("--vg", type=float, default=0.7, help="diode V_gamma (V)")
    p.add_argument("--out", default="images", help="output folder for plots")
    args = p.parse_args()

    circ = Circuit(vm=args.vm, f=args.f, r=args.r, c=args.c, v_gamma=args.vg)
    os.makedirs(args.out, exist_ok=True)

    print(f"Source: Vm = {circ.vm} V, f = {circ.f} Hz | "
          f"R = {circ.r} ohm, C = {circ.c * 1e6:.0f} uF, V_gamma = {circ.v_gamma} V\n")

    print("Saved:", plot_unfiltered(circ, args.out))
    path, results = plot_filtered(circ, args.out)
    print("Saved:", path)

    for kind, m in results.items():
        approx = ripple_formula(m["v_max"], circ, kind)
        print(f"\n[{kind}-wave + filter]")
        print(f"  Peak output     : {m['v_max']:.2f} V")
        print(f"  Ripple (sim)    : {m['v_ripple']:.2f} V")
        print(f"  Ripple (formula): {approx:.2f} V")
        print(f"  DC average      : {m['v_dc']:.2f} V")
        print(f"  Ripple factor   : {m['ripple_factor'] * 100:.1f} %")

    path, _ = plot_ripple_sweep(circ, args.out)
    print("\nSaved:", path)


if __name__ == "__main__":
    main()
