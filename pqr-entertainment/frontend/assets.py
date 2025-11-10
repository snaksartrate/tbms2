import os
try:
    from PIL import Image, ImageTk
except Exception:
    Image = None
    ImageTk = None
import tkinter as tk
from tkinter import messagebox

def load_asset_image(rel_path: str, size: tuple[int, int], cache_list: list | None = None):
    """Load image from assets with Pillow, return PhotoImage or None.
    cache_list prevents GC by retaining a reference in Tk.
    """
    if not rel_path or not Image or not ImageTk:
        return None
    try:
        abs_path = os.path.join(os.path.dirname(__file__), '..', rel_path)
        abs_path = os.path.abspath(abs_path)
        if not os.path.isfile(abs_path):
            return None
        img = Image.open(abs_path).convert('RGB')
        img = img.resize(size, Image.LANCZOS)
        photo = ImageTk.PhotoImage(img)
        if cache_list is not None:
            cache_list.append(photo)
        return photo
    except Exception:
        return None

def show_toast(root: tk.Tk, message: str, duration_ms: int = 2000, bg: str = "#323232", fg: str = "white"):
    """Show a transient toast message overlay relative to root window."""
    try:
        toast = tk.Toplevel(root)
        toast.overrideredirect(True)
        toast.configure(bg=bg)
        # position bottom center
        root.update_idletasks()
        x = root.winfo_x() + (root.winfo_width() // 2) - 150
        y = root.winfo_y() + root.winfo_height() - 100
        toast.geometry(f"300x40+{x}+{y}")
        tk.Label(toast, text=message, bg=bg, fg=fg, font=('Arial', 10)).pack(expand=True, fill=tk.BOTH)
        toast.after(duration_ms, toast.destroy)
    except Exception:
        try:
            messagebox.showinfo("Info", message)
        except Exception:
            pass
