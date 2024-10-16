class Logger:
    def log(*args):
        with open("logs.txt", 'a') as fp:
            fp.write(str(args)+"\n")
        return