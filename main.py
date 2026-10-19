import customtkinter as ctk
import tkinter as tk
from tkinter import messagebox
import sqlite3
from pathlib import Path
from datetime import date, datetime, timedelta
import calendar as cal


# MYPA - My Personal Assistant Pro | Version 2.5
# Tasks + Calendar + Notes + AI Assistant + Settings
# Modernized with CustomTkinter


BASE_DIR = Path(__file__).resolve().parent
DB_PATH = BASE_DIR / "mypa.db"

#Database Initialization
db = sqlite3.connect(str(DB_PATH))
db.execute("PRAGMA foreign_keys = ON")
cur = db.cursor()

# Ensure tables exist and schema migrations are applied
cur.execute("""
CREATE TABLE IF NOT EXISTS tasks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    done INTEGER NOT NULL DEFAULT 0,
    deadline TEXT,
    priority TEXT DEFAULT 'Sedang'
)
""")
cur.execute("PRAGMA table_info(tasks)")
task_cols = [r[1] for r in cur.fetchall()]
if "deadline" not in task_cols:
    cur.execute("ALTER TABLE tasks ADD COLUMN deadline TEXT")
if "priority" not in task_cols:
    cur.execute("ALTER TABLE tasks ADD COLUMN priority TEXT DEFAULT 'Sedang'")

cur.execute("""
CREATE TABLE IF NOT EXISTS events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    event_date TEXT NOT NULL,
    title TEXT NOT NULL,
    details TEXT DEFAULT ''
)
""")

cur.execute("""
CREATE TABLE IF NOT EXISTS notes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    content TEXT DEFAULT '',
    updated_at TEXT NOT NULL
)
""")

cur.execute("""
CREATE TABLE IF NOT EXISTS settings (
    key TEXT PRIMARY KEY,
    value TEXT NOT NULL
)
""")
db.commit()


def setting_get(key, default=""):
    row = db.execute("SELECT value FROM settings WHERE key=?", (key,)).fetchone()
    return row[0] if row else default


def setting_set(key, value):
    db.execute(
        "INSERT INTO settings(key, value) VALUES(?, ?) "
        "ON CONFLICT(key) DO UPDATE SET value=excluded.value",
        (key, str(value))
    )
    db.commit()


#App Appearance Configuration
initial_theme = setting_get("theme", "Dark")
ctk.set_appearance_mode(initial_theme)
ctk.set_default_color_theme("blue")

root = ctk.CTk()
root.title("MYPA - My Personal Assistant Pro")
root.geometry("1200x780")
root.minsize(1040, 700)

# Colors Palette: (Light Mode, Dark Mode)
CARD_BG = ("#FFFFFF", "#1E293B")
CARD_BORDER = ("#E2E8F0", "#334155")
SIDEBAR_BG = ("#F1F5F9", "#0F172A")
MAIN_BG = ("#F8FAFC", "#0B1120")
TEXT_PRIMARY = ("#0F172A", "#F8FAFC")
TEXT_MUTED = ("#64748B", "#94A3B8")

ACCENT_COLOR = "#6366F1"        # Modern Indigo
ACCENT_HOVER = "#4F46E5"
SUCCESS_COLOR = "#10B981"       # Emerald
SUCCESS_HOVER = "#059669"
DANGER_COLOR = "#EF4444"        # Rose Red
DANGER_HOVER = "#DC2626"
WARNING_COLOR = "#F59E0B"       # Amber
WARNING_HOVER = "#D97706"

current_page = "Dashboard"
selected_cal_date = date.today()
cal_year = date.today().year
cal_month = date.today().month
selected_note_id = None

#Layout Containers
# Sidebar
sidebar = ctk.CTkFrame(root, width=240, corner_radius=0, fg_color=SIDEBAR_BG)
sidebar.pack(side="left", fill="y")
sidebar.pack_propagate(False)

# App Brand
brand_frame = ctk.CTkFrame(sidebar, fg_color="transparent")
brand_frame.pack(fill="x", padx=20, pady=(24, 20))

brand_badge = ctk.CTkLabel(
    brand_frame, text="✨ MYPA",
    font=ctk.CTkFont(family="Segoe UI", size=24, weight="bold"),
    text_color=ACCENT_COLOR
)
brand_badge.pack(anchor="w")

sub_brand = ctk.CTkLabel(
    brand_frame, text="Productivity Suite v2.5",
    font=ctk.CTkFont(family="Segoe UI", size=11),
    text_color=TEXT_MUTED
)
sub_brand.pack(anchor="w")

# Main Content Area
main_area = ctk.CTkFrame(root, fg_color=MAIN_BG, corner_radius=0)
main_area.pack(side="right", fill="both", expand=True)

# Top Bar inside Main Area
topbar = ctk.CTkFrame(main_area, fg_color="transparent", height=55)
topbar.pack(fill="x", padx=28, pady=(18, 10))

page_title_label = ctk.CTkLabel(
    topbar, text="Dashboard",
    font=ctk.CTkFont(family="Segoe UI", size=24, weight="bold"),
    text_color=TEXT_PRIMARY
)
page_title_label.pack(side="left")

# Quick Theme Switcher Button in Header
def toggle_quick_theme():
    curr = ctk.get_appearance_mode()
    new_theme = "Light" if curr == "Dark" else "Dark"
    ctk.set_appearance_mode(new_theme)
    setting_set("theme", new_theme)
    quick_theme_btn.configure(text="🌙 Dark Mode" if new_theme == "Light" else "☀️ Light Mode")
    if current_page == "Settings":
        theme_segmented.set(new_theme)

curr_mode = ctk.get_appearance_mode()
quick_theme_btn = ctk.CTkButton(
    topbar,
    text="☀️ Light Mode" if curr_mode == "Dark" else "🌙 Dark Mode",
    width=120, height=32, corner_radius=16,
    fg_color=CARD_BG, hover_color=CARD_BORDER,
    text_color=TEXT_PRIMARY,
    font=ctk.CTkFont(family="Segoe UI", size=11, weight="bold"),
    command=toggle_quick_theme
)
quick_theme_btn.pack(side="right", padx=(10, 0))

date_badge = ctk.CTkLabel(
    topbar,
    text=datetime.now().strftime("%A, %d %B %Y"),
    font=ctk.CTkFont(family="Segoe UI", size=12),
    text_color=TEXT_MUTED
)
date_badge.pack(side="right")

# Page Content Holder
page_container = ctk.CTkFrame(main_area, fg_color="transparent")
page_container.pack(fill="both", expand=True, padx=28, pady=(0, 20))

pages = {}
nav_buttons = {}


def register_page(name):
    frame = ctk.CTkFrame(page_container, fg_color="transparent")
    pages[name] = frame
    return frame


def switch_page(name):
    global current_page
    current_page = name
    for p_name, frame in pages.items():
        if p_name == name:
            frame.pack(fill="both", expand=True)
        else:
            frame.pack_forget()

    page_title_label.configure(text=name)

    # Update active state of sidebar buttons
    for btn_name, btn in nav_buttons.items():
        if btn_name == name:
            btn.configure(
                fg_color=ACCENT_COLOR,
                hover_color=ACCENT_HOVER,
                text_color="#FFFFFF"
            )
        else:
            btn.configure(
                fg_color="transparent",
                hover_color=("rgba(0,0,0,0.06)", "rgba(255,255,255,0.06)"),
                text_color=TEXT_PRIMARY
            )

    # Page-specific refresh handlers
    if name == "Dashboard":
        update_dashboard()
    elif name == "Tasks":
        refresh_tasks()
    elif name == "Calendar":
        render_calendar()
    elif name == "Notes":
        refresh_notes()
    elif name == "Settings":
        load_settings()


# Navigation Items
nav_items = [
    ("Dashboard", "📊  Dashboard"),
    ("Tasks", "✅  Tugas & Deadline"),
    ("Calendar", "📅  Kalender Agenda"),
    ("Notes", "📝  Catatan"),
    ("AI Assistant", "🤖  AI Asisten"),
    ("Settings", "⚙️  Pengaturan")
]

