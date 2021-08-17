# when you update the packages: conda env export > environment.yml
# check package disk usage in heroku: du -BM -s ./.conda/pkgs/*  | sort -n
import os

import websocket


def main() -> None:
    websocket.goFast.run(host='0.0.0.0', port=int(os.environ.get('PORT')), workers=1, debug=False)
    # database sync error with multiple workers


if __name__ == "__main__":
    main()

    # performance note: could run 100 entities 10,000 times in 1 second. Ran 1,000,000 ents 1 time in 2 seconds
    # on MovementProcessor only, before numba integration
