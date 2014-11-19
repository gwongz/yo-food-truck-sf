from simpleapp import app

@app.route('/')
def home():
    return 'Ok'