nav_box = ctk.CTkFrame(sidebar, fg_color="transparent")
nav_box.pack(fill="x", padx=12, pady=0)

for key, label in nav_items:
    btn = ctk.CTkButton(
        nav_box, text=label,
        anchor="w",
        height=42,
        corner_radius=10,
        font=ctk.CTkFont(family="Segoe UI", size=13, weight="bold"),
        fg_color="transparent",
        text_color=TEXT_PRIMARY,
        command=lambda k=key: switch_page(k)
    )
    btn.pack(fill="x", pady=4)
    nav_buttons[key] = btn

# Sidebar Footer
sidebar_footer = ctk.CTkFrame(sidebar, fg_color=CARD_BG, corner_radius=12, border_width=1, border_color=CARD_BORDER)
sidebar_footer.pack(side="bottom", fill="x", padx=14, pady=16)

user_badge_text = ctk.CTkLabel(
    sidebar_footer,
    text=f"👤 {setting_get('username', 'Inka Kristiani')}",
    font=ctk.CTkFont(family="Segoe UI", size=12, weight="bold"),
    text_color=TEXT_PRIMARY
)
user_badge_text.pack(anchor="w", padx=12, pady=(10, 2))

status_dot_label = ctk.CTkLabel(
    sidebar_footer,
    text="🟢 Sistem Siap & Aktif",
    font=ctk.CTkFont(family="Segoe UI", size=10),
    text_color=SUCCESS_COLOR
)
status_dot_label.pack(anchor="w", padx=12, pady=(0, 10))



#DASHBOARD

dash_page = register_page("Dashboard")

dash_scroll = ctk.CTkScrollableFrame(dash_page, fg_color="transparent")
dash_scroll.pack(fill="both", expand=True)

# Greeting Banner
welcome_banner = ctk.CTkFrame(dash_scroll, fg_color=CARD_BG, corner_radius=14, border_width=1, border_color=CARD_BORDER)
welcome_banner.pack(fill="x", pady=(0, 16))

welcome_label = ctk.CTkLabel(
    welcome_banner,
    text=f"Selamat Datang, {setting_get('username', 'Inka Kristiani')}! 👋",
    font=ctk.CTkFont(family="Segoe UI", size=20, weight="bold"),
    text_color=TEXT_PRIMARY
)
welcome_label.pack(anchor="w", padx=20, pady=(16, 4))

welcome_sub = ctk.CTkLabel(
    welcome_banner,
    text="Berikut adalah ringkasan produktivitas, tugas tertunda, dan jadwal acara Anda hari ini.",
    font=ctk.CTkFont(family="Segoe UI", size=12),
    text_color=TEXT_MUTED
)
welcome_sub.pack(anchor="w", padx=20, pady=(0, 16))

# Stats Grid (4 Cards)
stats_grid = ctk.CTkFrame(dash_scroll, fg_color="transparent")
stats_grid.pack(fill="x", pady=(0, 16))
for i in range(4):
    stats_grid.columnconfigure(i, weight=1)


def create_stat_card(parent, col, title, initial_val, color_accent, subtext=""):
    card = ctk.CTkFrame(parent, fg_color=CARD_BG, corner_radius=12, border_width=1, border_color=CARD_BORDER)
    card.grid(row=0, column=col, padx=6 if col in (1, 2) else (0 if col == 0 else 0), sticky="ew")

    lbl_title = ctk.CTkLabel(card, text=title, font=ctk.CTkFont(family="Segoe UI", size=11, weight="bold"), text_color=TEXT_MUTED)
    lbl_title.pack(anchor="w", padx=16, pady=(14, 2))

    lbl_val = ctk.CTkLabel(card, text=initial_val, font=ctk.CTkFont(family="Segoe UI", size=28, weight="bold"), text_color=color_accent)
    lbl_val.pack(anchor="w", padx=16, pady=(0, 2))

    lbl_sub = ctk.CTkLabel(card, text=subtext, font=ctk.CTkFont(family="Segoe UI", size=10), text_color=TEXT_MUTED)
    lbl_sub.pack(anchor="w", padx=16, pady=(0, 12))
    return lbl_val, card


total_task_lbl, _ = create_stat_card(stats_grid, 0, "TOTAL TUGAS", "0", ACCENT_COLOR, "Semua tugas tersimpan")
done_task_lbl, _ = create_stat_card(stats_grid, 1, "SELESAI", "0", SUCCESS_COLOR, "Telah diselesaikan")
pending_task_lbl, _ = create_stat_card(stats_grid, 2, "MENUNGGU", "0", DANGER_COLOR, "Perlu diselesaikan")
progress_lbl, progress_card = create_stat_card(stats_grid, 3, "PROGRES", "0%", WARNING_COLOR, "Rasio penyelesaian")

dash_progress_bar = ctk.CTkProgressBar(progress_card, height=8, corner_radius=4, progress_color=SUCCESS_COLOR)
dash_progress_bar.pack(fill="x", padx=16, pady=(0, 14))
dash_progress_bar.set(0)

# Two-column Dashboard Details
dash_cols = ctk.CTkFrame(dash_scroll, fg_color="transparent")
dash_cols.pack(fill="both", expand=True)
dash_cols.columnconfigure(0, weight=3)
dash_cols.columnconfigure(1, weight=2)

# Column 1: Today's Agenda Card
today_card = ctk.CTkFrame(dash_cols, fg_color=CARD_BG, corner_radius=12, border_width=1, border_color=CARD_BORDER)
today_card.grid(row=0, column=0, sticky="nsew", padx=(0, 10))

today_header = ctk.CTkLabel(
    today_card, text="📌 Agenda & Tenggat Hari Ini",
    font=ctk.CTkFont(family="Segoe UI", size=15, weight="bold"),
    text_color=TEXT_PRIMARY
)
today_header.pack(anchor="w", padx=18, pady=(16, 12))

today_container = ctk.CTkFrame(today_card, fg_color="transparent")
today_container.pack(fill="both", expand=True, padx=18, pady=(0, 16))

# Column 2: Quick Actions & Priorities Card
action_card = ctk.CTkFrame(dash_cols, fg_color=CARD_BG, corner_radius=12, border_width=1, border_color=CARD_BORDER)
action_card.grid(row=0, column=1, sticky="nsew", padx=(0, 0))

action_header = ctk.CTkLabel(
    action_card, text="⚡ Aksi Cepat & Pintasan",
    font=ctk.CTkFont(family="Segoe UI", size=15, weight="bold"),
    text_color=TEXT_PRIMARY
)
action_header.pack(anchor="w", padx=18, pady=(16, 12))

quick_btn_frame = ctk.CTkFrame(action_card, fg_color="transparent")
quick_btn_frame.pack(fill="x", padx=18, pady=(0, 16))

ctk.CTkButton(
    quick_btn_frame, text="+ Tambah Tugas Baru",
    font=ctk.CTkFont(family="Segoe UI", size=12, weight="bold"),
    fg_color=ACCENT_COLOR, hover_color=ACCENT_HOVER,
    height=36, corner_radius=8,
    command=lambda: open_task_modal()
).pack(fill="x", pady=(0, 8))

ctk.CTkButton(
    quick_btn_frame, text="+ Tambah Acara Kalender",
    font=ctk.CTkFont(family="Segoe UI", size=12, weight="bold"),
    fg_color=CARD_BORDER, text_color=TEXT_PRIMARY,
    hover_color=ACCENT_COLOR,
    height=36, corner_radius=8,
    command=lambda: switch_page("Calendar")
).pack(fill="x", pady=(0, 8))

ctk.CTkButton(
    quick_btn_frame, text="+ Buat Catatan Cepat",
    font=ctk.CTkFont(family="Segoe UI", size=12, weight="bold"),
    fg_color=CARD_BORDER, text_color=TEXT_PRIMARY,
    hover_color=ACCENT_COLOR,
    height=36, corner_radius=8,
    command=lambda: (switch_page("Notes"), new_note())
).pack(fill="x")

