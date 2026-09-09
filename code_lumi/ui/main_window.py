import customtkinter as ctk
import tkinter as tk
from tkinter import filedialog, messagebox, simpledialog
import subprocess
import os
import pyttsx3
import threading
import sys
from PIL import Image, ImageTk
from pathlib import Path
from code_lumi.ui.admin_page import AdminPage
from code_lumi.ui.animation_page import AnimationPage
from code_lumi.execution.tracer import trace_python
from code_lumi.execution.runner import execute_code
from code_lumi.analyzer.ollama_analyzer import analyze_error, explain_code
from code_lumi.auth.database import UserDatabase
from code_lumi.ui.login_window import show_auth_window

PROJECT_DIR = Path(__file__).resolve().parents[2]
# --- MODERN THEME SETUP ---
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")
APP_BACKGROUND = ("#f0f0f0", "#1a1a1a")

# Authentication runs before the editor is created. Closing the login window
# exits the application; a successful login makes the user available to the UI.
authenticated_user = show_auth_window()
if authenticated_user is None:
    raise SystemExit(0)
user_database = UserDatabase()

# --- GLOBAL STATE ---
current_language = ""
file_extension = ""
notebook_cells = []
current_file_path = None
is_dialog_open = False
tts_engine = None
gif_frames = []
gif_frame_index = 0
animation_after_id = None

# Variables for Live Code Animation
execution_trace = []
is_animating = False

# --- INITIALIZE THE SPEECH ENGINE ---
# --- INITIALIZE THE SPEECH ENGINE ---
try:
    tts_engine = pyttsx3.init()
    
    # --- NEW: SET FEMALE VOICE ---
    voices = tts_engine.getProperty('voices')
    
    # Search through your computer's installed voices for a female one
    for voice in voices:
        voice_name = voice.name.lower()
        # "zira" and "hazel" are Windows female voices. "samantha" is Mac.
        if "zira" in voice_name or "samantha" in voice_name or "hazel" in voice_name or "female" in voice_name:
            tts_engine.setProperty('voice', voice.id)
            break
    else:
        # Fallback: On Windows, index 1 is almost always the female voice (Zira)
        if len(voices) > 1:
            tts_engine.setProperty('voice', voices[1].id)
            
    # Optional: You can also slow down her speaking rate a bit so it's easier to understand!
    # current_rate = tts_engine.getProperty('rate')
    # tts_engine.setProperty('rate', 175) # Default is usually 200

except Exception as e:
    print(f"Warning: Could not initialize Text-to-Speech engine: {e}")

# --- MASCOT ANIMATION ENGINE (Using Pillow) ---
def load_gif_frames():
    global gif_frames
    gif_frames = []
    try:
        mascot_path = PROJECT_DIR / "mascot.gif"
        if os.path.exists(mascot_path):
            with Image.open(mascot_path) as im:
                im.seek(0)
                while True:
                    frame = im.copy().resize((150, 150), Image.Resampling.LANCZOS)
                    gif_frames.append(ImageTk.PhotoImage(frame))
                    im.seek(im.tell() + 1)
    except EOFError:
        pass
    except Exception as e:
        print(f"Error loading GIF: {e}")

def update_animation(label):
    global gif_frame_index, animation_after_id
    if not gif_frames: return
    frame = gif_frames[gif_frame_index]
    label.configure(image=frame)
    label.image = frame 
    gif_frame_index = (gif_frame_index + 1) % len(gif_frames)
    animation_after_id = root.after(50, update_animation, label)

def stop_animation():
    if animation_after_id:
        root.after_cancel(animation_after_id)

# --- AI & SPEECH FUNCTIONS ---
def speak_text(text, mascot_label):
    def run_tts():
        try:
            mascot_frame.place(relx=0.02, rely=0.98, anchor="sw")
            mascot_frame.lift()
            if gif_frames: update_animation(mascot_label)
            tts_engine.say(text)
            tts_engine.runAndWait()
        except Exception as e:
            print(f"TTS Error: {e}")
        finally:
            stop_animation()
            mascot_frame.place_forget()
            
    if tts_engine:
        threading.Thread(target=run_tts, daemon=True).start()
    else:
        display_to_console("TTS unavailable.\n\n" + text)

