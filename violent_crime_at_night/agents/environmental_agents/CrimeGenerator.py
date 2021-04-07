import random
import uuid
import numpy as np
from mesa import Agent


class CrimeGenerator(Agent):
    """These are areas in the map which have a high crime reputation.

    Their criminal_reputation as well as their location is static, as they aim to represent
    areas (such as neighborhoods, parks, night-clubs...) which are known to be dangerous.

    The centroid of the area is the most dangerous, whilst the surrounding positions become less and
    less dangerous.

    The higher the criminal_reputation, the higher the percieved danger in the area.

    """

    def __init__(self, unique_id, model, cent_pos, rad):
        super().__init__(unique_id, model)

        self.centroid = cent_pos  # center position of the criminal position.
        self.radius = rad  # the radius of the criminal area

        self.criminal_reputation = round(random.uniform(0.5, 1),3) # the criminal reputation of the area
        self.poss = self.get_poss()  # List of CrimeAreaPos agents.
        self.add_to_model()

    def get_poss(self):
        """ Given the list of positions surrounding the radius,
        return a list of CrimeAreaPos agents"""

        # Get a radius of positions surrounding the centroid.
        poss = self.model.grid.get_neighborhood(self.centroid, moore=True, include_center=True, radius=self.radius)

        # Takes a list of regular positions surrounding the centroid and turns them into Crime
        # Area positions.
        crime_area_poss = []
        for pos in poss:
            crime_pos = GeneratorLoc(uuid.uuid4(), self.model, self, self.criminal_reputation, pos)
            crime_area_poss.append(crime_pos)

        return crime_area_poss

    def add_to_model(self):
        """Add the criminal area to the model by adding each of the positions within
        the criminal area. """
        for pos in self.poss:
            pos.set_reputation(self.centroid, self.radius)
            self.model.grid.place_agent(pos, pos.position)
            self.model.schedule.add(pos)


class GeneratorLoc(Agent):
    """ Represents a single location within a crime area. """

    def __init__(self, unique_id, model, area, centroid_reputation, pos):
        super().__init__(unique_id, model)

        self.area = area  # The criminal area to which this position agent belongs.
        self.centroid_reputation = centroid_reputation
        self.reputation = 0
        self.position = pos  # The position this agent has in the grid.

    def set_reputation(self, centroid, radius):
        """Set the reputation of the position depending on the reputation of the
        centroid and its distance from it. """

        distance_from_centroid = self.evaluate_distance(centroid, self.position)
        self.reputation = round((self.centroid_reputation / (distance_from_centroid + 1)), 3)
        # self.reputation = self.centroid_reputation - (self.centroid_reputation * (distance_from_centroid + 1))


    def evaluate_distance(self, a, b):
        """ Calculate the manhattan distance between two positions in the grid. """
        return round(np.linalg.norm(np.array(a) - np.array(b)))