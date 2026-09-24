import xpress as xp

problem = xp.problem(name="Advertising")
x1 = xp.var(name="search package", lb=0, vartype=xp.continuous)
x2 = xp.var(name="social-media package", lb=0, vartype=xp.continuous)


Profit = 40*x1 + 30*x2

budget = 300*x1 + 200*x2 <= 1800
staff_time = x1 + 2*x2 <= 12

problem.addVariable(x1, x2)
problem.addConstraint(budget)
problem.addConstraint(staff_time)
problem.setObjective(Profit, sense=xp.maximize)

problem.solve()
print("search package =", problem.getSolution(x1))
print("social-media package =", problem.getSolution(x2))
print("Profit =", problem.getObjVal())
