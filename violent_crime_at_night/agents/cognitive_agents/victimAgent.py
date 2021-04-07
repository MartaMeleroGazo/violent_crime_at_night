import operator
import random
import statistics
import numpy as np

from mesa import Agent
from agents.environmental_agents.CrimeAttractor import AttractorLoc
from agents.environmental_agents.CrimeGenerator import GeneratorLoc
from agents.environmental_agents.lightAgent import Light


class SafeLocation(Agent):
    """
    Safe locations for the agents. Each agent has an associated safe location.
    The safe location must be removed when the agent has reached it.
    """
    def __init__(self, unique_id, model):
        super().__init__(unique_id, model)

    def remove(self):
        self.model.grid._remove_agent(self.pos, self)
        self.model.schedule.remove(self)


class PossibleVictim(Agent):
    """
    Represent the possible victims in the model.
    These agents move about  where they feel safest with the goal of reaching
    their destination.
    """

    def __init__(self, unique_id, model, goal):
        super().__init__(unique_id, model)

        # This is the destination of the agent - its home location.
        self.goal = goal
        self.goal_pos = goal.pos
        self.is_safe = False  # Indicates whether the agent has reached the goal location.

        # Represents the emotional state of fear of the agent - initially the agent feels completly safe.
        self.fear = 0

        # The ability this victim has to recognise and evaluate the environment accurately.
        self.PERCEPTION_CAPABILITIES = round(random.uniform(0, 1), 3)

        # Represents how scared the agent gets generally - how much or how little its
        # fear is affected when in dangerous situations.
        self.FEAR_SUSCEPTIBILITY = round(random.uniform(0, 1), 3)

        # Represents to what extent the agent is influenced by its surroundings,
        # by keeping in mind their perception capabilities and their fear susceptibility.
        self.ENVIRONMENTAL_INFLUENCE = statistics.mean([self.FEAR_SUSCEPTIBILITY, self.PERCEPTION_CAPABILITIES])

        # The visibility of the agent
        self.VISIBILITY = 4

        # Represents the area surrounding the safe location with which the agent is familiar with.
        self.SAFE_AREA_PERIMETER = 4

        # Represents the preference this agent has for the illuminance on the street
        self.LIGHT_PREFERENCE = round(random.uniform(0, 1), 3)

    def get_surr_pos(self, pos, visibility=1):
        """Get the positions surrounding pos given the visibility, 1 by default"""
        return self.model.grid.get_neighborhood(pos, moore=True, include_center=False, radius=visibility)

    def evaluate_distance(self, a, b):
        """Evaluate the manhattan distance between points a and b on the grid"""
        return np.abs(np.array(a) - np.array(b)).sum()

    def familiar_area(self):
        """Returns True if the agent is familiar with the area
                - the agent's visibility allows the perception of the
                perimeter of its safe location.
         False otherwise. """
        familiar_area = self.get_surr_pos(self.goal_pos, visibility=self.SAFE_AREA_PERIMETER)
        surr_curr_pos = self.get_surr_pos(self.pos, visibility=self.VISIBILITY)

        if list(set(familiar_area) & set(surr_curr_pos)):
            return True
        else:
            return False

    def move_towards_safe_location(self):
        """Move towards the safe location """
        curr_dist = self.evaluate_distance(self.pos, self.goal_pos)
        self.move(curr_dist, self.goal_pos, 'closer')

    def move_away_from_danger(self, surr_danger):
        """Moves away from what this agent considers the greatest danger.

        The agent makes its move based on the tradeoff between:
        - the shortest resulting distance to the goal location
        - the lowest resulting criminal reputation of the area
        - the longest distance from the nearest crime position
        - the highest incident illuminance
        """

        def find_move_pair(tuple_list, search):
            """Find the search item in the list of tuples. """
            return [item for item in tuple_list if item[1] == search]

        # List of possible next moves.
        next_moves = self.model.grid.get_neighborhood(self.pos, moore=True, include_center=False, radius=1)

        # List of moves ordered by the different preferences
        moves_goal_dist = self.moves_according_to_goal_distance(next_moves)
        moves_min_crime_dists = self.moves_according_to_crime_dist(next_moves, surr_danger)
        moves_reps = self.moves_according_to_crime_rep(next_moves, surr_danger)
        moves_light = self.moves_according_to_light(next_moves)

        move_tradeoff = []
        for (dist, move) in moves_goal_dist:
            move_goal_dist_idx = moves_goal_dist.index((dist, move)) + 1
            move_min_crime_dists_idx = moves_min_crime_dists.index(find_move_pair(moves_min_crime_dists, move)[0]) + 1
            move_reps_idx = moves_reps.index(find_move_pair(moves_reps, move)[0]) + 1
            move_light_idx = moves_light.index(find_move_pair(moves_light, move)[0]) + 1

            idx_sum = move_goal_dist_idx + move_reps_idx + move_min_crime_dists_idx + move_light_idx
            move_tradeoff.append((idx_sum, move))

        next_move = min(move_tradeoff)[1]

        fear_decrease_factor = random.uniform(0, 0.6)
        self.fear -= self.fear * fear_decrease_factor

        self.model.grid.move_agent(self, next_move)

    def moves_according_to_goal_distance(self, next_moves):
        """ Create a list with all the possible moves, sorted in increasing order of resulting
            distance from the goal. """
        return sorted([(self.evaluate_distance(pos, self.goal_pos), pos) for pos
                       in next_moves])

    def moves_according_to_crime_dist(self, next_moves, surr_danger):
        """ Create a list with all the possible moves, sorted in decreasing order of resulting
                distances from the positions to the nearest criminal location. """
        move_min_crime_dists = []
        for move in next_moves:
            move_dist = []
            for (rep, pos, dist) in surr_danger:
                resulting_dist = self.evaluate_distance(move, pos)
                move_dist.append((resulting_dist, move))
            move_min_crime_dists.append(min(move_dist))

        return sorted(move_min_crime_dists, reverse=True)

    def moves_according_to_crime_rep(self, next_moves, surr_danger):
        """ Create a list with all the possible moves, sorted in increasing order of
        resulting, criminal reputations, 0 if none. """

        def find_move_pair(tuple_list, search):
            """Find the search item in the list of tuples. """
            return [item for item in tuple_list if item[1] == search]

        move_reps = []
        for move in next_moves:
            rep_pos_dist = find_move_pair(surr_danger, move)
            if not rep_pos_dist:
                move_reps.append((0, move))
            else:
                rep_pos_pair = (rep_pos_dist[0][0], rep_pos_dist[0][1])
                move_reps.append(rep_pos_pair)
        return sorted(move_reps)

    def moves_according_to_light(self, next_moves):
        cell_contents = self.model.grid.get_cell_list_contents(next_moves)
        surr_light = sorted([(agent.illuminance, agent.pos) for agent in cell_contents
                             if isinstance(agent, Light)])

        return surr_light
        # self.model.grid.move_agent(self, new_pos.pos)

    def move(self, curr_dist, pos, condition):
        """Move (according to the condition) either further or closer to pos"""

        # Surrounding positions.
        next_moves = self.get_surr_pos(self.pos)

        # Function to compare a and b based on the comparator.
        def compare(a, comparator, b):
            ops = {'closer': operator.gt,
                   'further': operator.lt}
            return ops[comparator](a, b)

        next_move = next_moves[0]
        for n_pos in next_moves:
            if compare(curr_dist, condition, self.evaluate_distance(pos, n_pos)):
                curr_dist = self.evaluate_distance(pos, n_pos)
                next_move = n_pos

        fear_decrease_factor = random.uniform(0, 0.6)
        self.fear -= self.fear * fear_decrease_factor

        self.model.grid.move_agent(self, next_move)

    def surrounding_danger(self):
        """Return a list of reputation, location, distance tuples where:
            - reputation is the reputation of the crime position
            - location is the coordinate of the crime position in the grid
            - distance is the distance from the agent to the criminal position
        All the tuples returned are within the agents' visibility."""

        surr_danger = [(crime_pos.reputation, crime_pos.position,
                        self.evaluate_distance(crime_pos.position, self.pos))
                       for crime_pos in
                       self.model.grid.get_neighbors(self.pos, moore=True, radius=self.VISIBILITY)
                       if (isinstance(crime_pos, AttractorLoc) or
                           isinstance(crime_pos, GeneratorLoc))]

        return surr_danger

    def average_surr_reputation(self, surr_danger):
        """Return an average of the surrounding criminal reputations. """
        reps = [rep for (rep, pos, dist) in surr_danger]
        average = sum(reps) / len(reps)
        return round(average, 3)

    def remove_agent(self):
        """Remove the agent and its safe location from the grid"""
        self.goal.remove()
        self.model.grid._remove_agent(self.pos, self)
        self.model.schedule.remove(self)

    def step(self):
        """
        This is the action the victim agent makes with every tick.
        The victim's ultimate goal is to make it back to their safe location.
        The agents will either chose to move in the direction of the safe location,
        or if they feel scared enough, they will try to move away from danger or
        go around dangerous areas.
        """

        # If the agent is already in the safe location, remove it from the grid.
        if self.pos == self.goal_pos:
            self.remove_agent()

        else:
            # Check for surrounding danger
            surr_danger = self.surrounding_danger()
            if surr_danger:
                # Average criminal reputation of surrounding danger.
                avg_surr_reputation = self.average_surr_reputation(surr_danger)

                # Check familiarity of the agent with surroundings.
                if not self.familiar_area():
                    # Increase the fear depending on how much the agent is influenced by
                    # its environment and the average surrounding criminal reputation.
                    self.fear += (avg_surr_reputation * self.ENVIRONMENTAL_INFLUENCE)
                else:
                    # Decrease the fear of the agent, as it is familiar with the area.
                    fear_decrease_factor = random.uniform(0, 0.1)
                    self.fear -= self.fear * fear_decrease_factor

            # If the fear is high enough, and there is surrounding danger
            # move away from the danger location,
            # otherwise continue moving in the direction of the goal position.
            sample_probability = random.uniform(0, 1)

            if surr_danger and self.fear > sample_probability:
                self.move_away_from_danger(surr_danger)
            else:
                self.move_towards_safe_location()