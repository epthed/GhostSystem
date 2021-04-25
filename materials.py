class Materials:
    def __init__(self):
        self.mat = [
            {
                "name": 'air',
                "number": 0,
                # can be seen through
                "opaque": False,
                # can be walked through
                "blocking": False,
                "structure": 0,
                "effect": None,
                # items below here are special and will rarely differ from above blocking and opacity
                # these three opacities are different "sight" modes with different tradeoffs and counters
                "opaque_thermal": False,
                "opaque_sonar": False,
                "opaque_radar": False,
                # cant see through in the astral, most blocking materials and spell barriers
                "opaque_astral": False,
                # cant see through on the net, very few things
                "opaque_net": False,
                # only living biological things block astral movement
                "blocking_astral": False,
                # only faraday cages block net movement
                "blocking_net": False,
            },
            {
                "name": 'glass',
                "number": 1,
                "opaque": False,
                "blocking": True,
                "structure": 2,
                "effect": None,
                "opaque_thermal": False,
                "opaque_sonar": True,
                "opaque_radar": False,
                "opaque_astral": True,
                "opaque_net": False,
                "blocking_astral": False,
                "blocking_net": False,
            },
            {
                "name": 'smoke',
                "number": 2,
                "opaque": True,
                "blocking": False,
                "structure": 0,
                "effect": None,
                "opaque_thermal": False,
                "opaque_sonar": False,
                "opaque_radar": False,
                "opaque_astral": False,
                "opaque_net": False,
                "blocking_astral": False,
                "blocking_net": False,
            },
            {
                "name": 'concrete',
                "number": 3,
                "opaque": True,
                "blocking": True,
                "structure": 12,
                "effect": None,
                "opaque_thermal": True,
                "opaque_sonar": True,
                "opaque_radar": False,
                "opaque_astral": True,
                "opaque_net": False,
                "blocking_astral": False,
                "blocking_net": False,
            },
        ]
        self.material_dict = {}
        for material in self.mat:
            self.material_dict[material['name']] = material

#
# class Material():
#     def __init__(self, **kwargs):
#         self.name = name
#         self.number = number
#         self.opaque= opaque,
#         self.blocking= blocking,
#         self.structure= structure,
#         self.effect= effect,
#         self.opaque_thermal= opaque_thermal,
#         self.opaque_sonar= opaque_sonar,
#         self.opaque_radar= opaque_radar,
#         self.opaque_astral= opaque_astral,
#         self.opaque_net= opaque_net,
#         self.blocking_astral= blocking_astral,
#         self.blocking_net= blocking_net,