def highlight_error_line(line_no):
    """Highlights the offending line in the standard code editor, red-on-white,
    similar to the yellow 'currently running' highlight used in the animator."""
    try:
        standard_editor.tag_remove("error_highlight", "1.0", "end")
        if not line_no:
            return
        standard_editor.tag_add("error_highlight", f"{line_no}.0", f"{line_no}.end")
        standard_editor.tag_config("error_highlight", background="#f14c4c", foreground="white")
        standard_editor.see(f"{line_no}.0")
    except Exception:
        pass  # editor may not exist yet (e.g. called before UI is built)

def get_friendly_error_explanation(lang, code, raw_error):
    """Analyze an error and display the result in the current UI."""

    try:
        analysis = analyze_error(
            language=lang,
            code=code,
            raw_error=raw_error,
        )

        highlight_error_line(analysis.issue_line)

        if analysis.explanation:
            speak_text(analysis.explanation, mascot_label)

        return analysis.display_text

    except Exception as error:
        return f"AI Error: {error}\nRaw Error:\n{raw_error}"

def explain_standard_code():
    """Explain the code currently displayed in the editor."""

    code = standard_editor.get("1.0", "end-1c").strip()
    if not code:
        return

    display_to_console("🤖 Code Lumi AI is thinking...")
    root.update()

    try:
        explanation = explain_code(
            language=current_language,
            code=code,
        )

        display_to_console(f"🤖 Code Lumi AI says:\n\n{explanation}")
        speak_text(explanation, mascot_label)

    except Exception as error:
        display_to_console(f"AI Error: {error}")

# --- NEW: IN-APP LIVE CODE ANIMATOR ---

def start_code_animation():
    """Generate a Python trace and open the animation player."""

    if current_language not in [
        "Python",
        "Python (.ipynb)",
    ]:
        messagebox.showwarning(
            "Not Supported",
            "Animation is only available for Python!",
        )
        return

    code = standard_editor.get(
        "1.0",
        "end-1c",
    ).strip()

    if not code:
        return

    global execution_trace, is_animating
    execution_trace = []

    try:
        execution_trace = trace_python(code)

    except Exception as error:
        messagebox.showerror(
            "Error",
            f"Animation stopped due to code error: {error}",
        )
        return

    if not execution_trace:
        messagebox.showinfo(
            "Info",
            "No executable steps were found in the code.",
        )
        return

    page2_editor.pack_forget()
    page4_animation.pack(
        fill="both",
        expand=True,
    )

    anim_code_display.configure(state="normal")
    anim_code_display.delete("1.0", "end")
    anim_code_display.insert("1.0", code)
    anim_code_display.configure(state="disabled")

    if gif_frames:
        anim_mascot_label.place(
            relx=0.85,
            rely=0.05,
        )
        update_animation(anim_mascot_label)

    is_animating = True
    play_trace_step(0)

def exit_animation():
    """Stops animation and returns to the editor."""
    global is_animating
    is_animating = False
    stop_animation()
    anim_mascot_label.place_forget()
    page4_animation.pack_forget()
    page2_editor.pack(fill="both", expand=True)

