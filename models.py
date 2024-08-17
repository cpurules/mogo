import csv
import logging
import re
from thefuzz import fuzz

log = logging.getLogger()

class BoardTile:
    def __init__(self, index, title):
        self._index = index
        self._title = title
    
    def is_corner(self):
        return self._index % 10 == 0
    
    def is_railroad(self):
        return self._index % 10 == 5
    
    def is_chest(self):
        return self._title == "Community Chest"
    
    def is_chance(self):
        return self._title == "Chance"
    
    def is_tax_utility(self):
        return self._index in [4, 12, 28, 38]

    def distance_to(self, target):
        tmp = (target._index - self._index) % 40
        if tmp < 2: # Cannot roll a 0 or a 1
            tmp += 40
        return tmp
    
    def __eq__(self, other):
        if isinstance(other, BoardTile):
            return self._index == other._index
    
    def __hash__(self):
        return self._index
    
    def __str__(self):
        return f"{self._index}.{self._title}"

class Board:
    def __init__(self):
        with open('tiles.txt', 'r') as f:
            self._tiles = [BoardTile(index, tile.strip()) for index, tile in enumerate(f.readlines())]
    
    def _search_tile(self, search: str):
        if search.lower().endswith("rr"):
            search = search[:-2] + " Railroad"

        scores = {tile._title: fuzz.ratio(tile._title, search) for tile in self._tiles}
        return max(scores, key=scores.get)
    
    def get_railroads(self):
        return [tile for tile in self._tiles if tile.is_railroad()]
    
    def get_chances(self):
        return [tile for tile in self._tiles if tile.is_chance()]
    
    def get_chests(self):
        return [tile for tile in self._tiles if tile.is_chest()]
    
    def get_tax_utilities(self):
        return [tile for tile in self._tiles if tile.is_tax_utility()]
    
    def get_corners(self):
        return [tile for tile in self._tiles if tile.is_corner()]

    def get_tiles_by_name(self, search):
        tile_name = self._search_tile(search)

        return [tile for tile in self._tiles if tile._title == tile_name]
    
    def find_next_tile(self, current, target):
        target_tiles = self.get_tiles_by_name(target)
        scores = {tile: current.distance_to(tile) for tile in target_tiles if not current == tile}
        return min(scores, key=scores.get)

    def get_tile_after(self, current, roll):
        if isinstance(roll, dict):
            roll = next(iter(roll.values()))[0]
        return self._tiles[(current._index + roll) % len(self._tiles)]

class Targets:
    def __init__(self):
        self._targets = []
        self._pickups = []
    
    def count(self):
        return len(self._targets)
    
    def get(self):
        return self._targets
    
    def reset(self):
        self._targets = []

    def add(self, targets, pickup=False):
        if isinstance(targets, BoardTile):
            if not targets in self._targets:
                self._targets.append(targets)
                if pickup: self._pickups.append(targets)
        else:
            for target in targets:
                self.add(target, pickup)
    
    def is_target(self, target):
        return target in self._targets

    def is_pickup(self, target):
        return self.is_target(target) and target in self._pickups
    
    def remove(self, targets):
        if isinstance(targets, BoardTile):
            if targets in self._targets:
                self._targets.remove(targets)
                if self.is_pickup(targets): self._pickups.remove(targets)
        else:
            for target in targets:
                self.remove(target)
    
    def get_sorted(self, start):        
        return sorted(self._targets, key=start.distance_to)

class RollSet:
    def __init__(self):
        self._rolls = {}
        self._multipliers = []
        self.roll = 0
    
    def load_rolls(self, path):
        multipliers = []

        with open(path, 'r') as f:
            reader = csv.reader(f, dialect='excel')
            for row in reader:
                if len(multipliers) == 0:
                    multipliers = [int(re.sub(r"[^\d]", "", x)) for x in row]
                    self._rolls = {m: [] for m in multipliers}
                    continue

                for idx, roll in enumerate(row):
                    if not (not roll):
                        self._rolls[multipliers[idx]].append(int(roll))
    
    def add(self, multiplier, roll):
        if not multiplier in self._rolls:
            self._rolls[multiplier] = []
        self._rolls[multiplier].append(roll)
        self._multipliers.append(multiplier)
    
    def inc(self):
        self.roll += 1

    def reset_counter(self):
        self.roll = 0
    
    def reset(self):
        self.__init__()

    def remove_last(self):
        if len(self._multipliers) > 0:
            self._rolls[self._multipliers.pop()].pop()
    
    def get_next(self, multiplier=None, skip=0):
        ret = None
        if multiplier is None:
            ret = {m: self._rolls[m][self.roll+skip] for m in self._rolls if (self.roll+skip) < len(self._rolls[m])}
        else:
            ret = {multiplier: self._rolls[multiplier][(self.roll+skip):(self.roll+skip+1)]}

        if len(ret) == 0:
            return None

        return ret

    
    def get_all(self, multiplier=None):
        if multiplier is None:
            return self._rolls
        else:
            return self._rolls[multiplier]