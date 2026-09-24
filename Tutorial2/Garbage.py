import xpress as xp

problem = xp.problem(name="Incineration")

# Decision variables
stacks_waste = xp.var(name="stacks_waste",lb=0,vartype=xp.continuous)

new_plant_waste = xp.var(name="new_plant_waste",lb=0,vartype=xp.continuous)

# Waste sent elsewhere
external_waste = 1000 - stacks_waste - new_plant_waste

# Objective function
total_cost = (
    4500 * stacks_waste
    + 6000 * new_plant_waste
    + 14000 * external_waste
)

# Constraints
hydrocarbon_limit = (2 * stacks_waste + new_plant_waste <= 350)

particulate_limit = (6 * stacks_waste + 2 * new_plant_waste <= 900)

stacks_capacity = (stacks_waste <= 200)

new_plant_capacity = (new_plant_waste <= 400)

available_waste = (stacks_waste + new_plant_waste <= 1000)

# Add variables and constraints to the problem
problem.addVariable(stacks_waste, new_plant_waste)

problem.addConstraint(hydrocarbon_limit)
problem.addConstraint(particulate_limit)
problem.addConstraint(stacks_capacity)
problem.addConstraint(new_plant_capacity)
problem.addConstraint(available_waste)

# Set and solve the objective
problem.setObjective(total_cost, sense=xp.minimize)

problem.solve()

# Display the solution
stacks_solution = problem.getSolution(stacks_waste)
new_plant_solution = problem.getSolution(new_plant_waste)
external_solution = 1000 - stacks_solution - new_plant_solution

print("Waste processed at the Stacks =", stacks_solution)
print("Waste processed at the new plant =", new_plant_solution)
print("Waste sent elsewhere =", external_solution)
print("Total cost =", problem.getObjVal())
