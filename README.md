# techwatch

Aggregator CLI de veille tech : suit des flux RSS, stocke les articles dans
SQLite, permet de les taguer et de les marquer comme lus.

## Installation

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
```

## Utilisation

```bash
python main.py add-feed https://example.com/feed.xml
python main.py import-feeds          # ajoute toutes les sources de feeds.txt
python main.py refresh
python main.py list --unread
python main.py read 3
python main.py tag 3 ia
python main.py list --tag ia
```

Les sources suivies sont listées dans **`feeds.txt`** (une URL par ligne) ;
`import-feeds` les ajoute toutes d'un coup — pratique pour repartir d'une base
vide ou sur une autre machine.

### Numéros d'articles

Le numéro affiché par `list` est une **position dans la liste courante** (1 = en
haut), pas un identifiant fixe. `read N` et `tag N` agissent sur le N-ième
article de la **dernière liste affichée** — lance donc un `list` avant. Changer
de liste renumérote : `list --unread` trie par date de publication (plus récent
en haut), `list --tag X` par ordre d'attribution du tag (plus récent en haut).

## Automatisation

Le pipeline `techwatch/pipeline.py` récupère les nouveautés puis envoie un
rapport par e-mail (voir ci-dessous). Pour le lancer à la main :

```bash
python auto.py          # ou : python -m techwatch.pipeline
```

Chaque exécution est journalisée dans `techwatch.log` (à la racine du projet).

Pour l'exécuter **tous les matins à 8h** via le Planificateur de tâches Windows :

```powershell
powershell -ExecutionPolicy Bypass -File install_task.ps1
```

Le script crée la tâche `TechwatchRefresh` (compatible portable/batterie, avec
rattrapage si la machine était éteinte). Pour la supprimer :

```powershell
Unregister-ScheduledTask -TaskName "TechwatchRefresh" -Confirm:$false
```

## Tri de pertinence

Chaque article reçoit un score de pertinence (`techwatch/controllers/ranking.py`),
entièrement piloté par le fichier **`ranking.toml`** que tu édites : thèmes et
mots-clés (poids positif pour remonter, négatif pour enfoncer), bonus par
source, et fraîcheur. Le matching se fait sur le titre (mot entier, insensible à
la casse/accents). Le rapport par e-mail n'envoie que les mieux classés.

## Rapport par e-mail

Après chaque refresh, le pipeline envoie par e-mail les articles arrivés depuis
le dernier rapport (jamais deux fois le même). La configuration se fait via un
fichier `.env` à la racine, **ignoré par git** :

```bash
cp .env.example .env     # puis renseigne tes valeurs
```

Pour Gmail : active la validation en 2 étapes puis crée un *mot de passe
d'application* (https://myaccount.google.com/apppasswords) et reporte-le dans
`TECHWATCH_SMTP_PASSWORD`. Si le SMTP n'est pas configuré, le refresh fonctionne
quand même — seul l'envoi est ignoré (un avertissement est journalisé).

## Tests

```bash
pytest -q
```
