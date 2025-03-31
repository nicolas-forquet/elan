# pylint: skip-file

"""
The aim of this code is to produce any flow by analysing the rain type (mall, medium or big) and using the according runoff coefficients.

Author: Miguel José ÁLVAREZ VELÁSQUEZ
Created on: 30/04/2023
"""

from . import MIG_TOOLBOX


def GENERIC_FLOW(rain_type, effective_intensity, surface, small_RC, medium_RC, big_RC):
    # It starts by initializing empty list that will be used as temporary lists or final results.

    flow = []  # This list will be filled with the generated flow.

    # The flow is evaluated for every effective rain intensity. It checks every one at a time.
    # It uses the rational method at every time step and changes the parameters depending on the rain type.
    for i in range(len(rain_type)):
        # ----------SMALL RAINS-------------
        if rain_type[i] == "small":
            flow.append(MIG_TOOLBOX.RATIONAL_METHOD(effective_intensity[i], surface, small_RC))

        # ----------MEDIUM RAINS------------
        if rain_type[i] == "medium":
            flow.append(MIG_TOOLBOX.RATIONAL_METHOD(effective_intensity[i], surface, medium_RC))

        # ----------BIG RAINS---------------
        if rain_type[i] == "big":
            flow.append(MIG_TOOLBOX.RATIONAL_METHOD(effective_intensity[i], surface, big_RC))

    return flow
