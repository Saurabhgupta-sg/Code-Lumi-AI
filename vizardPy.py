import customtkinter as ctk
import tkinter as tk
from tkinter import filedialog, messagebox
import subprocess
import os
import tempfile
import ollama
import webbrowser
import ast
import pyttsx3
import threading
from PIL import Image, ImageTk

# --- MODERN THEME SETUP ---
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

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

# --- INITIALIZE THE SPEECH ENGINE ---
try:
    tts_engine = pyttsx3.init()
except Exception as e:
    print(f"Warning: Could not initialize Text-to-Speech engine: {e}")

# --- ANIMATION ENGINE (Using Pillow) ---
def load_gif_frames():
    """Loads all frames from the mascot GIF using a reliable, absolute path."""
    global gif_frames
    try:
        # --- ROBUST FILE PATH ---
        # Get the absolute directory where this script is located
        script_dir = os.path.dirname(os.path.abspath(__file__))
        # Create the full path to where the mascot SHOULD be
        mascot_path = os.path.join(script_dir, "mascot.gif")

        # --- DIAGNOSTIC PRINT ---
        print(f"Attempting to load mascot from: {mascot_path}")

        if os.path.exists(mascot_path):
            with Image.open(mascot_path) as im:
                im.seek(0)
                while True:
                    frame = im.copy().resize((200, 200), Image.Resampling.LANCZOS)
                    gif_frames.append(ImageTk.PhotoImage(frame))
                    im.seek(im.tell() + 1)
            print("SUCCESS: Mascot GIF loaded successfully.")
        else:
            print("ERROR: Mascot file not found at the path above.")
            
    except EOFError:
        # This is a normal and expected way to end the loop
        print("SUCCESS: Reached end of GIF frames.")
    except Exception as e:
        print(f"CRITICAL ERROR loading GIF: {e}")


def update_animation(label):
    """Cycles through the loaded GIF frames to create animation."""
    global gif_frame_index, animation_after_id
    if not gif_frames: return

    frame = gif_frames[gif_frame_index]
    label.configure(image=frame)
    gif_frame_index = (gif_frame_index + 1) % len(gif_frames)
    animation_after_id = root.after(50, update_animation, label)

def stop_animation():
    """Stops the animation loop."""
    if animation_after_id:
        root.after_cancel(animation_after_id)

# --- AI & ANIMATION FUNCTIONS ---
def speak_text(text, mascot_label):
    def run_tts():
        try:
            mascot_frame.place(relx=0.02, rely=0.98, anchor="sw")
            mascot_frame.lift() # Bring to front
            update_animation(mascot_label)
            
            tts_engine.say(text)
            tts_engine.runAndWait()
        except Exception as e:
            print(f"TTS Error: {e}")
        finally:
            stop_animation()
            mascot_label.place_forget()
            
    if tts_engine and gif_frames:
        threading.Thread(target=run_tts, daemon=True).start()
    else:
        display_to_console("TTS/Mascot not available. Make sure 'mascot.gif' is in the folder.\n\n" + text)

def get_friendly_error_explanation(lang, code, raw_error):
    try:
        # Using a more direct Qwen prompt for error explanation
        prompt = f"Explain this {lang} error in a simple, friendly way for a beginner. The error is: {raw_error}. The code is: ```{lang}\n{code}\n```. Give a 'What went wrong' and a 'How to fix it' section."
        response = ollama.chat(model='qwen:1.8b', messages=[{'role': 'user', 'content': prompt}]) # Switched to a standard qwen model for broader compatibility
        explanation = response['message']['content']
        speak_text(explanation, mascot_label)
        return explanation
    except Exception as e:
        return f"Could not connect to local AI. Raw Error:\n{raw_error}. AI Error: {e}"

def explain_standard_code():
    code = standard_editor.get("1.0", "end-1c").strip()
    if not code: return
    display_to_console("🤖 Code Lumi AI is thinking...")
    root.update()
    try:
        prompt = f"Explain what this {current_language} code does in one simple sentence. Be very concise.\n\n```{current_language}\n{code}\n```"
        response = ollama.chat(model='qwen:1.8b', messages=[{'role': 'user', 'content': prompt}])
        explanation = response['message']['content']
        display_to_console(f"🤖 Code Lumi AI says:\n\n{explanation}")
        speak_text(explanation, mascot_label)
    except Exception as e: 
        display_to_console(f"AI Error: {e}")