priority_box = ctk.CTkFrame(action_card, fg_color="transparent")
priority_box.pack(fill="x", padx=18, pady=(10, 16))

priority_title = ctk.CTkLabel(
    priority_box, text="Ringkasan Prioritas Tugas Aktif:",
    font=ctk.CTkFont(family="Segoe UI", size=12, weight="bold"),
    text_color=TEXT_PRIMARY
)
priority_title.pack(anchor="w", pady=(0, 8))

priority_counts_lbl = ctk.CTkLabel(
    priority_box, text="",
    font=ctk.CTkFont(family="Segoe UI", size=11),
    text_color=TEXT_MUTED, justify="left"
)
priority_counts_lbl.pack(anchor="w")


def update_dashboard():
    # Update greeting
    uname = setting_get("username", "Inka Kristiani")
    welcome_label.configure(text=f"Selamat Datang, {uname}! 👋")
    user_badge_text.configure(text=f"👤 {uname}")

    # Fetch tasks
    rows = db.execute("SELECT done, deadline, name, priority FROM tasks").fetchall()
    total = len(rows)
    completed = sum(1 for r in rows if r[0])
    pending = total - completed
    pct = int((completed / total * 100)) if total > 0 else 0

    total_task_lbl.configure(text=str(total))
    done_task_lbl.configure(text=str(completed))
    pending_task_lbl.configure(text=str(pending))
    progress_lbl.configure(text=f"{pct}%")
    dash_progress_bar.set(pct / 100.0 if total > 0 else 0)

    # Active priority count
    high_cnt = sum(1 for r in rows if not r[0] and r[3] == "Tinggi")
    med_cnt = sum(1 for r in rows if not r[0] and r[3] == "Sedang")
    low_cnt = sum(1 for r in rows if not r[0] and r[3] == "Rendah")
    priority_counts_lbl.configure(
        text=f"🔴 Prioritas Tinggi: {high_cnt}\n🟡 Prioritas Sedang: {med_cnt}\n🟢 Prioritas Rendah: {low_cnt}"
    )

    # Today's agenda
    for w in today_container.winfo_children():
        w.destroy()

    today_str = date.today().isoformat()
    tasks_today = [r for r in rows if r[1] == today_str]
    events_today = db.execute(
        "SELECT id, title, details FROM events WHERE event_date=? ORDER BY id", (today_str,)
    ).fetchall()

    if not tasks_today and not events_today:
        empty_lbl = ctk.CTkLabel(
            today_container,
            text="🎉 Tidak ada jadwal acara atau batas waktu tugas hari ini!\nSemua terkelola dengan baik.",
            font=ctk.CTkFont(family="Segoe UI", size=12),
            text_color=TEXT_MUTED, justify="center"
        )
        empty_lbl.pack(pady=20)
    else:
        if tasks_today:
            ctk.CTkLabel(
                today_container, text="Tugas Jatuh Tempo Hari Ini:",
                font=ctk.CTkFont(family="Segoe UI", size=11, weight="bold"),
                text_color=ACCENT_COLOR
            ).pack(anchor="w", pady=(2, 4))

            for done, dline, name, prio in tasks_today:
                item_row = ctk.CTkFrame(today_container, fg_color=CARD_BORDER, corner_radius=6, height=30)
                item_row.pack(fill="x", pady=2)
                status_icon = "✅" if done else "⏳"
                ctk.CTkLabel(
                    item_row, text=f" {status_icon} {name}",
                    font=ctk.CTkFont(family="Segoe UI", size=11),
                    text_color=TEXT_PRIMARY
                ).pack(side="left", padx=8, pady=4)

        if events_today:
            ctk.CTkLabel(
                today_container, text="Acara Kalender Hari Ini:",
                font=ctk.CTkFont(family="Segoe UI", size=11, weight="bold"),
                text_color=SUCCESS_COLOR
            ).pack(anchor="w", pady=(10, 4))

            for eid, title, details in events_today:
                item_row = ctk.CTkFrame(today_container, fg_color=CARD_BORDER, corner_radius=6, height=30)
                item_row.pack(fill="x", pady=2)
                ctk.CTkLabel(
                    item_row, text=f" 📅 {title}" + (f" ({details})" if details else ""),
                    font=ctk.CTkFont(family="Segoe UI", size=11),
                    text_color=TEXT_PRIMARY
                ).pack(side="left", padx=8, pady=4)



#TASKS

tasks_page = register_page("Tasks")

# Tasks Top Bar (Search, Filters, New Task Button)
tasks_toolbar = ctk.CTkFrame(tasks_page, fg_color="transparent")
tasks_toolbar.pack(fill="x", pady=(0, 14))

task_search_var = ctk.StringVar()
task_search_entry = ctk.CTkEntry(
    tasks_toolbar,
    placeholder_text="🔍 Cari tugas...",
    textvariable=task_search_var,
    width=260, height=38, corner_radius=8
)
task_search_entry.pack(side="left", padx=(0, 10))

task_filter_seg = ctk.CTkSegmentedButton(
    tasks_toolbar,
    values=["Semua", "Aktif", "Selesai"],
    height=38, corner_radius=8,
    command=lambda _: refresh_tasks()
)
task_filter_seg.set("Semua")
task_filter_seg.pack(side="left", padx=(0, 10))

task_priority_filter = ctk.CTkOptionMenu(
    tasks_toolbar,
    values=["Semua Prioritas", "Tinggi", "Sedang", "Rendah"],
    height=38, corner_radius=8,
    command=lambda _: refresh_tasks()
)
task_priority_filter.set("Semua Prioritas")
task_priority_filter.pack(side="left")

new_task_btn = ctk.CTkButton(
    tasks_toolbar,
    text="+ Tambah Tugas",
    font=ctk.CTkFont(family="Segoe UI", size=12, weight="bold"),
    fg_color=ACCENT_COLOR, hover_color=ACCENT_HOVER,
    height=38, corner_radius=8,
    command=lambda: open_task_modal()
)
new_task_btn.pack(side="right")

# Scrollable Task Cards Container
tasks_scroll = ctk.CTkScrollableFrame(tasks_page, fg_color="transparent")
tasks_scroll.pack(fill="both", expand=True)


def get_all_tasks():
    rows = db.execute("SELECT id, name, done, deadline, priority FROM tasks ORDER BY done ASC, id DESC").fetchall()
    return [{"id": r[0], "name": r[1], "done": bool(r[2]), "deadline": r[3] or "", "priority": r[4] or "Sedang"} for r in rows]


def toggle_task_status(task_id, current_done):
    new_val = 0 if current_done else 1
    db.execute("UPDATE tasks SET done=? WHERE id=?", (new_val, task_id))
    db.commit()
    refresh_tasks()
    update_dashboard()


def delete_task_by_id(task_id, task_name):
    if messagebox.askyesno("Hapus Tugas", f"Yakin ingin menghapus tugas:\n'{task_name}'?"):
        db.execute("DELETE FROM tasks WHERE id=?", (task_id,))
        db.commit()
        refresh_tasks()
        update_dashboard()


