# SYNTHÈSE TECHNIQUE 

## 1. Définition Formelle du Problème

### Énoncé

L'**Orienteering Problem (OP)** est un problème de routage combinatoire défini comme suit:

**Données** :
- Un graphe complet G = (V, E) avec |V| = n sommets
- Un sommet de départ s et un sommet d'arrivée t (potentiellement identiques)
- Pour chaque sommet v ∈ V : un profit (score) p_v ≥ 0
- Pour chaque arête (i,j) ∈ E : une distance/coût d_{i,j} ≥ 0
- Un budget maximum (longueur, temps, énergie) T_max

**Variables de décision** :
- Chemin/tournée reliant s à t
- Ensemble des sommets visités

**Objectif** :
```
Maximiser : Σ_{v visités} p_v
```

**Contraintes** :
```
Σ_{arêtes du chemin} d_{i,j} ≤ T_max
Le chemin commence en s et se termine en t
```

---

## 2. Formulation Mathématique

### Programmation Linéaire Entière (MILP)

```
Variables :
  x_{i,j} ∈ {0,1}   pour tout (i,j) ∈ E×E, i ≠ j
  y_v ∈ {0,1}       pour tout v ∈ V
  u_v ∈ ℝ^+         pour tout v ∈ V (variable d'ordre MTZ)

Objectif :
  max Σ_v p_v × y_v

Contraintes :
  (1) Conservation du flot (départ) :
      Σ_{j ≠ s} x_{s,j} = 1
  
  (2) Conservation du flot (arrivée) :
      Σ_{i ≠ t} x_{i,t} = 1
  
  (3) Conservation du flot (sommets intermédiaires) :
      Pour tout v ≠ s,t :
      Σ_{i ≠ v} x_{i,v} = Σ_{j ≠ v} x_{v,j}
  
  (4) Budget de distance :
      Σ_{i,j} d_{i,j} × x_{i,j} ≤ T_max
  
  (5) Élimination des sous-tours (MTZ) :
      Pour tout i,j ≠ s, i ≠ j, j ≠ t :
      u_j ≥ u_i + 1 - (n-1)×(1 - x_{i,j})
      avec 0 ≤ u_v ≤ n-1
  
  (6) Lien visite-profit :
      Pour tout v ≠ s :
      p_v × y_v ≤ p_v × Σ_{i ≠ v} x_{i,v}
```

**Complexité théorique** : NP-difficile (réduction depuis TSP)

---

## 3. Méthodes Exactes Implémentées

### 3.1 Programmation Dynamique (DP Bitmask)

#### Principe
Exploite la structure du problème en utilisantun état DP sur l'ensemble des clients visités.

#### État DP
```
dp[S][v] = meilleur profit collecté quand :
  - S ⊆ V est l'ensemble des sommets déjà visités (codé en bitmask)
  - v est le sommet actuel (dernier visité)
  
Garantit : distance du chemin S ≤ T_max
```

#### Récurrence
```
dp[S ∪ {u}][u] = max{
  dp[S][v] + score[u]
  pour tout v ∈ S tel que dist_accum(S ∪ {u}) ≤ T_max
}
```

#### Complexité
- **Temps** : O(2^n × n²)
- **Espace** : O(2^n × n)
- **Applicabilité** : n ≤ 22 seulement

#### Avantages
- ✓ Garantit l'optimalité globale
- ✓ Très rapide pour n ≤ 20
- ✓ Facile à paralléliser

#### Inconvénients
- ✗ Limite stricte n ≤ 22
- ✗ Explosion exponentielle de mémoire

### 3.2 Branch and Bound (B&B)

#### Stratégie
Énumération implicite avec pruning basé sur bornes supérieures.

#### Algorithme
```
1. Initialisation :
   - Solution initiale greedy
   - Meilleure borne inférieure connue : LB = score_greedy
   
2. Pour chaque nœud de l'arborescence :
   - Calculer borne supérieure UB par heuristique greedy
   - Si UB ≤ LB : ÉLAGUER cette branche
   - Sinon : brancher sur le client non-visité avec meilleur ratio
   
3. Retourner la meilleure solution trouvée
```

#### Branchement
```
Pour client non-visité v avec meilleur score/coût :
  Branche 1 : Insérer v dans la tournée
  Branche 2 : Interdire v (ne pas le visiter)
```

