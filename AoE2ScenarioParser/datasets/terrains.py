from enum import IntEnum


class Terrain(IntEnum):
    BEACH = 2
    BEACH_NON_NAVIGABLE = 79
    BEACH_NON_NAVIGABLE_WET_GRAVEL = 81
    BEACH_NON_NAVIGABLE_WET_ROCK = 82
    BEACH_NON_NAVIGABLE_WET_SAND = 80
    BEACH_ICE = 37
    BEACH_VEGETATION = 52
    BEACH_WET = 107
    BEACH_WET_GRAVEL = 108
    BEACH_WET_ROCK = 109
    BEACH_WHITE = 53
    BEACH_WHITE_VEGETATION = 51
    BLACK = 47
    DESERT_CRACKED = 45
    DESERT_QUICKSAND = 46
    DESERT_SAND = 14
    DIRT_1 = 6
    DIRT_2 = 11
    DIRT_3 = 3
    DIRT_4 = 42
    DIRT_MUD = 76
    DIRT_SAVANNAH = 41
    FARM = 7
    FARM_0 = 29
    FARM_33 = 30
    FARM_67 = 31
    FARM_DEAD = 8
    FOREST_ACACIA = 50
    FOREST_AUTUMN = 104
    FOREST_AUTUMN_SNOW = 105
    FOREST_BAMBOO = 18
    FOREST_BAOBAB = 49
    FOREST_BUSH = 89
    FOREST_DEAD = 106
    FOREST_DRAGON_TREE = 48
    FOREST_JUNGLE = 17
    FOREST_MANGROVE = 55
    FOREST_MEDITERRANEAN = 88
    FOREST_OAK = 10
    FOREST_OAK_BUSH = 20
    FOREST_PALM_DESERT = 13
    FOREST_PINE = 19
    FOREST_PINE_SNOW = 21
    FOREST_RAINFOREST = 56
    FOREST_REEDS = 92
    FOREST_REEDS_BEACH = 91
    FOREST_REEDS_SHALLOWS = 90
    GRASS_1 = 0
    GRASS_2 = 12
    GRASS_3 = 9
    GRASS_DRY = 100
    GRASS_FOUNDATION = 27
    GRASS_JUNGLE = 60
    GRASS_JUNGLE_RAINFOREST = 83
    GRASS_OTHER = 16
    GRAVEL_DEFAULT = 70
    GRAVEL_DESERT = 102
    ICE = 35
    ICE_NAVIGABLE = 26
    RICE_FARM = 63
    RICE_FARM_0 = 65
    RICE_FARM_33 = 66
    RICE_FARM_67 = 67
    RICE_FARM_DEAD = 64
    ROAD = 24
    ROAD_BROKEN = 25
    ROAD_FUNGUS = 75
    ROAD_GRAVEL = 78
    ROCK_1 = 40
    SHALLOWS = 4
    SHALLOWS_AZURE = 59
    SHALLOWS_MANGROVE = 54
    SNOW = 32
    SNOW_FOUNDATION = 36
    SNOW_LIGHT = 73
    SNOW_STRONG = 74
    SWAMP_BOGLAND = 101
    UNDERBUSH = 5
    UNDERBUSH_JUNGLE = 77
    UNDERBUSH_LEAVES = 71
    UNDERBUSH_SNOW = 72
    WATER_2D_BRIDGE = 28
    WATER_2D_SHORELESS = 15
    WATER_AZURE = 58
    WATER_BROWN = 96
    WATER_DEEP = 22
    WATER_DEEP_OCEAN = 57
    WATER_GREEN = 95
    WATER_MEDIUM = 23
    WATER_SHALLOW = 1
