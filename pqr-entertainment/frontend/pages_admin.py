import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime
from dbwrap import db

def show_screen_manager(app):
    app.clear_container()
    app.add_navigation_bar()
    app.add_header(show_menu=True, show_username=True)

    content_frame = tk.Frame(app.main_container, bg='#1a1a1a')
    content_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)

    tk.Label(content_frame, text="📺 Screen Manager", font=('Arial', 24, 'bold'),
             bg='#1a1a1a', fg='white').pack(pady=(10, 12))

    controls = tk.Frame(content_frame, bg='#1a1a1a')
    controls.pack(fill=tk.X, pady=5)

    cities_rows = db.execute_query("SELECT DISTINCT city FROM theatres", fetch_all=True)
    cities = sorted([r['city'] for r in cities_rows]) if cities_rows else []
    tk.Label(controls, text="City:", bg='#1a1a1a', fg='white').pack(side=tk.LEFT)
    city_var = tk.StringVar(value=cities[0] if cities else '')
    ttk.Combobox(controls, textvariable=city_var, values=cities, width=18, state='readonly').pack(side=tk.LEFT, padx=5)

    tk.Label(controls, text="Date (YYYY-MM-DD):", bg='#1a1a1a', fg='white').pack(side=tk.LEFT, padx=(15, 0))
    date_var = tk.StringVar(value=datetime.now().strftime('%Y-%m-%d'))
    tk.Entry(controls, textvariable=date_var, width=14).pack(side=tk.LEFT, padx=5)

    list_container = tk.Frame(content_frame, bg='#1a1a1a')
    list_container.pack(fill=tk.BOTH, expand=True, pady=10)

    def load_list():
        for w in list_container.winfo_children():
            w.destroy()
        canvas = tk.Canvas(list_container, bg='#1a1a1a', highlightthickness=0)
        scrollbar = ttk.Scrollbar(list_container, orient="vertical", command=canvas.yview)
        inner = tk.Frame(canvas, bg='#1a1a1a')
        inner.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=inner, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        query = """
            SELECT ss.*, t.name as theatre_name, t.city, m.title as movie_title
            FROM scheduled_screens ss
            JOIN theatres t ON ss.theatre_id = t.theatre_id
            JOIN movies m ON ss.movie_id = m.movie_id
            WHERE t.city = ? AND DATE(ss.start_time) = DATE(?)
            ORDER BY ss.start_time
        """
        rows = db.execute_query(query, (city_var.get(), date_var.get()), fetch_all=True)

        if not rows:
            tk.Label(inner, text="No schedules found", bg='#1a1a1a', fg='#888', font=('Arial', 12)).pack(pady=20)
        else:
            # Table header
            table = tk.Frame(inner, bg='#1a1a1a'); table.pack(fill=tk.BOTH, expand=True)
            header_bg = '#333'
            cols = ["Movie", "Theatre", "Screen", "Start", "End", "Actions"]
            header = tk.Frame(table, bg=header_bg)
            header.grid(row=0, column=0, columnspan=6, sticky='ew')
            for i, c in enumerate(cols):
                tk.Label(header, text=c, font=('Arial', 11, 'bold'), bg=header_bg, fg='white', padx=10, pady=8).grid(row=0, column=i, sticky='w')
                header.grid_columnconfigure(i, weight=1)
            # Rows
            for idx, r in enumerate(rows, start=1):
                st = datetime.fromisoformat(r['start_time']).strftime('%Y-%m-%d %H:%M')
                et = datetime.fromisoformat(r['end_time']).strftime('%Y-%m-%d %H:%M')
                rowf = tk.Frame(table, bg='#2a2a2a'); rowf.grid(row=idx, column=0, sticky='ew', pady=2)
                for i in range(6): rowf.grid_columnconfigure(i, weight=1)
                tk.Label(rowf, text=r['movie_title'], bg='#2a2a2a', fg='white', font=('Arial', 10), padx=10, pady=6, anchor='w').grid(row=0, column=0, sticky='ew')
                tk.Label(rowf, text=r['theatre_name'], bg='#2a2a2a', fg='white', font=('Arial', 10), padx=10, pady=6, anchor='w').grid(row=0, column=1, sticky='ew')
                tk.Label(rowf, text=str(r['screen_number']), bg='#2a2a2a', fg='white', font=('Arial', 10), padx=10, pady=6, anchor='w').grid(row=0, column=2, sticky='ew')
                tk.Label(rowf, text=st, bg='#2a2a2a', fg='#ccc', font=('Arial', 10), padx=10, pady=6, anchor='w').grid(row=0, column=3, sticky='ew')
                tk.Label(rowf, text=et, bg='#2a2a2a', fg='#ccc', font=('Arial', 10), padx=10, pady=6, anchor='w').grid(row=0, column=4, sticky='ew')
                actions = tk.Frame(rowf, bg='#2a2a2a'); actions.grid(row=0, column=5, sticky='e', padx=8)
                tk.Button(actions, text="Reschedule", bg='#2196F3', fg='white', command=lambda sid=r['screen_id']: app.reschedule_screen_popup(sid)).pack(side=tk.LEFT, padx=4)
                tk.Button(actions, text="Delete Show", bg='#d32f2f', fg='white', command=lambda sid=r['screen_id']: app.admin_delete_show(sid)).pack(side=tk.LEFT, padx=4)

        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

    tk.Button(controls, text="Apply", bg='#4CAF50', fg='white', command=load_list).pack(side=tk.LEFT, padx=10)
    tk.Button(controls, text="Schedule New Show", bg='#2196F3', fg='white',
              command=lambda: app.admin_schedule_screen_popup(city_default=city_var.get(),
                                                              date_default=date_var.get(),
                                                              on_success=load_list)).pack(side=tk.LEFT, padx=6)
    load_list()


