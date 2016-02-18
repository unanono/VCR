

class a(object):
    b = 10
    def c(self):
        classV = self.__class__
        classV.b = 13

    def p(self):
        classV = self.__class__
        print classV.b

d= a()
d.c()
d.p()

f=a()
f.p()

