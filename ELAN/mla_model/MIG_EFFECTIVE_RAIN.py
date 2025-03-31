# pylint: skip-file

"""
The aim of this code is to produce the effective rain by analysing the rain type (mall, medium or big) and remving the initial losses according to the case.
This code will also count the number of rain events present during the study period according to the dry period stablished for two rains to be separated.

Author: Miguel José ÁLVAREZ VELÁSQUEZ
Created on: 30/04/2023
"""

from datetime import timedelta

from . import MIG_TOOLBOX


def EFFECTIVE_RAIN(
    rain_time, intensity_period, time_between_rains, small_IL, medium_IL, big_IL, small_rain_limit, big_rain_limit
):
    # It starts by initializing empty lists that will be used as temporary lists or final results.

    temporary_intensity_list = []  # Initialization of a temporary list of intensity that will be used then erased
    effective_intensity = []  # This list will be filled with the effective intensity

    # The effective intensity is evaluated for every rain event to corretly take into account the initial losses.
    # It checks every rain measure one at a time, except the last one.
    for i in range(len(rain_time) - 1):
        temporary_intensity_list.append(intensity_period[i])

        # Lets keep in mind that the rain_time list IS NOT continuous. When there is no rain it DOES NOT store data.
        # The next line will check how long was the dry period between two measures.
        # If it is larger than the indicated value, then these are considered to be two different rain events.
        if rain_time[i + 1] - rain_time[i] > timedelta(seconds=time_between_rains):
            cumulative_rainfall = sum(temporary_intensity_list)

            # ----------SMALL RAINS-------------
            if cumulative_rainfall <= small_rain_limit:
                effective_intensity_list = MIG_TOOLBOX.REMOVE_INITIAL_LOSSES(temporary_intensity_list, small_IL)

            # ----------MEDIUM RAINS------------
            if cumulative_rainfall > small_rain_limit and cumulative_rainfall < big_rain_limit:
                effective_intensity_list = MIG_TOOLBOX.REMOVE_INITIAL_LOSSES(temporary_intensity_list, medium_IL)

            # ----------BIG RAINS---------------
            if cumulative_rainfall >= big_rain_limit:
                effective_intensity_list = MIG_TOOLBOX.REMOVE_INITIAL_LOSSES(temporary_intensity_list, big_IL)

            effective_intensity = effective_intensity + effective_intensity_list

            # We clear the temporary time list and the temporary rain type list
            temporary_intensity_list = []

        # The last time period is checked
        if i + 1 == (len(rain_time) - 1):
            # The list is kept and the last element is added.
            temporary_intensity_list.append(intensity_period[i + 1])

            # Since this is the end of the list, everything that is currently in the temporary intensity list is considered
            # to be part of a same rain event. There is no need to check for dry periods.

            cumulative_rainfall = sum(temporary_intensity_list)

            # The process is done for both permeable and impermeable surfaces

            # ----------SMALL RAINS-------------
            if cumulative_rainfall <= small_rain_limit:
                effective_intensity_list = MIG_TOOLBOX.REMOVE_INITIAL_LOSSES(temporary_intensity_list, small_IL)

            # ----------MEDIUM RAINS------------
            if cumulative_rainfall > small_rain_limit and cumulative_rainfall < big_rain_limit:
                effective_intensity_list = MIG_TOOLBOX.REMOVE_INITIAL_LOSSES(temporary_intensity_list, medium_IL)

            # ----------BIG RAINS---------------
            if cumulative_rainfall >= big_rain_limit:
                effective_intensity_list = MIG_TOOLBOX.REMOVE_INITIAL_LOSSES(temporary_intensity_list, big_IL)

            effective_intensity = effective_intensity + effective_intensity_list

            # effective_intensity = The effective intensiry of the rain after removing the initial losses. List in mm/min.

    return effective_intensity
