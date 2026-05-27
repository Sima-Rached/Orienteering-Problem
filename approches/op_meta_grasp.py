"""
op_meta_grasp.py — Métaheuristique 3 : GRASP
(Greedy Randomized Adaptive Search Procedure)
Adapté à l'Orienteering Problem.

Principe
--------
GRASP alterne deux phases à chaque itération :
  1. Construction  : solution initiale par heuristique greedy randomisée
  2. Amélioration  : recherche locale (2-opt + insert/remove) jusqu'à
                     l'optimum local

La randomisation de la phase de construction (via la liste restreinte
de candidats — RCL) assure la diversification entre les itérations,
tandis que la recherche locale garantit la qualité de chaque solution.
Le meilleur résultat sur toutes les itérations est retenu.

Phase 1 — Construction greedy randomisée (RCL)
-----------------------------------------------
À chaque étape, on calcule un score d'attractivité pour chaque client
non visité (ratio profit / coût d'insertion). On construit la RCL :
ensemble des clients dont le score ≥ (1 - alpha) × max_score.
On tire uniformément un client dans la RCL et on l'insère.

alpha = 0   → greedy pur (deterministe)
alpha = 1   → aléatoire pur
alpha = 0.3 → bon compromis (calibré empiriquement)

Phase 2 — Recherche locale (Variable Neighborhood Descent)
------------------------------------------------------------
On applique successivement :
  - 2-opt : inversion de segments
  - Insert : insertion du meilleur client non visité
  - Remove : suppression du client le moins rentable
jusqu'à stabilisation (aucune amélioration).

Paramètres calibrés
--------------------
n_iter  : nombre d'itérations GRASP (100 par défaut)
alpha   : paramètre RCL (0.3)
"""

import random
import time
from typing import List, Optional, Tuple

from op_utils import OPInstance, OPResult, compute_dist


# ---------------------------------------------------------------------------
# Utilitaires
# ---------------------------------------------------------------------------

def _score(inst: OPInstance, tour: List[int]) -> float:
    return sum(inst.scores[v] for v in tour)


def _dist(inst: OPInstance, tour: List[int]) -> float:
    return sum(inst.dist[tour[k]][tour[k+1]] for k in range(len(tour)-1))


def _feasible(inst: OPInstance, tour: List[int]) -> bool:
    return _dist(inst, tour) <= inst.t_max + 1e-9


def _insert_cost(inst: OPInstance, tour: List[int], v: int, pos: int) -> float:
    prev, nxt = tour[pos-1], tour[pos]
    return inst.dist[prev][v] + inst.dist[v][nxt] - inst.dist[prev][nxt]


# ---------------------------------------------------------------------------
# Phase 1 : Construction greedy randomisée
# ---------------------------------------------------------------------------

def _greedy_randomized_construction(inst: OPInstance,
                                    alpha: float,
                                    rng: random.Random) -> List[int]:
    """
    Construit une solution greedy randomisée via la RCL.

    À chaque étape :
      - Calcule l'attractivité de chaque client candidat = score / coût_insertion
      - Forme la RCL : candidats dans [max_attr × (1 - alpha), max_attr]
      - Tire un candidat uniformément dans la RCL
      - L'insère à la meilleure position
    """
    s, e = inst.start, inst.end
    tour = [s, e]
    unvisited = set(inst.customers)

    while unvisited:
        # Calculer l'attractivité de chaque candidat
        candidates = []
        for v in unvisited:
            best_pos, best_cost = None, float('inf')
            for pos in range(1, len(tour)):
                cost = _insert_cost(inst, tour, v, pos)
                if cost < best_cost:
                    best_cost = cost
                    best_pos = pos

            # Vérifier faisabilité avec ce coût
            if best_pos is not None and best_cost < float('inf'):
                new_dist = _dist(inst, tour) + best_cost
                # Vérifier qu'on peut encore rejoindre l'arrivée
                if new_dist <= inst.t_max + 1e-9:
                    attractiveness = (inst.scores[v] / best_cost
                                      if best_cost > 1e-9 else inst.scores[v])
                    candidates.append((attractiveness, v, best_pos, best_cost))

        if not candidates:
            break  # aucun client insérable

        # Construire la RCL
        max_attr = max(c[0] for c in candidates)
        min_attr = min(c[0] for c in candidates)
        threshold = max_attr - alpha * (max_attr - min_attr)
        rcl = [c for c in candidates if c[0] >= threshold - 1e-9]

        # Tirer aléatoirement dans la RCL
        chosen = rng.choice(rcl)
        _, v, best_pos, _ = chosen

        # Insérer à la meilleure position
        tour = tour[:best_pos] + [v] + tour[best_pos:]
        unvisited.remove(v)

    return tour


# ---------------------------------------------------------------------------
# Phase 2 : Recherche locale (Variable Neighborhood Descent)
# ---------------------------------------------------------------------------

def _local_search(inst: OPInstance, tour: List[int]) -> List[int]:
    """
    Amélioration locale : applique 2-opt, insert et remove en boucle
    jusqu'à ce qu'aucun opérateur n'améliore la solution.
    """
    improved = True
    while improved:
        improved = False

        # --- 2-opt ---
        tour, imp = _2opt(inst, tour)
        if imp:
            improved = True

        # --- Insert : tenter d'ajouter le meilleur client non visité ---
        tour, imp = _best_insert(inst, tour)
        if imp:
            improved = True

        # --- Remove : retirer le client le moins rentable si ça libère du budget ---
        tour, imp = _worst_remove(inst, tour)
        if imp:
            improved = True

    return tour


