import esper
import Components as c


class MovementProcessor(esper.Processor):

    def process(self):
        for ent, (vel, pos) in self.world.get_components(c.Velocity, c.Position):
            pos.x += vel.x
            pos.y += vel.y
            print(pos.x, pos.y)
