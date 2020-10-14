from components.ai import HostileEnemy, BaseAI
from components.fighter import Fighter
from entity import Actor

player = Actor(char="@",
               color=(255, 255, 255),
               name="Player",
               ai_cls=BaseAI,
               fighter=Fighter(hp=30, dodge=12, soak=12, strength=8, attack=16),
               )

orc = Actor(char="o",
            color=(63, 127, 63),
            name="Orc",
            ai_cls=HostileEnemy,
            fighter=Fighter(hp=10, dodge=8, soak=12, strength=4, attack=8),
            )

troll = Actor(char="T",
              color=(0, 127, 0),
              name="Troll",
              ai_cls=HostileEnemy,
              fighter=Fighter(hp=12, dodge=6, soak=20, strength=12, attack=8),
              )
