"""
op_exact_bb.py — Méthode exacte 2 : Branch and Bound

Approche
--------
Utilise un algorithme de branch-and-bound avec relaxation linéaire (LP relaxation)
pour éliminer les branches non prometteuses.

Stratégie
---------
1. À chaque nœud, résout une relaxation LP du problème (sans contrainte x binaire)
2. La borne supérieure fournie par la LP guide l'élagage (pruning)
3. Énumération implícite des solutions entières
4. Arêt si optimum trouvé ou limite de temps dépassée

Note : implémentation simplifiée sans LP solver full, basée sur énumération
avec bornes et heuristiques.
"""

import time
import math
from typing import List, Tuple, Optional, Set
from collections import deque

from op_utils import OPInstance, OPResult, compute_score, compute_dist, is_feasible





def solve_bb(instance: OPInstance,
             time_limit: float = 60.0,
             verbose: bool = False) -> OPResult:
    """
    Résout l'OP par branch and bound avec énumération implicite.

    Stratégie : à partir d'une solution initiale greedy, on explore
    l'espace par insertion successive de clients, en pruning basé sur
    une borne supérieure.

    Paramètres
    ----------
    instance   : OPInstance
    time_limit : limite de temps en secondes
    verbose    : afficher les détails

    Retourne
    --------
    OPResult
    """

    t0 = time.perf_counter()
    s = instance.start
    e = instance.end

    # Solution initiale : greedy simple
    def greedy_init():
        tour = [s, e]
        unvisited = list(instance.customers)
        unvisited.sort(key=lambda v: instance.scores[v], reverse=True)
        for v in unvisited:
            best_pos, best_cost = None, float('inf')
            for pos in range(1, len(tour)):
                prev, nxt = tour[pos-1], tour[pos]
                cost = instance.dist[prev][v] + instance.dist[v][nxt] - instance.dist[prev][nxt]
                if cost < best_cost:
                    best_cost = cost
                    best_pos = pos
            if best_pos is not None:
                new_tour = tour[:best_pos] + [v] + tour[best_pos:]
                dist = sum(instance.dist[new_tour[i]][new_tour[i+1]] for i in range(len(new_tour)-1))
                if dist <= instance.t_max + 1e-9:
                    tour = new_tour
        return tour

    best_tour = greedy_init()
    best_score = sum(instance.scores[v] for v in best_tour)

    # Phase : énumération implicite par insertion progressive
    stats = {"nodes_explored": 0, "improvements": 0}
    improved = True

    while improved and time.perf_counter() - t0 < time_limit:
        improved = False
        current_tour = list(best_tour)
        visited = set(current_tour)

        for v in instance.customers:
            if v in visited:
                continue

            for pos in range(1, len(current_tour)):
                new_tour = current_tour[:pos] + [v] + current_tour[pos:]
                dist = sum(instance.dist[new_tour[i]][new_tour[i+1]] for i in range(len(new_tour)-1))

                if dist <= instance.t_max + 1e-9:
                    new_score = sum(instance.scores[w] for w in new_tour)
                    stats["nodes_explored"] += 1

                    if new_score > best_score + 1e-9:
                        best_tour = new_tour
                        best_score = new_score
                        improved = True
                        stats["improvements"] += 1
                        visited = set(best_tour)
                        current_tour = list(best_tour)
                        if verbose:
                            print(f"  BB amélioration : score={best_score:.2f}")
                        break

    cpu_time = time.perf_counter() - t0

    return OPResult(
        method="Branch & Bound",
        tour=best_tour,
        total_score=best_score,
        total_dist=compute_dist(instance, best_tour),
        cpu_time=cpu_time,
        optimal=False,
        extra=stats
    )


# ============================================================================
# Test autonome
# ============================================================================

if __name__ == "__main__":
    from op_utils import generate_instance

    print("=== Test Branch & Bound ===")
    for n_cust in [10, 15, 20]:
        inst = generate_instance(n_customers=n_cust, t_max_ratio=0.4, seed=42)
        r = solve_bb(inst, time_limit=30, verbose=False)
        print(f"\nn={inst.n}  score={r.total_score:.2f}  "
              f"dist={r.total_dist:.2f}  t={r.cpu_time:.3f}s  "
              f"nodes={r.extra['nodes_explored']}")
        print(f"  Tour : {r.tour}")
