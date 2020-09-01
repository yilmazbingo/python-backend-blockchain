# we inherit from here so we do not repeat ourselves
class Printable():
    def __str__(self):
        return str(self.__dict__)