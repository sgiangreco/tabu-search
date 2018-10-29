import random

class SATInstance:
    def parse_and_add_clause(self, line):
        clause = []
        for literal in line.split():
            negated = 1 if literal.startswith('-') else 0
            variable = literal[negated:] # slices off negative sign of literal
            encoded_literal = int(variable) << 1 | negated # multiplies value by 2 and adds 1 if negative
            clause.append(encoded_literal) # adds integer to current clause
        self.clauses.append(tuple(set(clause))) # adds clause to list of clauses for instance

    def __init__(self, tabuMax):
        self.assignment = []
        self.clauses = []
        self.tabu = []
        self.tabuMax = tabuMax

    def from_file(self, filename): # using self instead of cls
        with open(filename) as f:
            for line in f:
                if line.startswith('p'):
                    self.parse_problem_line_and_set_variable_length(line)
                elif len(line) > 0 and not line.startswith('c') and not line.startswith('p'):
                    self.parse_and_add_clause(line[:len(line)-2]) # 0 marks end of line
        return

    def literal_to_string(self, literal):
        s = '-' if literal & 1 else ''
        return s + self.assignment[literal >> 1]

    def clause_to_string(self, clause):
        return ' '.join(self.literal_to_string(l) for l in clause)

    # Pre: assignment is a binary array with each element corresponding to the value of its respective index
    #      self.clauses is list of tuples, each of which contains the encoding of its literals
    # Post: Returns positive integer
    # Desc: Takes in an assignment of variables and returns number of clauses it satisfies.
    #       If no assignment is given, will evaluate current assignment
    def count_satisfied_clauses(self, assignment=None):
        if assignment is None:
            assignment = self.assignment
        totalSatisfied = 0
        for clause in self.clauses:
            foundTrue = 0
            i = 0
            while not foundTrue and i < len(clause):
                foundTrue = (clause[i] & 1) ^ assignment[(clause[i] >> 1) - 1]
                i = i + 1
            totalSatisfied = totalSatisfied + foundTrue
        return totalSatisfied

    # Pre:  variables list is of desired length
    #       random module is installed
    # Post: Returns list of binary values
    # Desc: Creates a list of random binary values corresponding to assignments of variables
    def create_random_assignment(self):
        assignment = []
        for i in self.assignment:
            assignment.append(random.randrange(2))
        self.assignment = assignment
        return

    # Pre:  line is problem line of DIMACS graph format
    #       line contains 4 elements
    # Post: Changes variables list to empty of certain size
    # Desc: Parses the problem line of the input file and sets length of variable list
    def parse_problem_line_and_set_variable_length(self, line):
        self.assignment = [None] * int(line.split()[2])
        return

    # Pre:  None
    # Post: Returns 1-exchange neighbor of assignment
    # Desc: Flips the bit on the variable in the given index and returns altered assignment
    def find_neighbor(self, index, assignment=None):
        if assignment is None:
            assignment = self.assignment
        newAssignment = assignment.copy()
        newAssignment[index] = (newAssignment[index] + 1) % 2
        return newAssignment

    # Pre:  There exists an assignment of variables
    #       The clauses have been compiled
    # Post: 
    # Desc: Changes assignment;
    #       Mathematical description:
    #       Let x be a vector of length n where n is the number of variables.
    #       Let each x_i in x be the 1-exchange neighbor of the current assignment with the i-th variable.
    #       Let y be a vector of n elements wherein each y_i is the number of clauses satisfied by the assignment x_i minus the number of clauses satisfied by the current assignment (so it includes negatives where step worsens).
    #       Let y' be a vector of n elements wherein each y'_i is y_i + abs(infimum(y)) if infimum(y) is non-positive and y' = y if infimum(y) is positive.
    #       Then the probability of the assignment x_i being chosen is y'_i/m where m is sum of all elements of y'
    def find_next_assignment(self):
        sat = self.count_satisfied_clauses(self.assignment)
        worstChange = 0
        clauseImprov = []
        #print('--- Searching for next assignment ---')
        for varIndex in range(len(self.assignment)):
            clauseImprov.append(self.count_satisfied_clauses(self.find_neighbor(varIndex)) - sat)
            if clauseImprov[varIndex] < worstChange:
                worstChange = clauseImprov[varIndex]
        adjImprov = [x - worstChange + 1 for x in clauseImprov]
        #print('Clause improvement list: ', clauseImprov)
        #print('Adjusted clause improvement list: ', adjImprov)
        chosenNeighborIndex = self.calc_prob_assignment(adjImprov)
        #print('Chosen neighbor index: ', chosenNeighborIndex, '\n')
        self.assignment = self.find_neighbor(chosenNeighborIndex)
        return clauseImprov[chosenNeighborIndex]

    # Pre:  adjImprov is list of positive integers
    # Post: Returns non-negative integer
    # Desc: Calculates a random number from 1 to sum of elements of adjImprov (inclusive) and uses that to find where in the adjImprov list the sum of elements exceeds the random number
    def calc_prob_assignment(self, adjImprov):
        adjTotal = sum(adjImprov)
        selector = random.randrange(adjTotal) + 1
        #print('total: ', adjTotal)
        #print('selector: ', selector)
        currentSum = 0
        #make this less confusing
        i = -1
        while currentSum < selector and i < len(adjImprov):
            i = i + 1
            currentSum = currentSum + adjImprov[i]
            #print('for i =', i, 'sum is ', currentSum)
        return i

    def find_next_assignment_tabu(self):
        scores = self.get_scores()
        best = min(scores)
        currentPos = scores.index(best)
        while currentPos in self.tabu:
            if len(scores[:currentPos]) is len(scores) or scores[currentPos+1:].count(best) is 0:
                #include error catching for best greater than num of clauses
                best = best + 1
                while best not in scores:
                    best = best + 1
                currentPos = scores.index(best)
            else:
                currentPos = len(scores[:currentPos]) + scores[currentPos+1:].index(best)
            self.manage_tabu(currentPos) #extract from this method to improve generality
        return self.find_neighbor(currentPos)

    # Pre:  All clauses have been recorded in member list
    #       Assignment exists as member if no argument passed
    # Post: A list is returned
    # Desc: A list wherein each element is the number of clauses unsatisfied by the 1-exchange neighbor of the corresponding variable is created and returned
    def get_scores(self, assignment=None):
        if assignment is None:
            assignment = self.assignment.copy()
        scores = []
        numClauses = len(self.clauses)
        for i in range(len(assignment)):
            scores.append(numClauses - self.count_satisfied_clauses(self.find_neighbor(i)))
        return scores

    # Pre:  A new assignment not in the tabu list is to be entered
    #       The member for tabu length is a positive integer
    # Post: The tabu list member is changed
    # Desc: If the tabu list is at maximum size, then the first member is removed.
    #       An integer corresponding to the index of the variable in the corresponding 1-exchange neighbor to be added to the tabu is appended to the member tabu list
    def manage_tabu(self, varIndex):
        if len(self.tabu) is self.tabuMax:
            self.tabu.remove(0)
        self.tabu.append(varIndex)
        return
