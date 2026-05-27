"""
test_all_methods.py — Script de test rapide

Verifie que toutes les 6 methodes fonctionnent correctement
sur une petite instance.

Utilisation :
    python test_all_methods.py
"""

import sys
import time
import os

# -------------------------------------------------------------------
# Force UTF-8 output (important sous Windows)
# -------------------------------------------------------------------
try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

# -------------------------------------------------------------------
# Ajout des dossiers au PYTHONPATH
# -------------------------------------------------------------------
sys.path.insert(
    0,
    os.path.join(os.path.dirname(__file__), '..', 'approches')
)

sys.path.insert(
    0,
    os.path.join(os.path.dirname(__file__), '..', 'core')
)

# -------------------------------------------------------------------
# Imports
# -------------------------------------------------------------------
from op_utils import generate_instance
from op_exact_ilp import solve_ilp
from op_exact_bb import solve_bb
from op_exact_dp import solve_dp, dp_complexity_info
from op_meta_sa import solve_sa
from op_meta_tabu import solve_tabu
from op_meta_grasp import solve_grasp


# -------------------------------------------------------------------
# Separateurs ASCII (evite erreurs Unicode)
# -------------------------------------------------------------------
SEP = "-" * 70
BIG_SEP = "=" * 70


def ok(msg):
    return f"[OK] {msg}"


def fail(msg):
    return f"[ERROR] {msg}"


