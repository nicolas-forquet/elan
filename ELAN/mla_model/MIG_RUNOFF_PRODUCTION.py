# pylint: skip-file

"""
The aim of this code is to centralise the production of all runoff water that ends up in the unitary sewage system.
NO INFILTRATION WATER IS CONSIDERED IN THIS CODE

Author: Miguel José ÁLVAREZ VELÁSQUEZ
Created on: 26/04/2023
"""

from . import MIG_EFFECTIVE_RAIN, MIG_GENERIC_FLOW, MIG_RAIN_TYPE, MIG_TOOLBOX


def RUNOFF_PRODUCTION(
    p_imp_surface,
    imp_surface_before,
    p_per_surface,
    per_surface,
    imp_surface_after,
    IL,
    Hinf,
    Hsoil,
    FIMP,
    FPER,
    rain_time,
    intensity_period,
    full_study_period,
    time_between_rains,
):
    # Defines the limists for small and big rains
    small_rain_limit = Hinf  # If the cummulated rainfall of a rain event is smaller or equal to this, the rain is small
    big_rain_limit = Hsoil  # If the cummulated rainfall of a rain event is equal or bigger than this, the rain is big
    # medium_rain                    #Everything in the middle is a medium rain

    # Defines the Initial Losses for small, medium and big rains in both impermeable and permeable surfaces.
    # As a hypothesis, we suppose that the Initial Losses for the impermeable areas will remain the same before and after the intervention.
    # ----------SMALL RAINS-------------
    small_imp_IL = IL
    small_per_IL = Hsoil

    # ----------MEDIUM RAINS------------
    medium_imp_IL = IL
    medium_per_IL = Hsoil

    # ----------BIG RAINS---------------
    big_imp_IL = IL
    big_per_IL = Hsoil

    # Creation of the effective intensity for permeable and impermeable surfaces.
    # As a hypothesis, we suppose that the effective intensity for the impermeable areas will remain the same before and after the intervention.
    imp_effective_intensity = MIG_EFFECTIVE_RAIN.EFFECTIVE_RAIN(
        rain_time,
        intensity_period,
        time_between_rains,
        small_imp_IL,
        medium_imp_IL,
        big_imp_IL,
        small_rain_limit,
        big_rain_limit,
    )

    per_effective_intensity = MIG_EFFECTIVE_RAIN.EFFECTIVE_RAIN(
        rain_time,
        intensity_period,
        time_between_rains,
        small_per_IL,
        medium_per_IL,
        big_per_IL,
        small_rain_limit,
        big_rain_limit,
    )

    # imp_effective_intensity = The effective intensiry of the rain in the impermeable surfaces after removing the initial losses. List in mm/min.
    # per_effective_intensity = The effective intensiry of the rain in the permeable surfaces after removing the initial losses. List in mm/min.

    # Then it creates the list of type of rains and the counting the rains
    runoff_rain_type, runoff_num_rains = MIG_RAIN_TYPE.RAIN_TYPE(
        rain_time, intensity_period, time_between_rains, small_rain_limit, big_rain_limit
    )
    # runoff_rain_type = List that says the type of rain for every rain_time step. Only includes "small", "medium" or "big".
    # num_rains = number or fain events considering the dry time between rains.

    # Defines the Runoff Coefficients for the different size of rains for both permeable and impermeable surfaces
    # As a hypothesis, we suppose that the Runoff Coefficients for the impermeable areas will remain the same before and after the intervention.
    # The effect is seen since the surfaces are changed.
    # -------------------THIS IS ONLY FOR SUPERFITIAL RUNOFF. NO INFILTRATION IS CONSIDERED----------------------

    # ----------SMALL RAINS-------------
    small_imp_RC = FIMP / p_imp_surface
    small_per_RC = 0

    # ----------MEDIUM RAINS------------
    medium_imp_RC = FIMP / p_imp_surface
    medium_per_RC = 0

    # ----------BIG RAINS---------------
    big_imp_RC = FIMP / p_imp_surface
    big_per_RC = FPER / p_per_surface

    # The flow from the impermeable surface before and after the intervention is created as well as the one for permeable surfaces.
    # As a hypothesis, the flow from the permeable surface will not change before and after the intervention.
    imp_runoff_before_not_full = MIG_GENERIC_FLOW.GENERIC_FLOW(
        runoff_rain_type, imp_effective_intensity, imp_surface_before, small_imp_RC, medium_imp_RC, big_imp_RC
    )
    imp_runoff_after_not_full = MIG_GENERIC_FLOW.GENERIC_FLOW(
        runoff_rain_type, imp_effective_intensity, imp_surface_after, small_imp_RC, medium_imp_RC, big_imp_RC
    )
    per_runoff_not_full = MIG_GENERIC_FLOW.GENERIC_FLOW(
        runoff_rain_type, per_effective_intensity, per_surface, small_per_RC, medium_per_RC, big_per_RC
    )

    # The generated runoffs are only in the moments when there is rain meassure, but they are not in the full study period.
    # We generate the full list.

    imp_runoff_before = MIG_TOOLBOX.COMPLETE_STUDY_PERIOD(rain_time, full_study_period, imp_runoff_before_not_full, 0)
    imp_runoff_after = MIG_TOOLBOX.COMPLETE_STUDY_PERIOD(rain_time, full_study_period, imp_runoff_after_not_full, 0)
    per_runoff = MIG_TOOLBOX.COMPLETE_STUDY_PERIOD(rain_time, full_study_period, per_runoff_not_full, 0)

    # imp_runoff_before = The runoff of the impermeable surface before the intervention. List in m3/s. During all the study period.
    # imp_runoff_after = The runoff of the impermeable surface after the intervention. List in m3/s. During all the study period.
    # per_runoff = The runoff of the permeable surface. List in m3/s. During all the study period.

    return (
        imp_effective_intensity,
        per_effective_intensity,
        runoff_rain_type,
        runoff_num_rains,
        imp_runoff_before,
        imp_runoff_after,
        per_runoff,
    )
