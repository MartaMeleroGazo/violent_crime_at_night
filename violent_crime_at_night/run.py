from mesa.batchrunner import BatchRunner
from model.model import Model, compute_crime_rate
import matplotlib.pyplot as plt
import numpy as np

graph = 2  # Change the value of this variable to display a different graph.

if graph == 1:
    # ----------------------------------------------------------
    # 1 - Bar chart for crime rate and varying criminal preferences.
    # ----------------------------------------------------------

    fixed_params = {"n_victims": 50,  # Number of victims
                    "n_offenders": 15,  # Number of offenders
                    "n_criminal_generators": 3,  # Number of criminal generators
                    "r_criminal_generators": 4,  # Radius of criminal generators
                    # "max_cp": 0.5, # Maximum criminal preference
                    "pop_count": 335000,  # Population count

                    "width": 50,
                    "height": 50}

    # variable_params = None
    variable_params = {"max_cp": np.arange(0, 1.1, 0.1)}

    batch_run = BatchRunner(Model,
                            variable_params,
                            fixed_params,
                            iterations=7,  # Number of iterations the model runs for
                            max_steps=100,
                            model_reporters={"crimerate": compute_crime_rate})
    batch_run.run_all()
    run_data = batch_run.get_model_vars_dataframe()
    print(run_data)

    reduced_data = run_data.loc[:, ["max_cp", "crimerate"]]
    reduced_data = reduced_data.groupby(["max_cp"], as_index=False).max()

    x = list(round(i, 2) for i in reduced_data.max_cp)
    y = list(reduced_data.crimerate)

    x_pos = [i for i, _ in enumerate(x)]

    plt.bar(x_pos, y, color='red')
    plt.xlabel("Maximum Offender Criminal Preference")
    plt.ylabel("Crime Rate per 1000 population")
    plt.title("Effect of Offender Criminal Preference on Crime-rate")

    plt.xticks(x_pos, x)

    plt.show()

if graph == 2:
    # ----------------------------------------------------------
    # 2 - Line chart for crime rate.
    # ----------------------------------------------------------

    fixed_params = {"n_victims": 50,  # Number of victims
                    "n_offenders": 15,  # Number of offenders
                    "n_criminal_generators": 3,  # Number of criminal generators
                    "r_criminal_generators": 4,  # Radius of criminal generators
                    "max_cp": 0.5,  # Maximum criminal preference
                    "pop_count": 335000,  # Population count

                    "width": 50,
                    "height": 50}

    variable_params = None
    # variable_params = {"max_cp": np.arange(0, 1.1, 0.1)}

    batch_run = BatchRunner(Model,
                            variable_params,
                            fixed_params,
                            iterations=7,  # Number of iterations the model runs for
                            max_steps=100,
                            model_reporters={"crimerate": compute_crime_rate})
    batch_run.run_all()
    run_data = batch_run.get_model_vars_dataframe()
    print(run_data)

    run_data = run_data.sort_index()
    plt.plot(run_data.crimerate, label="Criminal Preference = " + str(fixed_params.get("max_cp")))
    plt.title("Crime-rate per 1000 Population Overtime")
    plt.ylabel("Crime Rate per 1000 population")
    plt.xlabel("Day")
    plt.legend()
    plt.show()
