from pytubefix import YouTube
from service import ApiClient
from cli.views import CliView
from cli.models import QueueItem, ResolvedTrack, Command

from typing import Callable

def best_audio_stream_url(yt: YouTube) -> str | None:
        try:
            stream = (
                yt.streams
                  .filter(only_audio=True, mime_type="audio/webm")
                  .order_by("abr")
                  .last()
                or
                yt.streams
                  .filter(only_audio=True)
                  .order_by("abr")
                  .last()
            )
        except Exception:
            return None
        if stream is None:
            return None
        try:
            return stream.url
        except Exception:
            return None

class CliController:
    def __init__(self, api: ApiClient, view: CliView):
        self.api = api
        self.view = view
        self._handlers: dict[str, Callable[[Command], bool]] = {
            "help": self._cmd_help,
            "quit": self._cmd_quit,
            "add": self._cmd_add,
            "size": self._cmd_size,
            "clear": self._cmd_clear,
            "peek": self._cmd_peek,
            "peek-resolve": self._cmd_peek_resolve,
            "pop": self._cmd_pop,
            "next": self._cmd_next,
            "list": self._cmd_list,
        }

    def _with_queue_item(
        self,
        fetch: Callable[[], QueueItem | None],
        on_item: Callable[[QueueItem], None],
        *,
        empty_msg: str = "Queue empty.",
    ) -> bool:
        item = fetch()
        if item is None:
            self.view.print_info(empty_msg)
        else:
            on_item(item)
        return True

    def _handle_payload(
        self,
        payload: dict,
        *,
        error_prefix: str,
        on_ok: Callable[[dict], None],
    ) -> bool:
        if not payload.get("ok"):
            self.view.print_error(error_prefix, payload)
            return True
        on_ok(payload)
        return True

    def _resolve_and_show(self, item: QueueItem) -> None:
        self.view.print_queue_item(item, prefix="Resolving item:")

        payload = self.api.resolve(item)
        if not payload.get("ok"):
            self.view.print_error("Resolve failed:", payload)
            return

        resolved = ResolvedTrack.from_dict(payload)
        self.view.print_resolved(resolved)

        stream_ok = False
        if resolved.value:
            try:
                yt = YouTube(resolved.value)
                stream_ok = best_audio_stream_url(yt) is not None
            except Exception:
                stream_ok = False

        self.view.print_stream_check(stream_ok)

    # -----------------------
    # Parsing and loop
    # -----------------------
    def _parse_command(self, raw: str) -> Command | None:
        raw = raw.strip()
        if not raw:
            return None

        if raw.startswith("add "):
            return Command(name="add", arg=raw[4:].strip())

        parts = raw.split()
        name = parts[0]

        if name == "list":
            arg = parts[1] if len(parts) > 1 else None
            return Command(name="list", arg=arg)

        if name in self._handlers:
            return Command(name=name)

        return None

    def run(self) -> None:
        if not self.api.health_ok():
            self.view.print_error(f"API not healthy at {self.api.cfg.api_base}. Is Flask running?")
            return

        self.view.show_banner(self.api.cfg)
        self.view.show_help()

        while True:
            size = self.api.fetch_queue_size()
            if size is None:
                self.view.print_error("Could not read queue size (server error?)")
                return

            raw = self.view.prompt(size)
            if not raw:
                continue

            cmd = self._parse_command(raw)
            if cmd is None:
                self.view.print_info("Unknown command. Type 'help'.")
                continue

            handler = self._handlers.get(cmd.name)
            if handler is None:
                self.view.print_info("Unknown command. Type 'help'.")
                continue

            if not handler(cmd):
                break

    # -----------------------
    # Command handlers
    # -----------------------
    def _cmd_help(self, cmd: Command) -> bool:
        self.view.show_help()
        return True

    def _cmd_quit(self, cmd: Command) -> bool:
        return False

    def _cmd_size(self, cmd: Command) -> bool:
        size = self.api.fetch_queue_size()
        if size is None:
            self.view.print_error("Could not read queue size (server error?)")
        else:
            self.view.print_info(f"Queue size: {size}")
        return True

    def _cmd_add(self, cmd: Command) -> bool:
        query = (cmd.arg or "").strip()
        if not query:
            self.view.print_info("Usage: add <query>")
            return True

        payload = self.api.enqueue(query, limit=200)

        def on_ok(enq: dict) -> None:
            added = enq.get("added", 0)
            new_size = enq.get("size", "?")
            inp = enq.get("input") or {}
            self.view.print_enqueued(added, new_size, inp.get("service"), inp.get("kind"))

        return self._handle_payload(payload, error_prefix="Enqueue failed:", on_ok=on_ok)

    def _cmd_clear(self, cmd: Command) -> bool:
        payload = self.api.clear()

        def on_ok(_: dict) -> None:
            self.view.print_info("Queue cleared.")

        return self._handle_payload(payload, error_prefix="Clear failed:", on_ok=on_ok)

    def _cmd_peek(self, cmd: Command) -> bool:
        return self._with_queue_item(
            fetch=self.api.fetch_peek_items,
            on_item=lambda item: self.view.print_queue_item(item, prefix="Next up:"),
        )

    def _cmd_peek_resolve(self, cmd: Command) -> bool:
        return self._with_queue_item(
            fetch=self.api.fetch_peek_items,
            on_item=self._resolve_and_show,
        )

    def _cmd_pop(self, cmd: Command) -> bool:
        return self._with_queue_item(
            fetch=self.api.fetch_next_item,
            on_item=lambda item: self.view.print_queue_item(item, prefix="Popped:"),
        )

    def _cmd_next(self, cmd: Command) -> bool:
        return self._with_queue_item(
            fetch=self.api.fetch_next_item,
            on_item=self._resolve_and_show,
        )

    def _cmd_list(self, cmd: Command) -> bool:
        n = 10
        if cmd.arg and cmd.arg.isdigit():
            n = int(cmd.arg)

        payload = self.api.snapshot(limit=n)

        def on_ok(snap: dict) -> None:
            total = int(snap.get("size") or 0)
            raw_items = snap.get("items") or []
            items: list[QueueItem] = []
            for it in raw_items:
                if isinstance(it, dict):
                    qi = QueueItem.from_dict(it)
                    if qi.kind and qi.value:
                        items.append(qi)
            self.view.print_queue_list(items, total)

        return self._handle_payload(payload, error_prefix="List failed:", on_ok=on_ok)