def play_trace_step(step_index):
    """Plays back the animation frame-by-frame."""
    if not is_animating: return 

    if step_index >= len(execution_trace):
        anim_status_label.configure(text="✅ Execution Complete!")
        anim_code_display.tag_remove("highlight", "1.0", "end")
        stop_animation()
        return

    step = execution_trace[step_index]
    line_no = step.line
    variables = step.variables

    # 1. Highlight Code Line (Yellow Video Style)
    anim_code_display.tag_remove("highlight", "1.0", "end")
    anim_code_display.tag_add("highlight", f"{line_no}.0", f"{line_no}.end")
    anim_code_display.tag_config("highlight", background="#f1c40f", foreground="black")
    
    anim_status_label.configure(text=f"▶ Running Line {line_no}...")

    # 2. Render Variables as 3D-looking visual "objects"
    for widget in anim_memory_frame.winfo_children():
        widget.destroy() 
        
    for name, data in variables.items():
        v_type = data["type"]
        val = data["value"]
        
        # Pick cute icons based on data type!
        if v_type in ["int", "float"]: icon, color = "🔢", "#c0392b" # Red
        elif v_type == "str": icon, color = "📝", "#f39c12" # Yellow
        elif v_type in ["list", "dict"]: icon, color = "📚", "#8e44ad" # Purple
        elif v_type == "bool": icon, color = "⚖️", "#27ae60" # Green
        else: icon, color = "📦", "#34495e" # Blue/Gray

        var_card = ctk.CTkFrame(anim_memory_frame, fg_color=color, corner_radius=8)
        var_card.pack(fill="x", pady=5)
        ctk.CTkLabel(var_card, text=f"{icon} {name}", font=("Arial", 16, "bold"), text_color="white").pack(side="left", padx=15, pady=10)
        ctk.CTkLabel(var_card, text=f"➡️   {val}", font=("Consolas", 16, "bold"), text_color="white").pack(side="right", padx=15, pady=10)

    # 3. Schedule next "frame" (1.5 seconds)
    if is_animating:
        root.after(1500, lambda: play_trace_step(step_index + 1))

# --- EXECUTION ENGINE (Standard Run) ---
def execute_code_in_memory(lang, code):
    """Send code to the independent execution service."""

    return execute_code(
        language=lang,
        code=code,
        explain_error=get_friendly_error_explanation,
    )

def run_standard_code(event=None):
    highlight_error_line(None)  # clear any highlight from a previous run
    display_to_console(f"Running {current_language} code...\n" + "-"*30 + "\n")
    root.update()
    try:
        output = execute_code_in_memory(current_language, standard_editor.get("1.0", "end-1c"))
    except Exception:
        import traceback
        traceback.print_exc()  # full traceback goes to the terminal so it's never truly invisible
        output = "Something went wrong running this code. Check the terminal window for the full error."
    if not output or not str(output).strip():
        output = "(No output, and no error was reported.)"
    try:
        display_to_console(output)
    except Exception:
        import traceback
        traceback.print_exc()
        display_to_console("Ran, but couldn't render the output. Check the terminal window.")

def display_to_console(text):
    standard_console.configure(state="normal")
    standard_console.delete("1.0", "end")
    standard_console.insert("end", text)
    standard_console.configure(state="disabled")

def add_notebook_cell():
    cell_idx = len(notebook_cells)
    cell_frame = ctk.CTkFrame(notebook_scroll_frame, corner_radius=10, fg_color=("#e0e0e0", "#2b2b2b"))
    cell_frame.pack(fill="x", padx=20, pady=10)
    top_row = ctk.CTkFrame(cell_frame, fg_color="transparent")
    top_row.pack(fill="x", padx=10, pady=5)
    ctk.CTkLabel(top_row, text=f"In [{cell_idx + 1}]:", font=("Arial", 14, "bold"), text_color="#3498db").pack(side="left")
    cell_editor = ctk.CTkTextbox(cell_frame, height=100, font=("Consolas", 16), fg_color=("#ffffff", "#1e1e1e"), border_color="#3b3b3b", border_width=1)
    cell_editor.pack(fill="x", padx=10, pady=5)
    for binding in ["<Control-c>", "<Control-v>", "<Control-x>"]: cell_editor.bind(binding, lambda e: "break")
    cell_editor.bind("<Shift-Return>", lambda event, idx=cell_idx: handle_shift_enter(event, idx))
    bot_row = ctk.CTkFrame(cell_frame, fg_color="transparent")
    bot_row.pack(fill="x", padx=10, pady=5)
    ctk.CTkLabel(bot_row, text=f"Out[{cell_idx + 1}]:", font=("Arial", 14, "bold"), text_color="#e74c3c").pack(side="left")
    ctk.CTkButton(bot_row, text="▶ Run Cell", fg_color="#27ae60", hover_color="#2ecc71", font=("Arial", 12, "bold"), command=lambda idx=cell_idx: run_notebook_cell(idx)).pack(side="right")
    cell_output = ctk.CTkTextbox(cell_frame, height=50, font=("Consolas", 14), fg_color=("#f5f5f5", "#1e1e1e"), text_color=("#333333", "#ecf0f1"))
    cell_output.pack(fill="x", padx=10, pady=5)
    cell_output.configure(state="disabled")
    notebook_cells.append({"editor": cell_editor, "output": cell_output})

