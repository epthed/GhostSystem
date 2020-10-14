from __future__ import annotations

from typing import Optional, Tuple, TYPE_CHECKING

if TYPE_CHECKING:
    from engine import Engine
    from entity import Entity, Actor

from components import dice


class Action:
    def __init__(self, entity: Actor):
        super().__init__()
        self.entity = entity

    @property
    def engine(self) -> Engine:
        """Return the engine this action belongs to."""
        return self.entity.gamemap.engine

    def perform(self) -> None:
        """perform this actions with the objects needed to determine its scope.

        'self.engine' is the scope the action is being performed in

        'self.entity' is the object performing the action.
        Must be overwritten by subclasses
        """
        raise NotImplementedError()


class EscapeAction(Action):
    def perform(self) -> None:
        raise SystemExit()


class WaitAction(Action):
    def perform(self) -> None:
        pass


class ActionWithDirection(Action):
    def __init__(self, entity: Actor, dx: int, dy: int):
        super().__init__(entity)

        self.dx = dx
        self.dy = dy

    @property
    def dest_xy(self) -> Tuple[int, int]:
        """Returns this actions destination."""
        return self.entity.x + self.dx, self.entity.y + self.dy

    @property
    def blocking_entity(self) -> Optional[Entity]:
        """Return the blocking entity at this actions destination.."""
        return self.engine.game_map.get_blocking_entity_at_location(*self.dest_xy)

    @property
    def target_actor(self) -> Optional[Actor]:
        return self.engine.game_map.get_actor_at_location(*self.dest_xy)

    def perform(self) -> None:
        raise NotImplementedError()


class MeleeAction(ActionWithDirection):
    def perform(self) -> None:
        target = self.target_actor
        if not target:
            return  # nothing here to attack

        atk_vs_dodge = dice.hits(self.entity.fighter.attack) - dice.hits(target.fighter.dodge)

        attack_desc = f"{self.entity.name.capitalize()} attacks {target.name}"

        if atk_vs_dodge <= 0:
            print(f"{attack_desc} but misses.")
            return

        damage = (atk_vs_dodge + self.entity.fighter.strength) - dice.hits(target.fighter.soak)

        if damage > 0:
            print(f"{attack_desc} for {damage} hp.")
            target.fighter.hp -= damage
        else:
            print(f"{attack_desc} but does no damage.")


class MovementAction(ActionWithDirection):

    def perform(self) -> None:
        dest_x, dest_y = self.dest_xy
        if not self.engine.game_map.in_bounds(dest_x, dest_y):
            return  # destination is oob
        if not self.engine.game_map.tiles["walkable"][dest_x, dest_y]:
            return  # destination is blocked by tile
        if self.engine.game_map.get_blocking_entity_at_location(dest_x, dest_y):
            return  # destination is blocked by entity
        self.entity.move(self.dx, self.dy)


class BumpAction(ActionWithDirection):
    def perform(self) -> None:
        dest_x, dest_y = self.dest_xy

        if self.target_actor:
            return MeleeAction(self.entity, self.dx, self.dy).perform()
        else:
            return MovementAction(self.entity, self.dx, self.dy).perform()
