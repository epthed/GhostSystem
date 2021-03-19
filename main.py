import esper
from time import sleep
import os

import Components as c
import Processors
import websocket


def main() -> None:
    websocket.goFast.run(port=os.environ.get('PORT'))


if __name__ == "__main__":
    main()

    # performance note: could run 100 entities 10,000 times in 1 second. Ran 1,000,000 ents 1 time in 2 seconds
    # on MovementProcessor only
