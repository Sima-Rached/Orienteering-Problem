"""
op_meta_sa.py — Métaheuristique 1 : Recuit Simulé (Simulated Annealing)
Adapté à l'Orienteering Problem.

Principe
--------
Le recuit simulé explore l'espace des solutions en acceptant parfois
des solutions dégradantes avec une probabilité P = exp(-Δ/T) qui décroît
au fil des itérations (T = température). Cela permet d'échapper aux
optima locaux en début de recherche, puis de converger vers un bon
optimum local en fin de recherche.

Représentation d'une solution
------------------------------
Une solution est une liste ordonnée de sommets : [0, v1, v2, ..., vk, n-1]
- Elle contient toujours le départ (0) et l'arrivée (n-1)
- Les sommets intermédiaires sont un sous-ensemble des clients

Opérateurs de voisinage (3 types)
-----------------------------------
1. INSERT   : insérer un client non visité à une position aléatoire
2. REMOVE   : retirer un client visité de la tournée
3. SWAP_POS : échanger deux positions consécutives dans la tournée

Critère d'acceptation
----------------------
- Si Δscore > 0  → acceptation systématique
- Si Δscore ≤ 0  → acceptation avec probabilité exp(Δscore / T)

Paramètres calibrés
--------------------
T0          : température initiale (auto-calibrée)
alpha       : taux de refroidissement (0.995 par défaut)
T_min       : température d'arrêt
iter_per_T  : itérations par palier de température
"""

import math
import random
import time
from typing import List, Tuple, Optional

from op_utils import OPInstance, OPResult, compute_score, compute_dist, is_feasible


# ---------------------------------------------------------------------------
# Utilitaires solution
# ---------------------------------------------------------------------------

def _tour_score(inst: OPInstance, tour: List[int]) -> float:
    return sum(inst.scores[v] for v in tour)


def _tour_dist(inst: OPInstance, tour: List[int]) -> float:
    return sum(inst.dist[tour[k]][tour[k+1]] for k in range(len(tour)-1))


def _is_feasible_tour(inst: OPInstance, tour: List[int]) -> bool:
    return _tour_dist(inst, tour) <= inst.t_max + 1e-9


# ---------------------------------------------------------------------------
# Construction initiale greedy-aléatoire
# ---------------------------------------------------------------------------

def _initial_solution(inst: OPInstance, rng: random.Random) -> List[int]:
    """
    Construit une solution initiale par insertion greedy avec bruit aléatoire.
    À chaque étape, choisit le meilleur client parmi un candidat tiré aléatoirement.
    """
    s, e = inst.start, inst.end
    tour = [s, e]
    unvisited = list(inst.customers)
    rng.shuffle(unvisited)

    for v in unvisited:
        # Trouver la meilleure position d'insertion pour v
        best_pos, best_cost = _best_insert_pos(inst, tour, v)
        if best_pos is not None:
            new_tour = tour[:best_pos] + [v] + tour[best_pos:]
            if _is_feasible_tour(inst, new_tour):
                tour = new_tour

    return tour


def _best_insert_pos(inst: OPInstance, tour: List[int], v: int):
    """Retourne la position d'insertion de v dans tour qui minimise le coût ajouté."""
    best_pos, best_delta = None, float('inf')
    for pos in range(1, len(tour)):
        prev, nxt = tour[pos-1], tour[pos]
        delta = inst.dist[prev][v] + inst.dist[v][nxt] - inst.dist[prev][nxt]
        if delta < best_delta:
            best_delta = delta
            best_pos = pos
    return best_pos, best_delta


# ---------------------------------------------------------------------------
# Opérateurs de voisinage
# ---------------------------------------------------------------------------

def _neighbor_insert(inst: OPInstance, tour: List[int],
                     rng: random.Random) -> Optional[List[int]]:
    """Insère un client non visité à la meilleure position réalisable."""
    visited = set(tour)
    candidates = [v for v in inst.customers if v not in visited]
    if not candidates:
        return None
    v = rng.choice(candidates)
    best_pos, _ = _best_insert_pos(inst, tour, v)
    if best_pos is None:
        return None
    new_tour = tour[:best_pos] + [v] + tour[best_pos:]
    return new_tour if _is_feasible_tour(inst, new_tour) else None


def _neighbor_remove(inst: OPInstance, tour: List[int],
                     rng: random.Random) -> Optional[List[int]]:
    """Retire un client aléatoire de la tournée."""
    removable = tour[1:-1]  # exclure départ et arrivée
    if not removable:
        return None
    v = rng.choice(removable)
    idx = tour.index(v)
    return tour[:idx] + tour[idx+1:]


