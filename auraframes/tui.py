"""Textual TUI for Aura Frames album captioning."""
from __future__ import annotations

import time
from typing import TYPE_CHECKING, Any

from dotenv import load_dotenv
from rich.markup import escape
from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Container, Center, Middle, Horizontal
from textual.screen import Screen
from textual.widgets import (
    Header, Footer, OptionList, Label, Input,
    Button, Switch, ProgressBar, LoadingIndicator
)
from textual.widgets.option_list import Option

from auraframes.aura import Aura
from auraframes.exceptions import (
    AuthenticationError,
    NetworkError,
    ValidationError,
    APIError,
    ConfigurationError,
)

if TYPE_CHECKING:
    from auraframes.models.frame import Frame

load_dotenv()


def get_user_friendly_error(e: Exception) -> str:
    """Convert exception to user-friendly message."""
    if isinstance(e, AuthenticationError):
        return "Login failed. Please check your email and password."
    elif isinstance(e, NetworkError):
        return "Network error. Please check your internet connection."
    elif isinstance(e, ValidationError):
        return f"Invalid input: {e}"
    elif isinstance(e, ConfigurationError):
        return f"Configuration error: {e}"
    elif isinstance(e, APIError):
        return f"API error: {e}"
    else:
        return f"Error: {escape(str(e))}"


class FrameSelectScreen(Screen):
    """Screen to select a frame when multiple frames exist."""

    BINDINGS = [
        Binding("escape", "quit", "Quit"),
    ]

    def compose(self) -> ComposeResult:
        yield Header()
        yield Container(
            Container(
                Label("Select a Frame", id="title"),
                OptionList(id="frame-list"),
                classes="content-card",
            ),
            id="main-container",
        )
        yield Footer()

    @property
    def aura_app(self) -> AuraApp:
        """Get the app cast to AuraApp type."""
        return self.app  # type: ignore[return-value]

    def on_mount(self) -> None:
        option_list = self.query_one("#frame-list", OptionList)
        for frame in self.aura_app.frames:
            option_list.add_option(Option(f"{frame.name} ({frame.num_assets} photos)", id=frame.id))

    def on_option_list_option_selected(self, event: OptionList.OptionSelected) -> None:
        frame_id = event.option.id
        self.aura_app.current_frame = next(f for f in self.aura_app.frames if f.id == frame_id)
        self.aura_app.push_screen(MainMenuScreen())


class MainMenuScreen(Screen):
    """Main menu with available actions."""

    BINDINGS = [
        Binding("escape", "go_back", "Back"),
        Binding("q", "quit", "Quit"),
    ]

    @property
    def aura_app(self) -> AuraApp:
        """Get the app cast to AuraApp type."""
        return self.app  # type: ignore[return-value]

    def compose(self) -> ComposeResult:
        yield Header()
        frame = self.aura_app.current_frame
        yield Container(
            Container(
                Label(f"{frame.name if frame else ''}", id="frame-name"),
                Label("Select an Action", id="title"),
                OptionList(
                    Option("View albums", id="albums"),
                    Option("Add caption to album", id="caption"),
                    Option("Exit", id="exit"),
                    id="action-list",
                ),
                classes="content-card",
            ),
            id="main-container",
        )
        yield Footer()

    def on_option_list_option_selected(self, event: OptionList.OptionSelected) -> None:
        if event.option.id == "albums":
            self.aura_app.push_screen(AlbumListScreen())
        elif event.option.id == "caption":
            self.aura_app.push_screen(AlbumSelectScreen())
        elif event.option.id == "exit":
            self.aura_app.exit()

    def action_go_back(self) -> None:
        if len(self.aura_app.frames) > 1:
            self.aura_app.pop_screen()
        else:
            self.aura_app.exit()


