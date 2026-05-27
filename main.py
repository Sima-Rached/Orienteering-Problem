"""
main.py — Point d'entrée principal du projet Orienteering Problem

Usage:
   python main.py                    # Dashboard interactif (défaut)
   python main.py --help             # Affiche l'aide
   python main.py --run-all          # Comparaison complète (6 tailles)
   python main.py --test             # Test rapide (6 méthodes, ~1 min)
   python main.py --method NAME      # Exécute une méthode spécifique
   python main.py --method NAME --n N  # Avec taille d'instance personnalisée

Méthodes disponibles : dp, bb, ilp, sa, tabu, grasp
"""

import os
import sys
import webbrowser
import argparse
import subprocess
from pathlib import Path

# ── Répertoire racine du projet ───────────────────────────────────────────────
PROJECT_DIR = Path(__file__).parent.resolve()

# ── Localisation du dashboard (racine ou web/) ───────────────────────────────
DASHBOARD_FILE = (
    PROJECT_DIR / "dashboard.html"
    if (PROJECT_DIR / "dashboard.html").exists()
    else PROJECT_DIR / "web" / "dashboard.html"
)

# ── Localisation des scripts (core/ ou racine) ───────────────────────────────
def _find(name):
    """Cherche un fichier dans core/ puis à la racine."""
    for candidate in [PROJECT_DIR / "core" / name, PROJECT_DIR / name]:
        if candidate.exists():
            return candidate
    return None

TEST_FILE    = _find("test_all_methods.py")
RUN_ALL_FILE = _find("op_run_all.py")

# ── Mapping méthode → fichier (approches/ puis racine) ───────────────────────
METHODS_MAP = {
    "dp":    "op_exact_dp.py",
    "bb":    "op_exact_bb.py",
    "ilp":   "op_exact_ilp.py",
    "sa":    "op_meta_sa.py",
    "tabu":  "op_meta_tabu.py",
    "grasp": "op_meta_grasp.py",
}

def _find_method_file(filename):
    for candidate in [
        PROJECT_DIR / "approches" / filename,
        PROJECT_DIR / filename,
    ]:
        if candidate.exists():
            return candidate
    return None


# ─────────────────────────────────────────────────────────────────────────────
# Configuration console (encodage UTF-8 sous Windows)
# ─────────────────────────────────────────────────────────────────────────────

def _configure_console():
    if os.name == "nt":
        try:
            import ctypes
            ctypes.windll.kernel32.SetConsoleOutputCP(65001)
            ctypes.windll.kernel32.SetConsoleCP(65001)
        except Exception:
            pass
    for stream_name in ("stdout", "stderr"):
        stream = getattr(sys, stream_name, None)
        if stream is not None and hasattr(stream, "reconfigure"):
            try:
                stream.reconfigure(encoding="utf-8", errors="replace")
            except Exception:
                pass

_configure_console()


# ─────────────────────────────────────────────────────────────────────────────
# Bannière
# ─────────────────────────────────────────────────────────────────────────────

SEP  = "=" * 64
SEP2 = "-" * 64

def _banner():
    print(f"""
{SEP}
  Orienteering Problem - Etude Comparative
  3 Methodes Exactes  +  3 Metaheuristiques
  Projet Optimisation Combinatoire - Mai 2026
{SEP}
""")


# ─────────────────────────────────────────────────────────────────────────────
# Paramètres alignés avec le dashboard
# (dashboard.html : n=7 sommets = 5 clients, T_max=15.0, seed=42,
#  GRASP alpha=0.35 n_iter=70, Tabu tenure=7 n_neighbors=30,
#  SA alpha=0.995 T_min=0.01)
# ─────────────────────────────────────────────────────────────────────────────

DASHBOARD_PARAMS = {
    "n_sommets"  : 7,       # affiché dans la topbar du dashboard
    "t_max"      : 15.0,    # affiché dans la topbar du dashboard
    "seed"       : 42,      # affiché dans la topbar du dashboard
    # GRASP
    "grasp_alpha": 0.35,    # dashboard : α (RCL) = 0.35
    "grasp_iter" : 70,      # dashboard : Itérations = 70
    # Tabu
    "tabu_tenure": 7,
    "tabu_neighbors": 30,
    "tabu_iter"  : 500,
    "tabu_restart": 80,
    # SA
    "sa_alpha"   : 0.995,
    "sa_tmin"    : 0.01,
    "sa_iter"    : 50_000,
}


# ─────────────────────────────────────────────────────────────────────────────
# Actions
# ─────────────────────────────────────────────────────────────────────────────

def launch_dashboard():
    _banner()
    if not DASHBOARD_FILE.exists():
        print(f"[ERREUR] dashboard.html introuvable.")
        print(f"  Cherche dans : {DASHBOARD_FILE}")
        sys.exit(1)

    url = f"file://{DASHBOARD_FILE}"
    print(f"[OK] Dashboard : {DASHBOARD_FILE.name}")
    print(f"[OK] Instance affichee : n={DASHBOARD_PARAMS['n_sommets']} sommets, "
          f"T_max={DASHBOARD_PARAMS['t_max']}, seed={DASHBOARD_PARAMS['seed']}")
    print(f"\n     Ouverture dans le navigateur...")
    print(f"     Si le navigateur ne s'ouvre pas : {url}\n")

    try:
        webbrowser.open(url)
    except Exception as e:
        print(f"[WARNING] Impossible d'ouvrir le navigateur : {e}")



