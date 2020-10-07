from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from engine import Engine
    from entity import Entity


class Action:
    def perform(self, engine: Engine, entity: Entity) -> None:
        """perform this actions with the objects needed to determine its scope.

        'engine' is the scope the action is being performed in

        'entity' is the object performing the action.
        Must be overwritten by subclasses
        """
        raise NotImplementedError()


class EscapeAction(Action):
    def perform(self, engine: Engine, entity: Entity) -> None:
        raise SystemExit()


class MovementAction(Action):
    def __init__(self, dx: int, dy: int):
        super().__init__()

        self.dx = dx
        self.dy = dy

    def perform(self, engine: Engine, entity: Entity) -> None:
        dest_x = entity.x + self.dx
        dest_y = entity.y + self.dy
        if not engine.game_map.in_bounds(dest_x, dest_y):
            return  # destination is oob
        if not engine.game_map.tiles["walkable"][dest_x, dest_y]:
            return
        entity.move(self.dx, self.dy)
