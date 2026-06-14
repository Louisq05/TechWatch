"""Minimal Tkinter GUI: a second view over the same model and controllers."""
import queue
import threading
import tkinter as tk
from tkinter import ttk

from ..models import db
from ..models import article as repo
from ..controllers import library

# Dark palette (editor-like) and fonts, kept in one place so the theme setup
# and the per-row colouring stay in sync.
DARK = {
    "bg": "#1e1f22",        # window / frames
    "surface": "#2b2d31",   # entries, list, status bar
    "text": "#e3e5e8",      # bright text (unread)
    "muted": "#9aa0a6",     # dimmed text (read, headings)
    "accent": "#5865f2",    # selection / pressed buttons
    "accent_hover": "#4752c4",
    "border": "#3a3c40",
}
FONT = ("Segoe UI", 10)
FONT_BOLD = ("Segoe UI", 9, "bold")


def _apply_dark_theme(root):
    """Paint the whole window with a dark palette via a tuned 'clam' theme."""
    c = DARK
    root.configure(bg=c["bg"])
    style = ttk.Style(root)
    style.theme_use("clam")  # the most styleable built-in ttk theme

    style.configure(".", background=c["bg"], foreground=c["text"], font=FONT,
                    bordercolor=c["border"], focuscolor=c["accent"])
    style.configure("TFrame", background=c["bg"])
    style.configure("TLabel", background=c["bg"], foreground=c["text"])
    style.configure("Status.TLabel", background=c["surface"],
                    foreground=c["muted"], padding=(8, 4))
    style.configure("TLabelframe", background=c["bg"], bordercolor=c["border"])
    style.configure("TLabelframe.Label", background=c["bg"],
                    foreground=c["muted"], font=FONT_BOLD)

    style.configure("TButton", background=c["surface"], foreground=c["text"],
                    bordercolor=c["surface"], padding=(10, 5), relief="flat")
    style.map("TButton",
              background=[("active", c["accent_hover"]), ("pressed", c["accent"])],
              foreground=[("active", "#ffffff")])

    style.configure("TEntry", fieldbackground=c["surface"], foreground=c["text"],
                    insertcolor=c["text"], bordercolor=c["border"], padding=4)

    style.configure("Treeview", background=c["surface"],
                    fieldbackground=c["surface"], foreground=c["text"],
                    rowheight=28, borderwidth=0, font=FONT)
    style.configure("Treeview.Heading", background=c["bg"], foreground=c["muted"],
                    font=FONT_BOLD, relief="flat", padding=6)
    style.map("Treeview.Heading", background=[("active", c["surface"])])
    style.map("Treeview", background=[("selected", c["accent"])],
              foreground=[("selected", "#ffffff")])

    style.configure("Vertical.TScrollbar", background=c["surface"],
                    troughcolor=c["bg"], bordercolor=c["bg"],
                    arrowcolor=c["muted"])


