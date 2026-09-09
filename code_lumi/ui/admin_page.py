"""Administrator user-management interface."""

import customtkinter as ctk


class AdminPage:
    """Build and expose the administrator-page widgets."""

    def __init__(
        self,
        parent,
        background,
        back_command,
        refresh_command,
        add_user_command,
    ):
        self.frame = ctk.CTkFrame(
            parent,
            fg_color=background,
        )

        self._build_header(
            background,
            back_command,
            refresh_command,
        )

        self._build_content(
            background,
            add_user_command,
        )

    def _build_header(
        self,
        background,
        back_command,
        refresh_command,
    ):
        header = ctk.CTkFrame(
            self.frame,
            fg_color=background,
        )

        header.pack(
            fill="x",
            padx=28,
            pady=(20, 10),
        )

        ctk.CTkButton(
            header,
            text="⬅ Back",
            width=90,
            command=back_command,
        ).pack(side="left")

        ctk.CTkLabel(
            header,
            text="Administrator · User Management",
            font=("Arial", 25, "bold"),
        ).pack(
            side="left",
            padx=20,
        )

        ctk.CTkButton(
            header,
            text="↻ Refresh",
            width=100,
            fg_color="#2563eb",
            hover_color="#3b82f6",
            command=refresh_command,
        ).pack(side="right")

    def _build_content(
        self,
        background,
        add_user_command,
    ):
        content = ctk.CTkFrame(
            self.frame,
            fg_color=background,
        )

        content.pack(
            fill="both",
            expand=True,
            padx=28,
            pady=(8, 26),
        )

        self._build_add_user_panel(
            content,
            add_user_command,
        )

        self._build_user_list(content)

    def _build_add_user_panel(
        self,
        parent,
        add_user_command,
    ):
        add_panel = ctk.CTkFrame(
            parent,
            width=390,
            fg_color=("#ffffff", "#23283f"),
            corner_radius=16,
            border_width=1,
            border_color=("#d8deea", "#343b5c"),
        )

        add_panel.pack(
            side="left",
            fill="y",
            padx=(0, 14),
        )

        add_panel.pack_propagate(False)

        ctk.CTkLabel(
            add_panel,
            text="Add a new user",
            font=("Arial", 21, "bold"),
        ).pack(
            anchor="w",
            padx=26,
            pady=(30, 6),
        )

        ctk.CTkLabel(
            add_panel,
            text="Create a standard or administrator account.",
            text_color=("#64748b", "#a8b0c5"),
            font=("Arial", 13),
        ).pack(
            anchor="w",
            padx=26,
            pady=(0, 20),
        )

        self.username_entry = ctk.CTkEntry(
            add_panel,
            placeholder_text="Username",
            height=44,
        )
        self.username_entry.pack(
            fill="x",
            padx=26,
            pady=7,
        )

        self.email_entry = ctk.CTkEntry(
            add_panel,
            placeholder_text="Email address",
            height=44,
        )
        self.email_entry.pack(
            fill="x",
            padx=26,
            pady=7,
        )

        self.password_entry = ctk.CTkEntry(
            add_panel,
            placeholder_text="Temporary password",
            show="•",
            height=44,
        )
        self.password_entry.pack(
            fill="x",
            padx=26,
            pady=7,
        )

        self.role_menu = ctk.CTkOptionMenu(
            add_panel,
            values=["user", "admin"],
            height=44,
        )
        self.role_menu.set("user")
        self.role_menu.pack(
            fill="x",
            padx=26,
            pady=7,
        )

        ctk.CTkButton(
            add_panel,
            text="Add user",
            height=46,
            fg_color="#198754",
            hover_color="#20a366",
            font=("Arial", 15, "bold"),
            command=add_user_command,
        ).pack(
            fill="x",
            padx=26,
            pady=(16, 10),
        )

        self.status_label = ctk.CTkLabel(
            add_panel,
            text="",
            wraplength=330,
            justify="left",
            font=("Arial", 13),
        )
        self.status_label.pack(
            anchor="w",
            padx=26,
            pady=8,
        )

    def _build_user_list(self, parent):
        list_panel = ctk.CTkFrame(
            parent,
            fg_color=("#ffffff", "#23283f"),
            corner_radius=16,
            border_width=1,
            border_color=("#d8deea", "#343b5c"),
        )

        list_panel.pack(
            side="left",
            fill="both",
            expand=True,
        )

        list_header = ctk.CTkFrame(
            list_panel,
            fg_color="transparent",
        )

        list_header.pack(
            fill="x",
            padx=24,
            pady=(24, 10),
        )

        ctk.CTkLabel(
            list_header,
            text="Registered users",
            font=("Arial", 21, "bold"),
        ).pack(side="left")

        self.user_count_label = ctk.CTkLabel(
            list_header,
            text="0 accounts",
            text_color=("#64748b", "#a8b0c5"),
            font=("Arial", 13),
        )
        self.user_count_label.pack(side="right")

        self.users_scroll = ctk.CTkScrollableFrame(
            list_panel,
            fg_color="transparent",
        )
        self.users_scroll.pack(
            fill="both",
            expand=True,
            padx=16,
            pady=(0, 16),
        )