#### Borne Supérieure (Relaxation)
```
À chaque nœud, insérer greedyment les clients restants
jusqu'à violer le budget → estime max profit possible
```

#### Complexité
- **Pire cas** : O(n!) avec peu de pruning
- **Cas moyen** : O(2^n) avec bon pruning
- **Applicabilité** : n ≤ 30-40 selon instance

#### Avantages
- ✓ Souvent trouve l'optimum
- ✓ Adaptatif à la structure de l'instance
- ✓ Pas limite stricte en n

#### Inconvénients
- ✗ Non garantie d'optimalité
- ✗ Temps imprévisible

### 3.3 ILP avec Solveur CBC (PuLP)

#### Approche
Formulation MILP standard résolue par solveur complet.

#### Solveur CBC (Coin-Or)
```
Type : Solveur Branch-and-Cut
Caractéristiques :
  - Open-source et gratuit
  - Inclus automatiquement avec PuLP
  - Utilise cutting planes pour renforcer LP relaxation
  - Heuristiques intégrées
```

#### Algorithme Interne
```
1. LP relaxation (remplacer binaires par continues)
2. Résoudre LP → borne supérieure
3. Branching sur variables fractionnaires
4. Coupes (cutting planes) pour renforcer
5. Heuristiques pour trouver bonnes solutions initiales
6. Pruning basé sur bornes
7. Retourner solution optimale (si trouvée dans time limit)
```

#### Complexité
- **Empirique** : O(n^3) à O(n^4) pour LP solves
- **Applicabilité** : n ≤ 30-40 en pratique

#### Avantages
- ✓ Garantit l'optimalité si trouvé
- ✓ Robustesse éprouvée
- ✓ Pas d'implémentation complexe

#### Inconvénients
- ✗ Temps très imprévisible
- ✗ Timeout fréquent sur grandes instances
- ✗ Code de formulation critique

---

## 4. Métaheuristiques Implémentées

### 4.1 Recuit Simulé (Simulated Annealing)

#### Inspiration
Analogie avec refroidissement physique de solides.

#### Algorithme
```
1. Initialisation :
   - Solution courante : construction greedy randomisée
   - T = T₀ (température initiale, auto-calibrée)
   - meilleure_solution = solution_courante
   
2. Boucle principale (T > T_min) :
   Pour i = 1 à iter_per_T :
     - Générer voisin aléatoire : new_solution
     - Δ = score(new_solution) - score(courante)
     
     Si Δ > 0 :
       Accepter toujours
     Sinon :
       Accepter avec probabilité exp(Δ/T)
     
     Mettre à jour meilleure_solution si amélioration
   
   T ← T × α (refroidissement)
3. Retourner meilleure_solution
```

#### Opérateurs de Voisinage
1. **INSERT(v)** : Ajouter client non-visité v à meilleure position
2. **REMOVE(v)** : Retirer client visité v
3. **SWAP(i,j)** : Échanger positions i et j
4. **2-OPT(i,j)** : Inverser segment [i,j]

#### Auto-calibration de T₀
```
Kirkpatrick heuristic :
  - Effectuer N_samples mouvements aléatoires
  - Calculer Δ moyen des dégradations
  - T₀ = -Δ_moyen / ln(accept_rate_cible)
  - Tyiquement accept_rate = 0.8
```

#### Paramètres Typiques
```
T₀        : auto-calibré (ex: 15-25)
α         : 0.995 (refroidissement lent = meilleure qualité)
T_min     : 0.01 (critère d'arrêt)
iter_per_T: 100 (itérations par palier)
max_iter  : 50,000
```

#### Complexité
- **Temps** : O(max_iter × k) où k = coût op.voisin
- **Espace** : O(n) pour solution courante

#### Avantages
- ✓ Simple à implémenter et comprendre
- ✓ Bonne capacité de fuite locale (début)
- ✓ Peu de paramètres à calibrer
- ✓ Très parallélisable

#### Inconvénients
- ✗ Sensible aux paramètres (T₀, α)
- ✗ Pas d'exploitation de structure (aveugle)
- ✗ Convergence lente vers optim local

---

### 4.2 Recherche Tabou (Tabu Search)

#### Inspiration
Mimique processus mémoire humaine pour éviter les oublis.