def handle_shift_enter(event, idx):
    run_notebook_cell(idx)
    return "break"

def run_notebook_cell(idx):
    cell = notebook_cells[idx]
    code = cell["editor"].get("1.0", "end-1c").strip()
    cell["output"].configure(state="normal")
    cell["output"].delete("1.0", "end")
    cell["output"].insert("end", "Running...")
    cell["output"].configure(state="disabled")
    root.update()
    result = execute_code_in_memory("Python (.ipynb)", code)
    cell["output"].configure(state="normal")
    cell["output"].delete("1.0", "end")
    cell["output"].insert("end", result)
    cell["output"].configure(state="disabled")

# --- FILE OPERATIONS ---
def safe_dialog(dialog_func):
    global is_dialog_open
    is_dialog_open = True
    root.attributes('-topmost', False)
    try:
        return dialog_func()
    finally:
        root.attributes('-topmost', True)
        root.lift()
        root.focus_force()
        is_dialog_open = False

def save_file_as(event=None):
    global current_file_path
    if not current_language: return
    def do_save():
        path = filedialog.asksaveasfilename(title="Save File As", filetypes=[(f"{current_language} Files", f"*{file_extension}"), ("All Files", "*.*")], defaultextension=file_extension)
        if path:
            with open(path, "w", encoding="utf-8") as f: f.write(standard_editor.get("1.0", "end-1c"))
            globals().update(current_file_path=path)
            lbl_editor_title.configure(text=f"Code Editor - {current_language} ({os.path.basename(path)})")
    safe_dialog(do_save)

def save_file(event=None):
    if current_file_path:
        with open(current_file_path, "w", encoding="utf-8") as f: f.write(standard_editor.get("1.0", "end-1c"))
    else: save_file_as()

def open_file(event=None):
    global current_file_path, current_language, file_extension
    if not current_language: return
    def do_open():
        path = filedialog.askopenfilename(title="Open File", filetypes=[(f"{current_language} Files", f"*{file_extension}"), ("All Files", "*.*")])
        if path:
            with open(path, "r", encoding="utf-8") as f: content = f.read()
            standard_editor.delete("1.0", "end")
            standard_editor.insert("1.0", content)
            globals().update(current_file_path=path)
            lbl_editor_title.configure(text=f"Code Editor - {current_language} ({os.path.basename(path)})")
    safe_dialog(do_open)

def set_theme_dark():
    ctk.set_appearance_mode("dark")
    root.configure(bg="#1a1a1a")
    root.update_idletasks()

def set_theme_light():
    ctk.set_appearance_mode("light")
    root.configure(bg="#f0f0f0")
    root.update_idletasks()

def open_editor(lang, ext):
    global current_language, file_extension, current_file_path
    current_language, file_extension, current_file_path = lang, ext, None
    page1_selection.pack_forget()
    if lang == "Python (.ipynb)":
        page3_notebook.pack(fill="both", expand=True)
        if not notebook_cells: add_notebook_cell()
    else:
        page2_editor.pack(fill="both", expand=True)
        lbl_editor_title.configure(text=f"Code Editor - {lang}")
        standard_editor.delete("1.0", "end")
        display_to_console("Ready (In-Memory Sandbox Active).")

