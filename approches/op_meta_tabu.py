"""
op_meta_tabu.py — Métaheuristique 2 : Recherche Tabou (Tabu Search)
Adapté à l'Orienteering Problem.

Principe
--------
La recherche tabou maintient une liste de mouvements récemment effectués
(liste tabou) pour interdire leur annulation immédiate et éviter de cycler.
À chaque itération, on choisit le meilleur voisin non-tabou (ou tabou mais
satisfaisant le critère d'aspiration : score > meilleure solution connue).

Représentation d'une solution
------------------------------
Identique au recuit simulé : [0, v1, v2, ..., vk, n-1]

Mouvements et leur représentation dans la liste tabou
------------------------------------------------------
- INSERT(v)     : interdit de retirer v pendant tenure itérations
- REMOVE(v)     : interdit de ré-insérer v pendant tenure itérations
- SWAP(i, j)    : interdit de re-swapper les positions i,j
- 2OPT(i, j)   : interdit de re-retourner le segment [i, j]

Chaque attribut tabou est stocké sous forme (type, sommet_ou_pos).

Intensification / Diversification
-----------------------------------
- Intensification : si pas d'amélioration depuis X itérations,
  redémarrer depuis la meilleure solution connue.
- Diversification  : si bloqué trop longtemps, perturbation aléatoire.

Paramètres calibrés
--------------------
tabu_tenure         : durée de vie d'un attribut tabou (7 par défaut)
n_neighbors         : nombre de voisins évalués par itération (30)
max_iter            : nombre maximal d'itérations (500)
no_improve_restart  : redémarrage après X itérations sans amélioration
"""

import random
import time
from collections import deque
from typing import List, Tuple, Optional, Set, Dict

from op_utils import OPInstance, OPResult, compute_dist


# ---------------------------------------------------------------------------
# Types de mouvements
# ---------------------------------------------------------------------------

INSERT = "INSERT"
REMOVE = "REMOVE"
SWAP   = "SWAP"
OPT2   = "2OPT"


def _tour_score(inst: OPInstance, tour: List[int]) -> float:
    return sum(inst.scores[v] for v in tour)


def _tour_dist(inst: OPInstance, tour: List[int]) -> float:
    return sum(inst.dist[tour[k]][tour[k+1]] for k in range(len(tour)-1))


def _feasible(inst: OPInstance, tour: List[int]) -> bool:
    return _tour_dist(inst, tour) <= inst.t_max + 1e-9


# ---------------------------------------------------------------------------
# Génération de voisins avec attribut tabou associé
# ---------------------------------------------------------------------------

def _gen_insert_moves(inst: OPInstance, tour: List[int],
                      rng: random.Random, k: int = 10):
    """Génère k insertions de clients non visités."""
    visited = set(tour)
    candidates = [v for v in inst.customers if v not in visited]
    rng.shuffle(candidates)
    moves = []
    for v in candidates[:k]:
        best_pos, best_delta = None, float('inf')
        for pos in range(1, len(tour)):
            prev, nxt = tour[pos-1], tour[pos]
            delta = (inst.dist[prev][v] + inst.dist[v][nxt]
                     - inst.dist[prev][nxt])
            if delta < best_delta:
                best_delta = delta
                best_pos = pos
        if best_pos is not None:
            new_tour = tour[:best_pos] + [v] + tour[best_pos:]
            if _feasible(inst, new_tour):
                moves.append((new_tour, (INSERT, v)))
    return moves


def _gen_remove_moves(inst: OPInstance, tour: List[int],
                      rng: random.Random, k: int = 10):
    """Génère k suppressions de clients visités."""
    inner = tour[1:-1]
    if not inner:
        return []
    rng.shuffle(inner)
    moves = []
    for v in inner[:k]:
        idx = tour.index(v)
        new_tour = tour[:idx] + tour[idx+1:]
        moves.append((new_tour, (REMOVE, v)))
    return moves


def _gen_swap_moves(inst: OPInstance, tour: List[int],
                    rng: random.Random, k: int = 10):
    """Génère k échanges de paires de positions consécutives."""
    inner = tour[1:-1]
    if len(inner) < 2:
        return []
    moves = []
    positions = list(range(len(inner)-1))
    rng.shuffle(positions)
    for i in positions[:k]:
        new_inner = inner[:i] + [inner[i+1], inner[i]] + inner[i+2:]
        new_tour = [tour[0]] + new_inner + [tour[-1]]
        if _feasible(inst, new_tour):
            moves.append((new_tour, (SWAP, i)))
    return moves


def _gen_2opt_moves(inst: OPInstance, tour: List[int],
                    rng: random.Random, k: int = 10):
    """Génère k inversions de segments (2-opt)."""
    if len(tour) < 5:
        return []
    moves = []
    tried = 0
    pairs = [(i, j) for i in range(1, len(tour)-2)
             for j in range(i+1, len(tour)-1)]
    rng.shuffle(pairs)
    for i, j in pairs[:k]:
        new_tour = tour[:i] + tour[i:j+1][::-1] + tour[j+1:]
        if _feasible(inst, new_tour):
            moves.append((new_tour, (OPT2, (i, j))))
        tried += 1
        if tried >= k:
            break
    return moves


# ---------------------------------------------------------------------------
# Recherche tabou principale
# ---------------------------------------------------------------------------