def run_test():
    _banner()
    if TEST_FILE is None:
        print("[ERREUR] test_all_methods.py introuvable (cherche dans core/ et racine).")
        sys.exit(1)
    print(f"[OK] Lancement des tests rapides ({TEST_FILE.relative_to(PROJECT_DIR)})...\n")
    result = subprocess.run(
        [sys.executable, str(TEST_FILE)],
        cwd=PROJECT_DIR
    )
    sys.exit(result.returncode)


def run_all():
    _banner()
    if RUN_ALL_FILE is None:
        print("[ERREUR] op_run_all.py introuvable (cherche dans core/ et racine).")
        sys.exit(1)
    print(f"[OK] Comparaison complete ({RUN_ALL_FILE.relative_to(PROJECT_DIR)})...")
    print("     Tailles : n_c in {8, 12, 16, 25, 40, 60}")
    print("     Duree estimee : 5-15 minutes\n")
    result = subprocess.run(
        [sys.executable, str(RUN_ALL_FILE)],
        cwd=PROJECT_DIR
    )
    sys.exit(result.returncode)


def run_method(method_name, n_customers=20):
    _banner()
    key = method_name.lower()
    if key not in METHODS_MAP:
        print(f"[ERREUR] Methode inconnue : '{method_name}'")
        print(f"         Disponibles : {', '.join(METHODS_MAP)}")
        sys.exit(1)

    method_file = _find_method_file(METHODS_MAP[key])
    if method_file is None:
        print(f"[ERREUR] Fichier introuvable : {METHODS_MAP[key]}")
        print(f"         Cherche dans approches/ et racine du projet.")
        sys.exit(1)

    print(f"[OK] Methode  : {key.upper()}")
    print(f"[OK] Fichier  : {method_file.relative_to(PROJECT_DIR)}")
    print(f"[OK] Clients  : {n_customers}")
    print(f"[OK] Seed ref : {DASHBOARD_PARAMS['seed']} (meme que le dashboard)\n")

    result = subprocess.run(
        [sys.executable, str(method_file)],
        cwd=PROJECT_DIR
    )
    sys.exit(result.returncode)


def show_methods():
    _banner()
    p = DASHBOARD_PARAMS
    print(f"""Methodes disponibles
{SEP2}

  Exactes:
    dp    Programmation Dynamique   (optimal, n <= 22)
    bb    Branch & Bound            (n <= ~40)
    ilp   ILP / PuLP-CBC            (n <= ~30)

  Metaheuristiques:
    sa    Recuit Simule             (alpha={p['sa_alpha']}, iter_max={p['sa_iter']:,})
    tabu  Recherche Tabou           (tenure={p['tabu_tenure']}, voisins={p['tabu_neighbors']}, restart={p['tabu_restart']})
    grasp GRASP                     (alpha_RCL={p['grasp_alpha']}, n_iter={p['grasp_iter']})

  Instance de reference du dashboard :
    n={p['n_sommets']} sommets, T_max={p['t_max']}, seed={p['seed']}

Usage : python main.py --method <nom> [--n <nb_clients>]
""")


def show_help():
    _banner()
    print(f"""Guide d'utilisation
{SEP2}

  python main.py                        Dashboard (defaut)
  python main.py --test                 Test rapide (~1 min)
  python main.py --run-all              Comparaison complete (~10 min)
  python main.py --method tabu          Recherche Tabou (20 clients)
  python main.py --method dp --n 15     DP sur 15 clients
  python main.py --list-methods         Liste des methodes
  python main.py --help                 Cette aide

Methodes : dp, bb, ilp, sa, tabu, grasp

Parametres alignes avec le dashboard :
  GRASP  alpha={DASHBOARD_PARAMS['grasp_alpha']}, n_iter={DASHBOARD_PARAMS['grasp_iter']}
  Tabu   tenure={DASHBOARD_PARAMS['tabu_tenure']}, neighbors={DASHBOARD_PARAMS['tabu_neighbors']}
  SA     alpha={DASHBOARD_PARAMS['sa_alpha']}, T_min={DASHBOARD_PARAMS['sa_tmin']}
  Seed   {DASHBOARD_PARAMS['seed']}

Documentation :
  START.md                    Demarrage en 30 secondes
  documentation/README.md     Documentation complete
  documentation/UTILISATION.md  Mode d'emploi
""")


# ─────────────────────────────────────────────────────────────────────────────
# Point d'entrée
# ─────────────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="Orienteering Problem - Etude Comparative",
        add_help=False
    )
    parser.add_argument("--dashboard",     action="store_true")
    parser.add_argument("--test",          action="store_true")
    parser.add_argument("--run-all",       action="store_true")
    parser.add_argument("--method",        type=str)
    parser.add_argument("--n",             type=int, default=20)
    parser.add_argument("--list-methods",  action="store_true")
    parser.add_argument("--help", "-h",    action="store_true")
    args = parser.parse_args()

    if args.help:
        show_help()
    elif args.list_methods:
        show_methods()
    elif args.test:
        run_test()
    elif args.run_all:
        run_all()
    elif args.method:
        run_method(args.method, args.n)
    else:
        launch_dashboard()

    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("\n[OK] Ferme par l'utilisateur.")
        sys.exit(0)
    except Exception as e:
        print(f"\n[ERREUR] {e}")
        sys.exit(1)