# --- EXECUTION ENGINE ---
def execute_code_in_memory(lang, code):
    if not code.strip(): return "Error: No code to run."
    try:
        if lang in ["Python", "Python (.ipynb)"]:
            try:
                tree = ast.parse(code)
                if tree.body and isinstance(tree.body[-1], ast.Expr):
                    tree.body[-1] = ast.Expr(value=ast.Call(func=ast.Name(id='print', ctx=ast.Load()), args=[tree.body[-1].value], keywords=[]))
                    code = ast.unparse(tree)
            except (SyntaxError, IndexError): pass
            process = subprocess.run(['python', '-c', code], capture_output=True, text=True, encoding='utf-8')
            if process.stderr: return get_friendly_error_explanation(lang, code, process.stderr)
            return process.stdout
        # ... (rest of the execute function is the same)
        elif lang == "JavaScript":
            process = subprocess.run(['node', '-e', code], capture_output=True, text=True, encoding='utf-8')
            if process.stderr: return get_friendly_error_explanation(lang, code, process.stderr)
            return process.stdout
        elif lang in ["C", "C++", "Java"]:
            temp_dir = tempfile.gettempdir()
            if lang == "Java": temp_src, temp_exe = os.path.join(temp_dir, "TempApp.java"), None
            else:
                ext = ".c" if lang == "C" else ".cpp"
                temp_src, temp_exe = os.path.join(temp_dir, f"temp_code{ext}"), os.path.join(temp_dir, "temp_app.exe")
            with open(temp_src, "w", encoding="utf-8") as f: f.write(code)
            output = ""
            try:
                if lang == "C":
                    comp = subprocess.run(['gcc', temp_src, '-o', temp_exe], capture_output=True, text=True, encoding='utf-8')
                    output = get_friendly_error_explanation(lang, code, comp.stderr) if comp.stderr else subprocess.run([temp_exe], capture_output=True, text=True, encoding='utf-8').stdout
                elif lang == "C++":
                    comp = subprocess.run(['g++', temp_src, '-o', temp_exe], capture_output=True, text=True, encoding='utf-8')
                    output = get_friendly_error_explanation(lang, code, comp.stderr) if comp.stderr else subprocess.run([temp_exe], capture_output=True, text=True, encoding='utf-8').stdout
                elif lang == "Java":
                    comp = subprocess.run(['javac', temp_src], capture_output=True, text=True, encoding='utf-8')
                    output = get_friendly_error_explanation(lang, code, comp.stderr) if comp.stderr else subprocess.run(['java', 'TempApp'], capture_output=True, text=True, cwd=temp_dir, encoding='utf-8').stdout
            finally:
                if os.path.exists(temp_src): os.remove(temp_src)
                if temp_exe and os.path.exists(temp_exe): os.remove(temp_exe)
                if os.path.exists(os.path.join(temp_dir, "TempApp.class")): os.remove(os.path.join(temp_dir, "TempApp.class"))
            return output
        elif lang == "HTML/CSS":
            temp_src = os.path.join(tempfile.gettempdir(), "temp_preview.html")
            with open(temp_src, "w", encoding="utf-8") as f: f.write(code)
            webbrowser.open('file://' + os.path.realpath(temp_src))
            return "HTML preview opened in default browser."
    except Exception as e: return f"Execution Error: {e}"

# --- STANDARD EDITOR & NOTEBOOK FUNCTIONS ---
def run_standard_code(event=None):
    display_to_console(f"Running {current_language} code...\n" + "-"*30 + "\n")
    root.update()
    output = execute_code_in_memory(current_language, standard_editor.get("1.0", "end-1c"))
    display_to_console(output)

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
    result = execute_code_in_memory("Python", code)
    cell["output"].configure(state="normal")
    cell["output"].delete("1.0", "end")
    cell["output"].insert("end", result)
    cell["output"].configure(state="disabled")