#### Concept Clé : Liste Tabou
```
Maintient attributs des mouvements récemment effectués.
Ces mouvements interdits pendant 'tabu_tenure' itérations.
But : éviter les cycles court-terme et explorer plus large
```

#### Algorithme
```
1. Initialisation :
   - Solution courante : greedy
   - meilleure_solution = courante
   - tabu_list = {}  # attribut → expiration
   
2. Boucle principale :
   - Générer voisinage complet (30 candidats)
   - Filtrer : retirer mouvements tabou (sauf aspiration)
   - Sélectionner : meilleur voisin restant
   - Appliquer le mouvement
   - Enregistrer inverse dans tabu_list
   
   Mise à jour mémorisation :
     Si amélioration globale : no_improve = 0
     Sinon : no_improve += 1
   
   Intensification :
     Si no_improve > seuil : restart depuis meilleure
   
3. Retourner meilleure_solution
```

#### Critère d'Aspiration
```
Accepter un mouvement TABOU si :
  score(nouveau) > score(meilleur_global)
  
Permet d'accepter des chemins déjà explorés si prometteurs
```

#### Stratégies

**Intensification** :
```
Quand: stagnation (pas d'amélioration depuis N itérations)
Quoi: Restart depuis meilleure solution connue
       Purger liste tabou
Effect: Explore profondément region de qualité
```

**Diversification** :
```
Quand: très longtemps bloqué
Quoi: Perturbation aléatoire, reset paramètres
Effect: Escape plateaux, explorer autres regions
```

#### Mouvements et Attributs Tabou

| Mouvement | Attribut | Interprétation |
|-----------|----------|------------------|
| INSERT(v) | (INSERT, v) | Interdit retirer v |
| REMOVE(v) | (REMOVE, v) | Interdit réinsérer v |
| SWAP(i,j) | (SWAP, i,j) | Interdit re-swapper |
| 2OPT(i,j) | (2OPT, i,j) | Interdit re-retourner |

#### Paramètres Typiques
```
tabu_tenure       : 7 (durée mémoire)
n_neighbors       : 30 (voisins/itération)
max_iter          : 500
no_improve_restart: 80 (redémarrage après 80 iter)
```

#### Complexité
- **Temps** : O(max_iter × n_neighbors)
- **Espace** : O(tabu_tenure) pour liste

#### Avantages
- ✓ **Très efficace en pratique** (souvent meilleur score)
- ✓ Peu sensible aux paramètres
- ✓ Mémoire guidée = exploration rationnelle
- ✓ Stratégies d'intensification/diversification

#### Inconvénients
- ✗ Plus complexe à implémenter
- ✗ Plus coûteux computationnellement
- ✗ Requiert ajustement selon instance

---

### 4.3 GRASP (Greedy Randomized Adaptive Search Procedure)

#### Philosophie
Alternance régulière entre **construction diversifiée** et **amélioration locale**.

#### Cycle GRASP Unique
```
ITÉRATION i:
  Phase 1 (Construction) :
    - Générer solution initiale greedy randomisée
    - Paramétrée par alpha ∈ [0,1]
  
  Phase 2 (Amélioration) :
    - Appliquer recherche locale (2-OPT + Insert/Remove)
    - Jusqu'à optimum local
  
  Mettre à jour meilleure trouvée
Fin boucle après n_iter itérations
```

#### Phase 1 : RCL (Restricted Candidate List)

```
À chaque étape de construction :
  1. Calculer attractivité pour chaque client non-visité :
     att[v] = score[v] / coût_insertion[v]
  
  2. Construire RCL (liste restreinte) :
     min_att = min{att[v] : v candidat}
     max_att = max{att[v] : v candidat}
     threshold = max_att - alpha × (max_att - min_att)
     RCL = {v : att[v] ≥ threshold}
  
  3. Sélectionner aléatoirement : v ← RCL
  
  4. Insérer v à meilleure position
  
  5. Itérer jusqu'à budget épuisé
```

#### Impact du Paramètre alpha

| alpha | Comportement | Résultat |
|-------|-------------|----------|
| 0 | RCL = argmax(att) | Greedy pur (déterministe) |
| 0.3 | RCL restreinte | **Bon équilibre** |
| 0.7 | RCL large | Presque aléatoire |
| 1 | RCL = tous | Aléatoire pur |

