class Task:
    def __init__(self, name, duration = 0):
        self.name = name
        self.duration = duration # s

    def __str__(self):
        return f"Task: {self.name}, Duration: {self.duration} s"
