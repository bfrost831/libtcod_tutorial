import math
import tcod as libtcod

from render_functions import RenderOrder
from components.inventory import Item

class Entity:
    """
    A Generic object to represent players, enemies, items, etc.
    """
    def __init__(self, x, y, char, color, name, blocks=False, render_order = RenderOrder.CORPSE, 
                 fighter=None, ai=None, item=None, inventory=None, stairs=None, level=None, 
                 equipment=None, equippable=None):
        self.x = x
        self.y = y
        self.char = char
        self.color = color
        self.name = name
        self.blocks = blocks
        self.render_order = render_order
        self.fighter = fighter
        self.ai = ai
        self.item = item
        self.inventory = inventory
        self.stairs = stairs
        self.level = level
        self.equipment = equipment
        self.equippable = equippable

        if self.fighter:
            self.fighter.owner = self

        if self.ai:
            self.ai.owner = self

        if self.item:
            self.item.owner = self

        if self.inventory:
            self.inventory.owner = self

        if self.stairs:
            self.stairs.owner = self

        if self.level:
            self.level.owner = self

        if self.equipment:
            self.equipment.owner = self

        if self.equippable:
            self.equippable.owner = self

            if not self.item:
                item = Item()
                self.item = item
                self.item.owner = self

    # Move the entity by a given amount
    def move(self, dx, dy):
        self.x += dx
        self.y += dy

    def move_towards(self, target_x, target_y, game_map, entities):
        dx = target_x - self.x
        dy = target_y - self.y
        distance = math.sqrt(dx ** 2 + dy ** 2)

        dx = int(round(dx / distance))
        dy = int(round(dy / distance))

        if not (game_map.is_blocked(self.x + dx, self.y + dy) or
                get_blocking_entities_at_location(entities, self.x + dx, self.y + dy)):
            self.move(dx, dy)

    def move_astar(self, target, entities, game_map):
        # Create FOV map w dimensions of the map
        fov = libtcod.map_new(game_map.width, game_map.height)

        # Scan current map each turn, set walls unwalkable
        for y1 in range(game_map.height):
            for x1 in range(game_map.width):
                libtcod.map_set_properties(fov, x1, y1, 
                                           not game_map.tiles[x1][y1].block_sight,
                                           not game_map.tiles[x1][y1].blocked)

        # Scan all objects to see if there are objects that must be navigated around
        for entity in entities:
            if entity.blocks and entity != self and entity != target:
                # Set tile as wall so it must be navigated around
                libtcod.map_set_properties(fov, entity.x, entity.y, True, False)

        # Allocate A* path
        # 1.41 is the normal diagonal cost of moving, set to 0.0 if diagonal moves prohibited
        my_path = libtcod.path_new_using_map(fov, 1.41)

        # Compute path between self coords and target coords
        libtcod.path_compute(my_path, self.x, self.y, target.x, target.y)

        # Check path exists and shorter than 25 tiles
        # Path size matters if you want monsters to use alternative longer paths
        #  ex if thru other rooms if player in corridor
        # Keep path size relatively low to keep monsters from running around the map 
        if not libtcod.path_is_empty(my_path) and libtcod.path_size(my_path) < 25:
            # Find next coords in computed path
            x, y = libtcod.path_walk(my_path, True)
            if x or y:
                # Set self's coords to next path tile
                self.x = x
                self.y = y

        else:
            # Keep old move function as backup so if there are no paths (monster blocking exit)
            # it will still try to move towards the player
            self.move_towards(target.x, target.y, game_map, entities)

        # Delete path to free memory
        libtcod.path_delete(my_path)

    def distance(self, x, y):
        return math.sqrt((x - self.x) ** 2 + (y - self.y) ** 2)

    def distance_to(self, other):
        dx = other.x - self.x
        dy = other.y - self.y
        return math.sqrt(dx ** 2 + dy ** 2)

def get_blocking_entities_at_location(entities, destination_x, destination_y):
    for entity in entities:
        if entity.blocks and entity.x == destination_x and entity.y == destination_y:
            return entity

    return None