def _neighbor_swap_pos(inst: OPInstance, tour: List[int],
                       rng: random.Random) -> Optional[List[int]]:
    """Échange deux clients consécutifs dans la tournée (2-opt partiel)."""
    inner = tour[1:-1]
    if len(inner) < 2:
        return None
    i = rng.randint(0, len(inner)-2)
    new_inner = inner[:i] + [inner[i+1], inner[i]] + inner[i+2:]
    new_tour = [tour[0]] + new_inner + [tour[-1]]
    return new_tour if _is_feasible_tour(inst, new_tour) else None


def _neighbor_2opt(inst: OPInstance, tour: List[int],
                   rng: random.Random) -> Optional[List[int]]:
    """Inversion d'un segment (2-opt classique)."""
    if len(tour) < 5:
        return None
    i = rng.randint(1, len(tour)-3)
    j = rng.randint(i+1, len(tour)-2)
    new_tour = tour[:i] + tour[i:j+1][::-1] + tour[j+1:]
    return new_tour if _is_feasible_tour(inst, new_tour) else None


OPERATORS = [_neighbor_insert, _neighbor_remove,
             _neighbor_swap_pos, _neighbor_2opt]


# ---------------------------------------------------------------------------
# Calibration automatique de T0
# ---------------------------------------------------------------------------

def _calibrate_T0(inst: OPInstance, rng: random.Random,
                  n_samples: int = 200, accept_rate: float = 0.8) -> float:
    """
    Estime T0 tel que ~accept_rate% des mouvements dégradants soient
    acceptés au début (principe de Kirk-patrick).
    """
    tour = _initial_solution(inst, rng)
    deltas = []
    for _ in range(n_samples):
        op = rng.choice(OPERATORS)
        new_tour = op(inst, tour, rng)
        if new_tour is None:
            continue
        delta = _tour_score(inst, new_tour) - _tour_score(inst, tour)
        if delta < 0:
            deltas.append(-delta)
        tour = new_tour  # marche aléatoire pour diversifier

    if not deltas:
        return 10.0
    avg_delta = sum(deltas) / len(deltas)
    # P = exp(-avg_delta / T0) = accept_rate → T0 = -avg_delta / ln(accept_rate)
    return -avg_delta / math.log(accept_rate) if avg_delta > 0 else 10.0


# ---------------------------------------------------------------------------
# Recuit simulé principal
# ---------------------------------------------------------------------------

def solve_sa(instance: OPInstance,
             alpha: float = 0.995,
             T_min: float = 0.01,
             iter_per_T: int = 100,
             max_iter: int = 50_000,
             time_limit: float = 60.0,
             seed: int = 0,
             verbose: bool = False) -> OPResult:
    """
    Résout l'OP par recuit simulé.

    Paramètres
    ----------
    alpha      : taux de refroidissement (T ← alpha × T)
    T_min      : température d'arrêt
    iter_per_T : nombre de mouvements tentés par palier
    max_iter   : nombre maximal d'itérations total
    time_limit : limite temps en secondes
    seed       : graine aléatoire
    """
    t0 = time.perf_counter()
    rng = random.Random(seed)

    # Initialisation
    current = _initial_solution(instance, rng)
    current_score = _tour_score(instance, current)

    best = list(current)
    best_score = current_score

    # Calibration T0
    T0 = _calibrate_T0(instance, rng)
    T = T0

    stats = {"accepted": 0, "rejected": 0, "improved": 0,
             "T0": T0, "iterations": 0}

    iteration = 0

    while T > T_min and iteration < max_iter:
        if time.perf_counter() - t0 > time_limit:
            break

        for _ in range(iter_per_T):
            iteration += 1

            # Choisir un opérateur aléatoire
            op = rng.choice(OPERATORS)
            new_tour = op(instance, current, rng)
            if new_tour is None:
                stats["rejected"] += 1
                continue

            new_score = _tour_score(instance, new_tour)
            delta = new_score - current_score

            # Critère d'acceptation
            if delta > 0 or rng.random() < math.exp(delta / T):
                current = new_tour
                current_score = new_score
                stats["accepted"] += 1

                if current_score > best_score + 1e-9:
                    best = list(current)
                    best_score = current_score
                    stats["improved"] += 1
                    if verbose:
                        print(f"  T={T:.4f}  iter={iteration}  "
                              f"score={best_score:.2f}")
            else:
                stats["rejected"] += 1

        T *= alpha  # refroidissement

    stats["iterations"] = iteration
    cpu_time = time.perf_counter() - t0

    return OPResult(
        method="Recuit simulé",
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

    print("=== Test Recuit Simulé ===")
    for n_cust in [10, 20, 40]:
        inst = generate_instance(n_customers=n_cust, t_max_ratio=0.4, seed=42)
        r = solve_sa(inst, seed=42, verbose=False)
        print(f"\nn={inst.n}  score={r.total_score:.2f}  "
              f"dist={r.total_dist:.2f}  t={r.cpu_time:.3f}s  "
              f"iter={r.extra['iterations']}  "
              f"accept={r.extra['accepted']}  T0={r.extra['T0']:.3f}")
        print(f"  Tour : {r.tour}")
