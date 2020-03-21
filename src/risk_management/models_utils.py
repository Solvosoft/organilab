
class PriorityCalculator:

    def operate(self, value):
        dev = False
        right_value = 0 if self.right_value is None else self.right_value
        if self.operation == '<':
            dev = self.left_value < value
        elif self.operation == '<=':
            dev = self.left_value <= value
        elif self.operation == '=':
            dev = self.left_value == value
        elif self.operation == '>':
            dev = self.left_value > value
        elif self.operation == '>=':
            dev = self.left_value >= value
        elif self.operation == '!':
            dev = self.left_value != value
        elif self.operation == '<>':
            dev = self.left_value < value > right_value
        elif self.operation == '=<>=':
            dev = self.left_value <= value >= right_value
        elif self.operation == '=<>=':
            dev = self.left_value <= value >= right_value
        elif self.operation == '<>=':
            dev = self.left_value < value >= right_value
        elif self.operation == '=<>':
            dev = self.left_value <= value > right_value
        elif self.operation == '<<':
            dev = self.left_value < value < right_value
        elif self.operation == '=<<=':
            dev = self.left_value <= value <= right_value
        elif self.operation == '=<<=':
            dev = self.left_value <= value <= right_value
        elif self.operation == '<<=':
            dev = self.left_value < value <= right_value
        elif self.operation == '=<<':
            dev = self.left_value <= value < right_value
        return dev