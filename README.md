#Running the Model

In the sections below, the user can find instructions on how to run the project
for a single iteration, how to batch-run the project, and how to change the 
parameters of the model in each of these scenarios. 

##Installation

- Make sure you have and are using Python version 3 or above to run this project. 
- In your directory, travel to the project folder _marta_melerogazo_PRJ21_ and  
using the command line run the command: `pip install -r  requirements.txt `

##Single Run

In order to run a single completion of the model, follow the procedure below: 
1. In your directory, travel to the project folder _violent_crime_at_night_ 
using the command line. 
2. From the command line, run the command: ``python server.py ``. <br />
This should open up a window on your default browser named 
_"Violent Crime when Walking Home Alone at Night"_ with the 
visualisation of the model.
3. To run the simulation, look at the buttons in the upper right corner of the 
screen. Press _**Start**_ to run the simulation until it finishes, or _**Step**_ 
to advance the model a single step.

###Changing the Parameters

In order to change the parameters used during the simulation: 
1. Alter the values of the parameters by adjusting the sliders on the 
left side of the window. 
2. Press _**Reset**_ on the upper right corner of the screen to refresh the model
to portray the newly set parameters. 
3. Re-run the model by pressing either _**Start**_ or _**Step**_.

##Batch Run

In order to run several completions of the model, follow the procedure below: 
1. In your directory, travel to the project folder _violent_crime_at_night_ using
the command line. 
2. From the command line, run the command: ``python run.py ``. <br />
This will open up a graph, which shows the weekly crime-rate given different
upper bounds on the offender's criminal preference.

###Varying the Graph Displayed
There is an option of two implemented graphs which can be displayed 
using batch run. One will plot crime-rates given the different upper bounds on 
the criminal preference of offenders using a bar chart. The other will plot a 
line graph of the crime-rate over time.These graphs are numbered 1 and 2. 

###Changing the Parameters

In order to change the parameters used during the several runs of the model: 
1. Open an editor and look at `run.py`.
2. Change the value of the variable `graph` in line 6 to either 1 or 2 depending on 
the graph to be shown. 
3. Change the values of the `fixed_parameters`, the `variable_parameters`, or 
the number of iterations the model completes, for the graph which is to be portrayed.  
4. Type ``python run.py `` in the command line again to run the model with 
the newly set parameters. 




