from dataclasses import dataclass, field
from typing import Dict, List, Optional


@dataclass
class PushInfo:
    push_tag: str
    pusher: str
    push_content: str
    push_datetime: str

    @classmethod
    def from_dict(cls, d: Dict[str, List[str]]):
        return [
            cls(**dict(zip(d.keys(), tup)))
            for tup in zip(*d.values())
        ]

    def to_dict(self):
        return self.__dict__

    def update(self, update_dict: dict = None, **kwargs):
        if update_dict:
            self.__dict__.update(update_dict)
        self.__dict__.update(kwargs)


@dataclass
class PostInfo:
    url: str
    push: int
    title: str = ''
    author: str = ''
    datetime: str = ''
    content: str = ''
    pushes: List[PushInfo] = field(default_factory=list)

    @classmethod
    def from_dict(cls, d: Dict[str, List[str]]):
        return [
            cls(**dict(zip(d.keys(), tup)))
            for tup in zip(*d.values())
        ]

    def to_dict(self):
        return self.__dict__

    def update(self, update_dict: dict = None, **kwargs):
        if update_dict:
            self.__dict__.update(update_dict)
        self.__dict__.update(kwargs)
