"""Cross-feature domain vocabulary (glossary terms shared across features).

These live in `core` so no feature has to import another feature's internals
(ADR-0005/0006). `Register` and `Category` are corpus/answer vocabulary used by
both `retrieval` and `chat`.
"""

from enum import StrEnum


class Register(StrEnum):
    textbook = "textbook"
    research = "research"
    consumer_health = "consumer_health"


class Category(StrEnum):
    cognitive = "cognitive"
    social = "social"
    clinical = "clinical"
    developmental = "developmental"
    biological = "biological"
    personality = "personality"
