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
python main.py refresh
python main.py list --unread
python main.py read 3
python main.py tag 3 ia
python main.py list --tag ia
```

### Numéros d'articles

Le numéro affiché par `list` est une **position dans la liste courante** (1 = en
haut), pas un identifiant fixe. `read N` et `tag N` agissent sur le N-ième
article de la **dernière liste affichée** — lance donc un `list` avant. Changer
de liste renumérote : `list --unread` trie par date de publication (plus récent
en haut), `list --tag X` par ordre d'attribution du tag (plus récent en haut).

## Tests

```bash
pytest -q
```
