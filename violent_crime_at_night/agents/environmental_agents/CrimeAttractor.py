import uuid
from agents.environmental_agents import CrimeGenerator, GeneratorLoc


class CrimeAttractor(CrimeGenerator):
    """These are areas in the map which have a high crime reputation.

        Their criminal_reputation as well as their location is dynamic, as they aim to represent
        spots in which crimes have been committed.

        The criminal_reputation of these areas will increase
        as more crimes are committed within a certain perimeter, and will deteriorate over time if no crimes are
        commited within a certain ratio.

        The centroid of the area (where the crime has been committed) is the most dangerous,
        whilst the surrounding positions become less and less dangerous.

        They inherit from the crime generator class.
        """

    def __init__(self, unique_id, model, cent_pos, rad):
        super(CrimeAttractor, self).__init__(unique_id, model, cent_pos, rad)

    def recalculate_centroid(self, centroids):
        """Calculate a centroid based on the halfway point of the centroids given"""
        sum_x = sum([c[0] for c in centroids])
        sum_y = sum([c[1] for c in centroids])
        n = len(centroids)
        return sum_x // n, sum_y // n

    def recalculate_criminal_reputation(self, criminal_reputations):
        """Calculate the criminal reputation of the area based on the reputations given. """
        new_reputation = max(criminal_reputations)
        return new_reputation

    def get_overlap(self):
        """Return the overlapping hotspots, if any. """
        hotspot_poss = self.model.grid.get_neighborhood(self.centroid, moore=True, include_center=True,
                                                        radius=(self.radius + 1))
        overlapping_hotspots = set([hotspot_pos.area for hotspot_pos in
                                    self.model.grid.get_cell_list_contents(hotspot_poss)
                                    if isinstance(hotspot_pos, AttractorLoc)])
        return overlapping_hotspots

    def delete_hotspots(self, hotspots):
        """Delete hotspot so there is only one remaining hotspot. """
        for h in hotspots:
            for h_pos in h.poss:
                self.model.grid._remove_agent(h_pos.pos, h_pos)
                self.model.schedule.remove(h_pos)

    def get_distances_from_centroid(self):
        distances = []
        for pos in self.poss:
            distances.append(pos.evaluate_distance(pos.position, self.centroid))

    def merge_hotspots(self, hotspots):
        """Merge all overlapping hotspots. """
        hotspots.add(self)

        self.centroid = self.recalculate_centroid([h.centroid for h in hotspots])
        self.radius = sum([h.radius for h in hotspots])
        self.criminal_reputation = self.recalculate_criminal_reputation([h.criminal_reputation for h in hotspots])
        self.poss = self.get_poss()

        hotspots.remove(self)
        self.delete_hotspots(hotspots)

    def add_to_model(self):
        """Add the new hotspot to the model. """
        overlapping_hotspots = self.get_overlap()
        while overlapping_hotspots:
            self.merge_hotspots(overlapping_hotspots)
            overlapping_hotspots = self.get_overlap()

        for hotspot_pos in self.poss:
            hotspot_pos.set_reputation(self.centroid, self.radius)
            self.model.grid.place_agent(hotspot_pos, hotspot_pos.position)
            self.model.schedule.add(hotspot_pos)

    def get_poss(self):
        """From the each of the positions in the hotspot, convert pos tuple to HotspotPos.
        Update the positions to portray this. """
        # Get a radius of positions surrounding the centroid.
        poss = self.model.grid.get_neighborhood(self.centroid, moore=True, include_center=True, radius=self.radius)

        hotspot_poss = []
        for pos in poss:
            crime_pos = AttractorLoc(uuid.uuid4(), self.model, self, self.criminal_reputation, pos)
            crime_pos.set_reputation(self.centroid, self.radius)
            hotspot_poss.append(crime_pos)

        return hotspot_poss

    def remove_pos(self, h_pos):
        self.poss.remove(h_pos)


class AttractorLoc(GeneratorLoc):
    """ Represents a single location within a hotspot area.
    Inherits from the more general class CrimeAreaPos"""

    def __int__(self, unique_id, model, area, centroid_reputation, pos):
        super(AttractorLoc, self).__init__(unique_id, model, area, centroid_reputation, pos)
        self.reputation = 0

    def __init__(self, unique_id, model, area, centroid_reputation, pos):
        super(AttractorLoc, self).__init__(unique_id, model, area, centroid_reputation, pos)
        self.reputation_decrease_factor = 0.15
        self.reputation_decrease = 0

    def set_reputation(self, centroid, radius):
        """Set the reputation of the position depending on the reputation of the
        centroid and its distance from it. """
        distance_from_centroid = self.evaluate_distance(centroid, self.position)
        self.reputation = self.centroid_reputation / (distance_from_centroid + 1)

        self.reputation_decrease = self.reputation * self.reputation_decrease_factor

    def step(self):
        """Deteriorate the reputation of the position by a percentage at each tick of the model"""
        self.reputation = self.reputation - self.reputation_decrease
        if self.reputation <= 0:
            self.model.grid._remove_agent(self.pos, self)
            self.model.schedule.remove(self)
            self.area.remove_pos(self)