def refresh_tasks():
    for w in tasks_scroll.winfo_children():
        w.destroy()

    query = task_search_var.get().strip().lower()
    filter_status = task_filter_seg.get()
    filter_prio = task_priority_filter.get()

    all_tasks = get_all_tasks()
    filtered = []
    for t in all_tasks:
        if query and query not in t["name"].lower():
            continue
        if filter_status == "Aktif" and t["done"]:
            continue
        if filter_status == "Selesai" and not t["done"]:
            continue
        if filter_prio != "Semua Prioritas" and t["priority"] != filter_prio:
            continue
        filtered.append(t)

    if not filtered:
        empty_card = ctk.CTkFrame(tasks_scroll, fg_color=CARD_BG, corner_radius=12, border_width=1, border_color=CARD_BORDER)
        empty_card.pack(fill="x", pady=20)
        ctk.CTkLabel(
            empty_card,
            text="Tidak ada tugas yang sesuai kriteria pencarian / filter.",
            font=ctk.CTkFont(family="Segoe UI", size=13),
            text_color=TEXT_MUTED
        ).pack(pady=24)
        return

    today_str = date.today().isoformat()

    for t in filtered:
        card = ctk.CTkFrame(tasks_scroll, fg_color=CARD_BG, corner_radius=10, border_width=1, border_color=CARD_BORDER)
        card.pack(fill="x", pady=4)

        # Checkbox & Task Name
        cb_val = ctk.BooleanVar(value=t["done"])
        cb = ctk.CTkCheckBox(
            card,
            text=t["name"],
            variable=cb_val,
            onvalue=True, offvalue=False,
            font=ctk.CTkFont(
                family="Segoe UI", size=13,
                weight="normal" if not t["done"] else "normal",
                slant="italic" if t["done"] else "roman"
            ),
            text_color=TEXT_MUTED if t["done"] else TEXT_PRIMARY,
            checkmark_color="#FFFFFF",
            fg_color=SUCCESS_COLOR,
            command=lambda tid=t["id"], cur=t["done"]: toggle_task_status(tid, cur)
        )
        cb.pack(side="left", padx=(14, 10), pady=12, fill="x", expand=True)

        # Priority Badge
        prio_color = DANGER_COLOR if t["priority"] == "Tinggi" else (WARNING_COLOR if t["priority"] == "Sedang" else SUCCESS_COLOR)
        prio_badge = ctk.CTkLabel(
            card,
            text=f"● {t['priority']}",
            font=ctk.CTkFont(family="Segoe UI", size=11, weight="bold"),
            text_color=prio_color
        )
        prio_badge.pack(side="left", padx=10)

        # Deadline Badge
        dline = t["deadline"]
        if dline:
            is_overdue = (not t["done"]) and (dline < today_str)
            dline_color = DANGER_COLOR if is_overdue else TEXT_MUTED
            dline_text = f"⚠️ Terlambat: {dline}" if is_overdue else f"📅 {dline}"
        else:
            dline_color = TEXT_MUTED
            dline_text = "📅 Tanpa batas"

        dline_lbl = ctk.CTkLabel(
            card, text=dline_text,
            font=ctk.CTkFont(family="Segoe UI", size=11),
            text_color=dline_color
        )
        dline_lbl.pack(side="left", padx=10)

        # Action Buttons (Edit, Delete)
        edit_btn = ctk.CTkButton(
            card, text="✏️", width=34, height=30, corner_radius=6,
            fg_color="transparent", hover_color=CARD_BORDER,
            text_color=TEXT_PRIMARY,
            command=lambda task_obj=t: open_task_modal(task_obj)
        )
        edit_btn.pack(side="right", padx=(2, 6), pady=8)

        del_btn = ctk.CTkButton(
            card, text="🗑️", width=34, height=30, corner_radius=6,
            fg_color="transparent", hover_color=DANGER_HOVER,
            text_color=DANGER_COLOR,
            command=lambda tid=t["id"], tname=t["name"]: delete_task_by_id(tid, tname)
        )
        del_btn.pack(side="right", padx=2, pady=8)


task_search_var.trace_add("write", lambda *_: refresh_tasks())


def open_task_modal(task_data=None):
    is_edit = task_data is not None
    win = ctk.CTkToplevel(root)
    win.title("Ubah Tugas" if is_edit else "Tambah Tugas Baru")
    win.geometry("440x360")
    win.resizable(False, False)
    win.transient(root)
    win.grab_set()

    modal_frame = ctk.CTkFrame(win, fg_color=CARD_BG, corner_radius=0)
    modal_frame.pack(fill="both", expand=True, padx=20, pady=20)

    title_lbl = ctk.CTkLabel(
        modal_frame,
        text="✏️ Ubah Tugas" if is_edit else "➕ Tambah Tugas Baru",
        font=ctk.CTkFont(family="Segoe UI", size=16, weight="bold"),
        text_color=TEXT_PRIMARY
    )
    title_lbl.pack(anchor="w", pady=(0, 12))

    ctk.CTkLabel(modal_frame, text="Nama Tugas", font=ctk.CTkFont(family="Segoe UI", size=11, weight="bold"), text_color=TEXT_MUTED).pack(anchor="w")
    name_entry = ctk.CTkEntry(modal_frame, height=36, corner_radius=6, placeholder_text="Contoh: Selesaikan laporan akhir...")
    name_entry.pack(fill="x", pady=(2, 10))
    if is_edit:
        name_entry.insert(0, task_data["name"])

    ctk.CTkLabel(modal_frame, text="Batas Waktu (Deadline: YYYY-MM-DD)", font=ctk.CTkFont(family="Segoe UI", size=11, weight="bold"), text_color=TEXT_MUTED).pack(anchor="w")
    deadline_entry = ctk.CTkEntry(modal_frame, height=36, corner_radius=6, placeholder_text="YYYY-MM-DD")
    deadline_entry.pack(fill="x", pady=(2, 6))

    default_date = task_data["deadline"] if is_edit else date.today().isoformat()
    if default_date:
        deadline_entry.insert(0, default_date)

    # Date helper shortcuts
    shortcut_frame = ctk.CTkFrame(modal_frame, fg_color="transparent")
    shortcut_frame.pack(fill="x", pady=(0, 10))

    def set_date_shortcut(days_ahead):
        t_date = date.today() + timedelta(days=days_ahead)
        deadline_entry.delete(0, tk.END)
        deadline_entry.insert(0, t_date.isoformat())

    ctk.CTkButton(shortcut_frame, text="Hari ini", width=60, height=24, font=ctk.CTkFont(size=10), fg_color=CARD_BORDER, text_color=TEXT_PRIMARY, command=lambda: set_date_shortcut(0)).pack(side="left", padx=(0, 4))
    ctk.CTkButton(shortcut_frame, text="Besok", width=60, height=24, font=ctk.CTkFont(size=10), fg_color=CARD_BORDER, text_color=TEXT_PRIMARY, command=lambda: set_date_shortcut(1)).pack(side="left", padx=4)
    ctk.CTkButton(shortcut_frame, text="+3 Hari", width=60, height=24, font=ctk.CTkFont(size=10), fg_color=CARD_BORDER, text_color=TEXT_PRIMARY, command=lambda: set_date_shortcut(3)).pack(side="left", padx=4)
    ctk.CTkButton(shortcut_frame, text="+1 Minggu", width=70, height=24, font=ctk.CTkFont(size=10), fg_color=CARD_BORDER, text_color=TEXT_PRIMARY, command=lambda: set_date_shortcut(7)).pack(side="left", padx=4)

    ctk.CTkLabel(modal_frame, text="Prioritas", font=ctk.CTkFont(family="Segoe UI", size=11, weight="bold"), text_color=TEXT_MUTED).pack(anchor="w")
    prio_var = ctk.StringVar(value=task_data["priority"] if is_edit else "Sedang")
    prio_menu = ctk.CTkOptionMenu(modal_frame, values=["Tinggi", "Sedang", "Rendah"], variable=prio_var, height=36, corner_radius=6)
    prio_menu.pack(fill="x", pady=(2, 14))

    def save_task_modal():
        t_name = name_entry.get().strip()
        t_dline = deadline_entry.get().strip()
        t_prio = prio_var.get()
        if not t_name:
            messagebox.showwarning("Peringatan", "Nama tugas tidak boleh kosong!", parent=win)
            return
        if t_dline:
            try:
                datetime.strptime(t_dline, "%Y-%m-%d")
            except ValueError:
                messagebox.showwarning("Format Tanggal Salah", "Gunakan format YYYY-MM-DD (contoh: 2026-10-25)", parent=win)
                return

        if is_edit:
            db.execute("UPDATE tasks SET name=?, deadline=?, priority=? WHERE id=?", (t_name, t_dline or None, t_prio, task_data["id"]))
        else:
            db.execute("INSERT INTO tasks(name, done, deadline, priority) VALUES(?, 0, ?, ?)", (t_name, t_dline or None, t_prio))
        db.commit()
        win.destroy()
        refresh_tasks()
        update_dashboard()

    btn_row = ctk.CTkFrame(modal_frame, fg_color="transparent")
    btn_row.pack(fill="x", pady=(4, 0))

    ctk.CTkButton(btn_row, text="Batal", width=90, height=34, corner_radius=6, fg_color=CARD_BORDER, text_color=TEXT_PRIMARY, command=win.destroy).pack(side="right", padx=(8, 0))
    ctk.CTkButton(btn_row, text="Simpan", width=100, height=34, corner_radius=6, fg_color=ACCENT_COLOR, hover_color=ACCENT_HOVER, command=save_task_modal).pack(side="right")



