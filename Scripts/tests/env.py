import sys
import os

# Used as import in the testing files, to create the proper environment for them (python quirk)

# append module root directory to sys.path
sys.path.append(
    os.path.dirname(
        os.path.dirname(
            os.path.abspath(__file__)
        )
    )
)