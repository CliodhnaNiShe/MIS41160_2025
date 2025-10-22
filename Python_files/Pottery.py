import xpress as xp
##xp.init('C:/xpressmp/bin/xpauth.xpr') #Path to license file 

#Implementation of the Pottery problem: two decision variables, two constraints

problem = xp.problem(name="Pottery Problem") # Create and name the Problem

#Step 1: declare the decision variables
x_b = xp.var(name = 'bowl_quantity', lb = 0, vartype = xp.continuous)
x_m = xp.var(name = 'mug_quantity', lb = 0, vartype = xp.continuous)


#############################LP Model#######################
Profit = 40*x_b + 50*x_m  #Objective function
labour_constraint = 1*x_b + 2*x_m <= 40 # hours of labour availability
clay_constraint = 4*x_b + 3*x_m <= 120 # lbs of clay availability
###################################################################


problem.addVariable(x_b) # Add the bowl variable to the problem
problem.addVariable(x_m) # Add the mug variable to the problem
problem.addConstraint(labour_constraint) # Add the labour constraint to the problem
problem.addConstraint(clay_constraint) # Add the clay constraint to the problem
problem.setObjective(Profit, sense=xp.maximize) # Add the objective function to the problem


problem.solve()  # Solve the problem

solution = problem.getSolution()  # Get the solution values
objective_value = problem.getObjVal()

print("\n")
print("Make {} bowl(s)".format(solution[0]))
print("Make {} mug(s)".format(solution[1]))
print("Best profit is €{} ".format(objective_value))