#CALENDAR

calendar_page = register_page("Calendar")

cal_layout = ctk.CTkFrame(calendar_page, fg_color="transparent")
cal_layout.pack(fill="both", expand=True)
cal_layout.columnconfigure(0, weight=3)
cal_layout.columnconfigure(1, weight=2)

# Left Column: Interactive Month Grid
cal_left = ctk.CTkFrame(cal_layout, fg_color=CARD_BG, corner_radius=12, border_width=1, border_color=CARD_BORDER)
cal_left.grid(row=0, column=0, sticky="nsew", padx=(0, 10))

# Calendar Navigation Bar
cal_nav = ctk.CTkFrame(cal_left, fg_color="transparent")
cal_nav.pack(fill="x", padx=16, pady=(16, 10))

cal_month_label = ctk.CTkLabel(
    cal_nav, text="",
    font=ctk.CTkFont(family="Segoe UI", size=18, weight="bold"),
    text_color=TEXT_PRIMARY
)
cal_month_label.pack(side="left")

def change_cal_month(delta):
    global cal_year, cal_month
    cal_month += delta
    if cal_month > 12:
        cal_month = 1
        cal_year += 1
    elif cal_month < 1:
        cal_month = 12
        cal_year -= 1
    render_calendar()

def reset_to_today():
    global cal_year, cal_month, selected_cal_date
    today = date.today()
    cal_year = today.year
    cal_month = today.month
    selected_cal_date = today
    render_calendar()

ctk.CTkButton(cal_nav, text="▶", width=34, height=32, corner_radius=6, fg_color=CARD_BORDER, text_color=TEXT_PRIMARY, command=lambda: change_cal_month(1)).pack(side="right", padx=(4, 0))
ctk.CTkButton(cal_nav, text="◀", width=34, height=32, corner_radius=6, fg_color=CARD_BORDER, text_color=TEXT_PRIMARY, command=lambda: change_cal_month(-1)).pack(side="right", padx=4)
ctk.CTkButton(cal_nav, text="Hari Ini", width=70, height=32, corner_radius=6, fg_color=ACCENT_COLOR, hover_color=ACCENT_HOVER, command=reset_to_today).pack(side="right", padx=4)

cal_grid_frame = ctk.CTkFrame(cal_left, fg_color="transparent")
cal_grid_frame.pack(fill="both", expand=True, padx=14, pady=(0, 16))

# Right Column: Schedule & Event Manager
cal_right = ctk.CTkFrame(cal_layout, fg_color=CARD_BG, corner_radius=12, border_width=1, border_color=CARD_BORDER)
cal_right.grid(row=0, column=1, sticky="nsew")

event_header = ctk.CTkLabel(
    cal_right, text="📅 Agenda Harian",
    font=ctk.CTkFont(family="Segoe UI", size=16, weight="bold"),
    text_color=TEXT_PRIMARY
)
event_header.pack(anchor="w", padx=18, pady=(16, 2))

selected_date_display = ctk.CTkLabel(
    cal_right, text="",
    font=ctk.CTkFont(family="Segoe UI", size=12, weight="bold"),
    text_color=ACCENT_COLOR
)
selected_date_display.pack(anchor="w", padx=18, pady=(0, 12))

# Add Event Box
add_event_card = ctk.CTkFrame(cal_right, fg_color=CARD_BORDER, corner_radius=8)
add_event_card.pack(fill="x", padx=18, pady=(0, 12))

event_title_entry = ctk.CTkEntry(add_event_card, placeholder_text="Judul acara / kegiatan...", height=34, corner_radius=6)
event_title_entry.pack(fill="x", padx=10, pady=(10, 6))

event_details_entry = ctk.CTkEntry(add_event_card, placeholder_text="Catatan / waktu (opsional)...", height=34, corner_radius=6)
event_details_entry.pack(fill="x", padx=10, pady=(0, 8))

def add_event_handler():
    title = event_title_entry.get().strip()
    details = event_details_entry.get().strip()
    if not title:
        messagebox.showwarning("Peringatan", "Masukkan judul acara!")
        return
    db.execute("INSERT INTO events(event_date, title, details) VALUES(?, ?, ?)", (selected_cal_date.isoformat(), title, details))
    db.commit()
    event_title_entry.delete(0, tk.END)
    event_details_entry.delete(0, tk.END)
    render_calendar()
    update_dashboard()

ctk.CTkButton(
    add_event_card, text="+ Tambah ke Tanggal Ini",
    font=ctk.CTkFont(family="Segoe UI", size=11, weight="bold"),
    fg_color=SUCCESS_COLOR, hover_color=SUCCESS_HOVER,
    height=32, corner_radius=6,
    command=add_event_handler
).pack(fill="x", padx=10, pady=(0, 10))

event_list_scroll = ctk.CTkScrollableFrame(cal_right, fg_color="transparent")
event_list_scroll.pack(fill="both", expand=True, padx=18, pady=(0, 14))


def delete_event_by_id(eid, title):
    if messagebox.askyesno("Hapus Acara", f"Hapus agenda:\n'{title}'?"):
        db.execute("DELETE FROM events WHERE id=?", (eid,))
        db.commit()
        render_calendar()
        update_dashboard()


def select_cal_day(day):
    global selected_cal_date
    selected_cal_date = date(cal_year, cal_month, day)
    render_calendar()