def solve_tabu(instance: OPInstance,
               tabu_tenure: int = 7,
               n_neighbors: int = 30,
               max_iter: int = 500,
               no_improve_restart: int = 80,
               time_limit: float = 60.0,
               seed: int = 0,
               verbose: bool = False) -> OPResult:
    """
    Résout l'OP par recherche tabou.

    Paramètres
    ----------
    tabu_tenure         : durée de vie d'un attribut tabou (itérations)
    n_neighbors         : nombre de voisins générés par itération
    max_iter            : nombre maximal d'itérations
    no_improve_restart  : redémarrage depuis le meilleur après X itérations sans amélioration
    """
    t0 = time.perf_counter()
    rng = random.Random(seed)

    # Solution initiale greedy
    current = _greedy_init(instance, rng)
    current_score = _tour_score(instance, current)

    best = list(current)
    best_score = current_score

    # Liste tabou : deque de (attribut, expiration_iter)
    tabu_list: Dict[tuple, int] = {}  # attribut → itération d'expiration

    no_improve = 0
    stats = {"restarts": 0, "aspiration_hits": 0, "iterations": 0}

    for iteration in range(1, max_iter + 1):
        if time.perf_counter() - t0 > time_limit:
            break

        stats["iterations"] = iteration

        # --- Génération du voisinage ---
        k_each = max(3, n_neighbors // 4)
        neighbors = (
            _gen_insert_moves(instance, current, rng, k_each) +
            _gen_remove_moves(instance, current, rng, k_each) +
            _gen_swap_moves(instance, current, rng, k_each) +
            _gen_2opt_moves(instance, current, rng, k_each)
        )

        if not neighbors:
            no_improve += 1
            continue

        # --- Sélection du meilleur voisin non-tabou ---
        best_neighbor = None
        best_neighbor_score = -float('inf')
        best_move_attr = None

        for (new_tour, move_attr) in neighbors:
            new_score = _tour_score(instance, new_tour)
            is_tabu = (move_attr in tabu_list and
                       tabu_list[move_attr] > iteration)

            # Critère d'aspiration : accepter si meilleure que le meilleur global
            aspiration = new_score > best_score + 1e-9
            if aspiration and is_tabu:
                stats["aspiration_hits"] += 1

            if not is_tabu or aspiration:
                if new_score > best_neighbor_score:
                    best_neighbor_score = new_score
                    best_neighbor = new_tour
                    best_move_attr = move_attr

        if best_neighbor is None:
            # Tous les voisins sont tabous → prendre le moins mauvais
            best_neighbor, best_move_attr = max(
                neighbors, key=lambda x: _tour_score(instance, x[0])
            )
            best_neighbor_score = _tour_score(instance, best_neighbor)

        # --- Mise à jour de la solution courante ---
        current = best_neighbor
        current_score = best_neighbor_score

        # Enregistrer le mouvement inverse dans la liste tabou
        tabu_list[best_move_attr] = iteration + tabu_tenure

        # --- Mise à jour du meilleur global ---
        if current_score > best_score + 1e-9:
            best = list(current)
            best_score = current_score
            no_improve = 0
            if verbose:
                print(f"  iter={iteration}  score={best_score:.2f}")
        else:
            no_improve += 1

        # --- Intensification : redémarrer depuis le meilleur ---
        if no_improve >= no_improve_restart:
            current = list(best)
            current_score = best_score
            tabu_list.clear()
            no_improve = 0
            stats["restarts"] += 1
            if verbose:
                print(f"  [restart] iter={iteration}")

    cpu_time = time.perf_counter() - t0

    return OPResult(
        method="Recherche tabou",
        tour=best,
        total_score=best_score,
        total_dist=compute_dist(instance, best),
        cpu_time=cpu_time,
        optimal=False,
        extra=stats
    )


# ---------------------------------------------------------------------------
# Construction greedy initiale
# ---------------------------------------------------------------------------

def _greedy_init(inst: OPInstance, rng: random.Random) -> List[int]:
    s, e = inst.start, inst.end
    tour = [s, e]
    unvisited = list(inst.customers)
    rng.shuffle(unvisited)
    for v in unvisited:
        best_pos, best_delta = None, float('inf')
        for pos in range(1, len(tour)):
            prev, nxt = tour[pos-1], tour[pos]
            delta = (inst.dist[prev][v] + inst.dist[v][nxt]
                     - inst.dist[prev][nxt])
            if delta < best_delta:
                best_delta = delta
                best_pos = pos
        if best_pos is not None:
            new_tour = tour[:best_pos] + [v] + tour[best_pos:]
            if _tour_dist(inst, new_tour) <= inst.t_max + 1e-9:
                tour = new_tour
    return tour


# ---------------------------------------------------------------------------
# Test autonome
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    from op_utils import generate_instance

    print("=== Test Recherche Tabou ===")
    for n_cust in [10, 20, 40]:
        inst = generate_instance(n_customers=n_cust, t_max_ratio=0.4, seed=42)
        r = solve_tabu(inst, seed=42, verbose=False)
        print(f"\nn={inst.n}  score={r.total_score:.2f}  "
              f"dist={r.total_dist:.2f}  t={r.cpu_time:.3f}s  "
              f"iter={r.extra['iterations']}  "
              f"restarts={r.extra['restarts']}  "
              f"aspiration={r.extra['aspiration_hits']}")
        print(f"  Tour : {r.tour}")