class TechwatchGUI:
    """A small window to refresh feeds, browse articles, add feeds and tag."""

    def __init__(self, root, conn):
        self.root = root
        self.conn = conn               # used only from the main thread
        self._queue = queue.Queue()    # results coming back from worker threads
        self._current_tag = None       # active tag filter; None means "all"

        root.title("techwatch")
        root.geometry("760x480")
        _apply_dark_theme(root)
        self._build_widgets()
        self._reload()
        self._poll_queue()

    # --- UI construction -----------------------------------------------------
    def _build_widgets(self):
        # Feeds: add a feed URL, or refresh every feed.
        top = ttk.LabelFrame(self.root, text="Flux")
        top.pack(fill="x", padx=8, pady=(8, 4))
        self.url_var = tk.StringVar()
        ttk.Entry(top, textvariable=self.url_var).pack(
            side="left", fill="x", expand=True, padx=4, pady=4
        )
        ttk.Button(top, text="Ajouter le flux", command=self._add_feed).pack(
            side="left", padx=4
        )
        self.refresh_btn = ttk.Button(top, text="Rafraîchir", command=self._refresh)
        self.refresh_btn.pack(side="left", padx=4)

        # Article list. The Treeview item id is the article id, so a selection
        # maps straight back to its row.
        mid = ttk.Frame(self.root)
        mid.pack(fill="both", expand=True, padx=8, pady=4)
        self.tree = ttk.Treeview(
            mid, columns=("lu", "titre"), show="headings", selectmode="browse"
        )
        self.tree.heading("lu", text="Lu")
        self.tree.heading("titre", text="Titre")
        self.tree.column("lu", width=40, anchor="center", stretch=False)
        self.tree.column("titre", anchor="w")
        # Unread rows stand out (bright), read rows are dimmed.
        self.tree.tag_configure("unread", foreground=DARK["text"])
        self.tree.tag_configure("read", foreground=DARK["muted"])
        sb = ttk.Scrollbar(mid, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=sb.set)
        self.tree.pack(side="left", fill="both", expand=True)
        sb.pack(side="right", fill="y")

        # Tagging and filtering by tag.
        bottom = ttk.LabelFrame(self.root, text="Tags")
        bottom.pack(fill="x", padx=8, pady=4)
        self.tag_var = tk.StringVar()
        ttk.Entry(bottom, textvariable=self.tag_var, width=20).pack(
            side="left", padx=4, pady=4
        )
        ttk.Button(
            bottom, text="Taguer la sélection", command=self._tag_selected
        ).pack(side="left", padx=4)
        ttk.Button(
            bottom, text="Filtrer par ce tag", command=self._filter_by_tag
        ).pack(side="left", padx=4)
        ttk.Button(bottom, text="Tout afficher", command=self._show_all).pack(
            side="left", padx=4
        )

        # Status bar.
        self.status = tk.StringVar(value="Prêt.")
        ttk.Label(
            self.root, textvariable=self.status, style="Status.TLabel", anchor="w"
        ).pack(fill="x", side="bottom")

    # --- data <-> view -------------------------------------------------------
    def _reload(self):
        """Refill the list from the database, honouring the current filter."""
        self.tree.delete(*self.tree.get_children())
        rows = repo.list_articles(self.conn, tag=self._current_tag)
        for r in rows:
            unread = not r["is_read"]
            flag = "●" if unread else ""
            self.tree.insert(
                "", "end", iid=str(r["id"]), values=(flag, r["title"]),
                tags=("unread" if unread else "read",),
            )
        scope = f"tag « {self._current_tag} »" if self._current_tag else "tous"
        self.status.set(f"{len(rows)} article(s) — {scope}.")

    # --- actions -------------------------------------------------------------
    def _add_feed(self):
        url = self.url_var.get().strip()
        if not url:
            self.status.set("Saisis une adresse de flux.")
            return
        self.status.set("Ajout du flux…")
        self.url_var.set("")
        self._run_async(lambda c: library.add_feed(c, url), self._on_feed_added)

    def _on_feed_added(self, kind, payload):
        if kind == "err":
            self.status.set(f"Erreur : {payload}")
        else:
            self.status.set(f"Flux ajouté (#{payload}).")
            self._reload()

    def _refresh(self):
        self.refresh_btn.config(state="disabled")
        self.status.set("Rafraîchissement…")
        self._run_async(library.refresh, self._on_refreshed)

    def _on_refreshed(self, kind, payload):
        self.refresh_btn.config(state="normal")
        if kind == "err":
            self.status.set(f"Erreur : {payload}")
        else:
            self.status.set(f"{payload} nouvel(s) article(s).")
            self._reload()

    def _tag_selected(self):
        sel = self.tree.selection()
        tag = self.tag_var.get().strip()
        if not sel:
            self.status.set("Sélectionne un article d'abord.")
            return
        if not tag:
            self.status.set("Saisis un tag.")
            return
        repo.add_tag(self.conn, int(sel[0]), tag)
        self.status.set(f"Article tagué « {tag} ».")

    def _filter_by_tag(self):
        tag = self.tag_var.get().strip()
        if not tag:
            self.status.set("Saisis un tag pour filtrer.")
            return
        self._current_tag = tag
        self._reload()

    def _show_all(self):
        self._current_tag = None
        self._reload()

    # --- background tasks ----------------------------------------------------
    def _run_async(self, fn, on_done):
        """Run fn(conn) in a worker thread with its own DB connection, then hand
        the result to on_done(kind, payload) back on the main thread."""
        def worker():
            try:
                c = db.connect()
                db.init_db(c)
                res = fn(c)
                c.close()
                self._queue.put((on_done, "ok", res))
            except Exception as exc:  # surface any failure in the status bar
                self._queue.put((on_done, "err", str(exc)))

        threading.Thread(target=worker, daemon=True).start()

    def _poll_queue(self):
        """Deliver worker results on the main thread (Tk is not thread-safe)."""
        try:
            on_done, kind, payload = self._queue.get_nowait()
        except queue.Empty:
            pass
        else:
            on_done(kind, payload)
        self.root.after(150, self._poll_queue)


def run(conn):
    """Launch the GUI event loop against an initialised connection."""
    root = tk.Tk()
    TechwatchGUI(root, conn)
    root.mainloop()
