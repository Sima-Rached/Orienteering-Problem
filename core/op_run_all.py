"""
op_run_all.py — Comparaison complète : 3 méthodes exactes + 3 métaheuristiques
Usage : python op_run_all.py
"""

import sys
import os

# -------------------------------------------------------------------
# Force UTF-8 output (important sous Windows)
# -------------------------------------------------------------------
try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'approches'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'core'))

from op_utils import generate_instance, print_comparison, OPResult
from op_exact_ilp import solve_ilp
from op_exact_bb import solve_bb
from op_exact_dp import solve_dp, dp_complexity_info
from op_meta_sa import solve_sa
from op_meta_tabu import solve_tabu
from op_meta_grasp import solve_grasp


# -------------------------------------------------------------------
# Séparateurs ASCII (évite les erreurs Unicode Windows)
# -------------------------------------------------------------------
SEP = "-" * 70
BIG_SEP = "=" * 70
BLOCK = "#" * 70


def run_all(n_customers: int,
            t_max_ratio: float = 0.4,
            seed: int = 42,
            time_limit_exact: float = 60.0,
            time_limit_meta: float = 10.0,
            n_seeds: int = 5):
    """
    Lance toutes les méthodes sur une instance et affiche le tableau comparatif.
    Les métaheuristiques sont lancées sur n_seeds graines différentes et le
    meilleur résultat est retenu.
    """

    inst = generate_instance(
        n_customers=n_customers,
        t_max_ratio=t_max_ratio,
        seed=seed
    )

    print(f"\n{BLOCK}")
    print(f"  Instance : {inst.n} sommets | "
          f"{n_customers} clients | "
          f"T_max = {inst.t_max:.2f} | "
          f"seed={seed}")
    print(BLOCK)

    results = []

    info = dp_complexity_info(inst.n)

    # ------------------------------------------------------------------
    # Méthodes exactes
    # ------------------------------------------------------------------
    print("\n-- Methodes exactes --")

    print("  [1/3] ILP (MTZ)...")
    results.append(
        solve_ilp(inst, time_limit=time_limit_exact)
    )

    print("  [2/3] Branch & Bound...")
    results.append(
        solve_bb(inst, time_limit=time_limit_exact)
    )

    if info["faisable"]:

        print("  [3/3] DP (bitmask)...")

        results.append(
            solve_dp(inst)
        )

    else:
        print(f"  [3/3] DP ignoree (n={inst.n} > 22)")

    # ------------------------------------------------------------------
    # Métaheuristiques
    # ------------------------------------------------------------------
    print("\n-- Metaheuristiques --")

    def best_of(solver_fn, **kwargs) -> OPResult:
        """
        Lance solver_fn sur plusieurs seeds
        et retourne le meilleur résultat.
        """

        best_r = None

        for s in range(n_seeds):

            r = solver_fn(
                inst,
                seed=s,
                time_limit=time_limit_meta,
                **kwargs
            )

            if best_r is None or r.total_score > best_r.total_score:
                best_r = r

        best_r.extra["n_seeds"] = n_seeds

        return best_r

    print("  [4/6] Recuit simule...")
    results.append(best_of(solve_sa))

    print("  [5/6] Recherche tabou...")
    results.append(best_of(solve_tabu))

    print("  [6/6] GRASP...")
    results.append(
        best_of(
            solve_grasp,
            n_iter=200,
            alpha=0.3
        )
    )

    # ------------------------------------------------------------------
    # Calcul des gaps
    # ------------------------------------------------------------------
    exact_results = [r for r in results if r.optimal]

    if exact_results:

        opt_score = max(
            r.total_score for r in exact_results
        )

        for r in results:

            if opt_score > 0:

                r.gap = max(
                    0.0,
                    (opt_score - r.total_score)
                    / opt_score * 100
                )

    print_comparison(results, inst)

    return results


# ---------------------------------------------------------------------------
# Étude expérimentale multi-tailles
# ---------------------------------------------------------------------------
if __name__ == "__main__":

    print("\n" + BIG_SEP)
    print("  COMPARAISON COMPLETE - 6 methodes - Orienteering Problem")
    print(BIG_SEP)

    # Petites instances
    for n in [8, 12, 16]:

        run_all(
            n_customers=n,
            t_max_ratio=0.4,
            seed=42,
            time_limit_exact=30,
            time_limit_meta=5,
            n_seeds=3
        )

    # Instances moyennes
    for n in [25, 40]:

        run_all(
            n_customers=n,
            t_max_ratio=0.4,
            seed=42,
            time_limit_exact=60,
            time_limit_meta=15,
            n_seeds=5
        )

    # Grande instance
    print("\n-- Grande instance (exactes limitees a 30s) --")

    run_all(
        n_customers=60,
        t_max_ratio=0.4,
        seed=42,
        time_limit_exact=30,
        time_limit_meta=30,
        n_seeds=5
    )