# --- FILE OPERATIONS & THEME ---
def trigger_dialog(dialog_func):
    global is_dialog_open
    is_dialog_open = True
    root.attributes('-topmost', False)
    dialog_func()
    root.attributes('-topmost', True)
    is_dialog_open = False

def save_file_as(event=None):
    global current_file_path
    if not current_language:
        trigger_dialog(lambda: messagebox.showwarning("Warning", "Please select a language first!"))
        return
    def do_save():
        file_path = filedialog.asksaveasfilename(title="Save File As", filetypes=[(f"{current_language} Files", f"*{file_extension}"), ("All Files", "*.*")], defaultextension=file_extension)
        if file_path:
            try:
                with open(file_path, "w", encoding="utf-8") as f: f.write(standard_editor.get("1.0", "end-1c"))
                current_file_path = file_path
                lbl_editor_title.configure(text=f"Code Editor - {current_language} ({os.path.basename(file_path)})")
            except Exception as e: messagebox.showerror("Error", f"Could not save file: {e}")
    trigger_dialog(do_save)

def save_file(event=None):
    if current_file_path:
        try:
            with open(current_file_path, "w", encoding="utf-8") as f: f.write(standard_editor.get("1.0", "end-1c"))
        except Exception as e: trigger_dialog(lambda: messagebox.showerror("Error", f"Could not save file: {e}"))
    else: save_file_as()

def open_file(event=None):
    global current_file_path, current_language, file_extension
    if not current_language:
        trigger_dialog(lambda: messagebox.showwarning("Warning", "Please select a language first!"))
        return
    def do_open():
        file_path = filedialog.askopenfilename(title="Open File", filetypes=[(f"{current_language} Files", f"*{file_extension}"), ("All Files", "*.*")])
        if file_path:
            try:
                with open(file_path, "r", encoding="utf-8") as f: content = f.read()
                standard_editor.delete("1.0", "end")
                standard_editor.insert("1.0", content)
                current_file_path = file_path
                lbl_editor_title.configure(text=f"Code Editor - {current_language} ({os.path.basename(file_path)})")
            except Exception as e: messagebox.showerror("Error", f"Could not read file: {e}")
    trigger_dialog(do_open)

def set_theme_dark(): ctk.set_appearance_mode("dark"); root.configure(bg="#1a1a1a")
def set_theme_light(): ctk.set_appearance_mode("light"); root.configure(bg="#f0f0f0")

# --- NAVIGATION & SECURITY ---
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
    page2_editor.pack_forget(); page3_notebook.pack_forget()
    page1_selection.pack(fill="both", expand=True)

def on_focus_out(event):
    if is_dialog_open: return
    if root.focus_get() is None:
        def verify_loss():
            if root.focus_get() is None and not is_dialog_open:
                print("[SECURITY] Focus lost. Terminating Code Lumi AI...")
                root.destroy()
        root.after(100, verify_loss)

# ==========================================
# GUI SETUP
# ==========================================
root = tk.Tk()
root.title("Code Lumi AI")
root.configure(bg="#1a1a1a")
root.attributes('-fullscreen', True)
root.attributes('-topmost', True)

def start_security_monitoring():
    root.focus_force()
    root.bind("<FocusOut>", on_focus_out)
    print("[SECURITY] Code Lumi AI Fullscreen and Security activated.")
root.after(500, start_security_monitoring)

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

# --- MASCOT ANIMATION SETUP (NEW PILLOW METHOD) ---
mascot_frame = ctk.CTkFrame(root, fg_color="transparent")
mascot_label = ctk.CTkLabel(mascot_frame, text="", fg_color="transparent")
mascot_label.pack(expand=True, fill="both")
load_gif_frames()

# --- UI PAGES ---
top_frame = ctk.CTkFrame(root, height=50, corner_radius=0, fg_color=("#dcdcdc", "#1a1a1a"))
top_frame.pack(fill="x")
ctk.CTkLabel(top_frame, text="Code Lumi AI", font=("Arial", 20, "bold")).pack(side="left", padx=20, pady=15)
ctk.CTkButton(top_frame, text="❌ Close App", fg_color="#c0392b", hover_color="#e74c3c", command=root.destroy).pack(side="right", padx=20)

