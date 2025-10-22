import xpress as xp

xp.init('C:/xpressmp/bin/xpauth.xpr')

problem = xp.problem(name="Pig Diet Problem")  # Create and name the Problem

# Set up the data for the problem

feed_names = [
	"corn",
	"barley",
	"hay",
]  # Create a list of feed name strings
nutrient_names = [
	"carbohydrates",
	"protein",
	"vitamins",
]  # Create a list of nutient name strings

feed_costs = {
	"corn": 0.84,
	"barley": 0.72,
	"hay": 0.82,
}  # Create a dictionary of the feed costs

carbohydrate_quantities = {
	"corn": 90,
	"barley": 20,
	"hay": 40,
}  # Create a dictionary of the carbohydrate quantities
protein_quantities = {
	"corn": 30,
	"barley": 80,
	"hay": 60,
}  # Create a dictionary of the protein quantities
vitamin_quantities = {
	"corn": 10,
	"barley": 20,
	"hay": 60,
}  # Create a dictionary of the vitamin quantities

nutrient_requirements = {
	"carbohydrates": 200,
	"protein": 180,
	"vitamins": 150,
}  # Create a dictionary of the required nutrients

nutrient_quantities = {
	"carbohydrates": carbohydrate_quantities,
	"protein": protein_quantities,
	"vitamins": vitamin_quantities,
}  # Create an embedded dictionary of the nutrient quantities

# Construct the problem

variables = [
	xp.var(name=feed_name, lb=0, vartype=xp.continuous) for feed_name in feed_names
]  # Use the strings to create a list of named variables
variable_dict = {
	feed_name: variable for (feed_name, variable) in zip(feed_names, variables)
}  # Create a dictionary of variables for easy access

feed_cost = sum([
	variable_dict[feed_name] * feed_costs[feed_name] for feed_name in feed_names
])  # Sum the costs of the feeds multiplied by the quanitites purchased

constraint_dict = {}  # Make an empty dictionary to contain the constraints for the

for nutrient_name in nutrient_names:  # For each of the nutrients
	nutrient_requirement = nutrient_requirements[nutrient_name]  # Get the required nutrient amount
	nutrient_quantity = nutrient_quantities[nutrient_name]  # Get the amount in each feed
	nutrient_sum = sum([
		variable_dict[feed_name] * nutrient_quantity[feed_name] for feed_name in feed_names
	])  # Compute the sum of the feed quantities times the nutrients in the feed
	nutrient_constraint = nutrient_sum >= nutrient_requirement  # Construct the nutrient constraint
	constraint_dict[nutrient_name] = nutrient_constraint  # Add the nutrient constraint to the dictionary

problem.addVariable(variable_dict)  # Add the variables to the problem
problem.addConstraint(constraint_dict)  # Add the constraints to the problem
problem.setObjective(feed_cost, sense=xp.minimize)  # Add the objective function to the problem

problem.solve()  # Solve the problem

solution_values = problem.getSolution()  # Get the solution values

print("\n\n\n")  # Print some blank lines
print("Objective function value: ", problem.getObjVal())  # Print the optimal objective function value
for variable_name, solution_value in zip(variable_dict.keys(), solution_values):
	print(variable_name + " quantity: ", solution_value)  # Print the value of the variable

	solution_values = []
	# Build an empty list for the solution values
	slack_values = []
	# Build an empty list for the slack values
	dual_values = []
	# Build an empty list for the dual values
	reduced_cost_values = []
	# Build an empty list for the reduced cost

	problem.getlpsol(
		solution_values,
		slack_values,
		dual_values,
		reduced_cost_values
	)
# Retrieve the solution, slack, dual and costs values from the solved problem

# print(f'slack values {slack_values}')
print(f'dual values {dual_values}')
# print(f'reduced cost values {reduced_cost_values}')

constraint_lower_sensitivity_values = []
# Build empty list for the constraint lower sensitivity values
constraint_upper_sensitivity_values = []
# Build empty list for the constraint upper sensitivity values

problem.rhssa(
	list(constraint_dict.values()),
	constraint_lower_sensitivity_values,
	constraint_upper_sensitivity_values,
) # Retrieve the sensitivity range values for the constraint RHGS

print(f'upper sensitivity {constraint_upper_sensitivity_values}')
print(f'lower sensitivity {constraint_lower_sensitivity_values}')
