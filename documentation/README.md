# Orienteering Problem — Etude Comparative

Six methodes de resolution implementees en Python : trois exactes (DP, Branch & Bound, ILP) et trois metaheuristiques (Recuit Simule, Recherche Tabou, GRASP).

---

## Lancer le projet

Depuis le dossier racine :

```bash
python main.py --test        # verifie que les 6 methodes fonctionnent (~1 min)
python main.py --run-all     # comparaison complete sur 6 tailles (~10 min)
python main.py               # ouvre le dashboard dans le navigateur
```

Prerequis : Python 3.7+. Aucune installation manuelle — PuLP se telecharge automatiquement au premier lancement de la methode ILP.

---

## Structure

```
optimisation_combinatoire_proj/
├── main.py                      point d'entree
├── approches/
│   ├── op_exact_dp.py           Programmation Dynamique (bitmask)
│   ├── op_exact_bb.py           Branch & Bound
│   ├── op_exact_ilp.py          ILP via PuLP/CBC
│   ├── op_meta_sa.py            Recuit Simule
│   ├── op_meta_tabu.py          Recherche Tabou
│   └── op_meta_grasp.py         GRASP
├── core/
│   ├── op_utils.py              structures de donnees, generation d'instances
│   ├── op_run_all.py            comparaison complete
│   └── test_all_methods.py      tests rapides
└── web/dashboard.html           interface graphique
```

Chaque fichier dans `approches/` est executable de facon independante.

---

## Methodes

### Exactes

**Programmation Dynamique** (`op_exact_dp.py`)
- Etat : `dp[S][v]` = meilleur profit quand l'ensemble S est visite et v est la position courante
- Complexite : O(2^n * n^2) en temps, O(2^n * n) en espace
- Garantit l'optimum. Limite stricte : n <= 22 clients.

**Branch & Bound** (`op_exact_bb.py`)
- Enumeration implicite par insertion progressive de clients
- Elagage quand la borne superieure (greedy optimiste) ne peut pas ameliorer le meilleur connu
- Applicable jusqu'a n ~ 40 avec une limite de temps de 60s

**ILP** (`op_exact_ilp.py`)
- Formulation MILP avec variables binaires x[i,j] par arc
- Contraintes MTZ pour l'elimination des sous-tours
- Solveur CBC via PuLP. Limite pratique : n <= 30

### Metaheuristiques

**Recuit Simule** (`op_meta_sa.py`)
- Acceptation probabiliste P = exp(delta/T), temperature T0 auto-calibree
- 4 operateurs de voisinage : INSERT, REMOVE, SWAP_POS, 2-OPT
- Parametres : alpha=0.995, T_min=0.01, iter_max=50 000

**Recherche Tabou** (`op_meta_tabu.py`)
- Liste tabou (tenure=7) stockant les attributs des mouvements recents
- Critere d'aspiration : mouvement tabou accepte si score > meilleur global
- Redemarrage depuis le meilleur apres 80 iterations sans amelioration

**GRASP** (`op_meta_grasp.py`)
- Construction greedy randomisee via RCL (alpha=0.35, n_iter=70)
- Recherche locale : 2-OPT + insertion du meilleur client + remplacement du moins rentable
- Chaque iteration est independante ; le meilleur resultat sur toutes les iterations est retenu

---

## Instances

Generees aleatoirement dans [0, 100]^2 :
- Depart et arrivee au centre
- Profits p_i dans {1, ..., 10}
- T_max = 0.4 * diametre du graphe (par defaut)
- Seed fixee a 42 pour la reproductibilite

---

## Executer une methode seule

```bash
python main.py --method dp
python main.py --method tabu
python main.py --method grasp --n 30   # 30 clients
```

Methodes disponibles : `dp`, `bb`, `ilp`, `sa`, `tabu`, `grasp`.


