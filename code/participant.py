class Operator:
    def __init__(self, name, gender, height, weight):
        self.name = name
        self.gender = gender
        self.height = height # cm
        self.weight = weight # kg

    def __str__(self):
        return f"Operator: {self.name}, Gender: {self.gender}, Height: {self.height} cm, Weight: {self.weight} kg"
