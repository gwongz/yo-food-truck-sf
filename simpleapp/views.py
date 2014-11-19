from simpleapp import simpleapp

@simpleapp.route('/')
def home():
    return 'Ok'