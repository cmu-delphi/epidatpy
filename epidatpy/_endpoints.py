from __future__ import annotations

import warnings
from collections.abc import Mapping, Sequence
from datetime import date
from typing import (
    Any,
    Final,
    Literal,
)

from epiweeks import Week
from requests import Session

from ._call import EpiDataCall, _request_with_retry
from ._constants import BASE_URL, CAST_BASE_URL
from ._covidcast import GeoType, TimeType, define_covidcast_fields
from ._model import (
    ApiVersion,
    CastPostFilter,
    EpidataFieldInfo,
    EpidataFieldType,
    EpiRange,
    EpiRangeParam,
    IntParam,
    InvalidArgumentException,
    StringParam,
    add_endpoint_to_url,
    format_list,
)
from ._parse import parse_api_date, parse_user_date_or_week, validate_report_time_query


def get_wildcard_equivalent_dates(time_value: EpiRangeParam, time_type: Literal["day", "week"]) -> EpiRangeParam:
    if isinstance(time_value, str) and time_value == "*":
        if time_type == "day":
            return EpiRange("10000101", "30000101")
        if time_type == "week":
            return EpiRange("100001", "300001")
    return time_value


class EpiDataContext:
    """Endpoint catalog and synchronous fetcher for Delphi's Epidata API."""

    _base_url: Final[str]
    _cast_base_url: Final[str]
    _session: Final[Session | None]

    def __init__(
        self,
        base_url: str = BASE_URL,
        session: Session | None = None,
        use_cache: bool | None = None,
        cache_max_age_days: int | None = None,
        cast_base_url: str = CAST_BASE_URL,
    ) -> None:
        self._base_url = base_url
        self._cast_base_url = cast_base_url
        self._session = session
        self.use_cache = use_cache
        self.cache_max_age_days = cache_max_age_days

    def with_base_url(self, base_url: str) -> EpiDataContext:
        return EpiDataContext(
            base_url,
            self._session,
            self.use_cache,
            self.cache_max_age_days,
            cast_base_url=self._cast_base_url,
        )

    def with_session(self, session: Session) -> EpiDataContext:
        return EpiDataContext(
            self._base_url,
            session,
            self.use_cache,
            self.cache_max_age_days,
            cast_base_url=self._cast_base_url,
        )

    def _create_call(
        self,
        endpoint: str,
        params: Mapping[str, EpiRangeParam | None],
        meta: Sequence[EpidataFieldInfo] | None = None,
        only_supports_classic: bool = False,
        api_version: ApiVersion = "classic",
        post_filter: CastPostFilter | None = None,
    ) -> EpiDataCall:
        base_url = self._cast_base_url if api_version == "cast" else self._base_url
        return EpiDataCall(
            base_url,
            self._session,
            endpoint,
            params,
            meta,
            only_supports_classic,
            self.use_cache,
            self.cache_max_age_days,
            api_version=api_version,
            post_filter=post_filter,
        )

    def epidata_meta(self, source: str) -> Any:
        """Fetch source-level metadata from the CAST API.

        Returns the parsed JSON (a list of signal/geo descriptors) for `source`.
        """
        url = add_endpoint_to_url(self._cast_base_url, "metadata/")
        response = _request_with_retry(
            url,
            {"source": source},
            self._session,
            stream=False,
            api_version="cast",
        )
        response.raise_for_status()
        return response.json()

    def pvt_cdc(
        self,
        auth: str,
        locations: StringParam,
        epiweeks: EpiRangeParam = "*",
    ) -> EpiDataCall:
        """Fetch CDC total and by topic webpage visits.

        API docs: <https://cmu-delphi.github.io/delphi-epidata/api/cdc.html>

        Parameters
        ----------
        auth : str
            Private API key.
        locations : StringParam
            Geographic locations to return. Supports a single string or a sequence of strings.
            See `Geographic Codes <https://cmu-delphi.github.io/delphi-epidata/api/geographic_codes.html#us-states>`__.
        epiweeks : EpiRangeParam
            Epiweeks to fetch. Supports :class:`~epidatpy.EpiRange` and defaults to all ("*") weeks.
            Format as ``epirange(startweek, endweek)``, where startweek and endweek are of the form
            YYYYWW (string or numeric).
        """
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
        state: str | None = None,
        ccn: str | None = None,
        city: str | None = None,
        zip: str | None = None,
        fips_code: str | None = None,
    ) -> EpiDataCall:
        """Helper for finding COVID hospitalization facilities.

        API docs: <https://cmu-delphi.github.io/delphi-epidata/api/covid_hosp_facility_lookup.html>

        Obtains unique identifiers and other metadata for COVID hospitalization
        facilities of interest. This is a companion endpoint to the
        :meth:`pub_covid_hosp_facility` endpoint.

        Only one location argument needs to be specified. Combinations of the
        arguments are not currently supported.

        Parameters
        ----------
        state : str, optional
            Two-letter state abbreviation.
        ccn : str, optional
            CMS Certification Number.
        city : str, optional
            City name.
        zip : str, optional
            5-digit zip code.
        fips_code : str, optional
            A 5-digit FIPS county code, zero-padded.
        """
        if all(v is None for v in (state, ccn, city, zip, fips_code)):
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
        publication_dates: EpiRangeParam | None = None,
    ) -> EpiDataCall:
        """Fetch COVID hospitalizations by facility.

        API docs: <https://cmu-delphi.github.io/delphi-epidata/api/covid_hosp_facility.html>

        Obtains the COVID-19 reported patient impact and hospital capacity data by
        facility. This dataset is provided by the US Department of Health & Human
        Services. The companion function :meth:`pub_covid_hosp_facility_lookup` can be
        used to look up facility identifiers in a variety of ways.

        Starting October 1, 2022, some facilities are only required to report
        annually.

        Parameters
        ----------
        hospital_pks : StringParam
            Unique identifiers for hospitals of interest. Supports a single string or a sequence of strings.
        collection_weeks : EpiRangeParam
            Weekly data collection periods to fetch. Supports :class:`~epidatpy.EpiRange` and defaults to all
            ("*") weeks.
            Note: This parameter expects dates in YYYY-MM-DD or YYYYMMDD format.
            If provided as ``Week``, they will be converted to the starting day of the week.
        publication_dates : EpiRangeParam, optional
            Publication dates to fetch. Supports :class:`~epidatpy.EpiRange`. Format as YYYY-MM-DD (string or numeric).
        """
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
        issues: EpiRangeParam | None = None,
        as_of: None | int | str = None,
    ) -> EpiDataCall:
        """Fetch COVID hospitalizations by state.

        API docs: <https://cmu-delphi.github.io/delphi-epidata/api/covid_hosp.html>

        Obtains the COVID-19 reported patient impact and hospital capacity data by
        state. This dataset is provided by the US Department of Health & Human
        Services.

        Starting October 1, 2022, some facilities are only required to report
        annually.

        Parameters
        ----------
        states : StringParam
            Geographic locations to return, formatted as two-letter state abbreviations.
            Supports a single string or a sequence of strings.
        dates : EpiRangeParam
            Dates to fetch. Supports :class:`~epidatpy.EpiRange` and defaults to all ("*") dates.
            Format as ``epirange(start, end)``, where start and end are of the form YYYYMMDD
            (string or numeric).
        issues : EpiRangeParam, optional
            Range or list of issue dates to fetch. Supports :class:`~epidatpy.EpiRange`. Format as YYYYMMDD.
            Mutually exclusive with `as_of`.
        as_of : Union[int, str], optional
            Fetch data as it was known as of this date. Format as YYYYMMDD.
            Mutually exclusive with `issues`.
        """
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

    def pub_covidcast_meta(self) -> EpiDataCall:
        """Fetch COVIDcast surveillance stream metadata.

        API docs: <https://cmu-delphi.github.io/delphi-epidata/api/covidcast_meta.html>

        Obtains a data frame of metadata describing all publicly available data
        streams from the COVIDcast API. See the `data source and signals
        documentation
        <https://cmu-delphi.github.io/delphi-epidata/api/covidcast_signals.html>`_
        for descriptions of the available sources.

        Returns
        -------
        EpiDataCall
            A ``EpiDataCall`` object containing the following information:

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
                example, if ``geo_type`` is county, the number of counties for which this
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
        geo_values: str | Sequence[str] = "*",
        time_values: EpiRangeParam = "*",
        as_of: None | str | int = None,
        issues: EpiRangeParam | None = None,
        lag: int | None = None,
    ) -> EpiDataCall:
        """Fetch Delphi's COVID-19 Surveillance Streams.

        API docs: <https://cmu-delphi.github.io/delphi-epidata/api/covidcast_signals.html>

        The primary endpoint for fetching COVID-19 data, providing access to a wide
        variety of signals from a wide variety of sources. Delphi's `COVIDcast public
        dashboard <https://delphi.cmu.edu/covidcast/>`_ is powered by this endpoint.

        Parameters
        ----------
        data_source : str
            The name of the data source to query.
            See `Covidcast Signals <https://cmu-delphi.github.io/delphi-epidata/api/covidcast_signals.html>`__.
        signals : StringParam
            The signals to query from a specific source.
            See `Covidcast Signals <https://cmu-delphi.github.io/delphi-epidata/api/covidcast_signals.html>`__.
        geo_type : GeoType
            The geographic resolution of the data.
            See `Covidcast Geography <https://cmu-delphi.github.io/delphi-epidata/api/covidcast_geography.html>`__.
        time_type : TimeType
            The temporal resolution of the data (either "day" or "week").
        geo_values : Union[str, Sequence[str]]
            The geographic locations to return. Supports a single string, a sequence of strings,
            or defaults to all locations ("*").
            See `Covidcast Geography <https://cmu-delphi.github.io/delphi-epidata/api/covidcast_geography.html>`__.
        time_values : EpiRangeParam
            Temporal points to fetch. Supports :class:`~epidatpy.EpiRange` and defaults to all ("*") dates/weeks.
            Format as ``epirange(start, end)``, where start and end are of the form YYYY-MM-DD
            or YYYYWW depending on the ``time_type``.
        as_of : Union[str, int], optional
            Fetch data as it was known as of this date.
            Mutually exclusive with ``issues`` and ``lag``.
        issues : EpiRangeParam, optional
            Range or list of issue dates to fetch.
            Mutually exclusive with ``as_of`` and ``lag``.
        lag : int, optional
            Number of days between the observation and its publication.
            Mutually exclusive with ``as_of`` and ``issues``.
        """
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

    def pub_delphi(self, system: str, epiweek: int | str) -> EpiDataCall:
        """Fetch Delphi's ILINet outpatient doctor visits forecasts.

        API docs: <https://cmu-delphi.github.io/delphi-epidata/api/delphi.html>

        Parameters
        ----------
        system : str
            The name of the forecast system.
            See `Forecasting Systems
            <https://cmu-delphi.github.io/delphi-epidata/api/delphi.html#forecasting-systems>`_.
        epiweek : Union[int, str]
            Epiweek to fetch. Does not support multiple dates.
            Make separate calls to fetch data for multiple epiweeks.
        """
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

    def pub_dengue_nowcast(self, locations: StringParam, epiweeks: EpiRangeParam = "*") -> EpiDataCall:
        """Fetch Delphi's PAHO dengue nowcasts (North and South America).

        API docs: <https://cmu-delphi.github.io/delphi-epidata/api/dengue_nowcast.html>

        Parameters
        ----------
        locations : StringParam
            Geographic locations to return. Supports a single string or a sequence of strings.
            See `Countries and Territories in the Americas
            <https://cmu-delphi.github.io/delphi-epidata/api/geographic_codes.html#countries-and-territories-in-the-americas>`__.
        epiweeks : EpiRangeParam
            Epiweeks to fetch. Supports :class:`~epidatpy.EpiRange` and defaults to all ("*") weeks.
            Format as ``epirange(startweek, endweek)``, where startweek and endweek are of the form
            YYYYWW (string or numeric).
        """
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
    ) -> EpiDataCall:
        """Fetch PAHO dengue digital surveillance sensors (North and South America).

        API docs: <https://cmu-delphi.github.io/delphi-epidata/api/dengue_sensors.html>

        Parameters
        ----------
        auth : str
            Private API key.
        names : StringParam
            Sensor names to fetch.
            See `Dengue Sensors Indicators
            <https://cmu-delphi.github.io/delphi-epidata/api/dengue_sensors.html#indicators>`__.
        locations : StringParam
            List of countries in the Americas to fetch.
            See `Countries and Territories in the Americas
            <https://cmu-delphi.github.io/delphi-epidata/api/geographic_codes.html#countries-and-teritories-in-the-americas>`_.
        epiweeks : EpiRangeParam
            Epiweeks to fetch. Supports :class:`~epidatpy.EpiRange` and defaults to all ("*") weeks.
            Format as ``epirange(startweek, endweek)``, where startweek and endweek are of the form
            YYYYWW (string or numeric).
        """
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
        issues: EpiRangeParam | None = None,
        lag: int | None = None,
    ) -> EpiDataCall:
        """Fetch ECDC ILI incidence (Europe).

        API docs: <https://cmu-delphi.github.io/delphi-epidata/api/ecdc_ili.html>

        Obtain information on influenza-like-illness from the European Centre for
        Disease Prevention and Control.

        Parameters
        ----------
        regions : StringParam
            List of European countries to fetch.
            See `European Countries
            <https://cmu-delphi.github.io/delphi-epidata/api/geographic_codes.html#european-countries>`_.
        epiweeks : EpiRangeParam
            Epiweeks to fetch. Supports :class:`~epidatpy.EpiRange` and defaults to all ("*") weeks.
            Format as ``epirange(startweek, endweek)``, where startweek and endweek are of the form
            YYYYWW (string or numeric).
        issues : EpiRangeParam, optional
            Range or list of issue dates to fetch. Supports :class:`~epidatpy.EpiRange`.
            Mutually exclusive with ``lag``.
        lag : int, optional
            Number of days between the observation and its publication.
            Mutually exclusive with ``issues``.
        """
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
        issues: EpiRangeParam | None = None,
        lag: int | None = None,
    ) -> EpiDataCall:
        """Fetch CDC FluSurv flu hospitalizations.

        API docs: <https://cmu-delphi.github.io/delphi-epidata/api/flusurv.html>

        Obtain information on influenza hospitalization rates from the Center of Disease
        Control.

        See also <https://gis.cdc.gov/GRASP/Fluview/FluHospRates.html>.

        Parameters
        ----------
        locations : StringParam
            List of locations to fetch.
            See `FluSurv Locations
            <https://cmu-delphi.github.io/delphi-epidata/api/geographic_codes.html#flusurv-locations>`_.
        epiweeks : EpiRangeParam
            Epiweeks to fetch. Supports :class:`~epidatpy.EpiRange` and defaults to all ("*") weeks.
            Format as ``epirange(startweek, endweek)``, where startweek and endweek are of the form
            YYYYWW (string or numeric).
        issues : EpiRangeParam, optional
            Range or list of issue dates to fetch. Supports `epirange()`.
            Mutually exclusive with ``lag``.
        lag : int, optional
            Number of days between the observation and its publication.
            Mutually exclusive with ``issues``.
        """
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
                EpidataFieldInfo("rate_age_5", EpidataFieldType.float),
                EpidataFieldInfo("rate_age_6", EpidataFieldType.float),
                EpidataFieldInfo("rate_age_7", EpidataFieldType.float),
                EpidataFieldInfo("rate_age_18t29", EpidataFieldType.float),
                EpidataFieldInfo("rate_age_30t39", EpidataFieldType.float),
                EpidataFieldInfo("rate_age_40t49", EpidataFieldType.float),
                EpidataFieldInfo("rate_age_5t11", EpidataFieldType.float),
                EpidataFieldInfo("rate_age_12t17", EpidataFieldType.float),
                EpidataFieldInfo("rate_age_lt18", EpidataFieldType.float),
                EpidataFieldInfo("rate_age_gte18", EpidataFieldType.float),
                EpidataFieldInfo("rate_age_0tlt1", EpidataFieldType.float),
                EpidataFieldInfo("rate_age_1t4", EpidataFieldType.float),
                EpidataFieldInfo("rate_age_gte75", EpidataFieldType.float),
                EpidataFieldInfo("rate_race_white", EpidataFieldType.float),
                EpidataFieldInfo("rate_race_black", EpidataFieldType.float),
                EpidataFieldInfo("rate_race_hisp", EpidataFieldType.float),
                EpidataFieldInfo("rate_race_asian", EpidataFieldType.float),
                EpidataFieldInfo("rate_race_natamer", EpidataFieldType.float),
                EpidataFieldInfo("rate_sex_male", EpidataFieldType.float),
                EpidataFieldInfo("rate_sex_female", EpidataFieldType.float),
                EpidataFieldInfo("rate_flu_a", EpidataFieldType.float),
                EpidataFieldInfo("rate_flu_b", EpidataFieldType.float),
                EpidataFieldInfo("season", EpidataFieldType.text),
            ],
        )

    def pub_fluview_clinical(
        self,
        regions: StringParam,
        epiweeks: EpiRangeParam = "*",
        issues: EpiRangeParam | None = None,
        lag: int | None = None,
    ) -> EpiDataCall:
        """Fetch CDC FluView flu tests from clinical labs.

        API docs: <https://cmu-delphi.github.io/delphi-epidata/api/fluview_clinical.html>

        Parameters
        ----------
        regions : StringParam
            List of regions to fetch.
            See `US Regions and States
            <https://cmu-delphi.github.io/delphi-epidata/api/geographic_codes.html#us-regions-and-states>`__.
        epiweeks : EpiRangeParam, default "*"
            Epiweeks to fetch. Supports :class:`~epidatpy.EpiRange` and defaults to all ("*") weeks.
            Format as ``epirange(startweek, endweek)``, where startweek and endweek are of the form
            YYYYWW (string or numeric).
        issues : EpiRangeParam, optional
            Range or list of issue dates to fetch. Supports :class:`~epidatpy.EpiRange`.
            Mutually exclusive with ``lag``.
        lag : int, optional
            Number of days between the observation and its publication.
            Mutually exclusive with ``issues``.
        """
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

    def pub_fluview_meta(self) -> EpiDataCall:
        """Fetch Metadata for the FluView endpoint.

        API docs: <https://cmu-delphi.github.io/delphi-epidata/api/fluview_meta.html>
        """
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
        issues: EpiRangeParam | None = None,
        lag: int | None = None,
        auth: str | None = None,
    ) -> EpiDataCall:
        """Fetch CDC FluView ILINet outpatient doctor visits.

        API docs: <https://cmu-delphi.github.io/delphi-epidata/api/fluview.html>

        Obtains information on outpatient inluenza-like-illness (ILI) from U.S.
        Outpatient Influenza-like Illness Surveillance Network (ILINet).

        See also <https://gis.cdc.gov/grasp/fluview/fluportaldashboard.html>.

        Parameters
        ----------
        regions : StringParam
            List of regions to fetch.
            See `US Regions and States
            <https://cmu-delphi.github.io/delphi-epidata/api/geographic_codes.html#us-regions-and-states>`__
            and `FluView Cities
            <https://cmu-delphi.github.io/delphi-epidata/api/geographic_codes.html#fluview-cities>`__.
        epiweeks : EpiRangeParam
            Epiweeks to fetch. Supports :class:`~epidatpy.EpiRange` and defaults to all ("*") weeks.
            Format as ``epirange(startweek, endweek)``, where startweek and endweek are of the form
            YYYYWW (string or numeric).
        issues : EpiRangeParam, optional
            Range or list of issue dates to fetch. Supports :class:`~epidatpy.EpiRange`.
            Mutually exclusive with ``lag``.
        lag : int, optional
            Number of days between the observation and its publication.
            Mutually exclusive with ``issues``.
        auth : str, optional
            Private API key.
        """
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

    def pub_gft(self, locations: StringParam, epiweeks: EpiRangeParam = "*") -> EpiDataCall:
        """Fetch Google Flu Trends flu search volume.

        API docs: <https://cmu-delphi.github.io/delphi-epidata/api/gft.html>

        Obtains estimates of inluenza activity based on volume of certain search
        queries from Google.

        Google has discontinued Flu Trends and this is now a static endpoint.

        Parameters
        ----------
        locations : StringParam
            List of locations to fetch.
            See `Geographic Codes
            <https://cmu-delphi.github.io/delphi-epidata/api/geographic_codes.html#us-states>`__.
        epiweeks : EpiRangeParam
            Epiweeks to fetch. Supports :class:`~epidatpy.EpiRange` and defaults to all ("*") weeks.
            Format as ``epirange(startweek, endweek)``, where startweek and endweek are of the form
            YYYYWW (string or numeric).
        """
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
    ) -> EpiDataCall:
        """Fetch Google Health Trends data.

        API docs: <https://cmu-delphi.github.io/delphi-epidata/api/ght.html>

        Requires a private API key.

        Parameters
        ----------
        auth : str
            Private API key.
        locations : StringParam
            List of locations to fetch.
            See `Geographic Codes
            <https://cmu-delphi.github.io/delphi-epidata/api/geographic_codes.html#us-states>`__.
        epiweeks : EpiRangeParam, default "*"
            Epiweeks to fetch. Supports :class:`~epidatpy.EpiRange` and defaults to all ("*") weeks.
            Format as ``epirange(startweek, endweek)``, where startweek and endweek are of the form
            YYYYWW (string or numeric).
        query : str, default ""
            GHT search query.
            See `Valid Queries <https://cmu-delphi.github.io/delphi-epidata/api/ght.html#valid-queries>`__.
        """
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
        issues: EpiRangeParam | None = None,
        lag: int | None = None,
    ) -> EpiDataCall:
        """Fetch KCDC ILI incidence (Korea).

        API docs: <https://cmu-delphi.github.io/delphi-epidata/api/kcdc_ili.html>

        Obtain information on influenza-like-illness from the Korea Centers for
        Disease Control and Prevention (KCDC).

        The list of location argument can be found in
        <https://github.com/cmu-delphi/delphi-epidata/blob/main/labels/kcdc_regions.txt>.

        Parameters
        ----------
        regions : StringParam
            List of regions to fetch.
            See `Republic of Korea
            <https://cmu-delphi.github.io/delphi-epidata/api/geographic_codes.html#republic-of-korea>`__.
        epiweeks : EpiRangeParam
            Epiweeks to fetch. Supports :class:`~epidatpy.EpiRange` and defaults to all ("*") weeks.
            Format as ``epirange(startweek, endweek)``, where startweek and endweek are of the form
            YYYYWW (string or numeric).
        issues : EpiRangeParam, optional
            Range or list of issue dates to fetch. Supports `epirange()`.
            Mutually exclusive with ``lag``.
        lag : int, optional
            Number of days between the observation and its publication.
            Mutually exclusive with ``issues``.
        """
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

    def pvt_meta_norostat(self, auth: str) -> EpiDataCall:
        """Fetch NoroSTAT metadata.

        API docs: <https://cmu-delphi.github.io/delphi-epidata/api/norostat_meta.html>

        Requires a private API key.

        Parameters
        ----------
        auth : str
            Private API key.
        """
        return self._create_call(
            "meta_norostat/",
            {"auth": auth},
            only_supports_classic=True,
        )

    def pub_meta(self) -> EpiDataCall:
        """Fetch API metadata.

        API docs: <https://cmu-delphi.github.io/delphi-epidata/api/meta.html>
        """
        return self._create_call(
            "meta/",
            {},
            only_supports_classic=True,
        )

    def pub_nidss_dengue(self, locations: StringParam, epiweeks: EpiRangeParam = "*") -> EpiDataCall:
        """Fetch NIDSS dengue data (Taiwan).

        API docs: <https://cmu-delphi.github.io/delphi-epidata/api/nidss_dengue.html>

        Parameters
        ----------
        locations : StringParam
            List of Taiwan locations to fetch.
            See `Taiwan Locations
            <https://cmu-delphi.github.io/delphi-epidata/api/geographic_codes.html#nidss>`_.
        epiweeks : EpiRangeParam
            Epiweeks to fetch. Supports :class:`~epidatpy.EpiRange` and defaults to all ("*") weeks.
            Format as ``epirange(startweek, endweek)``, where startweek and endweek are of the form
            YYYYWW (string or numeric).
        """
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
        issues: EpiRangeParam | None = None,
        lag: int | None = None,
    ) -> EpiDataCall:
        """Fetch NIDSS flu data (Taiwan).

        API docs: <https://cmu-delphi.github.io/delphi-epidata/api/nidss_flu.html>

        Parameters
        ----------
        regions : StringParam
            List of Taiwan locations to fetch.
            See `Taiwan Locations
            <https://cmu-delphi.github.io/delphi-epidata/api/geographic_codes.html#nidss>`_.
        epiweeks : EpiRangeParam
            Epiweeks to fetch. Supports :class:`~epidatpy.EpiRange` and defaults to all ("*") weeks.
            Format as ``epirange(startweek, endweek)``, where startweek and endweek are of the form
            YYYYWW (string or numeric).
        issues : EpiRangeParam, optional
            Range or list of issue dates to fetch. Supports `epirange()`.
            Mutually exclusive with ``lag``.
        lag : int, optional
            Number of days between the observation and its publication.
            Mutually exclusive with ``issues``.
        """
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

    def pvt_norostat(self, auth: str, location: str, epiweeks: EpiRangeParam = "*") -> EpiDataCall:
        """Fetch NoroSTAT data (point data, no min/max).

        API docs: <https://cmu-delphi.github.io/delphi-epidata/api/norostat.html>

        Requires a private API key.

        Parameters
        ----------
        auth : str
            Private API key.
        location : str
            Locations to fetch. Only a specific list of
            full state names are permitted. See the ``locations`` column in the
            output of :meth:`pvt_meta_norostat` for the allowed values.
        epiweeks : EpiRangeParam
            Epiweeks to fetch. Supports :class:`~epidatpy.EpiRange` and defaults to all ("*") weeks.
            Format as ``epirange(startweek, endweek)``, where startweek and endweek are of the form
            YYYYWW (string or numeric).
        """
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

    def pub_nowcast(self, locations: StringParam, epiweeks: EpiRangeParam = "*") -> EpiDataCall:
        """Fetch Delphi's wILI nowcast.

        API docs: <https://cmu-delphi.github.io/delphi-epidata/api/ili_nearby_nowcast.html>

        Parameters
        ----------
        locations : StringParam
            List of locations to fetch.
            See `Geographic Codes
            <https://cmu-delphi.github.io/delphi-epidata/api/geographic_codes.html#us-states>`__.
        epiweeks : EpiRangeParam
            Epiweeks to fetch. Supports :class:`~epidatpy.EpiRange` and defaults to all ("*") weeks.
            Format as ``epirange(startweek, endweek)``, where startweek and endweek are of the form
            YYYYWW (string or numeric).
        """
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
        issues: EpiRangeParam | None = None,
        lag: int | None = None,
    ) -> EpiDataCall:
        """Fetch PAHO Dengue data.

        API docs: <https://cmu-delphi.github.io/delphi-epidata/api/paho_dengue.html>

        Parameters
        ----------
        regions : StringParam
            List of American countries and territories to fetch.
            See `Countries and Territories in the Americas
            <https://cmu-delphi.github.io/delphi-epidata/api/geographic_codes.html#countries-and-territories-in-the-americas>`__.

        epiweeks : EpiRangeParam
            Epiweeks to fetch. Supports :class:`~epidatpy.EpiRange` and defaults to all ("*") weeks.
            Format as ``epirange(startweek, endweek)``, where startweek and endweek are of the form
            YYYYWW (string or numeric).
        issues : EpiRangeParam, optional
            Range or list of issue dates to fetch. Supports `epirange()`.
            Mutually exclusive with ``lag``.
        lag : int, optional
            Number of days between the observation and its publication.
            Mutually exclusive with ``issues``.
        """
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

    def pvt_quidel(self, auth: str, locations: StringParam, epiweeks: EpiRangeParam = "*") -> EpiDataCall:
        """Fetch Quidel data.

        API docs: <https://cmu-delphi.github.io/delphi-epidata/api/quidel.html>

        Requires a private API key.

        Parameters
        ----------
        auth : str
            Private API key.
        locations : StringParam
            List of locations to fetch.
            See `Geographic Codes
            <https://cmu-delphi.github.io/delphi-epidata/api/geographic_codes.html#us-states>`__.
        epiweeks : EpiRangeParam
            Epiweeks to fetch. Supports :class:`~epidatpy.EpiRange` and defaults to all ("*") weeks.
            Format as ``epirange(startweek, endweek)``, where startweek and endweek are of the form
            YYYYWW (string or numeric).
        """
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
    ) -> EpiDataCall:
        """Fetch Delphi's digital surveillance sensors.

        API docs: <https://cmu-delphi.github.io/delphi-epidata/api/digital_surveillance_sensors.html>

        Requires a private API key.

        Parameters
        ----------
        auth : str
            Private API key.
        names : StringParam
            Sensor names to fetch.
            See `Data Sources <https://cmu-delphi.github.io/delphi-epidata/api/sensors.html#data-sources>`_.
        locations : StringParam
            List of locations to fetch.
            See `Geographic Codes <https://cmu-delphi.github.io/delphi-epidata/api/geographic_codes.html#us-states>`__.
        epiweeks : EpiRangeParam
            Epiweeks to fetch. Supports :class:`~epidatpy.EpiRange` and defaults to all ("*") weeks.
            Format as ``epirange(startweek, endweek)``, where startweek and endweek are of the form
            YYYYWW (string or numeric).
        """
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
    ) -> EpiDataCall:
        """Fetch HealthTweets data.

        API docs: <https://cmu-delphi.github.io/delphi-epidata/api/twitter.html>

        Requires a private API key.

        Parameters
        ----------
        auth : str
            Private API key.
        locations : StringParam
            List of locations to fetch.
            See `Geographic Codes <https://cmu-delphi.github.io/delphi-epidata/api/geographic_codes.html#us-states>`__.
        time_type : Literal["day", "week"]
            The temporal resolution to use ("day" or "week").
        time_values : EpiRangeParam, default "*"
            Temporal points to fetch. Supports :class:`~epidatpy.EpiRange` and defaults to all ("*") dates/weeks.
            Format as ``epirange(start, end)``, where start and end are of the form YYYY-MM-DD
            or YYYYWW depending on the ``time_type``.
        """
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
        hours: IntParam | None = None,
        language: str = "en",
    ) -> EpiDataCall:
        """Fetch Wikipedia access data.

        API docs: <https://cmu-delphi.github.io/delphi-epidata/api/wiki.html>

        Parameters
        ----------
        articles : StringParam
            The Wikipedia article(s) to fetch. Supports a single string or a sequence of strings.
            See `Available Articles
            <https://cmu-delphi.github.io/delphi-epidata/api/wiki.html#available-articles>`_.
        time_type : Literal["day", "week"]
            The temporal resolution to use ("day" or "week").
        time_values : EpiRangeParam, default "*"
            Temporal points to fetch. Supports :class:`~epidatpy.EpiRange` and defaults to all ("*") dates/weeks.
            Format as ``epirange(start, end)``, where start and end are of the form YYYY-MM-DD
            or YYYYWW depending on the ``time_type``.
        hours : IntParam, optional
            A list of hours to include.
        language : str, default "en"
            Two-letter language code.
        """
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

    def epidata_snapshot(
        self,
        source: str,
        signals: StringParam,
        geo_type: str,
        geo_values: StringParam = "*",
        reference_time: EpiRangeParam = "*",
        fill_method: str | None = None,
        snapshot_date: str | date | int | None = None,
    ) -> EpiDataCall:
        """Fetch a snapshot of CAST-API signals as they appeared on `snapshot_date`.

        `snapshot_date=None` returns the latest available version. `geo_values`
        and `reference_time` are filtered locally after the API call.
        """
        if snapshot_date is None:
            snapshot_date_str: str | None = None
        elif isinstance(snapshot_date, date):
            snapshot_date_str = snapshot_date.strftime("%Y-%m-%d")
        else:
            parsed = parse_api_date(snapshot_date)
            if parsed is None:
                raise InvalidArgumentException(f"Invalid `snapshot_date` value: {snapshot_date!r}")
            snapshot_date_str = parsed.strftime("%Y-%m-%d")
        signal_str = format_list(signals)

        return self._create_call(
            "snapshot/",
            {
                "source": source,
                "signal": signal_str,
                "geo_type": geo_type,
                "fill_method": fill_method,
                "snapshot_date": snapshot_date_str,
            },
            _cast_signal_fields(),
            api_version="cast",
            post_filter=(geo_values, reference_time, None),
        )

    def epidata_archive(
        self,
        source: str,
        signals: StringParam,
        geo_type: str,
        geo_values: StringParam = "*",
        reference_time: EpiRangeParam = "*",
        fill_method: str | None = None,
        report_time: str | date | EpiRange | None = "*",
    ) -> EpiDataCall:
        """Fetch the full report-time history of CAST-API signals.

        `report_time` accepts an exact date, an operator-prefixed string
        (e.g. ``"<2025-10-16"``), or an :class:`EpiRange`. ``"*"`` (default)
        requests all report times. `geo_values`, `reference_time`, and the
        EpiRange lower bound are filtered locally after the API call.
        """
        report_time_str = validate_report_time_query(report_time)

        signal_str = format_list(signals)

        return self._create_call(
            "archive/",
            {
                "source": source,
                "signal": signal_str,
                "geo_type": geo_type,
                "fill_method": fill_method,
                "report_time": report_time_str,
            },
            _cast_signal_fields(),
            api_version="cast",
            post_filter=(
                geo_values,
                reference_time,
                report_time if isinstance(report_time, EpiRange) else None,
            ),
        )

    def epidata(
        self,
        source: str,
        signals: StringParam,
        geo_type: str,
        geo_values: StringParam = "*",
        reference_time: EpiRangeParam = "*",
        fill_method: str | None = None,
        snapshot_date: str | date | int | None = None,
        report_time: str | date | EpiRange | None = None,
    ) -> EpiDataCall:
        """Router for CAST-API queries.

        Dispatches to :meth:`epidata_archive` when ``report_time`` is
        supplied or ``snapshot_date == "*"``; otherwise to
        :meth:`epidata_snapshot`. ``report_time`` and ``snapshot_date``
        are mutually exclusive.
        """
        if report_time is not None and snapshot_date is not None:
            raise InvalidArgumentException("`report_time` and `snapshot_date` are mutually exclusive")

        if report_time is not None or snapshot_date == "*":
            return self.epidata_archive(
                source=source,
                signals=signals,
                geo_type=geo_type,
                geo_values=geo_values,
                reference_time=reference_time,
                fill_method=fill_method,
                report_time=report_time if report_time is not None else "*",
            )
        return self.epidata_snapshot(
            source=source,
            signals=signals,
            geo_type=geo_type,
            geo_values=geo_values,
            reference_time=reference_time,
            fill_method=fill_method,
            snapshot_date=snapshot_date,
        )


def _cast_signal_fields() -> Sequence[EpidataFieldInfo]:
    """Fields for CAST snapshot/archive responses; extras are skipped if absent."""
    return [
        EpidataFieldInfo("signal", EpidataFieldType.text),
        EpidataFieldInfo("report_time", EpidataFieldType.date),
        EpidataFieldInfo("geo_type", EpidataFieldType.text),
        EpidataFieldInfo("geo_value", EpidataFieldType.text),
        EpidataFieldInfo("fill_method", EpidataFieldType.text),
        EpidataFieldInfo("reference_time", EpidataFieldType.date),
        EpidataFieldInfo("value", EpidataFieldType.float),
        # Source-specific extras (skipped per-response if not present):
        EpidataFieldInfo("age_group", EpidataFieldType.text),  # pophive
        EpidataFieldInfo("nwss_source", EpidataFieldType.text),  # nwss
        EpidataFieldInfo("sample_index", EpidataFieldType.text),  # nwss
        EpidataFieldInfo("pcr_target", EpidataFieldType.text),  # nwss
    ]
