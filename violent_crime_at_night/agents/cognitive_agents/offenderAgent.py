import random
import uuid
import numpy as np

from mesa import Agent
from agents.cognitive_agents.victimAgent import PossibleVictim
from agents.environmental_agents import GeneratorLoc
from agents.environmental_agents.CrimeAttractor import AttractorLoc, CrimeAttractor


class PossibleOffender(Agent):
    """These agents commit crimes depending on internal and external factors and intensities. """

    def __init__(self, unique_id, model, max_criminal_preference):
        super().__init__(unique_id, model)

        # Level of criminal fulfillment with which this agent feels satisfied.
        self.CRIMINAL_PREFERENCE = round(random.uniform(0, max_criminal_preference), 3)

        # The greater the difference between CRIMINAL_PREFERENCE and the criminal_fulfillment,
        # the higher the chances the offender will commit a crime.
        self.criminal_fulfillment = round(random.uniform(0, 1), 3)

        # The extent to which this agent can look around.
        self.VISIBILITY = 5

        # Preference the agent has for criminal areas.
        self.AREA_PREFERENCE = round(random.uniform(0, 1), 3)

    def get_surr_pos(self, pos, visibility=1):
        """Get the positions surrounding pos given the visibility, 1 by default"""
        return self.model.grid.get_neighborhood(pos, moore=True, include_center=True, radius=visibility)

    def get_surr_crime(self):
        """Get the visible surrounding criminal area positions
            :return List of AttractorLoc and GeneratorLoc agents. """

        surr_pos = self.get_surr_pos(self.pos, self.VISIBILITY)
        cell_contents = self.model.grid.get_cell_list_contents(surr_pos)
        criminal_area_cell_contents = [agent for agent in cell_contents if
                                       (isinstance(agent, AttractorLoc) or
                                        isinstance(agent, GeneratorLoc))]

        return criminal_area_cell_contents

    def get_min_dist_to_crime_pos(self, surr_crime):
        """Returns the minimum distance and the position of the nearest criminal position. """
        crime_dist = [(self.evaluate_distance(self.pos, surr_pos.position), surr_pos.position)
                      for surr_pos in surr_crime]
        return min(crime_dist)

    def evaluate_distance(self, a, b):
        """ Calculate the manhattan distance between two positions a and b on the grid. """
        return np.abs(np.array(a) - np.array(b)).sum()

    def get_criminal_motive_intensity(self, surr_crime):
        """This is the criminal motive intensity to commit a crime.
        The relationships are the following:
            high criminal preference & low criminal fulfillment = most likely to commit crime
            low criminal preference & low criminal fulfillment = somewhat likely to commit crime
            high criminal preference & high criminal fulfillment = somewhat likely to commit crime
            low criminal preference & high criminal fulfillment = not likely to commit crime

        The criminal motive intensity varies depending on the different internal levels of each agent.
        Depending on each agent's criminal preference, criminal fulfillment and preference for criminal
        areas, the agent will have different criminal motive intensities.

        """
        # Get the difference between the preferred level of criminal fulfillment and the current level.
        criminal_motive_intensity = self.CRIMINAL_PREFERENCE - self.criminal_fulfillment

        # Take into consideration the preference this agent has for criminal areas.
        # If there is no surrounding crime, decrease the criminal motive intensity proportionally
        # to their preference to commit crimes in criminal areas.
        if not surr_crime:
            criminal_motive_intensity -= criminal_motive_intensity * self.AREA_PREFERENCE

        else:
            # Decrease the criminal motive intensity by a factor reflecting the agent's distance
            # to the nearest criminal position - as the agent gets closer to a criminal position
            # the decrease factor becomes smaller.

            # Get a list of all the distances and positions of surrounding crime and select the
            # nearest crime position

            min_dist_crime = self.get_min_dist_to_crime_pos(surr_crime)

            # Decrease the criminal motive intensity depending on the preference this agent
            # has for criminal areas and the distance from the criminal areas.
            dist_influence_factor = min_dist_crime[0] / ((self.VISIBILITY * 2) + 1)
            criminal_motive_intensity -= criminal_motive_intensity * \
                                         (dist_influence_factor * self.AREA_PREFERENCE)

        return criminal_motive_intensity

    def get_target(self):
        """Returns the closest PossibleVictim from the offender"""

        # Get surrounding possible victims
        surr_pos = self.get_surr_pos(self.pos, self.VISIBILITY)
        cell_contents = self.model.grid.get_cell_list_contents(surr_pos)
        surr_victims = [agent for agent in cell_contents if isinstance(agent, PossibleVictim)]

        target = None
        if surr_victims:
            dist_victims = [(self.evaluate_distance(self.pos, v.pos), v) for v in surr_victims]
            target = min(dist_victims, key=lambda x: x[0])[1]
        return target

    def chase(self, target):
        """ The offender chases a victim - moves to the position which gets the agent closest
        to the target.
        If the victim and the offender positions coincide, the offender will commit a crime. """

        # Decrease the criminal fulfillment, but not by as much as you would decrease it
        # by if the agent were not chasing a victim.
        decrease_factor = random.uniform(0, 0.01)
        self.criminal_fulfillment -= (self.criminal_fulfillment * decrease_factor)

        # Move which results in the smallest distance from the target.
        next_moves = self.get_surr_pos(self.pos)
        moves_target_dist = [(self.evaluate_distance(move, target.pos), move) for move
                             in next_moves]
        next_move = min(moves_target_dist)[1]
        self.model.grid.move_agent(self, next_move)

        if target.pos == self.pos:
            self.commit_organised_crime(target)

    def commit_organised_crime(self, target):
        """The offender agent will commit a crime against the victim it has been chasing if they
        coincide in the same location. """

        # Remove this victim agent from the simulation.
        self.model.grid._remove_agent(self.pos, target)
        self.model.schedule.remove(target)

        # Increase the criminal fulfillment of this offender
        fulfillment_increase = random.uniform(0.4, 1)
        self.criminal_fulfillment += fulfillment_increase

        # Record this crime in the model and add a crime attractor.
        self.model.increment_crimes()
        CrimeAttractor(uuid.uuid4(), self.model, self.pos, self.model.hotspot_rad)

    def move_towards_crime_area(self, surr_crime):
        """Move towards the nearest crime area, given the visibility of the agent. """

        # Get the min distance from the agent to a surrounding criminal position.
        min_crime_dist = self.get_min_dist_to_crime_pos(surr_crime)

        # Determine the next move based on the resulting distance from that move to the nearest
        # criminal position.
        next_moves = self.get_surr_pos(self.pos)
        crime_dist, crime_pos = min_crime_dist

        move_crime_dist = [(self.evaluate_distance(move, crime_pos), move) for move in
                           next_moves]
        next_move = min(move_crime_dist)[1]
        self.model.grid.move_agent(self, next_move)

    def random_move(self):
        """Move to a random location on the grid and decrease the criminal fulfillment."""
        # Decrease the criminal fulfilment
        decrease_factor = random.uniform(0, 0.02)
        self.criminal_fulfillment -= decrease_factor

        next_moves = self.get_surr_pos(self.pos)
        next_move = self.random.choice(next_moves)
        self.model.grid.move_agent(self, next_move)

    def step(self):
        """ With every tick of the simulation, depending on the different internal levels
         of the agent, it will either :
            - find a victim, chase the victim, and attempt commit a crime against the victim.
            - move towards a criminal area
            - commit an oportunistic crime
            - continue luring the area.
         """

        surr_crime = self.get_surr_crime()
        criminal_motive_intensity = self.get_criminal_motive_intensity(surr_crime)

        sample_probability_motivation = round(random.uniform(0, 1), 3)
        sample_probability_opportunity = round(random.uniform(0, 1), 3)
        target = self.get_target()

        # If the criminal motive intensity of the agent is high enough,
        # attempt to commit the crime, or if there is a target present, also consider committing a crime.
        if (criminal_motive_intensity > sample_probability_motivation) or \
                (target and criminal_motive_intensity > sample_probability_opportunity):
            # If the agent has found a target, chase the target.
            if target:
                self.chase(target)
            else:
                self.random_move()
        else:
            # If the criminal motive intensity is not high enough
            sample_probability = round(random.uniform(0, 1), 3)

            # If the preference towards criminal areas is high enough and there is a criminal
            # area within the visibility of the agent, move towards the nearest criminal area,
            # otherwise move randomly about the grid.
            if self.AREA_PREFERENCE > sample_probability and surr_crime:
                self.move_towards_crime_area(surr_crime)
            else:
                self.random_move()