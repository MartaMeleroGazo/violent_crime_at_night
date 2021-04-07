from colorsys import hls_to_rgb

from mesa.visualization.ModularVisualization import ModularServer
from mesa.visualization.UserParam import UserSettableParameter
from mesa.visualization.modules import CanvasGrid
from mesa.visualization.modules import ChartModule
from webcolors import rgb_to_hex

from agents.cognitive_agents.offenderAgent import PossibleOffender
from agents.cognitive_agents.victimAgent import SafeLocation, PossibleVictim
from agents.environmental_agents import GeneratorLoc
from agents.environmental_agents.CrimeAttractor import AttractorLoc
from agents.environmental_agents.lightAgent import Light
from model.model import Model


def adjust_color_lightness(hls_color, factor):
    h, l, s = hls_color
    l = factor
    n_r, n_g, n_b = hls_to_rgb(h, l, s)

    n_r *= 255
    n_g *= 255
    n_b *= 255

    new_hex = rgb_to_hex((int(n_r), int(n_g), int(n_b)))
    return new_hex


def agent_portrayal(agent):
    portrayal = {}

    if type(agent) is Light:
        portrayal["Shape"] = "rect"
        portrayal["Color"] = adjust_color_lightness((0, 0, 0), agent.illuminance)
        portrayal["Filled"] = "true"
        portrayal["Layer"] = 0
        portrayal["h"] = 1
        portrayal["w"] = 1

    if type(agent) is GeneratorLoc:
        portrayal["Shape"] = "rect"
        portrayal["Color"] = adjust_color_lightness((350, 0.36, .85), (1 - agent.reputation))
        portrayal["Filled"] = "true"
        portrayal["Layer"] = 1
        portrayal["h"] = 1
        portrayal["w"] = 1

    if type(agent) is AttractorLoc:
        portrayal["Shape"] = "rect"
        portrayal["Color"] = adjust_color_lightness((350, 0.36, .85),
                                                    (1 - (agent.reputation / agent.centroid_reputation)))
        portrayal["Filled"] = "true"
        portrayal["Layer"] = 1
        portrayal["h"] = 1
        portrayal["w"] = 1

    elif type(agent) is PossibleVictim:
        portrayal["Shape"] = "circle"
        portrayal["Color"] = "#66ccff"
        portrayal["Filled"] = True
        portrayal["Layer"] = 2
        portrayal["r"] = 0.5

    elif type(agent) is PossibleOffender:
        portrayal["Shape"] = "circle"
        portrayal["Color"] = "#e21818"
        portrayal["Filled"] = True
        portrayal["Layer"] = 2
        portrayal["r"] = .9

    if type(agent) is SafeLocation:
        portrayal["Shape"] = "rect"
        portrayal["Color"] = "	#0088cc"
        portrayal["Filled"] = "true"
        portrayal["Layer"] = 2
        portrayal["h"] = 1
        portrayal["w"] = 1

    return portrayal


grid = CanvasGrid(agent_portrayal, 50, 50, 800, 800)
chart1 = ChartModule(
    [{"Label": "Average Perception of Safety", "Color": "#0000FF"}],
    data_collector_name="datacollector"
)

chart2 = ChartModule(
    [{"Label": "Crime-rate", "Color": "black"}],
    data_collector_name="datacollector"
)

model_params = {
    "n_victims": UserSettableParameter('slider', 'Number of Possible Victims', value=50, min_value=0, max_value=100, step=1),
    "n_offenders": UserSettableParameter('slider', 'Number of Possible Offernders', value=15, min_value=0, max_value=30, step=1),
    "n_criminal_generators": UserSettableParameter('slider', 'Number of Criminal Generators', value=3, min_value=0, max_value=6, step=1),
    "r_criminal_generators": UserSettableParameter('slider', 'Radius of the Criminal Generator Area', value=4, min_value=0, max_value=8,
                                step=1),
    "max_cp": UserSettableParameter('slider', 'Upper Bound on Criminal Preference of Offenders', value=0.5, min_value=0,
                                    max_value=1,
                                    step=0.01),
    "pop_count": 0,
    "height": 50,
    "width": 50
}

server = ModularServer(Model,
                       [grid, chart1, chart2],
                       "Violent Crime when Walking Home Alone at Night",
                       model_params)

server.port = 8002
server.launch()