def render_calendar():
    for w in cal_grid_frame.winfo_children():
        w.destroy()

    indonesian_months = [
        "", "Januari", "Februari", "Maret", "April", "Mei", "Juni",
        "Juli", "Agustus", "September", "Oktober", "November", "Desember"
    ]
    cal_month_label.configure(text=f"{indonesian_months[cal_month]} {cal_year}")
    selected_date_display.configure(text=selected_cal_date.strftime("%A, %d %B %Y"))

    for col_idx, dname in enumerate(["Sen", "Sel", "Rab", "Kam", "Jum", "Sab", "Min"]):
        cal_grid_frame.columnconfigure(col_idx, weight=1)
        lbl = ctk.CTkLabel(
            cal_grid_frame, text=dname,
            font=ctk.CTkFont(family="Segoe UI", size=11, weight="bold"),
            text_color=TEXT_MUTED
        )
        lbl.grid(row=0, column=col_idx, pady=(4, 8))

    weeks = cal.monthcalendar(cal_year, cal_month)
    today = date.today()

    for r_idx, week in enumerate(weeks, start=1):
        cal_grid_frame.rowconfigure(r_idx, weight=1)
        for c_idx, day_num in enumerate(week):
            if day_num == 0:
                dummy = ctk.CTkLabel(cal_grid_frame, text="", height=42)
                dummy.grid(row=r_idx, column=c_idx, padx=2, pady=2)
                continue

            current_iter_date = date(cal_year, cal_month, day_num)
            has_event = db.execute("SELECT 1 FROM events WHERE event_date=? LIMIT 1", (current_iter_date.isoformat(),)).fetchone()
            is_selected = (current_iter_date == selected_cal_date)
            is_today = (current_iter_date == today)

            text_label = f"{day_num}\n●" if has_event else str(day_num)

            if is_selected:
                btn_fg = ACCENT_COLOR
                btn_text = "#FFFFFF"
            elif is_today:
                btn_fg = CARD_BORDER
                btn_text = ACCENT_COLOR
            else:
                btn_fg = "transparent"
                btn_text = TEXT_PRIMARY

            d_btn = ctk.CTkButton(
                cal_grid_frame,
                text=text_label,
                font=ctk.CTkFont(family="Segoe UI", size=11, weight="bold" if (is_selected or is_today) else "normal"),
                fg_color=btn_fg,
                text_color=btn_text,
                hover_color=ACCENT_HOVER,
                corner_radius=8,
                height=42,
                command=lambda d=day_num: select_cal_day(d)
            )
            d_btn.grid(row=r_idx, column=c_idx, padx=2, pady=2, sticky="nsew")

    # Render events on right panel
    for w in event_list_scroll.winfo_children():
        w.destroy()

    events = db.execute(
        "SELECT id, title, details FROM events WHERE event_date=? ORDER BY id",
        (selected_cal_date.isoformat(),)
    ).fetchall()

    if not events:
        ctk.CTkLabel(
            event_list_scroll,
            text="Belum ada agenda kegiatan pada tanggal ini.",
            font=ctk.CTkFont(family="Segoe UI", size=11),
            text_color=TEXT_MUTED
        ).pack(pady=20)
    else:
        for eid, title, details in events:
            e_card = ctk.CTkFrame(event_list_scroll, fg_color=CARD_BORDER, corner_radius=8)
            e_card.pack(fill="x", pady=4)

            text_box = ctk.CTkFrame(e_card, fg_color="transparent")
            text_box.pack(side="left", fill="both", expand=True, padx=10, pady=8)

            ctk.CTkLabel(
                text_box, text=title,
                font=ctk.CTkFont(family="Segoe UI", size=12, weight="bold"),
                text_color=TEXT_PRIMARY, anchor="w"
            ).pack(fill="x")

            if details:
                ctk.CTkLabel(
                    text_box, text=details,
                    font=ctk.CTkFont(family="Segoe UI", size=10),
                    text_color=TEXT_MUTED, anchor="w"
                ).pack(fill="x")

            del_btn = ctk.CTkButton(
                e_card, text="🗑️", width=30, height=30, corner_radius=6,
                fg_color="transparent", text_color=DANGER_COLOR, hover_color=DANGER_HOVER,
                command=lambda event_id=eid, event_title=title: delete_event_by_id(event_id, event_title)
            )
            del_btn.pack(side="right", padx=6, pady=8)



#NOTES

notes_page = register_page("Notes")

notes_split = ctk.CTkFrame(notes_page, fg_color="transparent")
notes_split.pack(fill="both", expand=True)
notes_split.columnconfigure(0, weight=2)
notes_split.columnconfigure(1, weight=5)

# Left Column: Note List & Search
notes_left = ctk.CTkFrame(notes_split, fg_color=CARD_BG, corner_radius=12, border_width=1, border_color=CARD_BORDER)
notes_left.grid(row=0, column=0, sticky="nsew", padx=(0, 10))

note_search_var = ctk.StringVar()
note_search_entry = ctk.CTkEntry(
    notes_left, placeholder_text="🔍 Cari catatan...",
    textvariable=note_search_var,
    height=36, corner_radius=8
)
note_search_entry.pack(fill="x", padx=14, pady=(14, 8))

new_note_btn = ctk.CTkButton(
    notes_left, text="+ Catatan Baru",
    font=ctk.CTkFont(family="Segoe UI", size=12, weight="bold"),
    fg_color=ACCENT_COLOR, hover_color=ACCENT_HOVER,
    height=34, corner_radius=8,
    command=lambda: new_note()
)
new_note_btn.pack(fill="x", padx=14, pady=(0, 10))

notes_list_scroll = ctk.CTkScrollableFrame(notes_left, fg_color="transparent")
notes_list_scroll.pack(fill="both", expand=True, padx=10, pady=(0, 12))

# Right Column: Note Editor
notes_right = ctk.CTkFrame(notes_split, fg_color=CARD_BG, corner_radius=12, border_width=1, border_color=CARD_BORDER)
notes_right.grid(row=0, column=1, sticky="nsew")

note_title_entry = ctk.CTkEntry(
    notes_right, placeholder_text="Judul Catatan...",
    font=ctk.CTkFont(family="Segoe UI", size=15, weight="bold"),
    height=42, corner_radius=8
)
note_title_entry.pack(fill="x", padx=18, pady=(18, 10))

note_content_box = ctk.CTkTextbox(
    notes_right, font=ctk.CTkFont(family="Segoe UI", size=13),
    corner_radius=8, wrap="word", undo=True
)
note_content_box.pack(fill="both", expand=True, padx=18, pady=(0, 10))

note_bar = ctk.CTkFrame(notes_right, fg_color="transparent")
note_bar.pack(fill="x", padx=18, pady=(0, 16))

note_stats_lbl = ctk.CTkLabel(
    note_bar, text="0 karakter | 0 kata",
    font=ctk.CTkFont(family="Segoe UI", size=11),
    text_color=TEXT_MUTED
)
note_stats_lbl.pack(side="left")

def update_note_stats(event=None):
    text = note_content_box.get("1.0", "end-1c")
    chars = len(text)
    words = len(text.split())
    note_stats_lbl.configure(text=f"{chars} karakter | {words} kata")

note_content_box.bind("<KeyRelease>", update_note_stats)

def save_note():
    global selected_note_id
    title = note_title_entry.get().strip()
    content = note_content_box.get("1.0", "end-1c").strip()
    if not title:
        messagebox.showwarning("Peringatan", "Beri judul pada catatan Anda terlebih dahulu!")
        return

    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    if selected_note_id is None:
        cur_n = db.execute("INSERT INTO notes(title, content, updated_at) VALUES(?, ?, ?)", (title, content, now_str))
        selected_note_id = cur_n.lastrowid
    else:
        db.execute("UPDATE notes SET title=?, content=?, updated_at=? WHERE id=?", (title, content, now_str, selected_note_id))
    db.commit()
    refresh_notes()
    messagebox.showinfo("Tersimpan", "Catatan berhasil disimpan!")

def delete_note():
    global selected_note_id
    if selected_note_id is None:
        messagebox.showwarning("Peringatan", "Pilih catatan yang ingin dihapus terlebih dahulu.")
        return
    if messagebox.askyesno("Hapus Catatan", "Yakin ingin menghapus catatan ini secara permanen?"):
        db.execute("DELETE FROM notes WHERE id=?", (selected_note_id,))
        db.commit()
        new_note()
        refresh_notes()

ctk.CTkButton(
    note_bar, text="🗑️ Hapus",
    font=ctk.CTkFont(family="Segoe UI", size=11, weight="bold"),
    fg_color=DANGER_COLOR, hover_color=DANGER_HOVER,
    width=80, height=34, corner_radius=6,
    command=delete_note
).pack(side="right", padx=(8, 0))

ctk.CTkButton(
    note_bar, text="💾 Simpan Catatan",
    font=ctk.CTkFont(family="Segoe UI", size=11, weight="bold"),
    fg_color=SUCCESS_COLOR, hover_color=SUCCESS_HOVER,
    width=130, height=34, corner_radius=6,
    command=save_note
).pack(side="right")


def select_note_card(nid):
    global selected_note_id
    selected_note_id = nid
    row = db.execute("SELECT title, content FROM notes WHERE id=?", (nid,)).fetchone()
    if row:
        note_title_entry.delete(0, tk.END)
        note_title_entry.insert(0, row[0])
        note_content_box.delete("1.0", tk.END)
        note_content_box.insert("1.0", row[1] or "")
        update_note_stats()
    refresh_notes()


def new_note():
    global selected_note_id
    selected_note_id = None
    note_title_entry.delete(0, tk.END)
    note_content_box.delete("1.0", tk.END)
    update_note_stats()
    note_title_entry.focus_set()
    refresh_notes()


