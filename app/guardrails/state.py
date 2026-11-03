from dataclasses import dataclass, field


@dataclass
class ConversationState:
    read_notes: dict[str, str] = field(default_factory=dict)