class AlbumListScreen(Screen):
    """Screen to view all albums in the current frame."""

    BINDINGS = [
        Binding("escape", "go_back", "Back"),
    ]

    @property
    def aura_app(self) -> AuraApp:
        """Get the app cast to AuraApp type."""
        return self.app  # type: ignore[return-value]

    def compose(self) -> ComposeResult:
        yield Header()
        frame = self.aura_app.current_frame
        yield Container(
            Container(
                Label(f"{frame.name if frame else ''}", id="frame-name"),
                Label("Albums", id="title"),
                OptionList(id="album-list"),
                classes="content-card",
            ),
            id="main-container",
        )
        yield Footer()

    def on_mount(self) -> None:
        option_list = self.query_one("#album-list", OptionList)
        frame = self.aura_app.current_frame
        playlists = frame.playlists if frame else None
        if playlists:
            for playlist in playlists:
                name = playlist.get("name", "Unknown")
                num_assets = playlist.get("num_assets", 0)
                option_list.add_option(Option(f"{name} ({num_assets} photos)", id=playlist["id"]))
        else:
            option_list.add_option(Option("No albums found", id="none"))

    def action_go_back(self) -> None:
        self.aura_app.pop_screen()


class AlbumSelectScreen(Screen):
    """Screen to select an album to caption."""

    BINDINGS = [
        Binding("escape", "go_back", "Back"),
    ]

    @property
    def aura_app(self) -> AuraApp:
        """Get the app cast to AuraApp type."""
        return self.app  # type: ignore[return-value]

    def compose(self) -> ComposeResult:
        yield Header()
        yield Container(
            Container(
                Label("Select Album to Caption", id="title"),
                OptionList(id="album-list"),
                classes="content-card",
            ),
            id="main-container",
        )
        yield Footer()

    def on_mount(self) -> None:
        option_list = self.query_one("#album-list", OptionList)
        frame = self.aura_app.current_frame
        if frame and frame.playlists:
            for playlist in frame.playlists:
                name = playlist.get("name", "Unknown")
                num_assets = playlist.get("num_assets", 0)
                option_list.add_option(Option(f"{name} ({num_assets} photos)", id=playlist["id"]))

    def on_option_list_option_selected(self, event: OptionList.OptionSelected) -> None:
        playlist_id = event.option.id
        frame = self.aura_app.current_frame
        if frame and frame.playlists:
            playlist = next(p for p in frame.playlists if p["id"] == playlist_id)
            self.aura_app.selected_album = playlist
            self.aura_app.push_screen(CaptionInputScreen())

    def action_go_back(self) -> None:
        self.aura_app.pop_screen()


class CaptionInputScreen(Screen):
    """Screen to input caption text."""

    BINDINGS = [
        Binding("escape", "cancel", "Cancel"),
    ]

    @property
    def aura_app(self) -> AuraApp:
        """Get the app cast to AuraApp type."""
        return self.app  # type: ignore[return-value]

    def compose(self) -> ComposeResult:
        album = self.aura_app.selected_album
        album_name = album.get("name", "") if album else ""
        yield Header()
        yield Container(
            Container(
                Label(f'Caption for "{album_name}"', id="title"),
                Input(value=album_name, placeholder="Enter caption...", id="caption-input"),
                Horizontal(
                    Switch(value=False, id="include-date"),
                    Label("Include photo date (e.g. March 2025)"),
                    id="date-toggle",
                ),
                Horizontal(
                    Button("Apply Caption", variant="primary", id="apply"),
                    Button("Cancel", variant="default", id="cancel"),
                    id="buttons",
                ),
                classes="content-card",
            ),
            id="main-container",
        )
        yield Footer()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "apply":
            caption_input = self.query_one("#caption-input", Input)
            include_date_switch = self.query_one("#include-date", Switch)
            caption = caption_input.value
            include_date = include_date_switch.value
            if caption:
                self.aura_app.push_screen(ProgressScreen(caption, include_date))
        elif event.button.id == "cancel":
            self.aura_app.pop_screen()

    def action_cancel(self) -> None:
        self.aura_app.pop_screen()