def refresh_notes():
    for w in notes_list_scroll.winfo_children():
        w.destroy()

    search_q = note_search_var.get().strip().lower()
    rows = db.execute("SELECT id, title, content, updated_at FROM notes ORDER BY updated_at DESC, id DESC").fetchall()

    filtered = []
    for nid, title, content, updated_at in rows:
        if search_q and search_q not in (title + " " + (content or "")).lower():
            continue
        filtered.append((nid, title, content, updated_at))

    if not filtered:
        ctk.CTkLabel(
            notes_list_scroll,
            text="Tidak ada catatan ditemukan.",
            font=ctk.CTkFont(family="Segoe UI", size=11),
            text_color=TEXT_MUTED
        ).pack(pady=20)
        return

    for nid, title, content, updated_at in filtered:
        is_sel = (nid == selected_note_id)
        card = ctk.CTkFrame(
            notes_list_scroll,
            fg_color=ACCENT_COLOR if is_sel else CARD_BORDER,
            corner_radius=8,
            cursor="hand2"
        )
        card.pack(fill="x", pady=3)

        title_lbl = ctk.CTkLabel(
            card, text=title or "(Tanpa Judul)",
            font=ctk.CTkFont(family="Segoe UI", size=12, weight="bold"),
            text_color="#FFFFFF" if is_sel else TEXT_PRIMARY,
            anchor="w"
        )
        title_lbl.pack(fill="x", padx=10, pady=(8, 2))

        # Snippet
        snippet = (content or "").replace("\n", " ")[:40]
        if len(content or "") > 40:
            snippet += "..."
        snippet_lbl = ctk.CTkLabel(
            card, text=snippet or "Belum ada isi...",
            font=ctk.CTkFont(family="Segoe UI", size=10),
            text_color="#E0E7FF" if is_sel else TEXT_MUTED,
            anchor="w"
        )
        snippet_lbl.pack(fill="x", padx=10, pady=(0, 2))

        date_lbl = ctk.CTkLabel(
            card, text=updated_at[:16] if updated_at else "",
            font=ctk.CTkFont(family="Segoe UI", size=9),
            text_color="#C7D2FE" if is_sel else TEXT_MUTED,
            anchor="e"
        )
        date_lbl.pack(fill="x", padx=10, pady=(0, 6))

        for item in (card, title_lbl, snippet_lbl, date_lbl):
            item.bind("<Button-1>", lambda e, note_id=nid: select_note_card(note_id))


note_search_var.trace_add("write", lambda *_: refresh_notes())



#AI ASSISTANT

ai_page = register_page("AI Assistant")

ai_card = ctk.CTkFrame(ai_page, fg_color=CARD_BG, corner_radius=12, border_width=1, border_color=CARD_BORDER)
ai_card.pack(fill="both", expand=True)

# Chat Messages Scrollable Box
chat_scroll = ctk.CTkScrollableFrame(ai_card, fg_color="transparent")
chat_scroll.pack(fill="both", expand=True, padx=16, pady=(16, 10))

# Suggestion Chips Frame
chips_frame = ctk.CTkFrame(ai_card, fg_color="transparent")
chips_frame.pack(fill="x", padx=16, pady=(0, 8))

# Chat Input Bar
chat_bar = ctk.CTkFrame(ai_card, fg_color="transparent")
chat_bar.pack(fill="x", padx=16, pady=(0, 16))

chat_input = ctk.CTkEntry(
    chat_bar,
    placeholder_text="Ketik pesan atau tanyakan tentang tugas Anda...",
    font=ctk.CTkFont(family="Segoe UI", size=12),
    height=42, corner_radius=8
)
chat_input.pack(side="left", fill="x", expand=True, padx=(0, 10))

send_btn = ctk.CTkButton(
    chat_bar, text="Kirim 🚀",
    font=ctk.CTkFont(family="Segoe UI", size=12, weight="bold"),
    fg_color=ACCENT_COLOR, hover_color=ACCENT_HOVER,
    height=42, width=90, corner_radius=8,
    command=lambda: send_chat_message()
)
send_btn.pack(side="right")


def append_chat_bubble(sender, message, is_user=False):
    bubble_row = ctk.CTkFrame(chat_scroll, fg_color="transparent")
    bubble_row.pack(fill="x", pady=6)

    bubble_bg = ACCENT_COLOR if is_user else CARD_BORDER
    text_col = "#FFFFFF" if is_user else TEXT_PRIMARY

    bubble = ctk.CTkFrame(bubble_row, fg_color=bubble_bg, corner_radius=12)
    bubble.pack(side="right" if is_user else "left", padx=6)

    sender_lbl = ctk.CTkLabel(
        bubble,
        text="👤 Anda" if is_user else "🤖 MYPA AI Asisten",
        font=ctk.CTkFont(family="Segoe UI", size=10, weight="bold"),
        text_color="#E0E7FF" if is_user else ACCENT_COLOR
    )
    sender_lbl.pack(anchor="w", padx=14, pady=(8, 2))

    msg_lbl = ctk.CTkLabel(
        bubble, text=message,
        font=ctk.CTkFont(family="Segoe UI", size=12),
        text_color=text_col,
        justify="left",
        wraplength=650
    )
    msg_lbl.pack(anchor="w", padx=14, pady=(0, 10))

    chat_scroll._parent_canvas.yview_moveto(1.0)


def generate_ai_reply(msg):
    text = msg.lower()
    uname = setting_get("username", "Inka Kristiani")

    if any(w in text for w in ["halo", "hai", "hello", "hi", "pagi", "siang", "sore", "malam"]):
        return f"Halo {uname}! Saya asisten cerdas MYPA. Ada yang bisa saya bantu terkait tugas, kalender, catatan, atau tips produktivitas Anda?"

    if "tugas" in text or "task" in text or "kerjaan" in text:
        rows = db.execute("SELECT name, done, deadline, priority FROM tasks ORDER BY done ASC, id DESC").fetchall()
        if not rows:
            return "Belum ada tugas yang tersimpan. Anda dapat menambahkannya melalui menu 'Tugas & Deadline'."
        pending = [r for r in rows if not r[0]]
        completed = [r for r in rows if r[0]]
        summary = [f"📊 Ringkasan Tugas Anda:\n• Total: {len(rows)} | Selesai: {len(completed)} | Menunggu: {len(pending)}\n"]
        if pending:
            summary.append("Berikut beberapa tugas yang perlu segera diselesaikan:")
            for name, done, deadline, priority in pending[:5]:
                d_str = f" (Deadline: {deadline})" if deadline else ""
                summary.append(f"• [{priority}] {name}{d_str}")
        else:
            summary.append("🎉 Hebat! Semua tugas Anda telah selesai dikerjakan.")
        return "\n".join(summary)

    if "jadwal" in text or "kalender" in text or "acara" in text or "event" in text:
        today_str = date.today().isoformat()
        events = db.execute(
            "SELECT event_date, title, details FROM events WHERE event_date >= ? ORDER BY event_date ASC LIMIT 6",
            (today_str,)
        ).fetchall()
        if not events:
            return "Belum ada agenda kegiatan mendatang di kalender. Anda dapat menambahkannya di menu 'Kalender Agenda'."
        lines = ["📅 Agenda kegiatan mendatang Anda:"]
        for edate, title, details in events:
            detail_str = f" - {details}" if details else ""
            lines.append(f"• {edate}: {title}{detail_str}")
        return "\n".join(lines)

    if "catatan" in text or "note" in text:
        notes = db.execute("SELECT title, updated_at FROM notes ORDER BY updated_at DESC LIMIT 5").fetchall()
        if not notes:
            return "Belum ada catatan yang tersimpan. Anda bisa membuat catatan ide baru di menu 'Catatan'."
        lines = ["📝 Catatan terbaru Anda:"]
        for title, u_at in notes:
            lines.append(f"• {title} ({u_at[:10]})")
        return "\n".join(lines)

    if "prioritas" in text or "penting" in text or "urgent" in text or "mulai" in text:
        high_task = db.execute(
            "SELECT name, deadline, priority FROM tasks WHERE done=0 AND priority='Tinggi' ORDER BY deadline ASC LIMIT 1"
        ).fetchone()
        if high_task:
            d_str = f" (Batas Waktu: {high_task[1]})" if high_task[1] else ""
            return f"🔥 Saran Prioritas Utama:\nFokuslah menyelesaikan: '{high_task[0]}'{d_str}. Tugas ini berprioritas TINGGI. Pecah menjadi langkah-langkah kecil agar lebih mudah dikerjakan!"
        any_task = db.execute(
            "SELECT name, deadline, priority FROM tasks WHERE done=0 ORDER BY id ASC LIMIT 1"
        ).fetchone()
        if any_task:
            return f"💡 Anda tidak memiliki tugas mendesak berprioritas Tinggi. Anda bisa mulai mengerjakan: '{any_task[0]}'."
        return "🎉 Tidak ada tugas aktif yang mendesak saat ini. Anda dapat beristirahat atau merencanakan tujuan baru!"

    if "tips" in text or "fokus" in text or "produktivitas" in text:
        return "💡 Tips Produktivitas MYPA:\n1. Terapkan Teknik Pomodoro (25 menit kerja fokus + 5 menit istirahat).\n2. Kerjakan tugas tersulit atau paling penting di pagi hari (*Eat That Frog*).\n3. Kelompokkan tugas serupa agar tidak membuang energi saat *context switching*."

    if "bantu" in text or "help" in text:
        return "🤖 Panduan Perintah yang Dapat Saya Jawab:\n• Ketik 'tugas' untuk melihat ringkasan tugas aktif.\n• Ketik 'jadwal' untuk memeriksa agenda mendatang.\n• Ketik 'prioritas' untuk saran tugas yang harus dikerjakan duluan.\n• Ketik 'catatan' untuk daftar catatan tersimpan.\n• Ketik 'tips' untuk tips produktivitas."

    return "Saya asisten lokal MYPA. Coba tanyakan tentang 'tugas', 'jadwal', 'prioritas', atau 'catatan' Anda, atau klik tombol saran di atas!"