def _2opt(inst: OPInstance, tour: List[int]) -> Tuple[List[int], bool]:
    """2-opt complet : parcourt toutes les paires (i, j) jusqu'à stabilisation."""
    improved = False
    n = len(tour)
    current_score = _score(inst, tour)

    for i in range(1, n - 2):
        for j in range(i + 1, n - 1):
            new_tour = tour[:i] + tour[i:j+1][::-1] + tour[j+1:]
            if not _feasible(inst, new_tour):
                continue
            new_score = _score(inst, new_tour)
            if new_score > current_score + 1e-9:
                tour = new_tour
                current_score = new_score
                improved = True

    return tour, improved


def _best_insert(inst: OPInstance, tour: List[int]) -> Tuple[List[int], bool]:
    """Insère le client non visité qui maximise le gain net."""
    visited = set(tour)
    best_gain = 0.0
    best_tour = None

    for v in inst.customers:
        if v in visited:
            continue
        for pos in range(1, len(tour)):
            cost = _insert_cost(inst, tour, v, pos)
            gain = inst.scores[v] - cost * 0.0  # gain pur en score
            new_tour = tour[:pos] + [v] + tour[pos:]
            if not _feasible(inst, new_tour):
                continue
            actual_gain = inst.scores[v]
            if actual_gain > best_gain + 1e-9:
                # Vérifier que le gain en score est positif
                best_gain = actual_gain
                best_tour = new_tour

    if best_tour is not None and _score(inst, best_tour) > _score(inst, tour) + 1e-9:
        return best_tour, True
    return tour, False


def _worst_remove(inst: OPInstance, tour: List[int]) -> Tuple[List[int], bool]:
    """
    Retire le client avec le pire ratio score/coût_de_passage uniquement si
    retirer ce client + insérer un meilleur améliore le score global.
    Critère : on retire si libérer de la distance permet d'insérer un meilleur client.
    """
    inner = tour[1:-1]
    if not inner:
        return tour, False

    # Retirer le client dont le coût de passage est élevé et le score faible
    worst_ratio = float('inf')
    worst_v = None
    worst_idx = None

    for idx, v in enumerate(inner):
        i = idx + 1  # position dans tour
        prev, nxt = tour[i-1], tour[i+1]
        passage_cost = inst.dist[prev][v] + inst.dist[v][nxt] - inst.dist[prev][nxt]
        ratio = inst.scores[v] / (passage_cost + 1e-9)
        if ratio < worst_ratio:
            worst_ratio = ratio
            worst_v = v
            worst_idx = i

    if worst_v is None:
        return tour, False

    # Construire la tournée sans worst_v
    candidate_tour = tour[:worst_idx] + tour[worst_idx+1:]

    # Essayer d'insérer un meilleur client à la place
    candidate_tour, inserted = _best_insert(inst, candidate_tour)

    if inserted and _score(inst, candidate_tour) > _score(inst, tour) + 1e-9:
        return candidate_tour, True

    return tour, False


# ---------------------------------------------------------------------------
# GRASP principal
# ---------------------------------------------------------------------------

def solve_grasp(instance: OPInstance,
                n_iter: int = 100,
                alpha: float = 0.3,
                time_limit: float = 60.0,
                seed: int = 0,
                verbose: bool = False) -> OPResult:
    """
    Résout l'OP par GRASP.

    Paramètres
    ----------
    n_iter     : nombre d'itérations (constructions + améliorations)
    alpha      : paramètre RCL (0 = greedy pur, 1 = aléatoire pur)
    time_limit : limite de temps en secondes
    seed       : graine aléatoire
    """
    t0 = time.perf_counter()
    rng = random.Random(seed)

    best: List[int] = [instance.start, instance.end]
    best_score: float = 0.0

    stats = {
        "iterations_done": 0,
        "improvements": 0,
        "alpha": alpha,
        "avg_construction_score": 0.0,
        "avg_local_score": 0.0,
    }
    scores_construction = []
    scores_local = []

    for it in range(n_iter):
        if time.perf_counter() - t0 > time_limit:
            break

        # Phase 1 : Construction greedy randomisée
        tour = _greedy_randomized_construction(instance, alpha, rng)
        sc = _score(instance, tour)
        scores_construction.append(sc)

        # Phase 2 : Amélioration locale
        tour = _local_search(instance, tour)
        sc = _score(instance, tour)
        scores_local.append(sc)

        if sc > best_score + 1e-9:
            best = list(tour)
            best_score = sc
            stats["improvements"] += 1
            if verbose:
                print(f"  iter={it+1}  score={best_score:.2f}")

        stats["iterations_done"] = it + 1

    stats["avg_construction_score"] = (sum(scores_construction) / len(scores_construction)
                                       if scores_construction else 0.0)
    stats["avg_local_score"] = (sum(scores_local) / len(scores_local)
                                if scores_local else 0.0)

    cpu_time = time.perf_counter() - t0

    return OPResult(
        method="GRASP",
        tour=best,
        total_score=best_score,
        total_dist=compute_dist(instance, best),
        cpu_time=cpu_time,
        optimal=False,
        extra=stats
    )


# ---------------------------------------------------------------------------
# Test autonome
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    from op_utils import generate_instance

    print("=== Test GRASP ===")
    for n_cust in [10, 20, 40]:
        inst = generate_instance(n_customers=n_cust, t_max_ratio=0.4, seed=42)
        r = solve_grasp(inst, n_iter=100, alpha=0.3, seed=42, verbose=False)
        print(f"\nn={inst.n}  score={r.total_score:.2f}  "
              f"dist={r.total_dist:.2f}  t={r.cpu_time:.3f}s  "
              f"iter={r.extra['iterations_done']}  "
              f"improvements={r.extra['improvements']}  "
              f"avg_local={r.extra['avg_local_score']:.2f}")
        print(f"  Tour : {r.tour}")
