import xpress as xp

xp.init('C:/xpressmp/bin/xpauth.xpr')

problem = xp.problem(name="Pig Diet Problem") # Create and name the Problem

x_corn = xp.var(name="corn_quantity", lb=0, vartype=xp.continuous) # Create corn variable
x_barley = xp.var(name="barley_quantity", lb=0, vartype=xp.continuous) # Create barley variable
x_hay = xp.var(name="hay_quantity", lb=0, vartype=xp.continuous) # Create hay variable

feed_cost = 0.84 * x_corn + 0.72 * x_barley + 0.82 * x_hay # Construct the objective function

carbohydrate_quantity = 90 * x_corn + 20 * x_barley + 40 * x_hay # Compute the carbohydrate quantity
protein_quantity = 30 * x_corn + 80 * x_barley + 60 * x_hay # Compute the protein quantity
vitamin_quantity = 10 * x_corn + 20 * x_barley + 60 * x_hay # Compute the vitamin quantity

carbohydrate_constraint = carbohydrate_quantity >= 200 # Construct the carbohydrate constraint
protein_constraint = protein_quantity >= 180 # Construct the protein constraint
vitamin_constraint = vitamin_quantity >= 150 # Construct the vitamin constraint

problem.addVariable(x_corn) # Add the corn variable to the problem
problem.addVariable(x_barley) # Add the barley variable to the problem
problem.addVariable(x_hay) # Add the hay variable to the problem
problem.addConstraint(carbohydrate_constraint) # Add the carbohydrate constraint to the problem
problem.addConstraint(protein_constraint) # Add the protein constraint to the problem
problem.addConstraint(vitamin_constraint) # Add the vitamin constraint to the problem
problem.setObjective(feed_cost, sense=xp.minimize) # Add the objective function to the problem

problem.solve() # Solve the problem

solution_values = problem.getSolution() # Get the solution values

print("\n\n")
print("Objective function value: ", problem.getObjVal()) # Print the optimal objective function value
print("Corn quantity: ", solution_values[0]) # Print the value of the corn variable
print("Barley quantity: ", solution_values[1]) # Print the value of the barley variable
print("Hay quantity: ", solution_values[2]) # Print the value of the hay variable