class ProgressScreen(Screen):
    """Screen showing captioning progress."""

    BINDINGS = [
        Binding("enter", "done", "Done"),
        Binding("escape", "done", "Done"),
    ]

    def __init__(self, caption: str, include_date: bool = False) -> None:
        super().__init__()
        self.caption: str = caption
        self.include_date: bool = include_date
        self.start_time: float | None = None
        self.completed: bool = False
        self.total_photos: int = 0

    @property
    def aura_app(self) -> AuraApp:
        """Get the app cast to AuraApp type."""
        return self.app  # type: ignore[return-value]

    def compose(self) -> ComposeResult:
        yield Header()
        yield Container(
            Container(
                Label("Adding Captions", id="title"),
                Label("Preparing...", id="phase-label"),
                ProgressBar(id="progress-bar", show_eta=True),
                Label("", id="progress-detail"),
                Horizontal(
                    Button("Done", variant="primary", id="done-btn", disabled=True),
                    id="buttons",
                ),
                classes="content-card",
            ),
            id="main-container",
        )
        yield Footer()

    def on_mount(self) -> None:
        self.start_time = time.time()
        self.run_worker(self.run_captioning(), exclusive=True)

    def update_progress(self, phase: str, current: int, total: int) -> None:
        """Update progress display based on phase."""
        try:
            bar = self.query_one("#progress-bar", ProgressBar)
            phase_label = self.query_one("#phase-label", Label)
            detail_label = self.query_one("#progress-detail", Label)

            if phase == "fetching":
                phase_label.update("Fetching photos...")
                if current > 0:
                    detail_label.update(f"{current} found")
                else:
                    detail_label.update("")
            elif phase == "deleting":
                self.total_photos = total
                phase_label.update("Removing old captions...")
                bar.update(total=total, progress=current)
                detail_label.update(f"{current} of {total}")
            elif phase == "captioning":
                phase_label.update("Adding captions...")
                bar.update(total=total, progress=current)
                detail_label.update(f"{current} of {total}")
        except Exception:
            pass  # Widget may not exist during shutdown

    def _format_duration(self, seconds: float) -> str:
        """Format duration in human-readable form."""
        if seconds < 60:
            return f"{seconds:.1f}s"
        minutes = int(seconds // 60)
        secs = seconds % 60
        return f"{minutes}m {secs:.0f}s"

    def show_completion(self, count: int, error: str | None = None) -> None:
        """Show completion status."""
        try:
            card = self.query_one(".content-card")
            title = self.query_one("#title", Label)
            phase_label = self.query_one("#phase-label", Label)
            detail_label = self.query_one("#progress-detail", Label)
            bar = self.query_one("#progress-bar", ProgressBar)
            done_btn = self.query_one("#done-btn", Button)

            duration = time.time() - self.start_time if self.start_time else 0

            # Hide progress bar
            bar.display = False

            if error:
                card.add_class("error-card")
                title.update("Error")
                phase_label.update(error)
                detail_label.update("")
            else:
                card.add_class("success-card")
                title.update("Complete!")
                phase_label.update(f"{count} photos captioned")
                detail_label.update(f"Time: {self._format_duration(duration)}")

            done_btn.disabled = False
            self.completed = True
        except Exception:
            pass  # Widget may not exist during shutdown

    async def run_captioning(self) -> None:
        album = self.aura_app.selected_album
        frame = self.aura_app.current_frame
        aura = self.aura_app.aura

        def progress_callback(phase: str, current: int, total: int) -> None:
            self.aura_app.call_later(self.update_progress, phase, current, total)

        if not album or not frame or not aura:
            self.aura_app.call_later(self.show_completion, 0, "Missing frame or album")
            return

        try:
            count = await aura.caption_album(
                frame.id, album["id"], self.caption,
                include_date=self.include_date,
                progress_callback=progress_callback
            )
            self.aura_app.call_later(self.show_completion, count)
        except Exception as e:
            self.aura_app.call_later(self.show_completion, 0, get_user_friendly_error(e))

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "done-btn":
            self.go_to_menu()

    def action_done(self) -> None:
        if self.completed:
            self.go_to_menu()

    def go_to_menu(self) -> None:
        while len(self.aura_app.screen_stack) > 1:
            self.aura_app.pop_screen()
        self.aura_app.push_screen(MainMenuScreen())


class AuraApp(App):
    """Main Textual app for Aura Frames."""

    CSS = """
    /* ===========================================
       Aura Frames TUI - Stylesheet
       =========================================== */

    /* --- Layout --- */
    #main-container {
        width: 100%;
        height: 1fr;
        align: center middle;
        padding: 1 2;
    }

    .content-card {
        width: 80%;
        min-width: 60;
        max-width: 120;
        height: auto;
        padding: 2 3;
        border: round $primary;
        background: $surface;
    }

    /* --- Typography --- */
    #title {
        text-style: bold;
        text-align: center;
        margin-bottom: 2;
        width: 100%;
    }

    #frame-name {
        color: $text-muted;
        text-style: italic;
        text-align: center;
        margin-bottom: 1;
        width: 100%;
    }

    /* --- Loading Screen --- */
    .loading-card {
        width: auto;
        min-width: 40;
        height: auto;
        padding: 3 5;
        border: round $primary;
        background: $surface;
        align: center middle;
    }

    #loading-text {
        text-align: center;
        color: $text-muted;
        margin-top: 1;
        width: 100%;
    }

    LoadingIndicator {
        width: 100%;
        height: 3;
        color: $primary;
    }

    /* --- Option Lists --- */
    OptionList {
        border: round $border;
        background: $surface;
        padding: 1;
        height: auto;
        min-height: 5;
        max-height: 20;
        margin-bottom: 1;
        width: 100%;
    }

    OptionList:focus {
        border: round $primary;
    }

    /* --- Progress Bar --- */
    #progress-bar {
        width: 100%;
        margin: 1 0;
    }

    Bar > .bar--complete {
        color: $success;
    }

    #phase-label {
        text-align: center;
        color: $text-muted;
        margin-bottom: 1;
        width: 100%;
    }

    #progress-detail {
        text-align: center;
        color: $text;
        width: 100%;
    }

    /* --- Form Elements --- */
    Input {
        border: round $border;
        width: 100%;
        margin-bottom: 1;
    }

    Input:focus {
        border: round $primary;
    }

    #caption-input {
        margin-bottom: 1;
    }

    #date-toggle {
        height: auto;
        margin-bottom: 2;
        align: left middle;
        width: 100%;
    }

    #date-toggle Switch {
        margin-right: 2;
    }

    #date-toggle Label {
        color: $text;
    }

    /* --- Buttons --- */
    #buttons {
        width: 100%;
        height: auto;
        align: center middle;
        margin-top: 2;
    }

    #buttons Button {
        margin: 0 1;
        min-width: 16;
    }

    /* --- Success/Error States --- */
    .success-card {
        border: round $success;
        background: $success 20%;
    }

    .error-card {
        border: round $error;
        background: $error 20%;
    }

    /* --- Header --- */
    Header {
        background: $primary;
    }
    """

    BINDINGS = [
        Binding("q", "quit", "Quit"),
    ]

    def __init__(self) -> None:
        super().__init__()
        self.aura: Aura | None = None
        self.frames: list[Frame] = []
        self.current_frame: Frame | None = None
        self.selected_album: dict[str, Any] | None = None

    def compose(self) -> ComposeResult:
        yield Header()
        yield Center(
            Middle(
                Container(
                    LoadingIndicator(id="spinner"),
                    Label("Connecting to Aura Frames...", id="loading-text"),
                    classes="loading-card",
                )
            ),
            id="main-container",
        )
        yield Footer()

    def on_mount(self) -> None:
        self.title = "Aura Frames"
        self.run_worker(self.initialize(), exclusive=True)

    async def initialize(self) -> None:
        try:
            self.aura = Aura()
            await self.aura.login()
            self.frames = await self.aura.frame_api.get_frames()

            if len(self.frames) > 1:
                self.push_screen(FrameSelectScreen())
            else:
                self.current_frame = self.frames[0]
                self.push_screen(MainMenuScreen())
        except Exception as e:
            loading_text = self.query_one("#loading-text", Label)
            loading_text.update(get_user_friendly_error(e))
            # Hide spinner on error
            spinner = self.query_one("#spinner", LoadingIndicator)
            spinner.display = False


def main() -> None:
    app = AuraApp()
    app.run()


if __name__ == "__main__":
    main()
