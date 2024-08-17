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

def input_check(i: str, type: str, default=None):
    global b

    i = i.strip().lower()

    if len(i) == 0:
        return default
    
    if i[0] == "~": i = i[1:]

    if i == "q":
        print("Okay, exiting!")
        exit()
    
    if type == "yn":
        return i[0] == "y"

    if type == "roll":
        z = int(i) if i.isnumeric() else 0
        if z < 2 or z > 12:
            return 0
        else:
            return z
    
    if type == "tile":
        if len(i) == 2 and i[1:].isnumeric():
            x = i[0]
            y = int(i[1:])
            return b._tiles[(10*{"b": 0, "l": 1, "t": 2, "r": 3}[x]+y)%len(b._tiles)]
        return b.get_tiles_by_name(i)[0]
    
    if type == "target":
        if i == "rr":
            return b.get_railroads()
        if i == "chance":
            return b.get_chances()
        if i == "chest":
            return b.get_chests()
        if i == "tu" or i == "tax" or i == "util":
            return b.get_tax_utilities()
        if i == "corners":
            return b.get_corners
        return input_check(i, "tile")
    
    return None


log = logging.getLogger()
logging.basicConfig(level=logging.WARN,
                    datefmt="%m%d%Y %H%M%S",
                    format="{created} [{levelname}] {message}",
                    style="{")

f = "rolls.csv"
r = RollSet()
log.info(f"Loading rolls from {f}")
r.load_rolls(f)
# r.roll = x

b = Board()
t = Targets()

quit = False
start = None
while not quit:
    start_in = input("Please enter your starting tile: ")
    start = input_check(start_in, "tile")
    if start is None:
        print(f"Unable to locate tile (searched for {start})")
        continue

    confirm_in = input(f"Found tile {start}, is this correct? (y/n): ")
    confirm = input_check(confirm_in, "yn", False)
    if confirm:
        quit = True
    
print(f"Set starting tile to {start}")

quit = False

quit = True
#t.add(b.get_railroads())
event = ["b1", "b3", "l1", "l3", "l6", "r1", "r2", "r7"]
x = [input_check(z, "tile") for z in event]
t.add(x, True)

while not quit:
    target_in = input("Please add a target (prefix with ~ to remove): ")
    target = input_check(target_in, "target")
    if target is None:
        print(f"Unable to locate tile(s) (searched for {target_in})")
        continue
    
    remove = (target_in[0] == "~")
    if isinstance(target, list):
        if remove:
            t.remove(target)
        else:
            t.add(target)
        print(f"{'Removed' if remove else 'Added'} targets: {' '.join([str(x) for x in target])}")
    else:
        confirm_in = input(f"Found tile {target}, is this correct? (y/n): ")
        confirm = input_check(confirm_in, "yn", False)

        remove = (target_in[0] == "~")
        if confirm:
            pickup = False
            if remove:
                t.remove(target)
            else:
                pickup_in = input(f"Is this target a pickup? (y/n): ")
                pickup = input_check(pickup_in, "yn", False)
                t.add(target, pickup)
            print(f"{'Removed' if remove else 'Added'} {'pickup ' if pickup else ''}target {target}")
        else:
            continue
    more_in = input(f"Continue updating targets? (y/n): ")
    more = input_check(more_in, "yn", False)
    if not more:
        quit = True


if t.count() == 0:
    print("No targets selected, cannot run.")
    exit()

log.info(f"Continuing with {t.count()} targets")

a = Algo(r)
target_count = 0
start_r = r.roll

def generate_path(targets: Targets, start: BoardTile):
    global log, r, a, target_count

    quit = False
    path = []

    start_r = r.roll

    while not quit:
        target_tiles = targets.get_sorted(start)
        log.info("Closest targets:")

        hit_target = None
        for target in target_tiles:
            distance = start.distance_to(target)
            log.info(f"{distance} {target}")

            c = cheapest_path(a.run(start.distance_to(target)))
            if len(c) == 0:
                log.info("Nothing found, continuing...")
            else:
                log.info("You can hit this target!")
                path.extend(c)
                hit_target = target
                target_count += 1
                r.roll += len(c)
                break
        
        if hit_target is None:
            quit = True
        else:
            start = hit_target
            a.clear_history()
    
    r.roll = start_r
    return path

quit = False
i = 0
regen = False
path = generate_path(t, start)

current = start
while not quit:
    if len(path) == 0 or i >= len(path):
        print(f"All done!")
        break

    print(f"Current Tile: {current}")
    multiplier, roll = path[i], r.get_next(path[i])
    roll = roll[multiplier][0]

    next_tile = b.get_tile_after(current, roll)
    is_target = t.is_target(next_tile)
    print(f"Suggested roll: {multiplier}x {roll} (hits {'TARGET! ' if is_target else ''} {b.get_tile_after(current, roll)})")
    rolled_in = input("Enter your actual roll: ")
    rolled = input_check(rolled_in, "roll", roll)
    if rolled == 0:
        print(f"Valid rolls are integers between 2 and 12, inclusive")
        continue

    current = b.get_tile_after(current, rolled)
    print(f"Hit tile {current}")
    if current.is_chance():
        move_rr_in = input("Did you move to the next railroad? (y/n): ")
        move_rr = input_check(move_rr_in, "yn", False)
        if move_rr:
            rr_dists = [current.distance_to(x) for x in b.get_railroads()]
            current = b.get_tile_after(current, min(rr_dists))
            regen = True
    elif t.is_pickup(current):
        print("Other pickup targets: "
              + ' '.join([x._title for x in t._pickups if x != current]))
        moved_pickup_in = input("Did this pickup move? (y/n): ")
        moved_pickup = input_check(moved_pickup_in, "yn", False)
        if moved_pickup:
            quit2 = False
            while not quit2:
                moved_to_in = input("Where did it move to? ")
                moved_to = input_check(moved_to_in, "tile", None)
                if moved_to is None:
                    print(f"Unable to locate tile(s) (searched for {moved_to})")
                    continue
                confirm_in = input(f"Found tile {moved_to}, is this correct? (y/n): ")
                confirm = input_check(confirm_in, "yn", False)

                if confirm and not current == moved_to:
                    regen = True
                    t.remove(current)
                    t.add(moved_to)
                    quit2 = True
                    print(f"Moved target from {current} to {moved_to}")
                elif confirm:
                    print(f"Target did not actually move, continuing")
                    break
    i += 1
    r.inc()
    if regen:
        log.info("Regenerating rest of path for changes...")
        i = 0
        path = generate_path(t, current)
        regen = False

log.info("That's the best I could do!")
log.info(f"Reset roll # to {r.roll + i}")