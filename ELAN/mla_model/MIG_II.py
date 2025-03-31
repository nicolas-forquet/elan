# pylint: skip-file

"""
The aim of this code is to centralize the production of all Inflow Infiltration that ends up in the unitary sewage system.

Author: Miguel José ÁLVAREZ VELÁSQUEZ
Created on: 30/04/2023
"""

from . import MIG_EFFECTIVE_RAIN, MIG_GENERIC_FLOW, MIG_RAIN_TYPE, MIG_TOOLBOX


# There are mainly two types of inflow infiltration infiltration: Permanent and Rain Induced. This code will tackle them one by one.
def II(rain_time, full_study_period, intensity_period, Hinf, Hsoil, per_surface, p_per_surface, PII, FRII, KRII):
    # The rain limits are defined
    small_rain_limit = Hinf  # If the cummulated rainfall of a rain event is smaller or equal to this, the rain is small
    big_rain_limit = Hsoil  # If the cummulated rainfall of a rain event is equal or bigger than this, the rain is big

    # Definition of the Initial Losses for small, medium and big rain events. Since this is for infiltration, the three are the same.
    small_IL = Hinf
    medium_IL = Hinf
    big_IL = Hinf

    # Generating the effective intensity for the rain induced infiltration.
    time_between_rains = (
        KRII * 24 * 3600
    )  # In this case the dry period between two rains must be of at leat KRII in seconds.
    II_effective_intensity = MIG_EFFECTIVE_RAIN.EFFECTIVE_RAIN(
        rain_time, intensity_period, time_between_rains, small_IL, medium_IL, big_IL, small_rain_limit, big_rain_limit
    )

    # Generating the rain type and the number of rains for the rain induced infiltration.
    II_rain_type, II_num_rains = MIG_RAIN_TYPE.RAIN_TYPE(
        rain_time, intensity_period, time_between_rains, small_rain_limit, big_rain_limit
    )

    # Definition of the Runoff Coefficient for small, medium and big rain events. Since this is only for infiltration, the three are the same.
    # This is only calculated in the permeable surface since it is the only place that generates infiltration.
    small_RC = FRII / p_per_surface
    medium_RC = FRII / p_per_surface
    big_RC = FRII / p_per_surface

    # Creating the Rain Induced Infiltration (RII) flow. This list is generated according to the rain and is not continuous.
    RII_not_full = MIG_GENERIC_FLOW.GENERIC_FLOW(
        II_rain_type, II_effective_intensity, per_surface, small_RC, medium_RC, big_RC
    )

    # The list is completed with zeros when there is no flow. Result in m3/s.
    Q_up_RII = MIG_TOOLBOX.COMPLETE_STUDY_PERIOD(rain_time, full_study_period, RII_not_full, 0)

    # We define a list as long as the full_study_period that has the value of the permanent inflow infiltration (PII)
    Q_up_PII = [PII * 0.001 for i in range(len(full_study_period))]

    return II_effective_intensity, II_rain_type, II_num_rains, Q_up_RII, Q_up_PII
