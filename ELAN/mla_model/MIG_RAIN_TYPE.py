# pylint: skip-file

"""
The aim of this code is to produce the a rain type list by analysing the cummulated rainfall of an event (mall, medium or big).
This code will also count the number of rain events present during the study period according to the dry period stablished for two rains to be separated.

Author: Miguel José ÁLVAREZ VELÁSQUEZ
Created on: 30/04/2023
"""

from datetime import timedelta


def RAIN_TYPE(rain_time, intensity_period, time_between_rains, small_rain_limit, big_rain_limit):
    # It starts by initializing empty lists that will be used as temporary lists or final results.

    temporary_intensity_list = []  # Initialization of a temporary list of intensity that will be used then erased
    rain_type = []  # This list will be filled with the type of rain (small, medium or big)
    num_rains = 0  # Counter of the number of rains

    # It checks every rain measure one at a time, except the last one.
    for i in range(len(rain_time) - 1):
        temporary_intensity_list.append(intensity_period[i])

        # Lets keep in mind that the rain_time list IS NOT continuous. When there is no rain it DOES NOT store data.
        # The next line will check how long was the dry period between two measures.
        # If it is larger than the indicated value, then these are considered to be two different rain events.
        if rain_time[i + 1] - rain_time[i] > timedelta(seconds=time_between_rains):
            num_rains = num_rains + 1  # Counts the number of rains
            cumulative_rainfall = sum(temporary_intensity_list)

            # Depending on the accumulated rain, a list of the same lenght as the rain event will be created with the labels 'small', 'medium' or 'big'.

            # ----------SMALL RAINS-------------
            if cumulative_rainfall <= small_rain_limit:
                rain_type_list = ["small" for j in range(len(temporary_intensity_list))]

            # ----------MEDIUM RAINS------------
            if cumulative_rainfall > small_rain_limit and cumulative_rainfall < big_rain_limit:
                rain_type_list = ["medium" for j in range(len(temporary_intensity_list))]

            # ----------BIG RAINS---------------
            if cumulative_rainfall >= big_rain_limit:
                rain_type_list = ["big" for j in range(len(temporary_intensity_list))]

            rain_type = rain_type + rain_type_list

            # We clear the temporary time list and the temporary rain type list
            temporary_intensity_list = []
            rain_type_list = []

        # The last time period is checked
        if i + 1 == (len(rain_time) - 1):
            # The list is kept and the last element is added.
            temporary_intensity_list.append(intensity_period[i + 1])

            # Since this is the end of the list, everything that is currently in the temporary intensity list is considered
            # to be part of a same rain event. There is no need to check for dry periods.

            num_rains = num_rains + 1  # Adds the last event as a last rain
            cumulative_rainfall = sum(temporary_intensity_list)

            # Depending on the accumulated rain, a list of the same lenght as the rain event will be created with the labels 'small', 'medium' or 'big'.

            # ----------SMALL RAINS-------------
            if cumulative_rainfall <= small_rain_limit:
                rain_type_list = ["small" for j in range(len(temporary_intensity_list))]

            # ----------MEDIUM RAINS------------
            if cumulative_rainfall > small_rain_limit and cumulative_rainfall < big_rain_limit:
                rain_type_list = ["medium" for j in range(len(temporary_intensity_list))]

            # ----------BIG RAINS---------------
            if cumulative_rainfall >= big_rain_limit:
                rain_type_list = ["big" for j in range(len(temporary_intensity_list))]

            rain_type = rain_type + rain_type_list

    return rain_type, num_rains
