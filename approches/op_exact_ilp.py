"""
op_exact_ilp.py — Méthode exacte 1 : Formulation en Programmation Linéaire Entière

Approche
--------
Modélise l'OP comme un MILP (Mixed-Integer Linear Program) avec :
- Variables x[i,j] binaires : arc (i,j) est utilisé
- Variables s[i] continues : score collecté jusqu'au sommet i
- Contraintes MTZ (Miller-Tucker-Zemlin) pour éliminer les sous-tours

Résolution
----------
Utilise PuLP (interface simple) avec CBC comme solveur.
CBC est inclus par défaut avec PuLP et ne nécessite pas d'installation externe.
"""

import time
from typing import List, Tuple, Optional
import numpy as np

from op_utils import OPInstance, OPResult, compute_score, compute_dist, is_feasible

try:
    from pulp import (
        LpMaximize, LpProblem, LpVariable, lpSum,
        LpStatus, value, PULP_CBC_CMD
    )
    PULP_AVAILABLE = True
except ImportError:
    PULP_AVAILABLE = False


# ============================================================================
# Formulation ILP
# ============================================================================

def _formulate_ilp(inst: OPInstance) -> Tuple[object, dict, dict]:
    """
    Formule l'OP en tant que MILP.

    Retourne
    --------
    prob       : objet LpProblem
    x          : dict des variables de flot (i, j)
    score_vars : dict des variables de score à chaque sommet
    """

    prob = LpProblem("OP", LpMaximize)

    n = inst.n
    s = inst.start
    e = inst.end

    # Variables x[i,j] : 1 si arc (i,j) est utilisé, 0 sinon
    x = {}
    for i in range(n):
        for j in range(n):
            if i != j:
                x[(i, j)] = LpVariable(f"x_{i}_{j}", cat="Binary")

    # Variables score[i] : score collecté à chaque sommet (continu, [0, score[i]])
    score = {}
    for i in range(n):
        score[i] = LpVariable(f"score_{i}", lowBound=0, upBound=inst.scores[i])

    # ========== Fonction objectif ==========
    prob += lpSum(score[i] for i in range(n)), "Total_Score"

    # ========== Contraintes ==========

    # 1. Conservation du flot et départ/arrivée
    prob += lpSum(x[(s, j)] for j in range(n) if j != s) == 1, "Leave_Start"
    prob += lpSum(x[(i, e)] for i in range(n) if i != e) == 1, "Enter_End"

    for i in range(n):
        if i != s and i != e:
            # Flot entrant = flot sortant pour chaque client
            prob += (
                lpSum(x[(j, i)] for j in range(n) if j != i) ==
                lpSum(x[(i, j)] for j in range(n) if j != i)
            ), f"Flow_Balance_{i}"

    # 2. Budget maximal de distance
    total_dist = lpSum(
        inst.dist[i][j] * x[(i, j)]
        for i in range(n)
        for j in range(n)
        if i != j
    )
    prob += total_dist <= inst.t_max, "Budget"

    # 3. Contraintes MTZ (Miller-Tucker-Zemlin) pour éliminer sous-tours
    # u[i] est une variable d'ordre de visite (continu)
    u = {}
    for i in range(n):
        u[i] = LpVariable(f"u_{i}", lowBound=0, upBound=n - 1)

    u[s].setInitialValue(0)  # Le départ a l'ordre 0
    u[e].setInitialValue(n - 1)  # L'arrivée a l'ordre n-1

    for i in range(n):
        for j in range(n):
            if i != j and i != s and j != e:
                # Si x[i,j] = 1, alors u[j] >= u[i] + 1
                prob += u[j] >= u[i] + 1 - (n - 1) * (1 - x[(i, j)]), f"MTZ_{i}_{j}"

    # 4. Lien score[i] avec la visite de i
    # Si sommet i n'est pas visité (pas d'arc entrant sauf pour start),
    # alors score[i] = 0
    for i in range(n):
        if i != s:
            incoming = lpSum(x[(j, i)] for j in range(n) if j != i)
            # score[i] <= scores[i] * incoming
            prob += score[i] <= inst.scores[i] * incoming, f"Visit_{i}"

    return prob, x, score


# ============================================================================
# Résolution ILP
# ============================================================================

def solve_ilp(instance: OPInstance,
              time_limit: float = 60.0,
              verbose: bool = False) -> OPResult:
    """
    Résout l'OP par formulation ILP (CBC solver).

    Paramètres
    ----------
    instance   : OPInstance
    time_limit : limite de temps en secondes
    verbose    : afficher les détails du solveur

    Retourne
    --------
    OPResult
    """

    if not PULP_AVAILABLE:
        raise RuntimeError(
            "PuLP n'est pas disponible. "
            "Installation : pip install pulp"
        )

    t0 = time.perf_counter()

    # Formulation
    prob, x, score = _formulate_ilp(instance)

    # Résolution
    solver = PULP_CBC_CMD(
        timeLimit=int(time_limit),
        msg=1 if verbose else 0
    )
    prob.solve(solver)

    cpu_time = time.perf_counter() - t0

    # Extraction de la solution
    n = instance.n
    s = instance.start
    e = instance.end

    if prob.status != 1:  # 1 = Optimal
        # Pas de solution trouvée
        return OPResult(
            method="ILP (PuLP/CBC)",
            tour=[s, e],
            total_score=0.0,
            total_dist=instance.dist[s][e],
            cpu_time=cpu_time,
            optimal=False,
            extra={"status": LpStatus[prob.status]}
        )

    # Reconstruction de la tournée à partir des variables x
    tour = _extract_tour(instance, x)
    total_score = compute_score(instance, tour)
    total_dist = compute_dist(instance, tour)

    return OPResult(
        method="ILP (PuLP/CBC)",
        tour=tour,
        total_score=total_score,
        total_dist=total_dist,
        cpu_time=cpu_time,
        optimal=(prob.status == 1),
        extra={"status": LpStatus[prob.status], "objective": value(prob.objective)}
    )


# ============================================================================
# Extraction de la tournée
# ============================================================================

def _extract_tour(inst: OPInstance, x: dict) -> List[int]:
    """
    Reconstruit la tournée à partir des variables x.
    """
    tour = [inst.start]
    current = inst.start

    while current != inst.end:
        # Trouver le prochain sommet
        found = False
        for j in range(inst.n):
            if j != current:
                if x[(current, j)].varValue is not None and x[(current, j)].varValue > 0.5:
                    tour.append(j)
                    current = j
                    found = True
                    break

        if not found:
            # Pas d'arc sortant trouvé (problème de solution infaisable)
            break

    return tour


# ============================================================================
# Test autonome
# ============================================================================

if __name__ == "__main__":
    from op_utils import generate_instance

    print("=== Test ILP ===")
    for n_cust in [8, 12, 16]:
        inst = generate_instance(n_customers=n_cust, t_max_ratio=0.4, seed=42)
        r = solve_ilp(inst, time_limit=30, verbose=False)
        print(f"\nn={inst.n}  score={r.total_score:.2f}  "
              f"dist={r.total_dist:.2f}  t={r.cpu_time:.3f}s  "
              f"optimal={r.optimal}")
        print(f"  Tour : {r.tour}")
