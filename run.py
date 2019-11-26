from app import app
from app.align_module import models

if __name__ == "__main__":
    models.init()
    app.run(host='192.168.15.11', port=9444)