def test_all():
    """
    Teste les 6 methodes sur une petite instance.
    """

    print("\n" + BIG_SEP)
    print("  VERIFICATION : Toutes les 6 methodes")
    print(BIG_SEP)

    # ---------------------------------------------------------------
    # Instance test
    # ---------------------------------------------------------------
    n_customers = 8

    inst = generate_instance(
        n_customers=n_customers,
        t_max_ratio=0.4,
        seed=42
    )

    print(f"\nInstance : {inst.n} sommets, "
          f"{n_customers} clients, "
          f"T_max = {inst.t_max:.2f}")

    print(SEP)

    results = {}
    errors = {}

    # ---------------------------------------------------------------
    # Test 1 : ILP
    # ---------------------------------------------------------------
    print("\n[1/6] ILP (PuLP/CBC)...",
          end=" ",
          flush=True)

    try:

        t0 = time.perf_counter()

        r = solve_ilp(
            inst,
            time_limit=10,
            verbose=False
        )

        elapsed = time.perf_counter() - t0

        results["ILP"] = r

        print(
            ok(f"score={r.total_score:.2f}, "
               f"t={elapsed:.4f}s")
        )

    except Exception as e:

        errors["ILP"] = str(e)

        print(
            fail(f"{type(e).__name__}: "
                 f"{str(e)[:50]}")
        )

    # ---------------------------------------------------------------
    # Test 2 : Branch & Bound
    # ---------------------------------------------------------------
    print("[2/6] Branch & Bound...",
          end=" ",
          flush=True)

    try:

        t0 = time.perf_counter()

        r = solve_bb(
            inst,
            time_limit=10,
            verbose=False
        )

        elapsed = time.perf_counter() - t0

        results["B&B"] = r

        print(
            ok(f"score={r.total_score:.2f}, "
               f"t={elapsed:.4f}s")
        )

    except Exception as e:

        errors["B&B"] = str(e)

        print(
            fail(f"{type(e).__name__}: "
                 f"{str(e)[:50]}")
        )

    # ---------------------------------------------------------------
    # Test 3 : DP
    # ---------------------------------------------------------------
    print("[3/6] DP (Bitmask)...",
          end=" ",
          flush=True)

    try:

        info = dp_complexity_info(inst.n)

        if info["faisable"]:

            t0 = time.perf_counter()

            r = solve_dp(inst)

            elapsed = time.perf_counter() - t0

            results["DP"] = r

            print(
                ok(f"score={r.total_score:.2f}, "
                   f"t={elapsed:.4f}s")
            )

        else:

            print(
                f"[SKIP] DP non applicable "
                f"(n={inst.n} > 22)"
            )

    except Exception as e:

        errors["DP"] = str(e)

        print(
            fail(f"{type(e).__name__}: "
                 f"{str(e)[:50]}")
        )

    # ---------------------------------------------------------------
    # Test 4 : Recuit Simule
    # ---------------------------------------------------------------
    print("[4/6] Recuit Simule...",
          end=" ",
          flush=True)

    try:

        t0 = time.perf_counter()

        r = solve_sa(
            inst,
            seed=42,
            time_limit=5,
            verbose=False
        )

        elapsed = time.perf_counter() - t0

        results["SA"] = r

        print(
            ok(f"score={r.total_score:.2f}, "
               f"t={elapsed:.4f}s")
        )

    except Exception as e:

        errors["SA"] = str(e)

        print(
            fail(f"{type(e).__name__}: "
                 f"{str(e)[:50]}")
        )

    # ---------------------------------------------------------------
    # Test 5 : Recherche Tabou
    # ---------------------------------------------------------------
    print("[5/6] Recherche Tabou...",
          end=" ",
          flush=True)

    try:

        t0 = time.perf_counter()

        r = solve_tabu(
            inst,
            seed=42,
            time_limit=5,
            verbose=False
        )

        elapsed = time.perf_counter() - t0

        results["Tabu"] = r

        print(
            ok(f"score={r.total_score:.2f}, "
               f"t={elapsed:.4f}s")
        )

    except Exception as e:

        errors["Tabu"] = str(e)

        print(
            fail(f"{type(e).__name__}: "
                 f"{str(e)[:50]}")
        )

    # ---------------------------------------------------------------
    # Test 6 : GRASP
    # ---------------------------------------------------------------
    print("[6/6] GRASP...",
          end=" ",
          flush=True)

    try:

        t0 = time.perf_counter()

        r = solve_grasp(
            inst,
            n_iter=50,
            alpha=0.3,
            seed=42,
            time_limit=5,
            verbose=False
        )

        elapsed = time.perf_counter() - t0

        results["GRASP"] = r

        print(
            ok(f"score={r.total_score:.2f}, "
               f"t={elapsed:.4f}s")
        )

    except Exception as e:

        errors["GRASP"] = str(e)

        print(
            fail(f"{type(e).__name__}: "
                 f"{str(e)[:50]}")
        )

    # ---------------------------------------------------------------
    # Resume
    # ---------------------------------------------------------------
    print("\n" + SEP)
    print("\nRESULTATS DES TESTS")
    print(SEP)

    if results:

        print(
            f"\n[OK] {len(results)} methode(s) "
            f"ont fonctionne :"
        )

        for name in sorted(results.keys()):

            r = results[name]

            print(
                f"  - {name:15} : "
                f"score={r.total_score:6.2f}  "
                f"dist={r.total_dist:6.2f}  "
                f"optimal={r.optimal}"
            )

    if errors:

        print(
            f"\n[ERROR] {len(errors)} methode(s) "
            f"ont echoue :"
        )

        for name, error in errors.items():

            print(
                f"  - {name:15} : "
                f"{error[:60]}"
            )

    # ---------------------------------------------------------------
    # Verification finale
    # ---------------------------------------------------------------
    print("\n" + BIG_SEP)

    if len(results) == 6 or (
        len(results) >= 5 and "DP" not in results
    ):

        print("[OK] TOUS LES TESTS PASSENT")
        print("[OK] Le projet est pret !")

        print(BIG_SEP)

        return True

    else:

        print("[WARNING] Certains tests ont echoue.")
        print(BIG_SEP)

        return False


# -------------------------------------------------------------------
# Main
# -------------------------------------------------------------------
if __name__ == "__main__":

    success = test_all()

    sys.exit(0 if success else 1)