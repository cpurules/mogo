import logging

log = logging.getLogger()


class Algo:
    hit_with = 1000
    dont_roll_unless_hit = True

    def __init__(self, rollset):
        self._rollset = rollset
        self._paths = []
    
    def clear_history(self):
        self._paths = []
    
    def run(self, distance_remaining, current_path=[]):
        log.debug(f"REMAINING: {distance_remaining}")

        if len(current_path) > 0:
            log.debug(f"current path: {' '.join([str(x)+'x' for x in current_path])}")
        
        next_rolls = self._rollset.get_next(skip=len(current_path))

        if not Algo.hit_with in next_rolls:
            log.debug(f"Ran out of {Algo.hit_with}x rolls")
            return []
        
        if Algo.hit_with > 100:
            if 2 in next_rolls: del next_rolls[2]
            if 3 in next_rolls: del next_rolls[3]
        
        possible_rolls = {}
        for multiplier in next_rolls:
            if multiplier > Algo.hit_with: continue
            next_roll = next_rolls[multiplier]
            if (next_roll <= distance_remaining 
                and not (distance_remaining - next_roll) == 1):
                possible_rolls[multiplier] = next_roll
        
        if len(possible_rolls) == 0:
            log.debug("Cannot proceed from here without passing target")
            return []
 
        for multiplier in possible_rolls:
            roll = possible_rolls[multiplier]

            log.debug(f"testing {multiplier}x roll {roll}")
            if roll == distance_remaining:
                if multiplier == Algo.hit_with:
                    log.debug("hit!")
                    self._paths.append(current_path + [multiplier])
                    continue
                else:
                    log.debug("hit, but wrong multi")
                    continue
            else:
                if multiplier == Algo.hit_with and Algo.dont_roll_unless_hit:
                    continue
                rest = self.run(distance_remaining - roll, current_path + [multiplier])
                if len(rest) == 0:
                    log.debug(f"No path found from here")
                    continue

        return self._paths