page1_selection = ctk.CTkFrame(root, fg_color="transparent")
page1_selection.pack(fill="both", expand=True)
ctk.CTkLabel(page1_selection, text="Select Programming Language", font=("Arial", 28, "bold")).pack(pady=(100, 40))
lang_frame = ctk.CTkFrame(page1_selection, fg_color="transparent")
lang_frame.pack()
languages = [("Python", ".py"), ("C", ".c"), ("C++", ".cpp"), ("Java", ".java"), ("JavaScript", ".js"), ("HTML/CSS", ".html"), ("C#", ".cs"), ("Python (.ipynb)", ".py")]
row, col = 0, 0
for lang, ext in languages:
    btn = ctk.CTkButton(lang_frame, text=lang, font=("Arial", 18, "bold"), width=200, height=80, corner_radius=15, command=lambda l=lang, e=ext: open_editor(l, e))
    btn.grid(row=row, column=col, padx=20, pady=20)
    col += 1
    if col > 3: col = 0; row += 1

page2_editor = ctk.CTkFrame(root, fg_color="transparent")
editor_header = ctk.CTkFrame(page2_editor, fg_color="transparent")
editor_header.pack(fill="x", padx=20, pady=10)
ctk.CTkButton(editor_header, text="⬅️ Back", width=80, command=back_to_selection).pack(side="left")
lbl_editor_title = ctk.CTkLabel(editor_header, text="Code Editor", font=("Arial", 18, "bold"))
lbl_editor_title.pack(side="left", padx=20)
standard_editor = ctk.CTkTextbox(page2_editor, font=("Consolas", 18), fg_color=("#ffffff", "#1e1e1e"), text_color=("#000000", "#ffffff"), border_width=2, border_color="#3b3b3b")
standard_editor.pack(fill="both", expand=True, padx=20, pady=5)
for binding in ["<Control-c>", "<Control-v>", "<Control-x>"]: standard_editor.bind(binding, lambda e: "break")
btn_frame = ctk.CTkFrame(page2_editor, fg_color="transparent")
btn_frame.pack(pady=10)
ctk.CTkButton(btn_frame, text="▶ Run (Alt+F9)", fg_color="#27ae60", hover_color="#2ecc71", font=("Arial", 16, "bold"), command=run_standard_code).pack(side="left", padx=10)
ctk.CTkButton(btn_frame, text="🤖 Ask Code Lumi", fg_color="#2980b9", hover_color="#3498db", font=("Arial", 16, "bold"), command=explain_standard_code).pack(side="left", padx=10)
ctk.CTkLabel(page2_editor, text="Output Console:", font=("Arial", 14, "bold")).pack(anchor="w", padx=20)
standard_console = ctk.CTkTextbox(page2_editor, height=150, font=("Consolas", 16), fg_color=("#e6e6e6", "#000000"), text_color=("#000000", "#ecf0f1"))
standard_console.pack(fill="x", padx=20, pady=(0, 20))
standard_console.configure(state="disabled")

page3_notebook = ctk.CTkFrame(root, fg_color="transparent")
notebook_header = ctk.CTkFrame(page3_notebook, fg_color="transparent")
notebook_header.pack(fill="x", padx=20, pady=10)
ctk.CTkButton(notebook_header, text="⬅️ Back", width=80, command=back_to_selection).pack(side="left")
ctk.CTkLabel(notebook_header, text="Code Lumi AI - Jupyter Notebook", font=("Arial", 18, "bold")).pack(side="left", padx=20)
ctk.CTkButton(notebook_header, text="➕ Add Cell", fg_color="#2980b9", command=add_notebook_cell).pack(side="right", padx=20)
notebook_scroll_frame = ctk.CTkScrollableFrame(page3_notebook, fg_color=("#efefef", "#1a1a1a"))
notebook_scroll_frame.pack(fill="both", expand=True, padx=20, pady=10)

root.mainloop()

