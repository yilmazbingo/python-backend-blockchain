while True:
    name=input("enter your name")
    f = open("deneme.txt", mode="w")
    f.write(name)
    f.close()
    if name=="yilmaz":
        break