def show_admin_feedback(app):
    app.clear_container()
    app.add_navigation_bar()
    app.add_header(show_menu=True, show_username=True)

    content_frame = tk.Frame(app.main_container, bg='#1a1a1a')
    content_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)

    tk.Label(content_frame, text="💬 User Feedback", font=('Arial', 24, 'bold'), bg='#1a1a1a', fg='white').pack(pady=(10, 12))

    ctrl = tk.Frame(content_frame, bg='#1a1a1a'); ctrl.pack(fill=tk.X)
    tk.Label(ctrl, text="Filter:", bg='#1a1a1a', fg='white').pack(side=tk.LEFT)
    filter_var = tk.StringVar(value='unread')
    for label, val in [("Unread", 'unread'), ("Read", 'read'), ("All", 'all')]:
        ttk.Radiobutton(ctrl, text=label, variable=filter_var, value=val).pack(side=tk.LEFT, padx=6)
    tk.Button(ctrl, text="Mark All as Read", bg='#4CAF50', fg='white',
             command=lambda: [db.execute_query("UPDATE feedbacks SET read_flag = 1 WHERE read_flag = 0"), load_page(0)]).pack(side=tk.RIGHT)

    list_holder = tk.Frame(content_frame, bg='#1a1a1a'); list_holder.pack(fill=tk.BOTH, expand=True)
    nav = tk.Frame(content_frame, bg='#1a1a1a'); nav.pack(fill=tk.X)
    page_var = tk.IntVar(value=0)
    page_size = 10

    def load_page(delta=0):
        newp = max(0, page_var.get() + delta)
        page_var.set(newp)
        for w in list_holder.winfo_children(): w.destroy()
        where = ""
        if filter_var.get() == 'unread':
            where = "WHERE f.read_flag = 0"
        elif filter_var.get() == 'read':
            where = "WHERE f.read_flag = 1"
        query = f"""
            SELECT f.*, u.name as user_name
            FROM feedbacks f
            JOIN users u ON f.user_id = u.user_id
            {where}
            ORDER BY f.timestamp DESC
            LIMIT {page_size} OFFSET {newp * page_size}
        """
        feedbacks = db.execute_query(query, None, fetch_all=True)
        if not feedbacks:
            tk.Label(list_holder, text="No feedback found", font=('Arial', 14), bg='#1a1a1a', fg='#888').pack(pady=50)
        else:
            # Table header
            table = tk.Frame(list_holder, bg='#1a1a1a'); table.pack(fill=tk.BOTH, expand=True)
            header_bg = '#333'
            cols = ["User", "Timestamp", "Text", "Status", "Actions"]
            header = tk.Frame(table, bg=header_bg)
            header.grid(row=0, column=0, columnspan=5, sticky='ew')
            for i, c in enumerate(cols):
                tk.Label(header, text=c, font=('Arial', 11, 'bold'), bg=header_bg, fg='white', padx=10, pady=8).grid(row=0, column=i, sticky='w')
                header.grid_columnconfigure(i, weight=1)
            # Rows
            for idx, feedback in enumerate(feedbacks, start=1):
                row = tk.Frame(table, bg='#2a2a2a'); row.grid(row=idx, column=0, sticky='ew', pady=2)
                for i in range(5): row.grid_columnconfigure(i, weight=1)
                tk.Label(row, text=feedback['user_name'], font=('Arial', 10), bg='#2a2a2a', fg='white', padx=10, pady=6, anchor='w').grid(row=0, column=0, sticky='ew')
                tk.Label(row, text=feedback['timestamp'][:19], font=('Arial', 10), bg='#2a2a2a', fg='#ccc', padx=10, pady=6, anchor='w').grid(row=0, column=1, sticky='ew')
                tk.Label(row, text=feedback['text'], font=('Arial', 10), bg='#2a2a2a', fg='#ccc', wraplength=800, justify='left', padx=10, pady=6, anchor='w').grid(row=0, column=2, sticky='ew')
                status = 'Unread' if feedback['read_flag'] == 0 else 'Read'
                tk.Label(row, text=status, font=('Arial', 10, 'bold'), bg='#2a2a2a', fg=('#FF9800' if status=='Unread' else '#8BC34A'), padx=10, pady=6, anchor='w').grid(row=0, column=3, sticky='ew')
                actions = tk.Frame(row, bg='#2a2a2a'); actions.grid(row=0, column=4, sticky='e', padx=8)
                if feedback['read_flag'] == 0:
                    tk.Button(actions, text="Mark as Read", bg='#4CAF50', fg='white', command=lambda fid=feedback['feedback_id']: [app.mark_feedback_read(fid), load_page(0)]).pack(side=tk.LEFT)
        for w in nav.winfo_children(): w.destroy()
        tk.Button(nav, text="← Prev", bg='#555', fg='white', command=lambda: load_page(-1)).pack(side=tk.LEFT, padx=4)
        tk.Label(nav, text=f"Page {page_var.get()+1}", bg='#1a1a1a', fg='white').pack(side=tk.LEFT)
        tk.Button(nav, text="Next →", bg='#555', fg='white', command=lambda: load_page(1)).pack(side=tk.LEFT, padx=4)

    def on_filter_change(*args):
        page_var.set(0)
        load_page(0)
    filter_var.trace_add('write', on_filter_change)
    load_page(0)

