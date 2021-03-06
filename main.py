import esper
import Components as c
import Processors


def main() -> None:
    world = esper.World()
    player = world.create_entity()
    world.add_component(player, c.Position(x=1, y=2))
    world.add_component(player, c.Velocity(x=.1, y=-.1))
    world.add_processor(Processors.MovementProcessor())
    print(world.components_for_entity(player))
    print(world.has_component(player, c.Position))
    world.process()
    world.process()








if __name__ == "__main__":
    main()