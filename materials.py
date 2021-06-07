# from numba import njit
# from numba.typed import Dict, List


def materials(material):
    if type(material) == int:
        return mat[material]
    else:
        return material_dict[material]


def material_id(string):
    return material_dict[string]['number']


mat = [
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
material_dict = {}
for m in mat:
    # n = Dict()
    # for key, item in m.items():
    #     n[key] = item
    material_dict[m['name']] = m
