# when you update the packages: conda env export > environment.yml
import esper
from time import sleep
import os

import Components as c
import Processors
import websocket


def main() -> None:
    websocket.goFast.run(host='0.0.0.0', port=os.environ.get('PORT'))  # set your local dev environment var PORT


if __name__ == "__main__":
    main()

    # performance note: could run 100 entities 10,000 times in 1 second. Ran 1,000,000 ents 1 time in 2 seconds
    # on MovementProcessor only, before numba integration
