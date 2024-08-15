import csv
import logging
from thefuzz import fuzz

from algo import Algo
from models import BoardTile, Board, Targets, RollSet

def cheapest_path(paths: list):
    if len(paths) == 0: return []

    costs = [sum(x) for x in paths]
    lowest_cost = min(costs)

    candidate_idxs = [i for i, x in enumerate(costs) if x == lowest_cost]
    if len(candidate_idxs) == 1:
        return paths[candidate_idxs[0]]
    else:
        lns = [len(paths[x]) for x in candidate_idxs]
        return paths[lns.index(min(lns))]

log = logging.getLogger()
logging.basicConfig(level=logging.INFO,
                    datefmt="%m%d%Y %H%M%S",
                    format="{created} [{levelname}] {message}",
                    style="{")

f = "testrolls.csv"
r = RollSet()
log.info(f"Loading rolls from {f}")
r.load_rolls(f)

b = Board()
t = Targets()
t.add(b.get_railroads())
log.info("Settings targets as railroads")

current = b.get_tiles_by_name("Virginia Avenbue")[0]
log.info(f"Starting at tile {current}")

log.debug("Testing find_next_tile")
tiles = ["read rr", "chance", "boardwalk"]
for tile in tiles:
    log.debug(f"{tile} => {b.find_next_tile(current, tile)}")


quit = False

total_path = []
target_count = 0
a = Algo(r)
while not quit:
    targets = t.get_sorted(current)
    log.info("Closest targets:")

    hit_target = None
    hit_path = None
    for target in targets:
        distance = current.distance_to(target)
        log.info(f"{distance} {target}")

        c = cheapest_path(a.run(current.distance_to(target)))
        if len(c) == 0:
            log.info("Nothing found, continuing...")
        else:
            log.info("You can hit this target!")
            total_path.extend(c)
            hit_path = c
            hit_target = target
            target_count += 1
            break
    
    if hit_target is None:
        quit = True
    else:
        for multi in hit_path:
            print(f"Roll {multi}x - {r.get_next(multi)[multi]}")
            r.inc()
        print(f"Hit target {hit_target}")
        current = hit_target
        a.clear_history()

log.info(f"Total dice used: {sum(total_path)}")
log.info(f"Total targets hit: {target_count}")
log.info("That's the best I could do!")