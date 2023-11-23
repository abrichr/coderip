from dataclasses import dataclass

@dataclass(frozen=True)
class File:
    path: str
    name: str

@dataclass(frozen=True)
class CodeSection:
    start_line: int
    end_line: int
    label: str

@dataclass
class SourceCodeMessage:
    code: str
    label: str

@dataclass
class FeedbackMessage:
    stdout: str
    stderr: str
    user_prompt: str
    coderip_prompt: str

@dataclass
class MetaMessage:
    # Fields related to code editing, command running, etc.
    pass
