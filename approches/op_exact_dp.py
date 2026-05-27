"""
op_exact_dp.py — Méthode exacte 3 : Programmation Dynamique (Bitmask DP)

Approche
--------
Résout l'OP par programmation dynamique avec représentation bitmask.

État DP
-------
dp[S][v] = meilleur profit collecté quand :
  - S est un ensemble de clients visités (bitmask)
  - v est le sommet actuel

Complexité
----------
O(2^n * n^2) en temps et O(2^n * n) en espace
Donc applicable pour n ≤ 20-22 clients seulement

Formulation
-----------
dp[S][v] = max{dp[S \ {v}][u] + score[v] : (u,v) réalisable avec S ∪ {v}}
           soumis à : distance(S ∪ {v}) ≤ t_max
"""

import time
from typing import List, Tuple, Optional, Dict

from op_utils import OPInstance, OPResult, compute_score, compute_dist, is_feasible


# ============================================================================
# Utilités pour bitmask
# ============================================================================

def _popcount(mask: int) -> int:
    """Compte le nombre de bits à 1 dans mask."""
    count = 0
    while mask:
        count += mask & 1
        mask >>= 1
    return count


def _is_set(mask: int, bit: int) -> bool:
    """Vérifie si le bit 'bit' est à 1 dans mask."""
    return (mask >> bit) & 1


def _set_bit(mask: int, bit: int) -> int:
    """Met le bit 'bit' à 1 dans mask."""
    return mask | (1 << bit)


def _unset_bit(mask: int, bit: int) -> int:
    """Met le bit 'bit' à 0 dans mask."""
    return mask & ~(1 << bit)


def _mask_to_list(mask: int, n: int) -> List[int]:
    """Convertit un bitmask en liste d'indices."""
    return [i for i in range(n) if _is_set(mask, i)]


# ============================================================================
# Programmation Dynamique
# ============================================================================

def solve_dp(instance: OPInstance,
             verbose: bool = False) -> OPResult:
    """
    Résout l'OP par programmation dynamique avec bitmask.

    Applicable seulement pour n ≤ 22 environ.

    Paramètres
    ----------
    instance : OPInstance
    verbose  : afficher les détails

    Retourne
    --------
    OPResult
    """

    t0 = time.perf_counter()

    n = instance.n
    s = instance.start  # 0
    e = instance.end    # n-1

    # Vérifier la faisabilité
    if n > 22:
        raise ValueError(f"DP inapplicable : n={n} > 22 (2^22 = {2**22})")

    # Nombre de clients (hors start et end)
    n_customers = n - 2
    start_mask = 1 << s  # inclure le départ

    # dp[mask][v] = (meilleur_score, distance_minimale)
    # mask : ensemble de clients visités + le départ
    # v    : dernier sommet de la tournée
    DP = {}

    # Initialisation
    DP[(start_mask, s)] = (instance.scores[s], 0.0)

    # Itération sur tous les masques
    for mask in range(start_mask, 1 << n):
        if not _is_set(mask, s):
            continue  # Le départ doit toujours être dans le chemin

        for v in range(n):
            if not _is_set(mask, v):
                continue  # Le sommet actuel doit être dans le masque

            if (mask, v) not in DP:
                continue

            current_score, current_dist = DP[(mask, v)]

            # Essayer d'ajouter un nouveau sommet u
            for u in range(n):
                if _is_set(mask, u):
                    continue  # u déjà visité
                if u == s:
                    continue  # Ne pas revisiter le départ
                if u != e and (u < 1 or u >= n - 1):
                    continue  # u doit être un client (1 à n-2) ou l'arrivée (n-1)

                new_dist = current_dist + instance.dist[v][u]

                # Vérifier contrainte de distance
                if new_dist > instance.t_max + 1e-9:
                    continue

                new_score = current_score + instance.scores[u]
                new_mask = _set_bit(mask, u)

                if (new_mask, u) not in DP or DP[(new_mask, u)][0] < new_score:
                    DP[(new_mask, u)] = (new_score, new_dist)

    # Extraction de la solution optimale
    best_score = 0.0
    best_mask = start_mask
    best_end = s

    for mask in range(start_mask, 1 << n):
        if not _is_set(mask, s):
            continue

        for v in range(n):
            if (mask, v) not in DP:
                continue

            score, dist = DP[(mask, v)]

            # Vérifier si on peut fermer la tournée vers l'arrivée
            final_dist = dist + instance.dist[v][e]
            if final_dist <= instance.t_max + 1e-9:
                if score > best_score:
                    best_score = score
                    best_mask = mask
                    best_end = v

    # Reconstruction de la tournée
    best_tour = _reconstruct_tour_dp(instance, DP, best_mask, best_end, s, n)

    cpu_time = time.perf_counter() - t0

    return OPResult(
        method="DP (Bitmask)",
        tour=best_tour,
        total_score=best_score,
        total_dist=compute_dist(instance, best_tour),
        cpu_time=cpu_time,
        optimal=True,  # DP garantit l'optimalité
        extra={"states_computed": len(DP)}
    )


# ============================================================================
# Reconstruction de la tournée
# ============================================================================

def _reconstruct_tour_dp(instance: OPInstance, DP: Dict, mask: int,
                         v: int, start: int, n: int) -> List[int]:
    """
    Reconstruit la tournée optimale en remontant l'arborescence DP.
    """
    tour = []
    current_v = v
    current_mask = mask

    while current_mask != (1 << start):
        tour.append(current_v)

        # Trouver le prédécesseur
        found_prev = False
        for prev_v in range(n):
            prev_mask = _unset_bit(current_mask, current_v)
            if (prev_mask, prev_v) in DP:
                if _is_set(prev_mask, prev_v):
                    # Vérifier que c'est cohérent
                    prev_score, prev_dist = DP[(prev_mask, prev_v)]
                    new_dist = prev_dist + instance.dist[prev_v][current_v]
                    if abs(new_dist - DP[(current_mask, current_v)][1]) < 1e-9:
                        current_v = prev_v
                        current_mask = prev_mask
                        found_prev = True
                        break

        if not found_prev:
            break

    tour.append(start)
    tour.reverse()
    tour.append(instance.end)

    return tour


# ============================================================================
# Informations de faisabilité
# ============================================================================

def dp_complexity_info(n: int) -> dict:
    """
    Retourne des infos sur la faisabilité de DP pour n sommets.
    """
    faisable = n <= 22
    n_states = 2 ** n * n if faisable else "inf"
    memory_mb = (2 ** n * n * 16) / (1024 * 1024) if faisable else "inf"

    return {
        "faisable": faisable,
        "n": n,
        "n_states": n_states,
        "memory_estimate_MB": memory_mb if faisable else "inf"
    }


# ============================================================================
# Test autonome
# ============================================================================

if __name__ == "__main__":
    from op_utils import generate_instance

    print("=== Test DP ===")
    for n_cust in [8, 12, 16, 20]:
        inst = generate_instance(n_customers=n_cust, t_max_ratio=0.4, seed=42)

        try:
            r = solve_dp(inst, verbose=False)
            print(f"\nn={inst.n}  score={r.total_score:.2f}  "
                  f"dist={r.total_dist:.2f}  t={r.cpu_time:.3f}s  "
                  f"optimal={r.optimal}  states={r.extra['states_computed']}")
            print(f"  Tour : {r.tour}")
        except ValueError as e:
            print(f"\nn={inst.n}  Erreur : {e}")
