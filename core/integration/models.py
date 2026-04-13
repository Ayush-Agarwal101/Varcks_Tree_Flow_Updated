# core/integration/models

from typing import List

class Variable:
    """
    Represents a semantic variable like user.user_id
    """

    def __init__(self, name: str, entity: str, var_type: str):
        self.name = name
        self.entity = entity
        self.type = var_type

        self.produced_by: List[str] = []
        self.used_by: List[str] = []

    @property
    def key(self) -> str:
        return f"{self.entity}.{self.name}"

    def add_producer(self, fn: str):
        if fn not in self.produced_by:
            self.produced_by.append(fn)

    def add_consumer(self, fn: str):
        if fn not in self.used_by:
            self.used_by.append(fn)

    def __repr__(self):
        return f"<Variable {self.key}>"