import re
from typing import List


class Variable:

    def __init__(self, name, coefficient=1.0):
        self.name = name

        if coefficient == '+' or coefficient == '':
            self.coefficient = 1
        elif coefficient == '-':
            self.coefficient = -1
        else:
            self.coefficient = float(coefficient)

    def __str__(self):
        coefficient_str = str(self.coefficient).rstrip('0').rstrip('.')

        if self.coefficient == 1:
            coefficient_str = ''
        elif self.coefficient == -1:
            coefficient_str = '-'

        return coefficient_str + (self.name if self.name is not None else '')

    def get_for(self, value):
        return self.coefficient * value if self.name is not None else self.coefficient


class Equation:

    def __init__(self, variables: List[Variable], value, sign='='):
        self.variables = variables
        self.sign = sign

        try:
            self.value = int(value)
        except ValueError:
            self.value = value

    def __str__(self):
        return ' + '.join(map(str, self.variables)) + f' {self.sign} ' + str(self.value)

    def replace_variable(self, variable_name, equation):
        base_coefficient = next((v.coefficient for v in self.variables if v.name == variable_name), None)

        if base_coefficient is not None:
            for v in equation.variables:
                old_var = next((v2 for v2 in self.variables if v2.name == v.name), None)

                if old_var is not None:
                    old_var.coefficient += v.coefficient * base_coefficient
                else:
                    self.variables.append(Variable(v.name, v.coefficient * base_coefficient))

            self.variables = [v for v in self.variables if v.name != variable_name and v.coefficient != 0]


def get_equation(line):
    items = re.split('(=|<=|>=)', line)
    variables = [Variable(v[1], v[0]) for v in re.findall(r"([+-]?\d*\.?\d*)(\w*\d*)", items[0].replace(' ', ''))
                 if v[1] != '']

    return Equation(variables, items[-1].replace(' ', ''), items[1])


def bring_to_standard_form(conditions: List[Equation], constraints: List[Equation]):
    # Replace negative variables with two positive ones
    for c in constraints[:]:
        if c.sign == '<=' and c.value == 0:
            variable = c.variables[0]

            for cond in conditions:
                for v in cond.variables:
                    if v.name == variable.name:
                        cond.variables.append(Variable(variable.name + '1', v.coefficient))
                        cond.variables.append(Variable(variable.name + '2', v.coefficient * -1))

                cond.variables = [v for v in cond.variables if v.name != variable.name]

            c.variables.append(Variable(variable.name + '1', variable.coefficient))
            c.variables.append(Variable(variable.name + '2', variable.coefficient))

            constraints.append(Equation([Variable(variable.name + '1', variable.coefficient)], 0, '>='))
            constraints.append(Equation([Variable(variable.name + '2', variable.coefficient)], 0, '>='))

            constraints.remove(c)

    # Reverse >= sign
    for c in conditions[:]:
        if c.sign == '>=':
            conditions.append(Equation([Variable(v.name, v.coefficient * -1) for v in c.variables], c.value * -1, '<='))
            conditions.remove(c)

    # Transform '=' sign in two '<=' signs
    for c in conditions[:]:
        if c.sign == '=':
            conditions.append(Equation(c.variables, c.value, '<='))
            conditions.append(Equation([Variable(v.name, v.coefficient * -1) for v in c.variables], c.value * -1, '<='))
            conditions.remove(c)


def bring_to_slack_form(conditions: List[Equation]):
    basic_variables = ['α', 'β', 'γ', 'δ', 'ε', 'ζ', 'η', 'θ']
    selected_basic = []

    # Generate basic variables
    for i in range(len(conditions)):
        conditions[i].variables = [Variable(v.name, v.coefficient * -1) for v in conditions[i].variables]
        conditions[i].variables.append(Variable(None, conditions[i].value))
        conditions[i].value = basic_variables[i] if i < len(basic_variables) else 'Δ' + str(i)
        conditions[i].sign = '='

        selected_basic.append(conditions[i].value)

    return selected_basic


def pivot(func: Equation, conditions: List[Equation], basic_variables: List[str]):
    vars_with_positive_coefficient = [v for v in func.variables
                                      if v.coefficient > 0 and v.name not in basic_variables and v.name is not None]

    if len(vars_with_positive_coefficient) == 0:
        return False

    nonbasic = vars_with_positive_coefficient[0]
    conditions_max = []

    for c in conditions:
        nonbasic_coefficient = next((v.coefficient for v in c.variables if v.name == nonbasic.name), None)

        if nonbasic_coefficient is None:
            conditions_max.append([c, nonbasic_coefficient, -99999999])
        else:
            conditions_max.append([c, nonbasic_coefficient,
                                   sum([v.get_for(0) for v in c.variables]) / nonbasic_coefficient * -1])

    print("\nConstraints: ", list(map(lambda x: x[2], conditions_max)))
    # Find the tightest constraint, selected condition
    selected = [(c, co) for c, co, val in conditions_max
                if val >= 0 and val == min(map(lambda x: x[2], [cm for cm in conditions_max if cm[2] > 0]))][0]

    # Switch roles
    selected[0].variables = [Variable(v.name, v.coefficient / selected[1] * -1)
                             for v in selected[0].variables if v.name != nonbasic.name]
    selected[0].variables.append(Variable(selected[0].value, 1 / selected[1]))
    selected[0].value = nonbasic.name

    # Replace in every equation the new equation
    func.replace_variable(nonbasic.name, selected[0])

    for c in conditions:
        c.replace_variable(nonbasic.name, selected[0])

    return True


def solve_maximize(func, conditions, constraints):
    func_equation = get_equation(func)
    conditions = [get_equation(c) for c in conditions]
    constraints = [get_equation(c) for c in constraints]

    print("Start form: ")
    print(str(func_equation) + '\n' + '\n'.join(map(str, conditions)) + '\n' + ', '.join(map(str, constraints)))

    bring_to_standard_form(conditions, constraints)

    print("\nStandard form")
    print(str(func_equation) + '\n' + '\n'.join(map(str, conditions)) + '\n' + ', '.join(map(str, constraints)))

    basic_variables = bring_to_slack_form(conditions)

    print("\nSlack form")
    print(str(func_equation) + '\n' + '\n'.join(map(str, conditions)) + '\n' + ', '.join(map(str, constraints)))

    i = 1
    while pivot(func_equation, conditions, basic_variables):
        print(f"\nPivot {i}")
        print(str(func_equation) + '\n' + '\n'.join(map(str, conditions)) + '\n' + ', '.join(map(str, constraints)))
        i += 1

    print(f"\nSolution: {sum([v.get_for(0) for v in func_equation.variables])}")


if __name__ == '__main__':
    """
    solve_maximize("6a + 5b + 4c = z",
                   ["2a + b + c <= 18",
                    "a + 2b + 2c <= 30",
                    "2a + 2b + 2c <= 24"],
                   ["a >= 0", "b >= 0", "c >= 0"])
    """
    solve_maximize("2x1 + 3x2 + 3x3 = z",
                   ["x1 + x2 + x3 <= 30",
                    "2x1 + x2 + 3x3 >= 60",
                    "x1 - x2 + 2x3 = 20"],
                   ["x1 >= 0", "x2 >= 0", "x3 >= 0"])
    # http://math.uww.edu/~mcfarlat/s-prob.htm
    """
    solve_maximize("x1 + 2x2 - x3 = z",
                   ["2x1 + x2 + x3 <= 14",
                    "4x1 + 2x2 + 3x3 <= 28",
                    "2x1 + 5x2 + 5x3 <= 30"],
                   ["x1 >= 0", "x2 >= 0", "x3 >= 0"])
    """