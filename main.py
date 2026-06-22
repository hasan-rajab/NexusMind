import sys, os
sys.path.insert(0, os.path.dirname(__file__))

import uvicorn
from config import HOST, PORT

if __name__ == "__main__":
    uvicorn.run("backend.app:app", host=HOST, port=PORT, reload=False)