#### Phase 2 : Recherche Locale (Variable Neighborhood Descent)

```
Amélioration par itération de 3 opérateurs :

1. 2-OPT :
   Pour chaque paire (i,j) de positions :
     Inverser segment [i,j]
     Si amélioration : appliquer, recommencer
   
2. INSERT :
   Pour chaque client non-visité :
     Trouver meilleure position d'insertion
     Si amélioration : appliquer, recommencer
   
3. REMOVE :
   Pour chaque client visité (sauf start/end) :
     Retirer si libère budget → réinsérer meilleur client
     Si amélioration : appliquer, recommencer

Itérer ces 3 opérateurs jusqu'à convergence
(aucun n'améliore plus)
```

#### Paramètres Typiques
```
n_iter : 200 (nombre total d'itérations)
alpha  : 0.3 (paramètre RCL)
```

#### Complexité
- **Temps** : O(n_iter × (construction + recherche_locale))
- Construction : O(n²)
- Recherche locale : O(n²) par opérateur
- **Total** : O(n_iter × n²)

#### Avantages
- ✓ Diversification garantie (construction randomisée)
- ✓ Qualité garantie (recherche locale)
- ✓ Très peu sensible aux paramètres
- ✓ Parallélisable trivial (chaque iteration indépendante)

#### Inconvénients
- ✗ Pas de mémoire entre itérations (vs Tabu)
- ✗ Peut avoir besoin de beaucoup d'itérations
- ✗ Peut être piégé dans même region à répétition

---

## 5. Analyse Comparative Théorique


### Recommandations par Taille

#### n ≤ 15 (Instances Petites)
```
1er choix  : DP (optimalité guaranteed, ultra-rapide)
2e choix   : ILP ou B&B (si DP pas disponible)
Méta       : Pour comparaison, mais perfectionnent DP
```

#### 15 < n ≤ 25 (Instances Moyennes)
```
1er choix  : ILP (avec limite temps 30-60s)
2e choix   : B&B (plus fiable que ILP en pratique)
Méta       : Tabu + SA très compétitives
Optimal? Tabu >= ILP souvent!
```

#### 25 < n ≤ 40 (Instances Grandes)
```
1er choix  : Tabu (meilleur tradeoff qualité/temps)
Alternative: SA (plus robuste, légèrement plus lent)
B&B, ILP : Limités à 10-20s, souvent timeout
Attention : Écarts à meilleur deviennent visibles
```

#### n > 40 (Très Grandes Instances)
```
Seules métaheuristiques faisables :
  1. Tabu (généralement meilleur)
  2. SA (bon backup)
  3. GRASP (plus d'itérations = meilleur)

Exactes = inutiles (100% timeout)
```

## 6. Structure de Fichiers

### Organisation Modulaire

```
op_utils.py ←─── Tous les autres dépendent de utils
  ├─ OPInstance (structure données)
  ├─ OPResult (résultats)
  ├─ generate_instance()
  └─ fonctions communes

op_exact_dp.py        (indépendant, optionnel)
op_exact_bb.py        (indépendant, optionnel)
op_exact_ilp.py       (indépendant, dépend PuLP)

op_meta_sa.py         (indépendant)
op_meta_tabu.py       (indépendant)
op_meta_grasp.py      (indépendant)

op_run_all.py ←─── Coordonne tout + comparaison
```


## 7. Validation Expérimentale

### Protocole de Test

```
1. Génération d'instances :
   - Seed fixe pour reproductibilité
   - Tailles : [8, 12, 16, 25, 40, 60]
   - Graphe : points aléatoires dans [0,100]²
   - Distances : euclidiennes
   - Scores : entiers [1,10]
   - T_max : 40% du diamètre du graphe

2. Pour chaque instance :
   - Lancer DP (si n ≤ 22) = RÉFÉRENCE OPTIMALE
   - Lancer 3 exactes : ILP, B&B
   - Lancer 3 métaheuristiques × 5 seeds chacune
   - Retenir meilleur sur 5 seeds pour métaheuristiques

3. Mesures :
   - Score absolu
   - Temps d'exécution
   - Gap = (opt - obtenu) / opt × 100%
   - Faisabilité (resp. budget)

4. Affichage :
   - Tableau comparatif formaté
   - Statistiques par méthode
```

