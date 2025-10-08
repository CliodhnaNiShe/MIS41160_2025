import xpress as xp
xp.init('C:/xpressmp/bin/xpauth.xpr')

#Implementation of the Pottery problem: two decision variables, two constraints

problem = xp.problem(name="Diet Mix Problem") # Create and name the Problem

#Step 1: declare the decision variables
x_1 = xp.var(name = 'Dry Cereal', lb = 0, vartype = xp.continuous)
x_2 = xp.var(name = 'Oat Bran', lb = 0, vartype = xp.continuous)
x_3 = xp.var(name = 'Milk', lb = 0, vartype = xp.continuous)
x_4 = xp.var(name = 'Toast', lb = 0, vartype = xp.continuous)



#############################LP Model#######################
Cost = 0.22 * x_1 + 0.12 * x_2 + 0.16 * x_3 + 0.07 * x_4       #! Objectivefunction
Calories = 110 * x_1 + 90 * x_2 + 100 * x_3 + 65 * x_4 >= 420
Iron = 12 * x_1 + 0 * x_2 + 0 * x_3 + 1 * x_4 >= 5
Calcium = 8 * x_1 + 270 * x_2 + 250 * x_3 + 26 * x_4 >= 400
Fibre = 0 * x_1 + 5 * x_2 + 0 * x_3 + 2 * x_4 >= 12
###################################################################


problem.addVariable(x_1)
problem.addVariable(x_2)
problem.addVariable(x_3)
problem.addVariable(x_4)
problem.addConstraint(Calories)
problem.addConstraint(Iron)
problem.addConstraint(Calcium)
problem.addConstraint(Fibre)
problem.setObjective(Cost, sense=xp.minimize) # Add the objective function to the problem


problem.solve()  # Solve the problem

solution = problem.getSolution()  # Get the solution values
objective_value = problem.getObjVal()

print("\n")
print("Have {} Dry Cereal".format(solution[0]))
print("Have {} Oat Bran".format(solution[1]))
print("Have {} Milk".format(solution[2]))
print("Have {} Toast".format(solution[3]))
print("Minimum cost is €{} ".format(objective_value))


