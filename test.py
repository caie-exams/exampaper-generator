class Person:
    def method(self):
        for i in range(0, 10):
            yield i


person = Person()
list = []
list.append(1, 2, 4)
print(list)
