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

## Tests

```bash
pytest -q
```
