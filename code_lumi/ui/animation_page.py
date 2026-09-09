"""Animation-page interface for Code Lumi AI."""

import customtkinter as ctk


class AnimationPage:
    """Widgets used to display Python execution traces."""

    def __init__(
        self,
        parent,
        background,
        stop_command,
    ):
        self.frame = ctk.CTkFrame(
            parent,
            fg_color=background,
        )

        self._build_header(
            background,
            stop_command,
        )

        self._build_content(background)

    def _build_header(
        self,
        background,
        stop_command,
    ):
        header = ctk.CTkFrame(
            self.frame,
            fg_color=background,
        )

        header.pack(
            fill="x",
            padx=20,
            pady=10,
        )

        ctk.CTkButton(
            header,
            text="🛑 Stop & Return",
            width=120,
            fg_color="#c0392b",
            hover_color="#e74c3c",
            command=stop_command,
        ).pack(side="left")

        self.status_label = ctk.CTkLabel(
            header,
            text="🎬 Live Animation Player",
            font=("Arial", 20, "bold"),
            text_color="#f1c40f",
        )

        self.status_label.pack(
            side="left",
            padx=40,
        )

    def _build_content(self, background):
        split_frame = ctk.CTkFrame(
            self.frame,
            fg_color=background,
        )

        split_frame.pack(
            fill="both",
            expand=True,
            padx=20,
            pady=10,
        )

        split_frame.grid_columnconfigure(
            0,
            weight=1,
        )

        split_frame.grid_columnconfigure(
            1,
            weight=1,
        )

        split_frame.grid_rowconfigure(
            0,
            weight=1,
        )

        self.code_display = ctk.CTkTextbox(
            split_frame,
            font=("Consolas", 22),
            fg_color="#1e1e1e",
            text_color="white",
            border_width=2,
        )

        self.code_display.grid(
            row=0,
            column=0,
            padx=10,
            pady=10,
            sticky="nsew",
        )

        right_panel = ctk.CTkFrame(
            split_frame,
            corner_radius=10,
            fg_color="#2c3e50",
        )

        right_panel.grid(
            row=0,
            column=1,
            padx=10,
            pady=10,
            sticky="nsew",
        )

        ctk.CTkLabel(
            right_panel,
            text="🧠 Active Memory Objects",
            font=("Arial", 18, "bold"),
        ).pack(pady=10)

        self.memory_frame = ctk.CTkScrollableFrame(
            right_panel,
            fg_color="transparent",
        )

        self.memory_frame.pack(
            fill="both",
            expand=True,
            padx=10,
            pady=5,
        )

        self.mascot_label = ctk.CTkLabel(
            right_panel,
            text="",
            fg_color="transparent",
        )