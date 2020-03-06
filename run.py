from app import app
from app.align_module import models

if __name__ == "__main__":
    models.init()
    app.run(host='localhost', port=9444)
