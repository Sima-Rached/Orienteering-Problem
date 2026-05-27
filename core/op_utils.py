"""
op_utils.py — Utilitaires communs pour l'Orienteering Problem

Contient :
- Classe OPInstance : représentation d'une instance
- Classe OPResult : résultats d'une méthode
- Fonctions communes : génération d'instances, calcul de scores/distances, etc.
"""

import random
import math
from dataclasses import dataclass, field
from typing import List, Dict, Any
import numpy as np


# ============================================================================
# Structure de données pour une instance
# ============================================================================

@dataclass
class OPInstance:
    """Représente une instance du Orienteering Problem."""
    n: int                              # nombre total de sommets (start + customers + end)
    start: int                          # indice du sommet de départ (= 0)
    end: int                            # indice du sommet d'arrivée (= n-1)
    customers: List[int]                # liste des sommets clients (1 à n-2)
    dist: np.ndarray                    # matrice n×n des distances euclidiennes
    scores: np.ndarray                  # tableau des scores (profits) pour chaque sommet
    t_max: float                        # budget maximal (distance ou temps)
    coords: np.ndarray                  # coordonnées (n, 2) des sommets


# ============================================================================
# Structure de données pour les résultats
# ============================================================================

@dataclass
class OPResult:
    """Représente le résultat d'une méthode de résolution."""
    method: str                         # nom de la méthode
    tour: List[int]                     # tournée obtenue
    total_score: float                  # somme des scores de la tournée
    total_dist: float                   # distance totale
    cpu_time: float                     # temps CPU en secondes
    optimal: bool = False               # True si la solution est certifiée optimale
    gap: float = 0.0                    # écart à l'optimum (%) si connu
    extra: Dict[str, Any] = field(default_factory=dict)  # données additionnelles


# ============================================================================
# Génération d'instances
# ============================================================================

def generate_instance(n_customers: int = 20,
                      t_max_ratio: float = 0.4,
                      seed: int = None,
                      width: float = 100.0) -> OPInstance:
    """
    Génère une instance aléatoire du Orienteering Problem.

    Paramètres
    ----------
    n_customers : nombre de clients (sommets intermédiaires)
    t_max_ratio : budget maximal = t_max_ratio * (diamètre du graphe)
    seed        : graine aléatoire
    width       : largeur/hauteur du domaine [0, width] × [0, width]

    Retourne
    --------
    OPInstance
    """
    if seed is not None:
        random.seed(seed)
        np.random.seed(seed)

    # n sommets totaux : 0 (start), 1 à n_customers (clients), n_customers+1 (end)
    n = n_customers + 2
    start_idx, end_idx = 0, n - 1

    # Génération des coordonnées
    coords = np.random.uniform(0, width, size=(n, 2))
    coords[start_idx] = [width / 2, width / 2]  # start au centre
    coords[end_idx] = [width / 2, width / 2]    # end au même endroit

    # Matrice des distances euclidiennes
    dist = np.zeros((n, n))
    for i in range(n):
        for j in range(n):
            dist[i][j] = np.linalg.norm(coords[i] - coords[j])

    # Scores : aléatoires dans [1, 10] sauf start et end (score = 0)
    scores = np.zeros(n)
    for i in range(1, n - 1):
        scores[i] = random.randint(1, 10)

    # Budget maximal : ratio × diamètre du graphe
    max_dist = np.max(dist)
    t_max = t_max_ratio * max_dist

    customers = list(range(1, n - 1))

    return OPInstance(
        n=n,
        start=start_idx,
        end=end_idx,
        customers=customers,
        dist=dist,
        scores=scores,
        t_max=t_max,
        coords=coords
    )


# ============================================================================
# Fonctions de calcul
# ============================================================================

def compute_dist(inst: OPInstance, tour: List[int]) -> float:
    """Calcule la distance totale d'une tournée."""
    if len(tour) < 2:
        return 0.0
    total = 0.0
    for k in range(len(tour) - 1):
        total += inst.dist[tour[k]][tour[k + 1]]
    return total


def compute_score(inst: OPInstance, tour: List[int]) -> float:
    """Calcule le score total d'une tournée."""
    return sum(inst.scores[v] for v in tour)


def is_feasible(inst: OPInstance, tour: List[int]) -> bool:
    """Vérifie qu'une tournée respecte le budget de distance."""
    dist = compute_dist(inst, tour)
    return dist <= inst.t_max + 1e-9


# ============================================================================
# Affichage comparatif
# ============================================================================

def print_comparison(results: List[OPResult], inst: OPInstance) -> None:
    """
    Affiche un tableau comparatif de toutes les methodes.
    """
    SEP = "-" * 130

    print("\n" + SEP)
    print(f"{'Methode':<25} {'Score':<12} {'Distance':<12} {'Temps (s)':<12} "
          f"{'Gap (%)':<10} {'Statut':<15} {'Details':<40}")
    print(SEP)

    for r in results:
        method_name = r.method[:24]
        score_str = f"{r.total_score:.2f}"
        dist_str = f"{r.total_dist:.2f}"
        time_str = f"{r.cpu_time:.4f}"
        gap_str = f"{r.gap:.2f}" if r.gap > 0 else "-"

        if r.optimal:
            status_str = "[meilleur]"
        elif is_feasible(inst, r.tour):
            status_str = "[Faisable]"
        else:
            status_str = "[Infaisable]"

        details = ""
        if "iterations" in r.extra:
            details += f"iter={r.extra['iterations']}"
        if "n_seeds" in r.extra:
            details += f" ({r.extra['n_seeds']} seeds)"
        if "accepted" in r.extra:
            accept_rate = (r.extra["accepted"] /
                          (r.extra["accepted"] + r.extra["rejected"] + 1)) * 100
            details += f" accept={accept_rate:.0f}%"

        print(f"{method_name:<25} {score_str:<12} {dist_str:<12} "
              f"{time_str:<12} {gap_str:<10} {status_str:<15} {details:<40}")

    print(SEP)


# ============================================================================
# Utilitaires pour visualisation (optionnel)
# ============================================================================

def tour_to_string(tour: List[int]) -> str:
    """Convertit une tournée en chaîne lisible."""
    return " → ".join(str(v) for v in tour)


def solution_info(inst: OPInstance, tour: List[int]) -> str:
    """Retourne une description textuelle d'une solution."""
    score = compute_score(inst, tour)
    dist = compute_dist(inst, tour)
    feasible = is_feasible(inst, tour)
    return (f"Score: {score:.2f}, Dist: {dist:.2f}, "
            f"Budget: {inst.t_max:.2f}, Faisable: {feasible}")