def back_to_selection():
    page2_editor.pack_forget(); page3_notebook.pack_forget(); page4_animation.pack_forget(); page5_admin.pack_forget()
    page1_selection.pack(fill="both", expand=True)

# --- ADMINISTRATOR USER MANAGEMENT ---
def set_admin_status(message, success=False):
    admin_status_label.configure(
        text=message,
        text_color="#198754" if success else "#dc3545",
    )

def open_admin_panel():
    if authenticated_user.role != "admin":
        safe_dialog(lambda: messagebox.showerror("Access denied", "Administrator access is required.", parent=root))
        return
    page1_selection.pack_forget()
    page2_editor.pack_forget()
    page3_notebook.pack_forget()
    page4_animation.pack_forget()
    page5_admin.pack(fill="both", expand=True)
    refresh_admin_users()

def refresh_admin_users():
    for widget in admin_users_scroll.winfo_children():
        widget.destroy()

    users, message = user_database.list_users(authenticated_user.id)
    if not users:
        set_admin_status(message)
        return

    admin_user_count_label.configure(text=f"{len(users)} account{'s' if len(users) != 1 else ''}")
    for user in users:
        user_card = ctk.CTkFrame(
            admin_users_scroll,
            fg_color=("#f4f6fb", "#2b304a"),
            corner_radius=12,
        )
        user_card.pack(fill="x", padx=8, pady=6)

        identity = ctk.CTkFrame(user_card, fg_color="transparent")
        identity.pack(side="left", fill="x", expand=True, padx=16, pady=12)
        ctk.CTkLabel(
            identity,
            text=f"{user.username}  {'(You)' if user.id == authenticated_user.id else ''}",
            font=("Arial", 15, "bold"),
        ).pack(anchor="w")
        ctk.CTkLabel(
            identity,
            text=user.email,
            text_color=("#64748b", "#a8b0c5"),
            font=("Arial", 13),
        ).pack(anchor="w", pady=(3, 0))

        role_color = "#7c3aed" if user.role == "admin" else "#2563eb"
        ctk.CTkLabel(
            user_card,
            text=user.role.upper(),
            width=80,
            height=30,
            corner_radius=9,
            fg_color=role_color,
            text_color="white",
            font=("Arial", 11, "bold"),
        ).pack(side="left", padx=8)

        ctk.CTkButton(
            user_card,
            text="Change password",
            width=130,
            fg_color="#d97706",
            hover_color="#f59e0b",
            command=lambda user_id=user.id, username=user.username: admin_change_password(user_id, username),
        ).pack(side="left", padx=6)

        delete_button = ctk.CTkButton(
            user_card,
            text="Delete",
            width=85,
            fg_color="#c0392b",
            hover_color="#e74c3c",
            command=lambda user_id=user.id, username=user.username: admin_delete_user(user_id, username),
        )
        delete_button.pack(side="left", padx=(6, 14))
        if user.id == authenticated_user.id:
            delete_button.configure(state="disabled", fg_color="#6b7280")

def admin_add_user():
    user, message = user_database.create_user_as_admin(
        authenticated_user.id,
        admin_username_entry.get(),
        admin_email_entry.get(),
        admin_password_entry.get(),
        admin_role_menu.get(),
    )
    if user is None:
        set_admin_status(message)
        return

    for entry in (admin_username_entry, admin_email_entry, admin_password_entry):
        entry.delete(0, "end")
    admin_role_menu.set("user")
    set_admin_status(message, success=True)
    refresh_admin_users()

def admin_change_password(user_id, username):
    new_password = safe_dialog(
        lambda: simpledialog.askstring(
            "Change password",
            f"Enter a new password for {username}:",
            show="*",
            parent=root,
        )
    )
    if new_password is None:
        return
    confirmation = safe_dialog(
        lambda: simpledialog.askstring(
            "Confirm password",
            "Enter the new password again:",
            show="*",
            parent=root,
        )
    )
    if new_password != confirmation:
        set_admin_status("Passwords do not match.")
        return

    success, message = user_database.change_password_as_admin(
        authenticated_user.id,
        user_id,
        new_password,
    )
    set_admin_status(message, success=success)

