from mesa import Agent


class Light(Agent):
    """
    The amount of light incident in each given cell.
    """

    def __init__(self, unique_id, illuminance, model):
        super().__init__(unique_id, model)
        grid_size = model.height + model.width
        self.illuminance = illuminance / (grid_size - 2)

    def set_illuminance(self, illuminance, grid_size):
        if illuminance > 0:
            self.illuminance = illuminance / (grid_size - 2)