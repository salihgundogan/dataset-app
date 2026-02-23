"""
gui.py — Tkinter tabanlı modern GUI modülü.
Görsel Veri Seti İndirme ve İşleme Aracı arayüzü.
"""

import os
import threading
import tkinter as tk
from tkinter import ttk, filedialog, messagebox

from downloader import download_images
from processor import process_images


class App:
    """Ana uygulama sınıfı — Tkinter GUI."""

    # Renk paleti
    BG_COLOR = "#1e1e2e"
    CARD_BG = "#2a2a3d"
    ACCENT = "#7c3aed"
    ACCENT_HOVER = "#6d28d9"
    TEXT_PRIMARY = "#e2e8f0"
    TEXT_SECONDARY = "#94a3b8"
    INPUT_BG = "#363650"
    INPUT_FG = "#f1f5f9"
    SUCCESS = "#22c55e"
    WARNING = "#f59e0b"
    ERROR = "#ef4444"
    BORDER = "#4a4a6a"

    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Görsel Veri Seti Aracı")
        self.root.geometry("560x670")
        self.root.resizable(False, False)
        self.root.configure(bg=self.BG_COLOR)

        # Değişkenler
        self.selected_dir = tk.StringVar(value="")
        self.status_text = tk.StringVar(value="Hazır")
        self.ai_enabled = tk.BooleanVar(value=False)
        self.is_running = False

        self._build_ui()
        self._center_window()

    # ── UI Oluşturma ──────────────────────────────────────────────

    def _build_ui(self):
        """Tüm UI bileşenlerini oluşturur."""
        # Ana container
        container = tk.Frame(self.root, bg=self.BG_COLOR, padx=30, pady=20)
        container.pack(fill="both", expand=True)

        # Başlık
        title = tk.Label(
            container,
            text="📸  Görsel Veri Seti Aracı",
            font=("Segoe UI", 18, "bold"),
            fg=self.TEXT_PRIMARY,
            bg=self.BG_COLOR,
        )
        title.pack(pady=(0, 5))

        subtitle = tk.Label(
            container,
            text="Bing Görseller'den toplu indirme ve format dönüştürme",
            font=("Segoe UI", 9),
            fg=self.TEXT_SECONDARY,
            bg=self.BG_COLOR,
        )
        subtitle.pack(pady=(0, 20))

        # ── Kart çerçevesi ───────────────────────────────────────
        card = tk.Frame(container, bg=self.CARD_BG, padx=24, pady=20)
        card.pack(fill="x")

        # Anahtar Kelime
        self._create_label(card, "Anahtar Kelime")
        self.entry_keyword = self._create_entry(card, "Örn: green olives")

        # Görsel Sayısı
        self._create_label(card, "Görsel Sayısı")
        self.entry_count = self._create_entry(card, "Örn: 50")

        # Başlangıç Numarası
        self._create_label(card, "Başlangıç Numarası")
        self.entry_start = self._create_entry(card, "Örn: 1")

        # Klasör Seçimi
        self._create_label(card, "İndirme Konumu")

        # Klasör yolu gösterimi — tam genişlik
        self.lbl_folder = tk.Label(
            card,
            textvariable=self.selected_dir,
            font=("Segoe UI", 10),
            fg=self.TEXT_SECONDARY,
            bg=self.INPUT_BG,
            anchor="w",
            padx=12,
            pady=10,
            relief="flat",
            highlightthickness=1,
            highlightcolor=self.ACCENT,
            highlightbackground=self.BORDER,
        )
        self.lbl_folder.pack(fill="x", pady=(0, 6))
        # Varsayılan metin
        self.selected_dir.set("Klasör seçilmedi...")

        # Klasör seç butonu — tam genişlik
        self.btn_browse = tk.Button(
            card,
            text="📁  Klasör Seç",
            font=("Segoe UI", 10, "bold"),
            fg=self.TEXT_PRIMARY,
            bg="#3d3d5c",
            activebackground=self.ACCENT,
            activeforeground=self.TEXT_PRIMARY,
            relief="flat",
            cursor="hand2",
            pady=8,
            command=self._browse_folder,
        )
        self.btn_browse.pack(fill="x", ipady=2, pady=(0, 12))

        # AI Filtreleme Toggle
        ai_frame = tk.Frame(card, bg=self.CARD_BG)
        ai_frame.pack(fill="x", pady=(0, 16))

        self.chk_ai = tk.Checkbutton(
            ai_frame,
            text="  🤖 AI Filtreleme  (Gemini 2.5 Flash)",
            variable=self.ai_enabled,
            font=("Segoe UI", 10, "bold"),
            fg=self.TEXT_PRIMARY,
            bg=self.CARD_BG,
            activebackground=self.CARD_BG,
            activeforeground=self.TEXT_PRIMARY,
            selectcolor=self.INPUT_BG,
            highlightthickness=0,
            cursor="hand2",
        )
        self.chk_ai.pack(side="left")

        ai_hint = tk.Label(
            ai_frame,
            text="Uygun olmayan görselleri eler",
            font=("Segoe UI", 8),
            fg=self.TEXT_SECONDARY,
            bg=self.CARD_BG,
        )
        ai_hint.pack(side="right")

        # Ayırıcı çizgi
        sep = ttk.Separator(card, orient="horizontal")
        sep.pack(fill="x", pady=(4, 16))

        # İndir & İşle Butonu
        self.btn_start = tk.Button(
            card,
            text="⬇  İndir & İşle",
            font=("Segoe UI", 12, "bold"),
            fg="#ffffff",
            bg=self.ACCENT,
            activebackground=self.ACCENT_HOVER,
            activeforeground="#ffffff",
            relief="flat",
            cursor="hand2",
            pady=10,
            command=self._on_start,
        )
        self.btn_start.pack(fill="x", ipady=2)

        # ── Durum alanı ──────────────────────────────────────────
        status_frame = tk.Frame(container, bg=self.BG_COLOR, pady=14)
        status_frame.pack(fill="x")

        self.lbl_status = tk.Label(
            status_frame,
            textvariable=self.status_text,
            font=("Segoe UI", 10),
            fg=self.TEXT_SECONDARY,
            bg=self.BG_COLOR,
        )
        self.lbl_status.pack()

        # İlerleme çubuğu
        style = ttk.Style()
        style.theme_use("clam")
        style.configure(
            "Custom.Horizontal.TProgressbar",
            troughcolor=self.CARD_BG,
            background=self.ACCENT,
            thickness=6,
        )
        self.progress = ttk.Progressbar(
            status_frame,
            style="Custom.Horizontal.TProgressbar",
            mode="indeterminate",
            length=400,
        )
        self.progress.pack(pady=(8, 0))

    def _create_label(self, parent, text: str):
        """Etiket oluşturur."""
        lbl = tk.Label(
            parent,
            text=text,
            font=("Segoe UI", 10, "bold"),
            fg=self.TEXT_PRIMARY,
            bg=self.CARD_BG,
            anchor="w",
        )
        lbl.pack(fill="x", pady=(0, 4))

    def _create_entry(self, parent, placeholder: str) -> tk.Entry:
        """Placeholder'lı Entry oluşturur."""
        entry = tk.Entry(
            parent,
            font=("Segoe UI", 10),
            fg=self.TEXT_SECONDARY,
            bg=self.INPUT_BG,
            insertbackground=self.INPUT_FG,
            relief="flat",
            highlightthickness=1,
            highlightcolor=self.ACCENT,
            highlightbackground=self.BORDER,
        )
        entry.pack(fill="x", ipady=8, pady=(0, 12))

        # Placeholder davranışı
        entry.insert(0, placeholder)
        entry._placeholder = placeholder
        entry._has_placeholder = True

        entry.bind("<FocusIn>", lambda e, ent=entry: self._on_focus_in(ent))
        entry.bind("<FocusOut>", lambda e, ent=entry: self._on_focus_out(ent))

        return entry

    def _on_focus_in(self, entry: tk.Entry):
        """Entry odaklandığında placeholder'ı kaldır."""
        if entry._has_placeholder:
            entry.delete(0, tk.END)
            entry.config(fg=self.INPUT_FG)
            entry._has_placeholder = False

    def _on_focus_out(self, entry: tk.Entry):
        """Entry odağını kaybettiğinde boşsa placeholder'ı geri koy."""
        if not entry.get().strip():
            entry.delete(0, tk.END)
            entry.insert(0, entry._placeholder)
            entry.config(fg=self.TEXT_SECONDARY)
            entry._has_placeholder = True

    # ── İşlemler ──────────────────────────────────────────────────

    def _browse_folder(self):
        """Klasör seçme diyaloğunu açar."""
        folder = filedialog.askdirectory(title="İndirme Konumunu Seç")
        if folder:
            self.selected_dir.set(folder)
            self.lbl_folder.config(fg=self.TEXT_PRIMARY)

    def _get_keyword(self) -> str:
        """Entry'den anahtar kelimeyi alır (placeholder hariç)."""
        val = self.entry_keyword.get().strip()
        if self.entry_keyword._has_placeholder or not val:
            return ""
        return val

    def _get_count(self) -> int | None:
        """Entry'den görsel sayısını alır."""
        val = self.entry_count.get().strip()
        if self.entry_count._has_placeholder or not val:
            return None
        try:
            num = int(val)
            return num if num > 0 else None
        except ValueError:
            return None

    def _get_start_index(self) -> int | None:
        """Entry'den başlangıç numarasını alır."""
        val = self.entry_start.get().strip()
        if self.entry_start._has_placeholder or not val:
            return 1  # Varsayılan değer
        try:
            num = int(val)
            return num if num > 0 else None
        except ValueError:
            return None

    def _validate_inputs(self) -> tuple[str, int, str] | None:
        """
        Kullanıcı girdilerini doğrular.
        Başarılıysa (keyword, count, directory, start_index) döndürür, değilse None.
        """
        keyword = self._get_keyword()
        if not keyword:
            messagebox.showwarning(
                "Eksik Alan", "Lütfen bir anahtar kelime girin."
            )
            return None

        count = self._get_count()
        if count is None:
            messagebox.showwarning(
                "Geçersiz Sayı",
                "Lütfen geçerli bir görsel sayısı girin (pozitif tam sayı).",
            )
            return None

        start_index = self._get_start_index()
        if start_index is None:
            messagebox.showwarning(
                "Geçersiz Numara",
                "Lütfen geçerli bir başlangıç numarası girin (pozitif tam sayı).",
            )
            return None

        directory = self.selected_dir.get()
        if not directory or directory == "Klasör seçilmedi...":
            messagebox.showwarning(
                "Klasör Seçilmedi", "Lütfen bir indirme konumu seçin."
            )
            return None

        if not os.path.isdir(directory):
            messagebox.showerror(
                "Geçersiz Dizin",
                f"Seçilen klasör bulunamadı:\n{directory}",
            )
            return None

        return keyword, count, directory, start_index

    def _on_start(self):
        """İndir & İşle butonuna tıklandığında çalışır."""
        if self.is_running:
            return

        result = self._validate_inputs()
        if result is None:
            return

        keyword, count, directory, start_index = result
        ai_on = self.ai_enabled.get()

        # UI'ı kilitle
        self._set_running(True)
        self._update_status("⏳ İndirme başlıyor...", self.WARNING)

        # Arka plan thread'i
        thread = threading.Thread(
            target=self._worker,
            args=(keyword, count, directory, start_index, ai_on),
            daemon=True,
        )
        thread.start()

    def _worker(self, keyword: str, count: int, directory: str, start_index: int, ai_on: bool):
        """Arka planda indirme ve dönüştürme işlemini yürütür."""
        try:
            # 1. İndirme
            self.root.after(0, self._update_status, "⬇  Görseller indiriliyor...", self.WARNING)
            self.root.after(0, self.progress.start, 12)

            download_images(keyword, count, directory)

            # 2. Dönüştürme (+ AI filtreleme)
            if ai_on:
                self.root.after(0, self._update_status, "🤖 AI ile filtreleniyor...", self.WARNING)
            else:
                self.root.after(0, self._update_status, "🔄 Görseller dönüştürülüyor...", self.WARNING)

            def status_cb(msg):
                self.root.after(0, self._update_status, msg, self.WARNING)

            processed = process_images(
                directory,
                start_index=start_index,
                ai_filter_enabled=ai_on,
                keyword=keyword,
                status_callback=status_cb,
            )

            # 3. Tamamlandı
            self.root.after(0, self.progress.stop)
            self.root.after(
                0,
                self._update_status,
                f"✅ Tamamlandı! {processed} görsel işlendi.",
                self.SUCCESS,
            )

        except Exception as e:
            self.root.after(0, self.progress.stop)
            self.root.after(
                0,
                self._update_status,
                f"❌ Hata oluştu!",
                self.ERROR,
            )
            self.root.after(
                0,
                lambda: messagebox.showerror("Hata", str(e)),
            )

        finally:
            self.root.after(0, self._set_running, False)

    # ── Yardımcılar ──────────────────────────────────────────────

    def _update_status(self, text: str, color: str):
        """Durum metnini ve rengini günceller."""
        self.status_text.set(text)
        self.lbl_status.config(fg=color)

    def _set_running(self, running: bool):
        """UI elemanlarını çalışma durumuna göre aktif/pasif yapar."""
        self.is_running = running
        state = "disabled" if running else "normal"
        self.btn_start.config(state=state)
        self.btn_browse.config(state=state)
        self.entry_keyword.config(state=state)
        self.entry_count.config(state=state)
        self.entry_start.config(state=state)
        self.chk_ai.config(state=state)

        if not running:
            self.progress.stop()

    def _center_window(self):
        """Pencereyi ekranın ortasına konumlandırır."""
        self.root.update_idletasks()
        w = self.root.winfo_width()
        h = self.root.winfo_height()
        x = (self.root.winfo_screenwidth() // 2) - (w // 2)
        y = (self.root.winfo_screenheight() // 2) - (h // 2)
        self.root.geometry(f"{w}x{h}+{x}+{y}")

    def run(self):
        """Uygulamayı başlatır."""
        self.root.mainloop()
