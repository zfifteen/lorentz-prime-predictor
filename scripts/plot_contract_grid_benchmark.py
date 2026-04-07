from __future__ import annotations

import csv
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np


REPO_ROOT = Path(__file__).resolve().parent.parent
BENCHMARK_CSV = REPO_ROOT / "benchmarks" / "contract_grid.csv"
PLOT_DIR = REPO_ROOT / "benchmarks" / "plots"


def _load_rows() -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    with BENCHMARK_CSV.open(newline="") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            n_value = int(row["n"])
            exponent = len(str(n_value)) - 1
            rows.append(
                {
                    "band": row["band"],
                    "n": n_value,
                    "exponent": exponent,
                    "p_n": int(row["p_n"]),
                    "lpp_seed": int(row["lpp_seed"]),
                    "lpp_seed_error": int(row["lpp_seed_error"]),
                    "lpp_seed_rel_ppm": float(row["lpp_seed_rel_ppm"]),
                    "lpp_refined_predictor": int(row["lpp_refined_predictor"]),
                    "lpp_refined_rel_ppm": float(row["lpp_refined_rel_ppm"]),
                }
            )
    if not rows:
        raise ValueError(f"no rows found in {BENCHMARK_CSV}")
    return rows


def _style() -> None:
    plt.style.use("seaborn-v0_8-whitegrid")
    plt.rcParams["figure.figsize"] = (10, 6)
    plt.rcParams["axes.titlesize"] = 15
    plt.rcParams["axes.labelsize"] = 12
    plt.rcParams["xtick.labelsize"] = 10
    plt.rcParams["ytick.labelsize"] = 10


def _save(fig: plt.Figure, name: str) -> Path:
    PLOT_DIR.mkdir(parents=True, exist_ok=True)
    path = PLOT_DIR / name
    fig.tight_layout()
    fig.savefig(path, dpi=180, bbox_inches="tight")
    plt.close(fig)
    return path


def plot_seed_ppm(rows: list[dict[str, object]]) -> Path:
    exponents = np.array([row["exponent"] for row in rows], dtype=float)
    ppm = np.array([row["lpp_seed_rel_ppm"] for row in rows], dtype=float)

    fig, ax = plt.subplots()
    ax.plot(exponents, ppm, color="#0B7285", marker="o", linewidth=2)
    ax.set_yscale("log")
    ax.set_xlabel("Band exponent k for n = 10^k")
    ax.set_ylabel("Seed relative error (ppm)")
    ax.set_title("LPP Seed Relative Error Across Contract Grid")
    ax.axvline(18, color="#999999", linestyle="--", linewidth=1)
    ax.text(18.2, ppm.max() / 3, "old shipped edge", color="#666666")
    return _save(fig, "contract_grid_seed_ppm.png")


def plot_seed_signed_error(rows: list[dict[str, object]]) -> Path:
    exponents = np.array([row["exponent"] for row in rows], dtype=float)
    signed_error = np.array([row["lpp_seed_error"] for row in rows], dtype=float)
    colors = np.where(signed_error >= 0, "#2B8A3E", "#C92A2A")

    fig, ax = plt.subplots()
    ax.bar(exponents, signed_error, color=colors, width=0.75)
    ax.axhline(0, color="black", linewidth=1)
    ax.set_xlabel("Band exponent k for n = 10^k")
    ax.set_ylabel("Seed signed error")
    ax.set_title("LPP Seed Signed Error by Band")
    return _save(fig, "contract_grid_seed_signed_error.png")


def plot_actual_vs_seed(rows: list[dict[str, object]]) -> Path:
    exponents = np.array([row["exponent"] for row in rows], dtype=float)
    exact = np.array([row["p_n"] for row in rows], dtype=float)
    seed = np.array([row["lpp_seed"] for row in rows], dtype=float)
    refined = np.array([row["lpp_refined_predictor"] for row in rows], dtype=float)

    fig, ax = plt.subplots()
    ax.plot(exponents, exact, color="#111111", linewidth=2.4, label="Exact $p_n$")
    ax.plot(exponents, seed, color="#E67700", marker="o", linewidth=1.8, label="LPP seed")
    ax.plot(exponents, refined, color="#1971C2", linestyle="--", linewidth=1.6, label="Refined predictor")
    ax.set_yscale("log")
    ax.set_xlabel("Band exponent k for n = 10^k")
    ax.set_ylabel("Prime value")
    ax.set_title("Exact Prime, Seed, and Refined Predictor on Log Scale")
    ax.legend()
    return _save(fig, "contract_grid_exact_vs_seed.png")


def plot_refinement_effect(rows: list[dict[str, object]]) -> Path:
    exponents = np.array([row["exponent"] for row in rows], dtype=float)
    seed_ppm = np.array([row["lpp_seed_rel_ppm"] for row in rows], dtype=float)
    refined_ppm = np.array([row["lpp_refined_rel_ppm"] for row in rows], dtype=float)

    fig, ax = plt.subplots()
    ax.plot(exponents, seed_ppm, color="#E67700", marker="o", linewidth=2, label="Seed ppm")
    ax.plot(exponents, refined_ppm + 1e-12, color="#1971C2", marker="s", linewidth=2, label="Refined ppm")
    ax.set_yscale("log")
    ax.set_xlabel("Band exponent k for n = 10^k")
    ax.set_ylabel("Relative error (ppm)")
    ax.set_title("Refinement Collapses Contract-Grid Error to Exact Zero")
    ax.legend()
    return _save(fig, "contract_grid_refinement_effect.png")


def main() -> int:
    _style()
    rows = _load_rows()
    output_paths = [
        plot_seed_ppm(rows),
        plot_seed_signed_error(rows),
        plot_actual_vs_seed(rows),
        plot_refinement_effect(rows),
    ]
    for path in output_paths:
        print(path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
