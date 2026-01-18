# Group Optimizer (Preferences + ILP)

Tkinter desktop app that collects each person’s preferences and then computes an assignment into groups that maximizes “preferred people in the same group” using Integer Linear Programming (PuLP / CBC).

## What it does

1. **Setup screen**: enter:

   * a comma-separated list of names
   * **N** = max group size
   * **M** = number of preferences each person selects
2. **Preference collection**: each person, one-by-one, selects exactly **M** people (search + double-click to add, remove if needed).
3. **Optimization**: solves a binary ILP to maximize the number of directed preferences that end up **within the same group**.
4. **Results**: shows the resulting groups in a final read-only window.

## How the scoring works

* Each person picks a list of preferred people.
* If person **A** prefers **B**, that counts as **1 point** if A and B are assigned to the same group.
* Preferences are **directed** (A→B is not the same as B→A).

## Requirements

* Python 3.9+ recommended
* Tkinter (usually included with Python on Windows/macOS; on some Linux distros you may need to install it separately)
* PuLP

## Install

```bash
pip install pulp
```

## Run

Save the script as `main.py` and run:

```bash
python main.py
```

## Notes on the optimizer (PuLP / CBC)

This project uses PuLP with CBC as the solver:

* In a normal Python environment, it uses:

  * `pulp.PULP_CBC_CMD(msg=False)`
* When packaged as a **frozen** app (PyInstaller / auto-py-to-exe), it tries to locate a bundled CBC binary under:

  * `.../_MEIPASS/pulp/solverdir/cbc/win/i64/cbc.exe`
    and then uses:
  * `pulp.COIN_CMD(path=cbc_path, msg=False)`

This is why the code checks `getattr(sys, "frozen", False)` and `sys._MEIPASS`.

## Packaging (Windows) overview

If you package with auto-py-to-exe / PyInstaller, you typically need to ensure that the CBC executable is included in the build output so that the frozen app can find it.

Common approach:

* Add PuLP’s solver directory (or specifically the CBC executable) as “additional files” so it ends up in the expected `_MEIPASS` path.

The exact configuration depends on your environment and the layout of your PuLP installation.

## Project structure

Single-file script (no separate modules). Main components:

* `SetupApp`: initial configuration UI
* `PreferenceApp`: preference collection UI
* `build_weight_matrix(...)`: converts preferences to an adjacency/weight matrix
* `solve_partition(...)`: ILP model construction + solve + group extraction

## Limitations / behavior

* Group sizes are constrained by **N** (upper bound). Some groups may have fewer members if the total number of people is not a multiple of `N`.
* Feasibility is always guaranteed (assignment with capacity constraints), but optimality depends on the solver run.
* Preferences are binary (no ranking/weights beyond 0/1).
