# Diode Rectifier Simulator

A Python simulator for **half-wave** and **full-wave (bridge) rectifiers** with an optional **filter capacitor**. It plots input/output waveforms and measures ripple voltage, DC average, and ripple factor, then compares the simulated ripple with the textbook formula.

Built as a hands-on project for **Electronics 1** (diode theory) at the University of Jeddah, following *Microelectronics* / *Electronic Circuit Analysis and Design* by Donald A. Neamen.

## Features

- Half-wave rectifier (1 diode)
- Full-wave bridge rectifier (4 diodes, 2 conducting at a time)
- Filter capacitor modeled step by step (charge / discharge through the load)
- Measurements: peak output, ripple voltage, DC average, ripple factor
- Ripple vs. capacitor sweep: simulation compared with the formula

## Diode model

Constant-voltage-drop model: the diode conducts only when the voltage across it exceeds `V_gamma` (0.7 V for silicon), and then drops exactly `V_gamma`.

| Circuit | Output (no filter) |
|---|---|
| Half-wave | `max(Vin - V_gamma, 0)` |
| Full-wave bridge | `max(abs(Vin) - 2*V_gamma, 0)` |

Source: `Vin = Vm * sin(2*pi*f*t)`

### Filter capacitor

At every time step:

- If the rectified source is higher than the capacitor voltage, the diode is ON and the capacitor follows the source.
- Otherwise the diode is OFF and the capacitor discharges through the load: `v(t+dt) = v(t) * exp(-dt / (R*C))`

### Ripple formula (textbook approximation)

- Half-wave: `Vr ~ VM / (f * R * C)`
- Full-wave: `Vr ~ VM / (2 * f * R * C)`

where `VM` is the peak output voltage.

## Run

```bash
pip install -r requirements.txt
python rectifier.py
```

Custom circuit:

```bash
python rectifier.py --vm 12 --f 60 --r 1000 --c 100e-6 --vg 0.7
```

| Option | Meaning | Default |
|---|---|---|
| `--vm` | Source peak voltage (V) | 12 |
| `--f` | Frequency (Hz) | 60 |
| `--r` | Load resistance (ohm) | 1000 |
| `--c` | Filter capacitor (F) | 100e-6 |
| `--vg` | Diode V_gamma (V) | 0.7 |
| `--out` | Output folder for plots | images |

## Results

Default circuit: Vm = 12 V, f = 60 Hz, R = 1 kohm, C = 100 uF.

| | Half-wave + filter | Full-wave + filter |
|---|---|---|
| Peak output | 11.30 V | 10.60 V |
| Ripple (simulation) | 1.60 V | 0.75 V |
| Ripple (formula) | 1.88 V | 0.88 V |
| DC average | 10.51 V | 10.24 V |
| Ripple factor | 4.4 % | 2.1 % |

Key observations:

- The full-wave rectifier has about **half the ripple** of the half-wave one, because the capacitor is recharged twice per cycle.
- Full-wave output peaks about 0.7 V lower because two diodes conduct in series.
- The formula slightly **overestimates** ripple because it assumes the capacitor discharges for the entire period, while in reality it recharges during part of it.

### Plots

![No filter](images/rectifiers_no_filter.png)
![With filter](images/rectifiers_with_filter.png)
![Ripple vs capacitor](images/ripple_vs_capacitor.png)

## Possible extensions

- Add a Zener diode regulator stage
- Compare results with SPICE (Multisim / PSpice / LTspice)
- Train a simple regression model (scikit-learn) to predict ripple from R and C

## Author

Abdullah Alruwaili, Electrical and Electronics Engineering student (Power Systems), University of Jeddah.
