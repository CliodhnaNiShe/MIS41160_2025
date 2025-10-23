import xpress as xp



# Define sets
team = ["a", "b", "c", "d", "e", "f", "g", "h", "i", "j"]
female = ["a", "b", "c", "d", "e"]
male = ["f", "g", "h", "i", "j"]
stu = ["a", "b", "c", "j"]
academ = ["d", "g", "h", "i"]
admin = ["e", "f"]


# Create problem
p = xp.problem()

# Define decision variables and add them to the problem
x = {i: xp.var(vartype=xp.binary) for i in team}
p.addVariable(x[i] for i in team)  # Adding the decision variables to the problem


OF = xp.Sum(x[i] for i in team)
# Objective function: Minimize the number of selected team members
p.setObjective(OF, sense=xp.minimize)
#
const_female= xp.Sum(x[i] for i in female)
const_male = xp.Sum(x[i] for i in male)
const_stu = xp.Sum(x[i] for i in stu)
const_academ = xp.Sum(x[i] for i in academ)
const_admin = xp.Sum(x[i] for i in admin)



# # Constraints
p.addConstraint(const_female >= 1)
p.addConstraint(const_male >= 1)
p.addConstraint(const_stu >= 1)
p.addConstraint(const_academ >= 1)
p.addConstraint(const_admin >= 1)
#
# # Solve the problem
p.solve()
#
print(f"Best min objective: {p.getObjVal()}")

# Output the selected team members
print("Team members are:")
for i in team:
    if p.getSolution(x[i]) == 1:
        print(i)

# Export the problem to file

p.write("team_problem.lp")