def send_chat_message(custom_text=None):
    msg = custom_text or chat_input.get().strip()
    if not msg:
        return
    if not custom_text:
        chat_input.delete(0, tk.END)

    append_chat_bubble("Anda", msg, is_user=True)
    reply = generate_ai_reply(msg)
    root.after(150, lambda: append_chat_bubble("MYPA", reply, is_user=False))


chat_input.bind("<Return>", lambda e: send_chat_message())

# Add Suggestion Chips
chips = [
    ("📋 Apa tugasku?", "Apa tugasku sekarang?"),
    ("📅 Jadwal mendatang", "Tampilkan jadwal kegiatan mendatang"),
    ("⚡ Prioritas hari ini", "Apa prioritas tugasku?"),
    ("💡 Tips fokus", "Berikan tips produktivitas dan fokus")
]

for label, query in chips:
    btn = ctk.CTkButton(
        chips_frame, text=label,
        font=ctk.CTkFont(family="Segoe UI", size=10),
        fg_color=CARD_BORDER, hover_color=ACCENT_COLOR,
        text_color=TEXT_PRIMARY, height=28, corner_radius=14,
        command=lambda q=query: send_chat_message(q)
    )
    btn.pack(side="left", padx=4)

append_chat_bubble(
    "MYPA",
    "Halo! Saya asisten cerdas MYPA siap membantu produktivitas Anda. Tanyakan tentang tugas, jadwal, atau klik salah satu saran di atas!",
    is_user=False
)



# 6. PAGE: SETTINGS
settings_page = register_page("Settings")

settings_scroll = ctk.CTkScrollableFrame(settings_page, fg_color="transparent")
settings_scroll.pack(fill="both", expand=True)

# Profile Card
profile_card = ctk.CTkFrame(settings_scroll, fg_color=CARD_BG, corner_radius=12, border_width=1, border_color=CARD_BORDER)
profile_card.pack(fill="x", pady=(0, 16))

ctk.CTkLabel(
    profile_card, text="👤 Profil Pengguna",
    font=ctk.CTkFont(family="Segoe UI", size=16, weight="bold"),
    text_color=TEXT_PRIMARY
).pack(anchor="w", padx=20, pady=(18, 6))

ctk.CTkLabel(
    profile_card, text="Nama Anda",
    font=ctk.CTkFont(family="Segoe UI", size=11, weight="bold"),
    text_color=TEXT_MUTED
).pack(anchor="w", padx=20)

user_entry = ctk.CTkEntry(profile_card, height=38, corner_radius=8, font=ctk.CTkFont(family="Segoe UI", size=12))
user_entry.pack(fill="x", padx=20, pady=(4, 14))

# Appearance Card
theme_card = ctk.CTkFrame(settings_scroll, fg_color=CARD_BG, corner_radius=12, border_width=1, border_color=CARD_BORDER)
theme_card.pack(fill="x", pady=(0, 16))

ctk.CTkLabel(
    theme_card, text="🎨 Tampilan & Tema",
    font=ctk.CTkFont(family="Segoe UI", size=16, weight="bold"),
    text_color=TEXT_PRIMARY
).pack(anchor="w", padx=20, pady=(18, 6))

ctk.CTkLabel(
    theme_card, text="Pilih Mode Tampilan (Berubah Langsung Seketika):",
    font=ctk.CTkFont(family="Segoe UI", size=11, weight="bold"),
    text_color=TEXT_MUTED
).pack(anchor="w", padx=20)


def on_theme_change(choice):
    ctk.set_appearance_mode(choice)
    setting_set("theme", choice)
    quick_theme_btn.configure(text="🌙 Dark Mode" if choice == "Light" else "☀️ Light Mode")


theme_segmented = ctk.CTkSegmentedButton(
    theme_card, values=["Dark", "Light", "System"],
    height=38, corner_radius=8,
    command=on_theme_change
)
theme_segmented.pack(anchor="w", padx=20, pady=(6, 18))

# System Information Card
sys_card = ctk.CTkFrame(settings_scroll, fg_color=CARD_BG, corner_radius=12, border_width=1, border_color=CARD_BORDER)
sys_card.pack(fill="x", pady=(0, 16))

ctk.CTkLabel(
    sys_card, text="ℹ️ Informasi Sistem & Database",
    font=ctk.CTkFont(family="Segoe UI", size=16, weight="bold"),
    text_color=TEXT_PRIMARY
).pack(anchor="w", padx=20, pady=(18, 10))

db_info_lbl = ctk.CTkLabel(
    sys_card,
    text=f"Lokasi Database: {DB_PATH}\nVersi Aplikasi: MYPA Pro Suite v2.5\nFramework: CustomTkinter 6.0",
    font=ctk.CTkFont(family="Segoe UI", size=11),
    text_color=TEXT_MUTED, justify="left"
)
db_info_lbl.pack(anchor="w", padx=20, pady=(0, 18))

save_settings_btn = ctk.CTkButton(
    settings_scroll, text="💾 Simpan Perubahan Pengaturan",
    font=ctk.CTkFont(family="Segoe UI", size=12, weight="bold"),
    fg_color=SUCCESS_COLOR, hover_color=SUCCESS_HOVER,
    height=40, corner_radius=8,
    command=lambda: save_all_settings()
)
save_settings_btn.pack(anchor="w", pady=(0, 20))


def load_settings():
    user_entry.delete(0, tk.END)
    user_entry.insert(0, setting_get("username", ""))
    theme_segmented.set(setting_get("theme", "Dark"))


def save_all_settings():
    uname = user_entry.get().strip() or "Inka Kristiani"
    setting_set("username", uname)
    setting_set("theme", theme_segmented.get())
    update_dashboard()
    messagebox.showinfo("Pengaturan Disimpan", "Profil dan preferensi Anda berhasil disimpan!")


# ------------------------- Window Close Handler -------------------------
def on_app_close():
    try:
        db.commit()
        db.close()
    finally:
        root.destroy()


root.protocol("WM_DELETE_WINDOW", on_app_close)

# Start on Dashboard
switch_page("Dashboard")

if __name__ == "__main__":
    root.mainloop()