def show_manage_movies(app):
    app.clear_container()
    app.add_navigation_bar()
    app.add_header(show_menu=True, show_username=True)

    content = tk.Frame(app.main_container, bg='#1a1a1a')
    content.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)

    tk.Label(content, text="🎬 Manage Movies", font=('Arial', 24, 'bold'), bg='#1a1a1a', fg='white').pack(pady=(10, 12))

    controls = tk.Frame(content, bg='#1a1a1a'); controls.pack(fill=tk.X)
    tk.Label(controls, text="Title:", bg='#1a1a1a', fg='white').pack(side=tk.LEFT)
    title_var = tk.StringVar(); tk.Entry(controls, textvariable=title_var, width=28).pack(side=tk.LEFT, padx=6)
    tk.Button(controls, text="Search", bg='#4CAF50', fg='white', command=lambda: load_list()).pack(side=tk.LEFT)

    list_holder = tk.Frame(content, bg='#1a1a1a'); list_holder.pack(fill=tk.BOTH, expand=True, pady=10)

    def load_list():
        for w in list_holder.winfo_children():
            w.destroy()
        query = "SELECT movie_id, title, average_rating FROM movies"
        params = []
        if title_var.get().strip():
            query += " WHERE title LIKE ?"; params.append(f"%{title_var.get().strip()}%")
        rows = db.execute_query(query, tuple(params) if params else None, fetch_all=True)
        if not rows:
            tk.Label(list_holder, text="No movies found", bg='#1a1a1a', fg='#888', font=('Arial', 12)).pack(pady=20)
            return
        table = tk.Frame(list_holder, bg='#1a1a1a'); table.pack(fill=tk.BOTH, expand=True)
        header_bg = '#333'
        cols = ["Title", "Avg Rating", "Actions"]
        header = tk.Frame(table, bg=header_bg); header.grid(row=0, column=0, columnspan=3, sticky='ew')
        for i, c in enumerate(cols):
            tk.Label(header, text=c, font=('Arial', 11, 'bold'), bg=header_bg, fg='white', padx=10, pady=8).grid(row=0, column=i, sticky='w')
            header.grid_columnconfigure(i, weight=1)
        for r, m in enumerate(rows, start=1):
            rowf = tk.Frame(table, bg='#2a2a2a'); rowf.grid(row=r, column=0, sticky='ew', pady=2)
            for i in range(3): rowf.grid_columnconfigure(i, weight=1)
            tk.Label(rowf, text=m['title'], bg='#2a2a2a', fg='white', font=('Arial', 10), padx=10, pady=6, anchor='w').grid(row=0, column=0, sticky='ew')
            tk.Label(rowf, text=str(m.get('average_rating') or 0), bg='#2a2a2a', fg='#ccc', font=('Arial', 10), padx=10, pady=6, anchor='w').grid(row=0, column=1, sticky='ew')
            actions = tk.Frame(rowf, bg='#2a2a2a'); actions.grid(row=0, column=2, sticky='e', padx=8)
            tk.Button(actions, text="Delete Movie", bg='#d32f2f', fg='white', command=lambda mid=m['movie_id']: app.admin_delete_movie(mid)).pack(side=tk.LEFT, padx=4)
    load_list()
