"""Typed bit-vector primitives for direct semantic recovery."""

from __future__ import annotations

from dataclasses import dataclass


SEMANTIC_TYPE_SCHEMA_VERSION = "semantic_type_v1"


@dataclass(frozen=True, order=True)
class SemanticType:
    kind: str
    width: int
    signed: bool = False

    def __post_init__(self) -> None:
        if self.kind not in {"bitvector", "boolean"}:
            raise ValueError(f"unsupported semantic type kind: {self.kind}")
        if self.width <= 0:
            raise ValueError("semantic type width must be positive")
        if self.kind == "boolean" and self.width != 1:
            raise ValueError("boolean scalar width must be one")

    @property
    def signedness(self) -> str:
        return "signed" if self.signed else "unsigned"

    @property
    def mask(self) -> int:
        return (1 << self.width) - 1

    def to_dict(self) -> dict[str, object]:
        return {"kind": self.kind, "width": self.width, "signed": self.signed, "schema_version": SEMANTIC_TYPE_SCHEMA_VERSION}


def unsigned_bitvector(width: int) -> SemanticType:
    return SemanticType("bitvector", width, False)


def signed_bitvector(width: int) -> SemanticType:
    return SemanticType("bitvector", width, True)


def boolean_scalar() -> SemanticType:
    return SemanticType("boolean", 1, False)


def mask(width: int) -> int:
    return (1 << width) - 1


def truncate(value: int, width: int) -> int:
    return value & mask(width)


def to_signed(value: int, width: int) -> int:
    value &= mask(width)
    sign = 1 << (width - 1)
    return value - (1 << width) if value & sign else value


def from_signed(value: int, width: int) -> int:
    return value & mask(width)