def admin_delete_user(user_id, username):
    confirmed = safe_dialog(
        lambda: messagebox.askyesno(
            "Delete user",
            f"Permanently delete {username}?",
            parent=root,
        )
    )
    if not confirmed:
        return
    success, message = user_database.delete_user_as_admin(
        authenticated_user.id,
        user_id,
    )
    set_admin_status(message, success=success)
    if success:
        refresh_admin_users()

# --- BUG-FREE SECURITY MONITOR ---
def on_focus_out(event):
    if is_dialog_open: return
    if event.widget == root:
        def verify_loss():
            if root.focus_get() is None and not is_dialog_open:
                print("[SECURITY] Global focus lost. Terminating Code Lumi AI...")
                root.destroy()
        root.after(200, verify_loss)

# ==========================================
# GUI SETUP 
# ==========================================
root = tk.Tk() 
root.title("Code Lumi AI")
root.configure(bg="#1a1a1a")
root.withdraw()

def force_fullscreen():
    """Force the main window to cover the complete physical display."""
    try:
        root.deiconify()
        root.update_idletasks()

        screen_width = root.winfo_screenwidth()
        screen_height = root.winfo_screenheight()

        # Ask Tk for fullscreen and also set exact pixel bounds. The explicit
        # geometry fixes the small borderless window seen on some Windows DPI
        # configurations.
        root.overrideredirect(True)
        root.attributes('-fullscreen', True)
        root.attributes('-topmost', True)
        root.tk.call(
            "wm",
            "geometry",
            root._w,
            f"{screen_width}x{screen_height}+0+0",
        )

        # On Windows, use the physical monitor dimensions as the final source
        # of truth so 125%, 150%, or 200% display scaling cannot shrink it.
        if sys.platform == "win32":
            try:
                import ctypes

                user32 = ctypes.windll.user32
                physical_width = user32.GetSystemMetrics(0)
                physical_height = user32.GetSystemMetrics(1)
                window_handle = user32.GetParent(root.winfo_id())
                user32.SetWindowPos(
                    window_handle,
                    -1,  # HWND_TOPMOST
                    0,
                    0,
                    physical_width,
                    physical_height,
                    0x0040,  # SWP_SHOWWINDOW
                )
            except Exception:
                pass

        root.lift()
        root.focus_force()
    except Exception as fullscreen_error:
        print(f"Warning: Could not enter fullscreen mode: {fullscreen_error}")
        root.deiconify()
        try:
            root.state("zoomed")
        except Exception:
            pass

root.after(75, force_fullscreen)

def activate_security():
    root.focus_force()
    root.bind("<FocusOut>", on_focus_out)

root.after(1000, activate_security)

def logout():
    """End this session and reliably reopen the login/sign-up screen."""
    confirmed = safe_dialog(
        lambda: messagebox.askyesno(
            "Log out",
            "Return to the login screen?",
            parent=root,
        )
    )
    if not confirmed:
        return

    # Disable the focus-loss shutdown while this process hands control to the
    # fresh login process. Hiding the current window prevents both screens from
    # appearing at the same time.
    root.unbind("<FocusOut>")
    root.attributes('-topmost', False)
    root.withdraw()
    root.update_idletasks()

    script_path = PROJECT_DIR / "main.py"
    try:
        subprocess.Popen(
            [sys.executable, str(script_path)],
            cwd=str(PROJECT_DIR),
        )
    except Exception as restart_error:
        root.deiconify()
        force_fullscreen()
        activate_security()
        safe_dialog(
            lambda: messagebox.showerror(
                "Logout failed",
                f"Could not reopen the login screen:\n{restart_error}",
                parent=root,
            )
        )
        return

    root.destroy()

root.bind("<F2>", save_file); root.bind("<F3>", open_file); root.bind("<Alt-F9>", run_standard_code)

