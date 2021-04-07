from mesa import Model
from mesa.time import RandomActivation
from mesa.space import MultiGrid
from agents.cognitive_agents.offenderAgent import PossibleOffender
from agents.cognitive_agents.victimAgent import SafeLocation, PossibleVictim
from agents.environmental_agents import CrimeGenerator, GeneratorLoc
from agents.environmental_agents.lightAgent import Light
import uuid
from mesa.datacollection import DataCollector

crime_number = 0


def compute_crime_rate(model):
    """Get the crime rate per 1000 poeple. """
    crime_rate = (crime_number / model.pop_count) * 1000
    return crime_rate


def crime_rate_single_run(model):
    """Get the number of crimes commited per time step. """
    crime_rate = (crime_number / (model.num_offenders + model.num_victims)) * 10
    return crime_rate


def crime_number_per_timestep(model):
    """Return the number of crimes committed per time step"""
    return model.crime_number


def average_perception_of_safety(model):
    """Returns the average perception of safety of all agents in the model. """
    agent_safety = [(1 - agent.fear) for agent in model.schedule.agents if
                    isinstance(agent, PossibleVictim)]

    if agent_safety:
        average_safety = sum(agent_safety) / len(agent_safety)
        return average_safety


class Model(Model):
    """A model with a number of agents.
    It represents a space where you can experiment by varying parameters"""

    def __init__(self, n_victims, n_offenders, n_criminal_generators, r_criminal_generators, max_cp,
                 pop_count, width, height):

        self.grid = MultiGrid(width, height, torus=False)
        self.schedule = RandomActivation(self)
        self.datacollector = DataCollector(
            model_reporters={"Average Perception of Safety": average_perception_of_safety,
                             "Crime-rate": crime_rate_single_run},
        )
        self.width = width
        self.height = height
        self.running = True

        # Number of crimes committed per time step.
        self.crime_number = 0.0


        # User settable parameters
        self.num_victims = n_victims
        self.num_offenders = n_offenders
        self.num_crime_areas = n_criminal_generators
        self.crime_area_rad = r_criminal_generators
        self.hotspot_rad = 1
        self.max_criminal_preference = max_cp
        self.pop_count = pop_count

        # add light agents to the grid
        self.light_layer()

        # add possible victims to the grid
        self.add_victims()

        # add possible offenders to the grid
        self.add_offenders()

        # add crime areas
        self.add_criminal_areas()

        self.datacollector.collect(self)

    def light_layer(self):
        """Add the light layer to the model. """
        for i in range(self.width):
            for j in range(self.height):
                l = Light(uuid.uuid4(), i + j, self)
                self.schedule.add(l)
                # light is ordered from darkest to lightest from the
                # bottom left corner to the top right corner.
                self.grid.place_agent(l, (i, j))

                # light is randomised, so long as the
                # luminance difference of surrounding cells is within a limit
                # self.grid.place_agent(l, self.r_pos(l))

    def r_pos(self, new_l):
        """Randomises the positions of the light realistically by considering the difference
        between the illuminance in one position and another"""

        # Position precisely one light agent per position.
        valid = False

        while not valid:
            x = self.random.randrange(self.width)
            y = self.random.randrange(self.height)

            # Check if there is already a light agent in this spot
            if not (any(isinstance(agent, Light)
                        for agent in self.grid.get_cell_list_contents((x, y)))):
                # Check whether given the difference in the influencing factors between the agent
                # and surrounding agents, the new agent can be placed in this position.
                # Returns True or False
                if self.valid_pos((x, y), new_l, 1):
                    valid = True
                    return x, y

    def valid_pos(self, n_pos, new_a, delta):
        """Check whether this position is a valid position given the difference in
        the inlfueincing factors between the new agent and the surrounding agents"""

        # Get the surrounding positions
        neighborhood = self.grid.get_neighborhood(n_pos, moore=True,
                                                  include_center=False)

        # print("Neighboring positions are " + str(neighborhood))

        # Get the surrounding positions containing light agents.
        cell_contents = []
        for pos in neighborhood:
            cell_contents.append(self.grid.get_cell_list_contents([pos]))

        # print("these are the surrounding cell contents " + str(cell_contents))
        f_cell_contents = [val for sublist in cell_contents for val in sublist]
        # print("this is the flat list of the surrounding cell contents " + str(cell_contents))

        surr_light = [a for a in f_cell_contents if isinstance(a, Light)]
        # print("This is the surrounding light list: " + str(surr_light) + " there are " + str(len(surr_light)))

        # If the surrounding light list is empty, return the position
        if len(surr_light) == 0:
            # print("I can be placed here because there is no surrounding light")
            return True
        else:
            # Check whether the difference in illuminance is within the valid scope
            for l in surr_light:
                # print("Illuminance of surr light = " + str(l.illuminance))
                # print("Illuminance of surr light = " + str(new_a.illuminance))
                # print("This is the delta between illuminances " + str(abs(l.illuminance - new_a.illuminance)))

                if abs(l.illuminance - new_a.illuminance) >= delta:
                    # print("I cant be placed here because the difference in illuminance is " + str(
                    #     abs(l.illuminance - new_a.illuminance)) +
                    #       " which is greater than the difference allowed " + str(delta))
                    return False

        return True

    def get_random_pos(self):
        x = self.random.randrange(self.grid.width)
        y = self.random.randrange(self.grid.height)
        return (x, y)

    def add_victims(self):
        for i in range(self.num_victims):
            # Generate a safe location for this agent.
            s = SafeLocation(uuid.uuid4(), self)
            self.schedule.add(s)
            self.grid.place_agent(s, self.get_random_pos())

            # Generate the agent given its safe location.
            p = PossibleVictim(uuid.uuid4(), self, s)
            self.schedule.add(p)
            self.grid.place_agent(p, self.get_random_pos())

    def add_offenders(self):
        for i in range(self.num_offenders):
            c = PossibleOffender(uuid.uuid4(), self, self.max_criminal_preference)
            self.schedule.add(c)
            x = self.random.randrange(self.grid.width)
            y = self.random.randrange(self.grid.height)
            self.grid.place_agent(c, (x, y))

    def generate_criminal_areas(self):
        """ Return a list of criminal areas with specified centroids and radius.
            If criminal areas overlap, update the criminal areas.

            DOES NOT ADD THE AREAS TO THE MODEL, AS IT IS ONLY THE POSITIONS
            WITHIN THE AREAS THAT ARE ADDED TO THE MODEL. """

        # ----- HELPER FUNCTION -----

        def generate_centroid_list(n):
            """ If no centroids have been passed,
            generate random centroids for the criminal areas. """
            centroids = []
            for i in range(n):
                x = self.random.randrange(self.grid.width)
                y = self.random.randrange(self.grid.height)
                centroids.append((x, y))
            return centroids

        def get_surr_pos(pos, r=3):
            return self.grid.get_neighborhood(pos, moore=True, include_center=True, radius=r)

        # ---------------------------
        centroids = self.num_crime_areas
        radius = self.crime_area_rad

        # If the parameter passed as the centroid is an int, generate this number of centroids.
        if isinstance(centroids, int):
            centroids = generate_centroid_list(centroids)

        criminal_area = []
        # For every centroid in the list, create either a hotspot or a criminal area depending
        # on the type.
        for c in centroids:
            criminal_area.append(CrimeGenerator(uuid.uuid4(), self, c, radius))

        # Return a list of criminal areas.
        return criminal_area

    def add_criminal_areas(self, criminal_area=None):
        """Add crime areas to the model. """
        # If no criminal area has been passed, generate random criminal area.
        if criminal_area is None:
            criminal_area = self.generate_criminal_areas()

    def increment_crimes(self):
        self.crime_number += 1
        global crime_number
        crime_number += 1

    def check_victim_agents(self):
        if not [agent for agent in self.schedule.agents if
                isinstance(agent, PossibleVictim)]:
            self.running = False

    def step(self):
        """Advance the model by one step."""
        self.schedule.step()
        self.datacollector.collect(self)
        self.check_victim_agents()
        self.crime_number = 0
