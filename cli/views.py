from __future__ import annotations
from cli.models import Config, QueueItem, ResolvedTrack
from typing import Any

class CliView:
    def show_banner(self, cfg: Config) -> None:
        print(f"Connected to API at {cfg.api_base}")
        print(f"Using queue_id='{cfg.queue_id}'")

    def show_help(self) -> None:
        print(
            "\nCommands:\n"
            "  add <query>        Enqueue from lookup text\n"
            "  next               Pop next item, resolve it, and show what would play\n"
            "  pop                Pop next item and show it (no resolve)\n"
            "  peek               Peek next item (no pop)\n"
            "  peek-resolve       Peek next item and resolve it (does not pop)\n"
            "  list [n]           Show first n queued items (default 10)\n"
            "  size               Show queue size\n"
            "  clear              Clear queue\n"
            "  help               Show commands\n"
            "  quit               Exit\n"
        )

    def prompt(self, queue_size: int) -> str:
        if queue_size == 0:
            return input("\nQueue is empty. Enter: add <query>  (or help/quit)\n> ").strip()
        return input(f"\nQueue has {queue_size} item(s). Enter a command (next/peek/list/clear/add ...)\n> ").strip()

    def print_error(self, msg: str, payload: dict | None = None) -> None:
        print(msg)
        if payload is not None:
            print(payload)

    def print_info(self, msg: str) -> None:
        print(msg)

    def print_queue_item(self, item: QueueItem, *, prefix: str | None = None) -> None:
        head = f"{prefix}\n" if prefix else ""
        if item.id:
            #print(f"value={item.value} - {head}- kind={item.kind} id={item.id}")
            print(f"{head} - {item.value}")
        else:
            print(f"value={item.value} - {head}- kind={item.kind}")

    def print_queue_list(self, items: list[QueueItem], total: int) -> None:
        print(f"Showing {len(items)} of {total}:")
        for it in items:
            self.print_queue_item(it)

    def print_enqueued(self, added: int, size: Any, service: Any, kind: Any) -> None:
        if service and kind:
            print(f"Queued {added} items from {service} {kind}. Queue size: {size}")
        else:
            print(f"Queued {added} items. Queue size: {size}")

    def print_resolved(self, resolved: ResolvedTrack) -> None:
        if resolved.title and resolved.value:
            print(f"Would play: {resolved.title} ({resolved.value})")
        elif resolved.value:
            print(f"Would play: {resolved.value}")
        else:
            print("Would play: (missing url?)")

    def print_stream_check(self, ok: bool) -> None:
        print("stream_url_found?", "Yes" if ok else "No")