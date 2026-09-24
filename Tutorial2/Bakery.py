import xpress as xp

problem = xp.problem(name="Bakery")
scones = xp.var(name="scones", lb=0, vartype=xp.continuous)
muffins = xp.var(name="muffins", lb=0, vartype=xp.continuous)


Profit = 30*scones + 25*muffins

flour = 2*scones + muffins <= 40
prep_time = scones + 2*muffins <= 50

problem.addVariable(scones, muffins)
problem.addConstraint(prep_time)
problem.addConstraint(flour)
problem.setObjective(Profit, sense=xp.maximize)

problem.solve()
print("scones =", problem.getSolution(scones))
print("muffins =", problem.getSolution(muffins))
print("contribution =", problem.getObjVal())
