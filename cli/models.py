from dataclasses import dataclass

@dataclass(frozen=True)
class Command:
    name: str
    arg: str | None = None
    
@dataclass(frozen=True)
class Config:
    api_base: str = "http://127.0.0.1:5000"
    queue_id: str = "cli"

@dataclass(frozen=True)
class QueueItem:
    kind: str
    value: str
    id: str | None = None

    @staticmethod
    def from_dict(d: dict) -> "QueueItem":
        return QueueItem(
            id=d.get("id"),
            kind=(d.get("kind") or "").strip(),
            value=(d.get("value") or "").strip(),
        )

    def to_resolve_payload(self) -> dict:
        return {"kind": self.kind, "value": self.value}


@dataclass(frozen=True)
class ResolvedTrack:
    kind: str
    value: str
    title: str | None = None
    author: str | None = None
    length_seconds: int | None = None
    video_id: str | None = None

    @staticmethod
    def from_dict(d: dict) -> "ResolvedTrack":
        return ResolvedTrack(
            kind=d.get("kind") or "",
            value=d.get("value") or d.get("video_url") or "",
            title=d.get("title"),
            author=d.get("author"),
            length_seconds=d.get("length_seconds"),
            video_id=d.get("video_id"),
        )