menu_bar = tk.Menu(root)
file_menu = tk.Menu(menu_bar, tearoff=0)
file_menu.add_command(label="Open (F3)", command=open_file)
file_menu.add_command(label="Save (F2)", command=save_file)
file_menu.add_command(label="Save As...", command=save_file_as)
file_menu.add_separator()
file_menu.add_command(label="Close IDE", command=root.destroy)
menu_bar.add_cascade(label="File", menu=file_menu)
theme_menu = tk.Menu(menu_bar, tearoff=0)
theme_menu.add_command(label="Dark Mode 🌙", command=set_theme_dark)
theme_menu.add_command(label="Light Mode ☀️", command=set_theme_light)
menu_bar.add_cascade(label="Theme", menu=theme_menu)
root.config(menu=menu_bar)

mascot_frame = ctk.CTkFrame(root, fg_color=APP_BACKGROUND)
mascot_label = ctk.CTkLabel(mascot_frame, text="", fg_color="transparent")
mascot_label.pack(expand=True, fill="both")
load_gif_frames()

top_frame = ctk.CTkFrame(root, height=50, corner_radius=0, fg_color=("#dcdcdc", "#1a1a1a"))
top_frame.pack(fill="x")
ctk.CTkLabel(top_frame, text="Code Lumi AI", font=("Arial", 20, "bold")).pack(side="left", padx=20, pady=15)
ctk.CTkButton(top_frame, text="❌ Close App", fg_color="#c0392b", hover_color="#e74c3c", command=root.destroy).pack(side="right", padx=20)
ctk.CTkButton(top_frame, text="Log out", width=90, fg_color="#6c63ff", hover_color="#827bff", command=logout).pack(side="right", padx=(8, 0))
if authenticated_user.role == "admin":
    ctk.CTkButton(
        top_frame,
        text="👥 Manage Users",
        width=130,
        fg_color="#7c3aed",
        hover_color="#8b5cf6",
        command=open_admin_panel,
    ).pack(side="right", padx=(8, 0))
account_title = f"Signed in as {authenticated_user.username}"
if authenticated_user.role == "admin":
    account_title += " (Admin)"
ctk.CTkLabel(top_frame, text=account_title, font=("Arial", 14), text_color=("#475569", "#a8b0c5")).pack(side="right", padx=12)

# --- PAGE 1: SELECTION ---
page1_selection = ctk.CTkFrame(root, fg_color=APP_BACKGROUND)
page1_selection.pack(fill="both", expand=True)
ctk.CTkLabel(page1_selection, text="Select Programming Language", font=("Arial", 28, "bold")).pack(pady=(100, 40))
lang_frame = ctk.CTkFrame(page1_selection, fg_color=APP_BACKGROUND)
lang_frame.pack()
languages = [("Python", ".py"), ("C", ".c"), ("C++", ".cpp"), ("Java", ".java"), ("JavaScript", ".js"), ("HTML/CSS", ".html"), ("C#", ".cs"), ("Python (.ipynb)", ".py")]
row, col = 0, 0
for lang, ext in languages:
    btn = ctk.CTkButton(lang_frame, text=lang, font=("Arial", 18, "bold"), width=200, height=80, corner_radius=15, command=lambda l=lang, e=ext: open_editor(l, e))
    btn.grid(row=row, column=col, padx=20, pady=20)
    col += 1
    if col > 3: col = 0; row += 1

# --- PAGE 2: STANDARD EDITOR ---
page2_editor = ctk.CTkFrame(root, fg_color=APP_BACKGROUND)
editor_header = ctk.CTkFrame(page2_editor, fg_color=APP_BACKGROUND)
editor_header.pack(fill="x", padx=20, pady=10)
ctk.CTkButton(editor_header, text="⬅️ Back", width=80, command=back_to_selection).pack(side="left")
lbl_editor_title = ctk.CTkLabel(editor_header, text="Code Editor", font=("Arial", 18, "bold"))
lbl_editor_title.pack(side="left", padx=20)
standard_editor = ctk.CTkTextbox(page2_editor, font=("Consolas", 18), fg_color=("#ffffff", "#1e1e1e"), text_color=("#000000", "#ffffff"), border_width=2, border_color="#3b3b3b")
standard_editor.pack(fill="both", expand=True, padx=20, pady=5)
for binding in ["<Control-c>", "<Control-v>", "<Control-x>"]: standard_editor.bind(binding, lambda e: "break")

