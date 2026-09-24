import xpress as xp

problem = xp.problem(name="Advertising")
x1 = xp.var(name="crypto", lb=0, vartype=xp.continuous)
x2 = xp.var(name="government bonds", lb=0, vartype=xp.continuous)


Profit = 0.145*x1 + 0.053*x2

risk = 4.1*x1 + 0.9*x2 <= 5000
budget = x1 + x2 <= 4000


problem.addVariable(x1, x2)
problem.addConstraint(risk)
problem.addConstraint(budget)
problem.setObjective(Profit, sense=xp.maximize)

problem.solve()
print("crypto =", problem.getSolution(x1))
print("government bonds =", problem.getSolution(x2))
print("Profit =", problem.getObjVal())
