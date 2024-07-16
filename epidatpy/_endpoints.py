import warnings
from abc import ABC, abstractmethod
from typing import (
    Generic,
    Literal,
    Mapping,
    Optional,
    Sequence,
    Union,
)

from epiweeks import Week

from ._covidcast import GeoType, TimeType, define_covidcast_fields
from ._model import (
    CALL_TYPE,
    EpidataFieldInfo,
    EpidataFieldType,
    EpiRange,
    EpiRangeParam,
    IntParam,
    InvalidArgumentException,
    ParamType,
    StringParam,
)
from ._parse import parse_user_date_or_week


def get_wildcard_equivalent_dates(time_value: EpiRangeParam, time_type: Literal["day", "week"]) -> EpiRangeParam:
    if isinstance(time_value, str) and time_value == "*":
        if time_type == "day":
            return EpiRange("10000101", "30000101")
        if time_type == "week":
            return EpiRange("100001", "300001")
    return time_value


class AEpiDataEndpoints(ABC, Generic[CALL_TYPE]):
    """
    epidata endpoint list and fetcher
    """

    @abstractmethod
    def _create_call(
        self,
        endpoint: str,
        params: Mapping[str, Optional[ParamType]],
        meta: Optional[Sequence[EpidataFieldInfo]] = None,
        only_supports_classic: bool = False,
    ) -> CALL_TYPE:
        raise NotImplementedError()

    def pvt_cdc(
        self,
        auth: str,
        locations: StringParam,
        epiweeks: EpiRangeParam = "*",
    ) -> CALL_TYPE:
        """Fetch CDC page hits."""
        epiweeks = get_wildcard_equivalent_dates(epiweeks, "day")

        return self._create_call(
            "cdc/",
            {"auth": auth, "epiweeks": epiweeks, "locations": locations},
            [
                EpidataFieldInfo("location", EpidataFieldType.text),
                EpidataFieldInfo("epiweek", EpidataFieldType.epiweek),
                EpidataFieldInfo("num1", EpidataFieldType.int),
                EpidataFieldInfo("num2", EpidataFieldType.int),
                EpidataFieldInfo("num3", EpidataFieldType.int),
                EpidataFieldInfo("num4", EpidataFieldType.int),
                EpidataFieldInfo("num5", EpidataFieldType.int),
                EpidataFieldInfo("num6", EpidataFieldType.int),
                EpidataFieldInfo("num7", EpidataFieldType.int),
                EpidataFieldInfo("num8", EpidataFieldType.int),
                EpidataFieldInfo("total", EpidataFieldType.int),
                EpidataFieldInfo("value", EpidataFieldType.float),
            ],
        )

    def pub_covid_hosp_facility_lookup(
        self,
        state: Optional[str] = None,
        ccn: Optional[str] = None,
        city: Optional[str] = None,
        zip: Optional[str] = None,  # pylint: disable=redefined-builtin
        fips_code: Optional[str] = None,
    ) -> CALL_TYPE:
        """Lookup COVID hospitalization facility identifiers."""

        if all((v is None for v in (state, ccn, city, zip, fips_code))):
            raise InvalidArgumentException("one of `state`, `ccn`, `city`, `zip`, or `fips_code` is required")

        return self._create_call(
            "covid_hosp_facility_lookup/",
            {
                "state": state,
                "ccn": ccn,
                "city": city,
                "zip": zip,
                "fips_code": fips_code,
            },
            [
                EpidataFieldInfo("hospital_pk", EpidataFieldType.text),
                EpidataFieldInfo("state", EpidataFieldType.text),
                EpidataFieldInfo("ccn", EpidataFieldType.text),
                EpidataFieldInfo("hospital_name", EpidataFieldType.text),
                EpidataFieldInfo("address", EpidataFieldType.text),
                EpidataFieldInfo("city", EpidataFieldType.text),
                EpidataFieldInfo("zip", EpidataFieldType.text),
                EpidataFieldInfo("hospital_subtype", EpidataFieldType.text),
                EpidataFieldInfo("fips_code", EpidataFieldType.text),
                EpidataFieldInfo("is_metro_micro", EpidataFieldType.int),
            ],
        )

    def pub_covid_hosp_facility(
        self,
        hospital_pks: StringParam,
        collection_weeks: EpiRangeParam = "*",
        publication_dates: Optional[EpiRangeParam] = None,
    ) -> CALL_TYPE:
        """Fetch COVID hospitalization data for specific facilities."""

        collection_weeks = get_wildcard_equivalent_dates(collection_weeks, "day")

        # Confusingly, the endpoint expects `collection_weeks` to be in day format,
        # but correspond to epiweeks. Allow `collection_weeks` to be provided in
        # either day or week format and convert to day format.
        parsed_weeks = collection_weeks
        if isinstance(collection_weeks, EpiRange) and isinstance(collection_weeks.start, Week):
            warnings.warn(
                "`collection_weeks` is in week format but `pub_covid_hosp_facility`"
                "expects day format; dates will be converted to day format but may not"
                "correspond exactly to desired time range",
                UserWarning,
            )
            parsed_weeks = EpiRange(
                parse_user_date_or_week(collection_weeks.start, "day"),
                parse_user_date_or_week(collection_weeks.end, "day"),
            )
        elif isinstance(collection_weeks, (str, int)) and len(str(collection_weeks)) == 6:
            warnings.warn(
                "`collection_weeks` is in week format but `pub_covid_hosp_facility`"
                "expects day format; dates will be converted to day format but may not"
                "correspond exactly to desired time range",
                UserWarning,
            )
            parsed_weeks = parse_user_date_or_week(collection_weeks, "day")

        fields_string = [
            "hospital_pk",
            "state",
            "ccn",
            "hospital_name",
            "address",
            "city",
            "zip",
            "hospital_subtype",
            "fips_code",
        ]
        fields_int = [
            "total_beds_7_day_sum",
            "all_adult_hospital_beds_7_day_sum",
            "all_adult_hospital_inpatient_beds_7_day_sum",
            "inpatient_beds_used_7_day_sum",
            "all_adult_hospital_inpatient_bed_occupied_7_day_sum",
            "total_adult_patients_hosp_confirmed_suspected_covid_7d_sum",
            "total_adult_patients_hospitalized_confirmed_covid_7_day_sum",
            "total_pediatric_patients_hosp_confirmed_suspected_covid_7d_sum",
            "total_pediatric_patients_hospitalized_confirmed_covid_7_day_sum",
            "inpatient_beds_7_day_sum",
            "total_icu_beds_7_day_sum",
            "total_staffed_adult_icu_beds_7_day_sum",
            "icu_beds_used_7_day_sum",
            "staffed_adult_icu_bed_occupancy_7_day_sum",
            "staffed_icu_adult_patients_confirmed_suspected_covid_7d_sum",
            "staffed_icu_adult_patients_confirmed_covid_7_day_sum",
            "total_patients_hospitalized_confirmed_influenza_7_day_sum",
            "icu_patients_confirmed_influenza_7_day_sum",
            "total_patients_hosp_confirmed_influenza_and_covid_7d_sum",
            "total_beds_7_day_coverage",
            "all_adult_hospital_beds_7_day_coverage",
            "all_adult_hospital_inpatient_beds_7_day_coverage",
            "inpatient_beds_used_7_day_coverage",
            "all_adult_hospital_inpatient_bed_occupied_7_day_coverage",
            "total_adult_patients_hosp_confirmed_suspected_covid_7d_cov",
            "total_adult_patients_hospitalized_confirmed_covid_7_day_coverage",
            "total_pediatric_patients_hosp_confirmed_suspected_covid_7d_cov",
            "total_pediatric_patients_hosp_confirmed_covid_7d_cov",
            "inpatient_beds_7_day_coverage",
            "total_icu_beds_7_day_coverage",
            "total_staffed_adult_icu_beds_7_day_coverage",
            "icu_beds_used_7_day_coverage",
            "staffed_adult_icu_bed_occupancy_7_day_coverage",
            "staffed_icu_adult_patients_confirmed_suspected_covid_7d_cov",
            "staffed_icu_adult_patients_confirmed_covid_7_day_coverage",
            "total_patients_hospitalized_confirmed_influenza_7_day_coverage",
            "icu_patients_confirmed_influenza_7_day_coverage",
            "total_patients_hosp_confirmed_influenza_and_covid_7d_cov",
            "previous_day_admission_adult_covid_confirmed_7_day_sum",
            "previous_day_admission_adult_covid_confirmed_18_19_7_day_sum",
            "previous_day_admission_adult_covid_confirmed_20_29_7_day_sum",
            "previous_day_admission_adult_covid_confirmed_30_39_7_day_sum",
            "previous_day_admission_adult_covid_confirmed_40_49_7_day_sum",
            "previous_day_admission_adult_covid_confirmed_50_59_7_day_sum",
            "previous_day_admission_adult_covid_confirmed_60_69_7_day_sum",
            "previous_day_admission_adult_covid_confirmed_70_79_7_day_sum",
            "previous_day_admission_adult_covid_confirmed_80plus_7_day_sum",
            "previous_day_admission_adult_covid_confirmed_unknown_7_day_sum",
            "previous_day_admission_pediatric_covid_confirmed_7_day_sum",
            "previous_day_covid_ed_visits_7_day_sum",
            "previous_day_admission_adult_covid_suspected_7_day_sum",
            "previous_day_admission_adult_covid_suspected_18_19_7_day_sum",
            "previous_day_admission_adult_covid_suspected_20_29_7_day_sum",
            "previous_day_admission_adult_covid_suspected_30_39_7_day_sum",
            "previous_day_admission_adult_covid_suspected_40_49_7_day_sum",
            "previous_day_admission_adult_covid_suspected_50_59_7_day_sum",
            "previous_day_admission_adult_covid_suspected_60_69_7_day_sum",
            "previous_day_admission_adult_covid_suspected_70_79_7_day_sum",
            "previous_day_admission_adult_covid_suspected_80plus_7_day_sum",
            "previous_day_admission_adult_covid_suspected_unknown_7_day_sum",
            "previous_day_admission_pediatric_covid_suspected_7_day_sum",
            "previous_day_total_ed_visits_7_day_sum",
            "previous_day_admission_influenza_confirmed_7_day_sum",
        ]
        fields_float = [
            "total_beds_7_day_avg",
            "all_adult_hospital_beds_7_day_avg",
            "all_adult_hospital_inpatient_beds_7_day_avg",
            "inpatient_beds_used_7_day_avg",
            "all_adult_hospital_inpatient_bed_occupied_7_day_avg",
            "total_adult_patients_hosp_confirmed_suspected_covid_7d_avg",
            "total_adult_patients_hospitalized_confirmed_covid_7_day_avg",
            "total_pediatric_patients_hosp_confirmed_suspected_covid_7d_avg",
            "total_pediatric_patients_hospitalized_confirmed_covid_7_day_avg",
            "inpatient_beds_7_day_avg",
            "total_icu_beds_7_day_avg",
            "total_staffed_adult_icu_beds_7_day_avg",
            "icu_beds_used_7_day_avg",
            "staffed_adult_icu_bed_occupancy_7_day_avg",
            "staffed_icu_adult_patients_confirmed_suspected_covid_7d_avg",
            "staffed_icu_adult_patients_confirmed_covid_7_day_avg",
            "total_patients_hospitalized_confirmed_influenza_7_day_avg",
            "icu_patients_confirmed_influenza_7_day_avg",
            "total_patients_hosp_confirmed_influenza_and_covid_7d_avg",
        ]

        return self._create_call(
            "covid_hosp_facility/",
            {
                "hospital_pks": hospital_pks,
                "collection_weeks": parsed_weeks,
                "publication_dates": publication_dates,
            },
            [
                *[EpidataFieldInfo(k, EpidataFieldType.text) for k in fields_string],
                EpidataFieldInfo("publication_date", EpidataFieldType.date),
                EpidataFieldInfo("collection_week", EpidataFieldType.date),
                EpidataFieldInfo("is_metro_micro", EpidataFieldType.bool),
                *[EpidataFieldInfo(k, EpidataFieldType.int) for k in fields_int],
                *[EpidataFieldInfo(k, EpidataFieldType.float) for k in fields_float],
            ],
        )

    def pub_covid_hosp_state_timeseries(
        self,
        states: StringParam,
        dates: EpiRangeParam = "*",
        issues: Optional[EpiRangeParam] = None,
        as_of: Union[None, int, str] = None,
    ) -> CALL_TYPE:
        """Fetch COVID hospitalization data."""

        if issues is not None and as_of is not None:
            raise InvalidArgumentException("`issues` and `as_of` are mutually exclusive")

        dates = get_wildcard_equivalent_dates(dates, "day")

        fields_int = [
            "hospital_onset_covid",
            "hospital_onset_covid_coverage",
            "inpatient_beds",
            "inpatient_beds_coverage",
            "inpatient_beds_used",
            "inpatient_beds_used_coverage",
            "inpatient_beds_used_covid",
            "inpatient_beds_used_covid_coverage",
            "previous_day_admission_adult_covid_confirmed",
            "previous_day_admission_adult_covid_confirmed_coverage",
            "previous_day_admission_adult_covid_suspected",
            "previous_day_admission_adult_covid_suspected_coverage",
            "previous_day_admission_pediatric_covid_confirmed",
            "previous_day_admission_pediatric_covid_confirmed_coverage",
            "previous_day_admission_pediatric_covid_suspected",
            "previous_day_admission_pediatric_covid_suspected_coverage",
            "staffed_adult_icu_bed_occupancy",
            "staffed_adult_icu_bed_occupancy_coverage",
            "staffed_icu_adult_patients_confirmed_suspected_covid",
            "staffed_icu_adult_patients_confirmed_suspected_covid_coverage",
            "staffed_icu_adult_patients_confirmed_covid",
            "staffed_icu_adult_patients_confirmed_covid_coverage",
            "total_adult_patients_hosp_confirmed_suspected_covid",
            "total_adult_patients_hosp_confirmed_suspected_covid_coverage",
            "total_adult_patients_hosp_confirmed_covid",
            "total_adult_patients_hosp_confirmed_covid_coverage",
            "total_pediatric_patients_hosp_confirmed_suspected_covid",
            "total_pediatric_patients_hosp_confirmed_suspected_covid_coverage",
            "total_pediatric_patients_hosp_confirmed_covid",
            "total_pediatric_patients_hosp_confirmed_covid_coverage",
            "total_staffed_adult_icu_beds",
            "total_staffed_adult_icu_beds_coverage",
            "inpatient_beds_utilization_coverage",
            "inpatient_beds_utilization_numerator",
            "inpatient_beds_utilization_denominator",
            "percent_of_inpatients_with_covid_coverage",
            "percent_of_inpatients_with_covid_numerator",
            "percent_of_inpatients_with_covid_denominator",
            "inpatient_bed_covid_utilization_coverage",
            "inpatient_bed_covid_utilization_numerator",
            "inpatient_bed_covid_utilization_denominator",
            "adult_icu_bed_covid_utilization_coverage",
            "adult_icu_bed_covid_utilization_numerator",
            "adult_icu_bed_covid_utilization_denominator",
            "adult_icu_bed_utilization_coverage",
            "adult_icu_bed_utilization_numerator",
            "adult_icu_bed_utilization_denominator",
        ]
        fields_float = [
            "inpatient_beds_utilization",
            "percent_of_inpatients_with_covid",
            "inpatient_bed_covid_utilization",
            "adult_icu_bed_covid_utilization",
            "adult_icu_bed_utilization",
        ]
        fields_bool = [
            "critical_staffing_shortage_today_yes",
            "critical_staffing_shortage_today_no",
            "critical_staffing_shortage_today_not_reported",
            "critical_staffing_shortage_anticipated_within_week_yes",
            "critical_staffing_shortage_anticipated_within_week_no",
            "critical_staffing_shortage_anticipated_within_week_not_reported",
        ]

        return self._create_call(
            "covid_hosp_state_timeseries/",
            {"states": states, "dates": dates, "issues": issues, "as_of": as_of},
            [
                EpidataFieldInfo("state", EpidataFieldType.text),
                EpidataFieldInfo("issue", EpidataFieldType.date),
                EpidataFieldInfo("date", EpidataFieldType.date),
                *[EpidataFieldInfo(k, EpidataFieldType.bool) for k in fields_bool],
                *[EpidataFieldInfo(k, EpidataFieldType.int) for k in fields_int],
                *[EpidataFieldInfo(k, EpidataFieldType.float) for k in fields_float],
            ],
        )

    def pub_covidcast_meta(self) -> CALL_TYPE:
        """Fetch COVIDcast surveillance stream metadata.

        Obtains a data frame of metadata describing all publicly available data
        streams from the COVIDcast API. See the `data source and signals
        documentation
        <https://cmu-delphi.github.io/delphi-epidata/api/covidcast_signals.html>`_
        for descriptions of the available sources.

        :returns: A `EpiDataCall` object containing the following information:

            ``data_source``
                Data source name.

            ``signal``
                Signal name.

            ``time_type``
                Temporal resolution at which this signal is reported. "day", for
                example, means the signal is reported daily.

            ``geo_type``
                Geographic level for which this signal is available, such as county,
                state, msa, hss, hrr, or nation. Most signals are available at multiple geographic
                levels and will hence be listed in multiple rows with their own
                metadata.

            ``min_time``
                First day for which this signal is available. For weekly signals, will be
                the first day of the epiweek.

            ``max_time``
                Most recent day for which this signal is available. For weekly signals, will be
                the first day of the epiweek.

            ``num_locations``
                Number of distinct geographic locations available for this signal. For
                example, if `geo_type` is county, the number of counties for which this
                signal has ever been reported.

            ``min_value``
                The smallest value that has ever been reported.

            ``max_value``
                The largest value that has ever been reported.

            ``mean_value``
                The arithmetic mean of all reported values.

            ``stdev_value``
                The sample standard deviation of all reported values.

            ``last_update``
                The UTC datetime for when the signal value was last updated.

            ``max_issue``
                Most recent date data was issued.

            ``min_lag``
                Smallest lag from observation to issue, in days.

            ``max_lag``
                Largest lag from observation to issue, in days.
        """
        return self._create_call(
            "covidcast_meta/",
            {},
            [
                EpidataFieldInfo("data_source", EpidataFieldType.text),
                EpidataFieldInfo("signal", EpidataFieldType.text),
                EpidataFieldInfo(
                    "time_type",
                    EpidataFieldType.categorical,
                    categories=["week", "day"],
                ),
                EpidataFieldInfo("min_time", EpidataFieldType.date_or_epiweek),
                EpidataFieldInfo("max_time", EpidataFieldType.date_or_epiweek),
                EpidataFieldInfo("num_locations", EpidataFieldType.int),
                EpidataFieldInfo("min_value", EpidataFieldType.float),
                EpidataFieldInfo("max_value", EpidataFieldType.float),
                EpidataFieldInfo("mean_value", EpidataFieldType.float),
                EpidataFieldInfo("stdev_value", EpidataFieldType.float),
                EpidataFieldInfo("last_update", EpidataFieldType.int),
                EpidataFieldInfo("max_issue", EpidataFieldType.date),
                EpidataFieldInfo("min_lag", EpidataFieldType.int),
                EpidataFieldInfo("max_lag", EpidataFieldType.int),
            ],
        )

    def pub_covidcast(
        self,
        data_source: str,
        signals: StringParam,
        geo_type: GeoType,
        time_type: TimeType,
        geo_values: Union[str, Sequence[str]] = "*",
        time_values: EpiRangeParam = "*",
        as_of: Union[None, str, int] = None,
        issues: Optional[EpiRangeParam] = None,
        lag: Optional[int] = None,
    ) -> CALL_TYPE:
        """Fetch Delphi's COVID-19 Surveillance Streams"""
        if sum([issues is not None, lag is not None, as_of is not None]) > 1:
            raise InvalidArgumentException("`issues`, `lag`, and `as_of` are mutually exclusive.")

        if data_source == "nchs-mortality" and time_type != "week":
            raise InvalidArgumentException("nchs-mortality data source only supports the week time type.")

        return self._create_call(
            "covidcast/",
            {
                "data_source": data_source,
                "signals": signals,
                "geo_type": geo_type,
                "time_type": time_type,
                "geo_values": geo_values,
                "time_values": time_values,
                "as_of": as_of,
                "issues": issues,
                "lag": lag,
            },
            define_covidcast_fields(),
        )

    def pub_delphi(self, system: str, epiweek: Union[int, str]) -> CALL_TYPE:
        """Fetch Delphi's forecast."""

        return self._create_call(
            "delphi/",
            {"system": system, "epiweek": epiweek},
            [
                EpidataFieldInfo("system", EpidataFieldType.text),
                EpidataFieldInfo("epiweek", EpidataFieldType.epiweek),
                EpidataFieldInfo("json", EpidataFieldType.text),
            ],
            only_supports_classic=True,
        )

    def pub_dengue_nowcast(self, locations: StringParam, epiweeks: EpiRangeParam = "*") -> CALL_TYPE:
        """Fetch Delphi's dengue nowcast."""
        epiweeks = get_wildcard_equivalent_dates(epiweeks, "week")

        return self._create_call(
            "dengue_nowcast/",
            {"locations": locations, "epiweeks": epiweeks},
            [
                EpidataFieldInfo("location", EpidataFieldType.text),
                EpidataFieldInfo("epiweek", EpidataFieldType.epiweek),
                EpidataFieldInfo("value", EpidataFieldType.float),
                EpidataFieldInfo("std", EpidataFieldType.float),
            ],
        )

    def pvt_dengue_sensors(
        self,
        auth: str,
        names: StringParam,
        locations: StringParam,
        epiweeks: EpiRangeParam = "*",
    ) -> CALL_TYPE:
        """Fetch Delphi's digital surveillance sensors."""
        epiweeks = get_wildcard_equivalent_dates(epiweeks, "week")

        return self._create_call(
            "dengue_sensors/",
            {
                "auth": auth,
                "names": names,
                "locations": locations,
                "epiweeks": epiweeks,
            },
            [
                EpidataFieldInfo("name", EpidataFieldType.text),
                EpidataFieldInfo("location", EpidataFieldType.text),
                EpidataFieldInfo("epiweek", EpidataFieldType.epiweek),
                EpidataFieldInfo("value", EpidataFieldType.float),
            ],
        )

    def pub_ecdc_ili(
        self,
        regions: StringParam,
        epiweeks: EpiRangeParam = "*",
        issues: Optional[EpiRangeParam] = None,
        lag: Optional[int] = None,
    ) -> CALL_TYPE:
        """Fetch ECDC ILI data."""
        epiweeks = get_wildcard_equivalent_dates(epiweeks, "week")

        if issues is not None and lag is not None:
            raise InvalidArgumentException("`issues` and `lag` are mutually exclusive")

        return self._create_call(
            "ecdc_ili/",
            {"regions": regions, "epiweeks": epiweeks, "issues": issues, "lag": lag},
            [
                EpidataFieldInfo("region", EpidataFieldType.text),
                EpidataFieldInfo("release_date", EpidataFieldType.date),
                EpidataFieldInfo("issue", EpidataFieldType.epiweek),
                EpidataFieldInfo("epiweek", EpidataFieldType.epiweek),
                EpidataFieldInfo("lag", EpidataFieldType.int),
                EpidataFieldInfo("incidence_rate", EpidataFieldType.float),
            ],
        )

    def pub_flusurv(
        self,
        locations: StringParam,
        epiweeks: EpiRangeParam = "*",
        issues: Optional[EpiRangeParam] = None,
        lag: Optional[int] = None,
    ) -> CALL_TYPE:
        """Fetch FluSurv data."""
        epiweeks = get_wildcard_equivalent_dates(epiweeks, "week")

        if issues is not None and lag is not None:
            raise InvalidArgumentException("`issues` and `lag` are mutually exclusive")

        return self._create_call(
            "flusurv/",
            {
                "locations": locations,
                "epiweeks": epiweeks,
                "issues": issues,
                "lag": lag,
            },
            [
                EpidataFieldInfo("release_date", EpidataFieldType.text),
                EpidataFieldInfo("location", EpidataFieldType.text),
                EpidataFieldInfo("issue", EpidataFieldType.date_or_epiweek),
                EpidataFieldInfo("epiweek", EpidataFieldType.epiweek),
                EpidataFieldInfo("lag", EpidataFieldType.int),
                EpidataFieldInfo("rate_age_0", EpidataFieldType.float),
                EpidataFieldInfo("rate_age_1", EpidataFieldType.float),
                EpidataFieldInfo("rate_age_2", EpidataFieldType.float),
                EpidataFieldInfo("rate_age_3", EpidataFieldType.float),
                EpidataFieldInfo("rate_age_4", EpidataFieldType.float),
                EpidataFieldInfo("rate_overall", EpidataFieldType.float),
            ],
        )

    def pub_fluview_clinical(
        self,
        regions: StringParam,
        epiweeks: EpiRangeParam = "*",
        issues: Optional[EpiRangeParam] = None,
        lag: Optional[int] = None,
    ) -> CALL_TYPE:
        """Fetch FluView clinical data."""
        epiweeks = get_wildcard_equivalent_dates(epiweeks, "week")

        if issues is not None and lag is not None:
            raise InvalidArgumentException("`issues` and `lag` are mutually exclusive")

        return self._create_call(
            "fluview_clinical/",
            {"regions": regions, "epiweeks": epiweeks, "issues": issues, "lag": lag},
            [
                EpidataFieldInfo("release_date", EpidataFieldType.date),
                EpidataFieldInfo("region", EpidataFieldType.text),
                EpidataFieldInfo("issue", EpidataFieldType.epiweek),
                EpidataFieldInfo("epiweek", EpidataFieldType.epiweek),
                EpidataFieldInfo("lag", EpidataFieldType.int),
                EpidataFieldInfo("total_specimens", EpidataFieldType.int),
                EpidataFieldInfo("total_a", EpidataFieldType.int),
                EpidataFieldInfo("total_b", EpidataFieldType.int),
                EpidataFieldInfo("percent_positive", EpidataFieldType.float),
                EpidataFieldInfo("percent_a", EpidataFieldType.float),
                EpidataFieldInfo("percent_b", EpidataFieldType.float),
            ],
        )

    def pub_fluview_meta(self) -> CALL_TYPE:
        return self._create_call(
            "fluview_meta",
            {},
            [
                EpidataFieldInfo("latest_update", EpidataFieldType.date),
                EpidataFieldInfo("latest_issue", EpidataFieldType.date),
                EpidataFieldInfo("table_rows", EpidataFieldType.int),
            ],
        )

    def pub_fluview(
        self,
        regions: StringParam,
        epiweeks: EpiRangeParam = "*",
        issues: Optional[EpiRangeParam] = None,
        lag: Optional[int] = None,
        auth: Optional[str] = None,
    ) -> CALL_TYPE:
        epiweeks = get_wildcard_equivalent_dates(epiweeks, "week")

        if issues is not None and lag is not None:
            raise InvalidArgumentException("`issues` and `lag` are mutually exclusive")

        return self._create_call(
            "fluview/",
            {
                "regions": regions,
                "epiweeks": epiweeks,
                "issues": issues,
                "lag": lag,
                "auth": auth,
            },
            [
                EpidataFieldInfo("release_date", EpidataFieldType.date),
                EpidataFieldInfo("region", EpidataFieldType.text),
                EpidataFieldInfo("issue", EpidataFieldType.epiweek),
                EpidataFieldInfo("epiweek", EpidataFieldType.epiweek),
                EpidataFieldInfo("lag", EpidataFieldType.int),
                EpidataFieldInfo("num_ili", EpidataFieldType.int),
                EpidataFieldInfo("num_patients", EpidataFieldType.int),
                EpidataFieldInfo("num_age_0", EpidataFieldType.int),
                EpidataFieldInfo("num_age_1", EpidataFieldType.int),
                EpidataFieldInfo("num_age_2", EpidataFieldType.int),
                EpidataFieldInfo("num_age_3", EpidataFieldType.int),
                EpidataFieldInfo("num_age_4", EpidataFieldType.int),
                EpidataFieldInfo("num_age_5", EpidataFieldType.int),
                EpidataFieldInfo("wili", EpidataFieldType.float),
                EpidataFieldInfo("ili", EpidataFieldType.float),
            ],
        )

    def pub_gft(self, locations: StringParam, epiweeks: EpiRangeParam = "*") -> CALL_TYPE:
        """Fetch Google Flu Trends data."""
        epiweeks = get_wildcard_equivalent_dates(epiweeks, "week")

        return self._create_call(
            "gft/",
            {"locations": locations, "epiweeks": epiweeks},
            [
                EpidataFieldInfo("location", EpidataFieldType.text),
                EpidataFieldInfo("epiweek", EpidataFieldType.epiweek),
                EpidataFieldInfo("num", EpidataFieldType.int),
            ],
        )

    def pvt_ght(
        self,
        auth: str,
        locations: StringParam,
        epiweeks: EpiRangeParam = "*",
        query: str = "",
    ) -> CALL_TYPE:
        """Fetch Google Health Trends data."""
        if auth is None or locations is None or query == "":
            raise InvalidArgumentException("`auth`, `locations`, `epiweeks`, and `query` are all required")

        return self._create_call(
            "ght/",
            {
                "auth": auth,
                "locations": locations,
                "epiweeks": epiweeks,
                "query": query,
            },
            [
                EpidataFieldInfo("location", EpidataFieldType.text),
                EpidataFieldInfo("epiweek", EpidataFieldType.epiweek),
                EpidataFieldInfo("value", EpidataFieldType.float),
            ],
        )

    def pub_kcdc_ili(
        self,
        regions: StringParam,
        epiweeks: EpiRangeParam = "*",
        issues: Optional[EpiRangeParam] = None,
        lag: Optional[int] = None,
    ) -> CALL_TYPE:
        """Fetch KCDC ILI data."""
        epiweeks = get_wildcard_equivalent_dates(epiweeks, "week")

        if issues is not None and lag is not None:
            raise InvalidArgumentException("`issues` and `lag` are mutually exclusive")

        return self._create_call(
            "kcdc_ili/",
            {"regions": regions, "epiweeks": epiweeks, "issues": issues, "lag": lag},
            [
                EpidataFieldInfo("release_date", EpidataFieldType.date),
                EpidataFieldInfo("region", EpidataFieldType.text),
                EpidataFieldInfo("issue", EpidataFieldType.epiweek),
                EpidataFieldInfo("epiweek", EpidataFieldType.epiweek),
                EpidataFieldInfo("lag", EpidataFieldType.int),
                EpidataFieldInfo("ili", EpidataFieldType.float),
            ],
        )

    def pvt_meta_norostat(self, auth: str) -> CALL_TYPE:
        """Fetch NoroSTAT metadata."""
        return self._create_call(
            "meta_norostat/",
            {"auth": auth},
            only_supports_classic=True,
        )

    def pub_meta(self) -> CALL_TYPE:
        """Fetch API metadata."""
        return self._create_call(
            "meta/",
            {},
            only_supports_classic=True,
        )

    def pub_nidss_dengue(self, locations: StringParam, epiweeks: EpiRangeParam = "*") -> CALL_TYPE:
        """Fetch NIDSS dengue data."""
        epiweeks = get_wildcard_equivalent_dates(epiweeks, "week")

        return self._create_call(
            "nidss_dengue/",
            {"locations": locations, "epiweeks": epiweeks},
            [
                EpidataFieldInfo("location", EpidataFieldType.text),
                EpidataFieldInfo("epiweek", EpidataFieldType.epiweek),
                EpidataFieldInfo("count", EpidataFieldType.int),
            ],
        )

    def pub_nidss_flu(
        self,
        regions: StringParam,
        epiweeks: EpiRangeParam = "*",
        issues: Optional[EpiRangeParam] = None,
        lag: Optional[int] = None,
    ) -> CALL_TYPE:
        """Fetch NIDSS flu data."""
        epiweeks = get_wildcard_equivalent_dates(epiweeks, "week")

        if issues is not None and lag is not None:
            raise InvalidArgumentException("`issues` and `lag` are mutually exclusive")

        return self._create_call(
            "nidss_flu/",
            {"regions": regions, "epiweeks": epiweeks, "issues": issues, "lag": lag},
            [
                EpidataFieldInfo("release_date", EpidataFieldType.date),
                EpidataFieldInfo("region", EpidataFieldType.text),
                EpidataFieldInfo("epiweek", EpidataFieldType.epiweek),
                EpidataFieldInfo("issue", EpidataFieldType.epiweek),
                EpidataFieldInfo("lag", EpidataFieldType.int),
                EpidataFieldInfo("visits", EpidataFieldType.int),
                EpidataFieldInfo("ili", EpidataFieldType.float),
            ],
        )

    def pvt_norostat(self, auth: str, location: str, epiweeks: EpiRangeParam = "*") -> CALL_TYPE:
        """Fetch NoroSTAT data (point data, no min/max)."""
        epiweeks = get_wildcard_equivalent_dates(epiweeks, "week")

        return self._create_call(
            "norostat/",
            {"auth": auth, "epiweeks": epiweeks, "location": location},
            [
                EpidataFieldInfo("release_date", EpidataFieldType.date),
                EpidataFieldInfo("epiweek", EpidataFieldType.epiweek),
                EpidataFieldInfo("value", EpidataFieldType.int),
            ],
        )

    def pub_nowcast(self, locations: StringParam, epiweeks: EpiRangeParam = "*") -> CALL_TYPE:
        """Fetch Delphi's wILI nowcast."""
        epiweeks = get_wildcard_equivalent_dates(epiweeks, "week")

        return self._create_call(
            "nowcast/",
            {"locations": locations, "epiweeks": epiweeks},
            [
                EpidataFieldInfo("location", EpidataFieldType.text),
                EpidataFieldInfo("epiweek", EpidataFieldType.epiweek),
                EpidataFieldInfo("value", EpidataFieldType.float),
                EpidataFieldInfo("std", EpidataFieldType.float),
            ],
        )

    def pub_paho_dengue(
        self,
        regions: StringParam,
        epiweeks: EpiRangeParam = "*",
        issues: Optional[EpiRangeParam] = None,
        lag: Optional[int] = None,
    ) -> CALL_TYPE:
        """Fetch PAHO Dengue data."""
        epiweeks = get_wildcard_equivalent_dates(epiweeks, "week")

        if issues is not None and lag is not None:
            raise InvalidArgumentException("`issues` and `lag` are mutually exclusive")

        return self._create_call(
            "paho_dengue/",
            {"regions": regions, "epiweeks": epiweeks, "issues": issues, "lag": lag},
            [
                EpidataFieldInfo("release_date", EpidataFieldType.date),
                EpidataFieldInfo("region", EpidataFieldType.text),
                EpidataFieldInfo("serotype", EpidataFieldType.text),
                EpidataFieldInfo("epiweek", EpidataFieldType.epiweek),
                EpidataFieldInfo("issue", EpidataFieldType.epiweek),
                EpidataFieldInfo("lag", EpidataFieldType.int),
                EpidataFieldInfo("total_pop", EpidataFieldType.int),
                EpidataFieldInfo("num_dengue", EpidataFieldType.int),
                EpidataFieldInfo("num_severe", EpidataFieldType.int),
                EpidataFieldInfo("num_deaths", EpidataFieldType.int),
                EpidataFieldInfo("incidence_rate", EpidataFieldType.float),
            ],
        )

    def pvt_quidel(self, auth: str, locations: StringParam, epiweeks: EpiRangeParam = "*") -> CALL_TYPE:
        """Fetch Quidel data."""
        epiweeks = get_wildcard_equivalent_dates(epiweeks, "week")

        return self._create_call(
            "quidel/",
            {"auth": auth, "epiweeks": epiweeks, "locations": locations},
            [
                EpidataFieldInfo("location", EpidataFieldType.text),
                EpidataFieldInfo("epiweek", EpidataFieldType.epiweek),
                EpidataFieldInfo("value", EpidataFieldType.float),
            ],
        )

    def pvt_sensors(
        self,
        auth: str,
        names: StringParam,
        locations: StringParam,
        epiweeks: EpiRangeParam = "*",
    ) -> CALL_TYPE:
        """Fetch Delphi's digital surveillance sensors."""
        epiweeks = get_wildcard_equivalent_dates(epiweeks, "week")

        return self._create_call(
            "sensors/",
            {
                "auth": auth,
                "names": names,
                "locations": locations,
                "epiweeks": epiweeks,
            },
            [
                EpidataFieldInfo("name", EpidataFieldType.text),
                EpidataFieldInfo("location", EpidataFieldType.text),
                EpidataFieldInfo("epiweek", EpidataFieldType.epiweek),
                EpidataFieldInfo("value", EpidataFieldType.float),
            ],
        )

    def pvt_twitter(
        self,
        auth: str,
        locations: StringParam,
        time_type: Literal["day", "week"],
        time_values: EpiRangeParam = "*",
    ) -> CALL_TYPE:
        """Fetch HealthTweets data."""
        if time_type == "day":
            dates = time_values
            epiweeks = None
            dates = get_wildcard_equivalent_dates(dates, "day")
        else:
            epiweeks = time_values
            dates = None
            epiweeks = get_wildcard_equivalent_dates(epiweeks, "week")

        time_field = (
            EpidataFieldInfo("date", EpidataFieldType.date)
            if dates
            else EpidataFieldInfo("epiweek", EpidataFieldType.epiweek)
        )

        return self._create_call(
            "twitter/",
            {
                "auth": auth,
                "locations": locations,
                "epiweeks": epiweeks,
                "dates": dates,
            },
            [
                EpidataFieldInfo("location", EpidataFieldType.text),
                time_field,
                EpidataFieldInfo("num", EpidataFieldType.int),
                EpidataFieldInfo("total", EpidataFieldType.int),
                EpidataFieldInfo("percent", EpidataFieldType.float),
            ],
        )

    def pub_wiki(
        self,
        articles: StringParam,
        time_type: Literal["day", "week"],
        time_values: EpiRangeParam = "*",
        hours: Optional[IntParam] = None,
        language: str = "en",
    ) -> CALL_TYPE:
        """Fetch Wikipedia access data."""
        if time_type == "day":
            dates = time_values
            epiweeks = None
            dates = get_wildcard_equivalent_dates(dates, "day")
        else:
            epiweeks = time_values
            dates = None
            epiweeks = get_wildcard_equivalent_dates(epiweeks, "week")

        return self._create_call(
            "wiki/",
            {
                "articles": articles,
                "dates": dates,
                "epiweeks": epiweeks,
                "hours": hours,
                "language": language,
            },
            [
                EpidataFieldInfo("article", EpidataFieldType.text),
                (
                    EpidataFieldInfo("date", EpidataFieldType.date)
                    if dates
                    else EpidataFieldInfo("epiweek", EpidataFieldType.epiweek)
                ),
                EpidataFieldInfo("count", EpidataFieldType.int),
                EpidataFieldInfo("total", EpidataFieldType.int),
                EpidataFieldInfo("hour", EpidataFieldType.int),
                EpidataFieldInfo("value", EpidataFieldType.float),
            ],
        )