btn_frame = ctk.CTkFrame(page2_editor, fg_color=APP_BACKGROUND)
btn_frame.pack(pady=10)
ctk.CTkButton(btn_frame, text="▶ Run (Alt+F9)", fg_color="#27ae60", hover_color="#2ecc71", font=("Arial", 16, "bold"), command=run_standard_code).pack(side="left", padx=10)
ctk.CTkButton(btn_frame, text="🤖 Ask Code Lumi", fg_color="#2980b9", hover_color="#3498db", font=("Arial", 16, "bold"), command=explain_standard_code).pack(side="left", padx=10)
ctk.CTkButton(btn_frame, text="🎬 Auto-Animate Code", fg_color="#8e44ad", hover_color="#9b59b6", font=("Arial", 16, "bold"), command=start_code_animation).pack(side="left", padx=10)

ctk.CTkLabel(page2_editor, text="Output Console:", font=("Arial", 14, "bold")).pack(anchor="w", padx=20)
standard_console = ctk.CTkTextbox(page2_editor, height=150, font=("Consolas", 16), fg_color=("#e6e6e6", "#000000"), text_color=("#000000", "#ecf0f1"))
standard_console.pack(fill="x", padx=20, pady=(0, 20))
standard_console.configure(state="disabled")

# --- PAGE 3: JUPYTER NOTEBOOK ---
page3_notebook = ctk.CTkFrame(root, fg_color=APP_BACKGROUND)
notebook_header = ctk.CTkFrame(page3_notebook, fg_color=APP_BACKGROUND)
notebook_header.pack(fill="x", padx=20, pady=10)
ctk.CTkButton(notebook_header, text="⬅️ Back", width=80, command=back_to_selection).pack(side="left")
ctk.CTkLabel(notebook_header, text="Code Lumi AI - Jupyter Notebook", font=("Arial", 18, "bold")).pack(side="left", padx=20)
ctk.CTkButton(notebook_header, text="➕ Add Cell", fg_color="#2980b9", command=add_notebook_cell).pack(side="right", padx=20)
notebook_scroll_frame = ctk.CTkScrollableFrame(page3_notebook, fg_color=("#efefef", "#1a1a1a"))
notebook_scroll_frame.pack(fill="both", expand=True, padx=20, pady=10)

# --- PAGE 4: THE IN-APP ANIMATION PLAYER ---
animation_page = AnimationPage(
    parent=root,
    background=APP_BACKGROUND,
    stop_command=exit_animation,
)

# Temporary aliases allow the existing animation functions to keep working.
page4_animation = animation_page.frame
anim_status_label = animation_page.status_label
anim_code_display = animation_page.code_display
anim_memory_frame = animation_page.memory_frame
anim_mascot_label = animation_page.mascot_label

# --- PAGE 5: ADMINISTRATOR USER MANAGER ---
admin_page = AdminPage(
    parent=root,
    background=APP_BACKGROUND,
    back_command=back_to_selection,
    refresh_command=refresh_admin_users,
    add_user_command=admin_add_user,
)

# Temporary aliases allow the existing administrator functions to work.
page5_admin = admin_page.frame
admin_username_entry = admin_page.username_entry
admin_email_entry = admin_page.email_entry
admin_password_entry = admin_page.password_entry
admin_role_menu = admin_page.role_menu
admin_status_label = admin_page.status_label
admin_user_count_label = admin_page.user_count_label
admin_users_scroll = admin_page.users_scroll

root.mainloop()
