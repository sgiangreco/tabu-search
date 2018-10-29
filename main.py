import numpy.random
from solver import SATInstance

def main(inputFileName, maxSteps, tabuMax):
    instance = SATInstance(tabuMax)
    instance.from_file(inputFileName) # have some way to make sure is text file
    instance.create_random_assignment()
    clauseTotal = len(instance.clauses)
    unsat = clauseTotal - instance.count_satisfied_clauses()
    minUnsat = unsat
    bestAssignment = instance.assignment.copy()
    step = 1
    while minUnsat > 0 and step < maxSteps:
        instance.assignment = instance.find_next_assignment_tabu()
        unsat = clauseTotal - instance.count_satisfied_clauses()
        if unsat < minUnsat:
            minUnsat = unsat
            bestAssignment = instance.assignment.copy()
        step = step + 1
    print(minUnsat, 'clauses unsatisfied with assignment', bestAssignment, 'in', step, 'moves')
    return
