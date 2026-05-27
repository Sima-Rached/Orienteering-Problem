# Guide d'Exécution du Projet


Pour vérifier que **tout fonctionne**, exécutez simplement:

```bash
python test_all_methods.py
```

**Résultat attendu** :
- ✓ 6 méthodes testées sur une petite instance (8 clients)
- Affichage des scores et temps d'exécution
- Message final : "✓ TOUS LES TESTS PASSENT"

##  Lancer l'Étude Complète

Pour la comparaison complète sur plusieurs tailles d'instances:

```bash
python op_run_all.py
```

**Ce qu'il fait** :
- Teste les 6 méthodes sur des instances de tailles croissantes:
  - Petites: 8, 12, 16 clients (tous les exactes + métaheuristiques)
  - Moyennes: 25, 40 clients (ILP/B&B/Métaheuristiques limités en temps)
  - Grandes: 60 clients (métaheuristiques principalement)

- Affiche un **tableau comparatif** pour chaque taille montrant:
  - Score obtenu
  - Distance parcourue
  - Temps d'exécution
  - Gap par rapport à l'optimum (si connu)
  - Statut (Optimal/Faisable/Infaisable)
  - Détails supplémentaires (iterations, restarts, seeds, etc.)


##  Tester une Méthode Isolée

Pour démontrer une méthode spécifique:

### Recuit Simulé
```bash
python op_meta_sa.py
```
**Sortie** : Résultats sur 3 instances (n=10, 20, 40) avec statistiques de convergence

### Recherche Tabou
```bash
python op_meta_tabu.py
```
**Sortie** : Résultats avec nombre de redémarrages et aspirations

### GRASP
```bash
python op_meta_grasp.py
```
**Sortie** : Résultats avec nombre de seeds et scores moyens

### Programmation Dynamique
```bash
python op_exact_dp.py
```
**Sortie** : Résultats OPTIMAUX sur instances petites (n≤20)

### Branch & Bound
```bash
python op_exact_bb.py
```
**Sortie** : Résultats avec exploration d'arbres

### ILP (PuLP/CBC)
```bash
python op_exact_ilp.py
```
**Sortie** : Résultats avec status du solveur


## Format des Résultats

Tableau typique affiché :

```
──────────────────────────────────────────────────────────────────────────────
Méthode                   Score        Distance     Temps (s)    Gap (%)    Statut
──────────────────────────────────────────────────────────────────────────────
ILP (PuLP/CBC)            25.00        156.42       0.0450       0.00       ✓ Optimal
Branch & Bound            25.00        156.42       0.0023       0.00       ✓ Faisable
DP (Bitmask)              25.00        156.42       0.0089       0.00       ✓ Optimal
Recuit simulé             25.00        156.42       0.1234       0.00       ✓ Faisable
Recherche tabou           25.00        156.42       0.0156       0.00       ✓ Faisable
GRASP                     25.00        156.42       0.0432       0.00       ✓ Faisable
──────────────────────────────────────────────────────────────────────────────
```

**Interprétation** :
- **Score** : Somme des profits collectés (maximisé)
- **Distance** : Coût total du parcours (doit être ≤ T_max)
- **Temps** : Secondes d'exécution
- **Gap** : Écart à l'optimum en % (0% = optimal)
- **Statut** : ✓ meilleur / ✓ Faisable / ✗ Infaisable


##  Personnalisation

### Modifier la Taille des Instances

Éditer `op_run_all.py`, ligne ~102-114 :

**Avant** :
```python
for n in [8, 12, 16]:
    run_all(n_customers=n, ...)
```

**Après** (pour tester n=5, 10, 15) :
```python
for n in [5, 10, 15]:
    run_all(n_customers=n, ...)
```

### Modifier les Limites de Temps

Dans `op_run_all.py`, paramètre `time_limit_exact` et `time_limit_meta` :

```python
run_all(n_customers=n,
        time_limit_exact=120,  # 2 minutes pour les exactes
        time_limit_meta=30,    # 30 secondes pour les métaheuristiques
        ...)
```

### Modifier les Paramètres des Métaheuristiques

#### Recuit Simulé (op_meta_sa.py, solve_sa)
```python
alpha = 0.99      # Plus bas = refroidissement plus lent
T_min = 0.001     # Plus bas = recherche plus longue
iter_per_T = 500  # Plus haut = exploration plus complète
```

#### Recherche Tabou (op_meta_tabu.py, solve_tabu)
```python
tabu_tenure = 10       # Plus haut = mémoire plus longue
n_neighbors = 50       # Plus haut = plus de candidats
no_improve_restart = 100  # Redémarrage plus fréquent
```

#### GRASP (op_meta_grasp.py, solve_grasp)
```python
n_iter = 200   # Plus haut = plus d'itérations
alpha = 0.5    # 0=greedy, 1=aléatoire, 0.5=équilibré
```




##  Commandes Rapides à Copier

```bash
# Test rapide (1 minute)
python test_all_methods.py

# Comparaison complète (5-10 minutes)
python op_run_all.py

# Métaheuristique 1 (Recuit Simulé)
python op_meta_sa.py

# Métaheuristique 2 (Tabu)
python op_meta_tabu.py

# Métaheuristique 3 (GRASP)
python op_meta_grasp.py

# Exacte 1 (DP - rapide et exact)
python op_exact_dp.py

# Exacte 2 (Branch & Bound)
python op_exact_bb.py

# Exacte 3 (ILP)
python op_exact_ilp.py
```


