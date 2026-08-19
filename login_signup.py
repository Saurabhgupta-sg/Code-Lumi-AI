"""CustomTkinter login and sign-up frontend for Code Lumi AI."""

from __future__ import annotations

import customtkinter as ctk

from auth_database import AuthenticatedUser, UserDatabase


ACCENT = "#6C63FF"
ACCENT_HOVER = "#827BFF"
PANEL = "#171A2B"
CARD = "#20243A"
MUTED = "#9CA3B8"
SUCCESS = "#30C48D"
ERROR = "#FF6B7A"


class LoginSignupWindow(ctk.CTk):
    """Blocking authentication window that returns the signed-in user."""

    def __init__(self, database: UserDatabase | None = None) -> None:
        super().__init__()
        self.database = database or UserDatabase()
        self.authenticated_user: AuthenticatedUser | None = None
        self.password_is_visible = False

        self.title("Code Lumi AI - Welcome")
        self.configure(fg_color="#0D1020")
        self.withdraw()
        self.protocol("WM_DELETE_WINDOW", self._close)
        self.bind("<F11>", self._close)
        self.bind("<Escape>", self._close)

        self.grid_columnconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        self._build_brand_panel()
        self.form_panel = ctk.CTkFrame(
            self,
            fg_color=PANEL,
            corner_radius=24,
            border_width=1,
            border_color="#303653",
        )
        self.form_panel.grid(row=0, column=1, sticky="nsew", padx=(12, 32), pady=32)
        self.form_panel.grid_columnconfigure(0, weight=1)
        self._show_login()

        # Apply fullscreen only after CustomTkinter has finished calculating its
        # requested content size. Calling fullscreen before this point can leave
        # a borderless window at roughly 1050x680 on Windows.
        self.after(50, self._force_fullscreen)
        self.after(1200, self._activate_focus_security)

    def _force_fullscreen(self) -> None:
        """Cover the complete monitor, including on scaled Windows displays."""
        try:
            self.deiconify()
            self.update_idletasks()
            screen_width = self.winfo_screenwidth()
            screen_height = self.winfo_screenheight()

            # Bypass CTk's geometry scaling and send the pixel dimensions
            # directly to Tk's window manager.
            self.overrideredirect(True)
            self.tk.call(
                "wm",
                "geometry",
                self._w,
                f"{screen_width}x{screen_height}+0+0",
            )
            self.attributes("-fullscreen", True)
            self.attributes("-topmost", True)
            self.lift()
            self.focus_force()
        except Exception:
            # Native maximize is a safe fallback if a window manager does not
            # support Tk's fullscreen attribute.
            self.deiconify()
            try:
                self.state("zoomed")
            except Exception:
                pass

    def _activate_focus_security(self) -> None:
        """Close authentication if the user switches away from the app."""
        self.focus_force()
        self.bind("<FocusOut>", self._on_focus_out)

    def _on_focus_out(self, _event=None) -> None:
        def verify_focus_loss() -> None:
            try:
                if self.focus_get() is None:
                    self._close()
            except Exception:
                pass

        self.after(200, verify_focus_loss)

    def _build_brand_panel(self) -> None:
        brand = ctk.CTkFrame(self, fg_color="#11152A", corner_radius=24)
        brand.grid(row=0, column=0, sticky="nsew", padx=(32, 12), pady=32)
        brand.grid_columnconfigure(0, weight=1)
        brand.grid_rowconfigure(3, weight=1)

        ctk.CTkLabel(
            brand,
            text="</>",
            width=82,
            height=82,
            corner_radius=22,
            fg_color=ACCENT,
            text_color="white",
            font=("Consolas", 30, "bold"),
        ).grid(row=0, column=0, padx=44, pady=(64, 28), sticky="w")
        ctk.CTkLabel(
            brand,
            text="Code Lumi AI",
            text_color="white",
            font=("Arial", 34, "bold"),
        ).grid(row=1, column=0, padx=44, sticky="w")
        ctk.CTkLabel(
            brand,
            text="Learn, build, and understand code\nwith your AI coding companion.",
            justify="left",
            text_color=MUTED,
            font=("Arial", 18),
        ).grid(row=2, column=0, padx=44, pady=(14, 0), sticky="w")

        features = ctk.CTkFrame(brand, fg_color="transparent")
        features.grid(row=3, column=0, padx=44, pady=50, sticky="sw")
        for index, text in enumerate(
            ("Run code in multiple languages", "Friendly AI error explanations", "Visual Python code animation")
        ):
            ctk.CTkLabel(
                features,
                text=f"✓  {text}",
                text_color="#D7DAE8",
                font=("Arial", 15),
            ).grid(row=index, column=0, pady=7, sticky="w")

    def _clear_form(self) -> None:
        for widget in self.form_panel.winfo_children():
            widget.destroy()
        self.password_is_visible = False

    def _form_header(self, title: str, subtitle: str) -> None:
        ctk.CTkLabel(
            self.form_panel,
            text=title,
            text_color="white",
            font=("Arial", 30, "bold"),
        ).grid(row=0, column=0, padx=56, pady=(62, 8), sticky="w")
        ctk.CTkLabel(
            self.form_panel,
            text=subtitle,
            text_color=MUTED,
            font=("Arial", 15),
        ).grid(row=1, column=0, padx=56, pady=(0, 26), sticky="w")

    def _entry(self, row: int, placeholder: str, password: bool = False) -> ctk.CTkEntry:
        entry = ctk.CTkEntry(
            self.form_panel,
            height=50,
            corner_radius=12,
            border_width=1,
            border_color="#3A405F",
            fg_color=CARD,
            text_color="white",
            placeholder_text=placeholder,
            placeholder_text_color="#7D849E",
            font=("Arial", 15),
            show="•" if password else "",
        )
        entry.grid(row=row, column=0, padx=56, pady=8, sticky="ew")
        return entry

    def _status_label(self, row: int) -> ctk.CTkLabel:
        label = ctk.CTkLabel(
            self.form_panel,
            text="",
            wraplength=370,
            justify="left",
            text_color=ERROR,
            font=("Arial", 13),
        )
        label.grid(row=row, column=0, padx=56, pady=(8, 0), sticky="w")
        return label

    def _primary_button(self, row: int, text: str, command) -> None:
        ctk.CTkButton(
            self.form_panel,
            text=text,
            height=50,
            corner_radius=12,
            fg_color=ACCENT,
            hover_color=ACCENT_HOVER,
            font=("Arial", 16, "bold"),
            command=command,
        ).grid(row=row, column=0, padx=56, pady=(18, 10), sticky="ew")

    def _switch_button(self, row: int, prompt: str, action: str, command) -> None:
        switch_frame = ctk.CTkFrame(self.form_panel, fg_color="transparent")
        switch_frame.grid(row=row, column=0, pady=12)
        ctk.CTkLabel(
            switch_frame,
            text=prompt,
            text_color=MUTED,
            font=("Arial", 14),
        ).pack(side="left")
        ctk.CTkButton(
            switch_frame,
            text=action,
            width=75,
            fg_color="transparent",
            hover_color=CARD,
            text_color="#9D98FF",
            font=("Arial", 14, "bold"),
            command=command,
        ).pack(side="left", padx=(4, 0))

    def _show_login(self) -> None:
        self._clear_form()
        self._form_header("Welcome back", "Sign in to continue to your workspace")
        self.login_identifier = self._entry(2, "Username or email")
        self.login_password = self._entry(3, "Password", password=True)
        self.login_status = self._status_label(4)
        self._primary_button(5, "Sign in", self._login)
        self._switch_button(6, "New to Code Lumi?", "Sign up", self._show_signup)
        self.login_identifier.focus_set()
        self.bind("<Return>", lambda _event: self._login())

    def _show_signup(self) -> None:
        self._clear_form()
        self._form_header("Create account", "Your workspace is only a few details away")
        self.signup_username = self._entry(2, "Username")
        self.signup_email = self._entry(3, "Email address")
        self.signup_password = self._entry(4, "Password (8+ characters)", password=True)
        self.signup_confirmation = self._entry(5, "Confirm password", password=True)
        self.signup_status = self._status_label(6)
        self._primary_button(7, "Create account", self._signup)
        self._switch_button(8, "Already have an account?", "Sign in", self._show_login)
        self.signup_username.focus_set()
        self.bind("<Return>", lambda _event: self._signup())

    def _login(self) -> None:
        user, message = self.database.authenticate(
            self.login_identifier.get(),
            self.login_password.get(),
        )
        if user is None:
            self.login_status.configure(text=message, text_color=ERROR)
            return
        self.login_status.configure(text=message, text_color=SUCCESS)
        self.authenticated_user = user
        self.after(150, self.destroy)

    def _signup(self) -> None:
        password = self.signup_password.get()
        if password != self.signup_confirmation.get():
            self.signup_status.configure(text="Passwords do not match.", text_color=ERROR)
            return

        user, message = self.database.create_user(
            self.signup_username.get(),
            self.signup_email.get(),
            password,
        )
        if user is None:
            self.signup_status.configure(text=message, text_color=ERROR)
            return

        self.signup_status.configure(text=message, text_color=SUCCESS)
        self.authenticated_user = user
        self.after(250, self.destroy)

    def _close(self, _event=None) -> None:
        self.authenticated_user = None
        self.destroy()


def show_auth_window() -> AuthenticatedUser | None:
    """Show the login/sign-up UI and return only after it is closed."""

    window = LoginSignupWindow()
    window.mainloop()
    return window.authenticated_user