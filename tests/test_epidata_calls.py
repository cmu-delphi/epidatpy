"""
Requirements to run these:
- DELPHI_EPIDATA_KEY environment variable is set https://api.delphi.cmu.edu/epidata/admin/registration_form
- it has access to the private endpoints being tested
"""

import os

import pytest

from epidatpy.request import Epidata, EpiRange

auth = os.environ.get("DELPHI_EPIDATA_KEY", "")
secret_cdc = os.environ.get("SECRET_API_AUTH_CDC", "")
secret_fluview = os.environ.get("SECRET_API_AUTH_FLUVIEW", "")
secret_ght = os.environ.get("SECRET_API_AUTH_GHT", "")
secret_norostat = os.environ.get("SECRET_API_AUTH_NOROSTAT", "")
secret_quidel = os.environ.get("SECRET_API_AUTH_QUIDEL", "")
secret_sensors = os.environ.get("SECRET_API_AUTH_SENSORS", "")
secret_twitter = os.environ.get("SECRET_API_AUTH_TWITTER", "")


@pytest.mark.skipif(not auth, reason="DELPHI_EPIDATA_KEY not available.")
class TestEpidataCalls:
    @pytest.mark.skipif(not secret_cdc, reason="CDC key not available.")
    def test_pvt_cdc(self) -> None:
        apicall = Epidata.pvt_cdc(auth=secret_cdc, locations="fl,ca", epiweeks=EpiRange(201501, 201601))
        data = apicall.df()
        assert len(data) > 0
        assert str(data["location"].dtype) == "string"
        assert str(data["epiweek"].dtype) == "string"
        assert str(data["num1"].dtype) == "Int64"
        assert str(data["num2"].dtype) == "Int64"
        assert str(data["num3"].dtype) == "Int64"
        assert str(data["num4"].dtype) == "Int64"
        assert str(data["num5"].dtype) == "Int64"
        assert str(data["num6"].dtype) == "Int64"
        assert str(data["num7"].dtype) == "Int64"
        assert str(data["num8"].dtype) == "Int64"
        assert str(data["total"].dtype) == "Int64"
        assert str(data["value"].dtype) == "Float64"

    def test_pub_covid_hosp_facility_lookup(self) -> None:
        apicall = Epidata.pub_covid_hosp_facility_lookup(state="fl")
        data = apicall.df()
        assert len(data) > 0

        apicall = Epidata.pub_covid_hosp_facility_lookup(city="southlake")
        data = apicall.df()
        assert len(data) > 0
        assert str(data["hospital_pk"].dtype) == "string"
        assert str(data["state"].dtype) == "string"
        assert str(data["ccn"].dtype) == "string"
        assert str(data["hospital_name"].dtype) == "string"
        assert str(data["address"].dtype) == "string"
        assert str(data["city"].dtype) == "string"
        assert str(data["zip"].dtype) == "string"
        assert str(data["hospital_subtype"].dtype) == "string"
        assert str(data["fips_code"].dtype) == "string"
        assert str(data["is_metro_micro"].dtype) == "Int64"

    @pytest.mark.filterwarnings("ignore:`collection_weeks` is in week format")
    def test_pub_covid_hosp_facility(self) -> None:
        apicall = Epidata.pub_covid_hosp_facility(hospital_pks="100075", collection_weeks=EpiRange(20200101, 20200501))
        data = apicall.df()
        assert len(data) > 0
        assert str(data["hospital_pk"].dtype) == "string"
        assert str(data["state"].dtype) == "string"
        assert str(data["ccn"].dtype) == "string"
        assert str(data["hospital_name"].dtype) == "string"
        assert str(data["address"].dtype) == "string"
        assert str(data["city"].dtype) == "string"
        assert str(data["zip"].dtype) == "string"
        assert str(data["hospital_subtype"].dtype) == "string"
        assert str(data["fips_code"].dtype) == "string"
        assert str(data["publication_date"].dtype) == "datetime64[ns]"
        assert str(data["collection_week"].dtype) == "datetime64[ns]"
        assert str(data["is_metro_micro"].dtype) == "bool"

        apicall2 = Epidata.pub_covid_hosp_facility(hospital_pks="100075", collection_weeks=EpiRange(202001, 202030))
        data2 = apicall2.df()
        assert len(data2) > 0

    def test_pub_covid_hosp_state_timeseries(self) -> None:
        apicall = Epidata.pub_covid_hosp_state_timeseries(states="fl", dates=EpiRange(20200101, 20200501))
        data = apicall.df()
        assert len(data) > 0
        assert str(data["state"].dtype) == "string"
        assert str(data["issue"].dtype) == "datetime64[ns]"
        assert str(data["date"].dtype) == "datetime64[ns]"

    def test_pub_covidcast_meta(self) -> None:
        apicall = Epidata.pub_covidcast_meta()
        data = apicall.df()

        assert len(data) > 0
        assert str(data["data_source"].dtype) == "string"
        assert str(data["signal"].dtype) == "string"
        assert str(data["time_type"].dtype) == "category"
        assert str(data["min_time"].dtype) == "string"
        assert str(data["max_time"].dtype) == "datetime64[ns]"
        assert str(data["num_locations"].dtype) == "Int64"
        assert str(data["min_value"].dtype) == "Float64"
        assert str(data["max_value"].dtype) == "Float64"
        assert str(data["mean_value"].dtype) == "Float64"
        assert str(data["stdev_value"].dtype) == "Float64"
        assert str(data["last_update"].dtype) == "Int64"
        assert str(data["max_issue"].dtype) == "datetime64[ns]"
        assert str(data["min_lag"].dtype) == "Int64"
        assert str(data["max_lag"].dtype) == "Int64"

    def test_pub_covidcast(self) -> None:
        apicall = Epidata.pub_covidcast(
            data_source="jhu-csse",
            signals="confirmed_7dav_incidence_prop",
            geo_type="state",
            time_type="day",
            geo_values=["ca", "fl"],
            time_values=EpiRange(20200601, 20200801),
        )
        data = apicall.df()

        assert len(data) > 0

        apicall = Epidata.pub_covidcast(
            data_source="jhu-csse",
            signals="confirmed_7dav_incidence_prop",
            geo_type="state",
            time_type="day",
            geo_values="*",
            time_values=EpiRange(20200601, 20200801),
        )
        data = apicall.df()

        print(data.dtypes)

        assert str(data["source"].dtype) == "string"
        assert str(data["signal"].dtype) == "string"
        assert str(data["geo_type"].dtype) == "category"
        assert str(data["geo_value"].dtype) == "string"
        assert str(data["time_type"].dtype) == "category"
        assert str(data["time_value"].dtype) == "datetime64[ns]"
        assert str(data["issue"].dtype) == "datetime64[ns]"
        assert str(data["lag"].dtype) == "Int64"
        assert str(data["value"].dtype) == "Float64"
        assert str(data["missing_value"].dtype) == "Int64"
        assert str(data["missing_stderr"].dtype) == "Int64"
        assert str(data["missing_sample_size"].dtype) == "Int64"

    def test_pub_delphi(self) -> None:
        apicall = Epidata.pub_delphi(system="ec", epiweek=201501)
        data = apicall.classic()  # only supports classic
        assert len(data) > 0

    def test_pub_dengue_nowcast(self) -> None:
        apicall = Epidata.pub_dengue_nowcast(locations="pr", epiweeks=EpiRange(201401, 202301))
        data = apicall.df()

        assert len(data) > 0
        assert str(data["location"].dtype) == "string"
        assert str(data["epiweek"].dtype) == "string"
        assert str(data["value"].dtype) == "Float64"
        assert str(data["std"].dtype) == "Float64"

    @pytest.mark.skipif(not secret_sensors, reason="Dengue sensors key not available.")
    def test_pvt_dengue_sensors(self) -> None:
        apicall = Epidata.pvt_dengue_sensors(
            auth=secret_sensors, names="ght", locations="ag", epiweeks=EpiRange(201501, 202001)
        )
        data = apicall.df()

        assert len(data) > 0
        assert str(data["location"].dtype) == "string"
        assert str(data["epiweek"].dtype) == "string"
        assert str(data["value"].dtype) == "Float64"

    def test_pub_ecdc_ili(self) -> None:
        apicall = Epidata.pub_ecdc_ili(regions="austria", epiweeks=EpiRange(201901, 202001))
        data = apicall.df()

        assert len(data) > 0
        assert str(data["release_date"].dtype) == "datetime64[ns]"
        assert str(data["issue"].dtype) == "string"
        assert str(data["epiweek"].dtype) == "string"

    def test_pub_flusurv(self) -> None:
        apicall = Epidata.pub_flusurv(locations="CA", epiweeks=EpiRange(201701, 201801))
        data = apicall.df()

        assert len(data) > 0
        assert str(data["release_date"].dtype) == "string"
        assert str(data["location"].dtype) == "string"
        assert str(data["issue"].dtype) == "string"
        assert str(data["epiweek"].dtype) == "string"
        assert str(data["lag"].dtype) == "Int64"
        assert str(data["rate_age_0"].dtype) == "Float64"
        assert str(data["rate_age_1"].dtype) == "Float64"
        assert str(data["rate_age_2"].dtype) == "Float64"
        assert str(data["rate_age_3"].dtype) == "Float64"
        assert str(data["rate_age_4"].dtype) == "Float64"
        assert str(data["rate_overall"].dtype) == "Float64"

    def test_pub_fluview_clinical(self) -> None:
        apicall = Epidata.pub_fluview_clinical(regions="nat", epiweeks=EpiRange(201601, 201701))
        data = apicall.df()

        assert len(data) > 0
        assert str(data["release_date"].dtype) == "datetime64[ns]"
        assert str(data["region"].dtype) == "string"
        assert str(data["issue"].dtype) == "string"
        assert str(data["epiweek"].dtype) == "string"
        assert str(data["lag"].dtype) == "Int64"
        assert str(data["total_specimens"].dtype) == "Int64"
        assert str(data["total_a"].dtype) == "Int64"
        assert str(data["total_b"].dtype) == "Int64"
        assert str(data["percent_positive"].dtype) == "Float64"
        assert str(data["percent_a"].dtype) == "Float64"
        assert str(data["percent_b"].dtype) == "Float64"

    def test_pub_fluview_meta(self) -> None:
        apicall = Epidata.pub_fluview_meta()
        data = apicall.df()

        assert len(data) > 0
        assert str(data["latest_update"].dtype) == "datetime64[ns]"
        assert str(data["latest_issue"].dtype) == "datetime64[ns]"
        assert str(data["table_rows"].dtype) == "Int64"

    def test_pub_fluview(self) -> None:
        apicall = Epidata.pub_fluview(regions="nat", epiweeks=EpiRange(201201, 202005))
        data = apicall.df()

        assert len(data) > 0
        assert str(data["release_date"].dtype) == "datetime64[ns]"
        assert str(data["region"].dtype) == "string"
        assert str(data["issue"].dtype) == "string"
        assert str(data["epiweek"].dtype) == "string"
        assert str(data["lag"].dtype) == "Int64"
        assert str(data["num_ili"].dtype) == "Int64"
        assert str(data["num_patients"].dtype) == "Int64"
        assert str(data["wili"].dtype) == "Float64"
        assert str(data["ili"].dtype) == "Float64"

    def test_pub_gft(self) -> None:
        apicall = Epidata.pub_gft(locations="hhs1", epiweeks=EpiRange(201201, 202001))
        data = apicall.df()

        assert len(data) > 0
        assert str(data["location"].dtype) == "string"
        assert str(data["epiweek"].dtype) == "string"
        assert str(data["num"].dtype) == "Int64"

    @pytest.mark.skipif(not secret_ght, reason="GHT key not available.")
    def test_pvt_ght(self) -> None:
        apicall = Epidata.pvt_ght(
            auth=secret_ght, locations="ma", epiweeks=EpiRange(199301, 202304), query="how to get over the flu"
        )
        data = apicall.df()

        assert len(data) > 0
        assert str(data["location"].dtype) == "string"
        assert str(data["epiweek"].dtype) == "string"
        assert str(data["value"].dtype) == "Float64"

    def test_pub_kcdc_ili(self) -> None:
        apicall = Epidata.pub_kcdc_ili(regions="ROK", epiweeks=200436)
        data = apicall.df()

        assert len(data) > 0
        assert str(data["release_date"].dtype) == "datetime64[ns]"
        assert str(data["region"].dtype) == "string"
        assert str(data["issue"].dtype) == "string"
        assert str(data["epiweek"].dtype) == "string"
        assert str(data["lag"].dtype) == "Int64"
        assert str(data["ili"].dtype) == "Float64"

    @pytest.mark.skipif(not secret_norostat, reason="Norostat key not available.")
    def test_pvt_meta_norostat(self) -> None:
        apicall = Epidata.pvt_meta_norostat(auth=secret_norostat)
        data = apicall.classic()
        assert len(data) > 0

    def test_pub_meta(self) -> None:
        apicall = Epidata.pub_meta()
        data = apicall.classic()  # only supports classic
        assert len(data) > 0

    def test_pub_nidss_dengue(self) -> None:
        apicall = Epidata.pub_nidss_dengue(locations="taipei", epiweeks=EpiRange(201201, 201301))
        data = apicall.df()

        assert len(data) > 0
        assert str(data["location"].dtype) == "string"
        assert str(data["epiweek"].dtype) == "string"
        assert str(data["count"].dtype) == "Int64"

    def test_pub_nidss_flu(self) -> None:
        apicall = Epidata.pub_nidss_flu(regions="taipei", epiweeks=EpiRange(201501, 201601))
        data = apicall.df()

        assert len(data) > 0
        assert str(data["release_date"].dtype) == "datetime64[ns]"
        assert str(data["region"].dtype) == "string"
        assert str(data["issue"].dtype) == "string"
        assert str(data["epiweek"].dtype) == "string"
        assert str(data["lag"].dtype) == "Int64"
        assert str(data["visits"].dtype) == "Int64"
        assert str(data["ili"].dtype) == "Float64"

    @pytest.mark.skipif(not secret_norostat, reason="Norostat key not available.")
    def test_pvt_norostat(self) -> None:
        apicall = Epidata.pvt_norostat(auth=secret_norostat, location="1", epiweeks=201233)
        data = apicall.df()

        # TODO: Need a non-trivial query for Norostat
        # assert len(data) > 0
        # assert str(data['release_date'].dtype) == 'datetime64[ns]'
        # assert str(data['epiweek'].dtype) == 'string'

    def test_pub_nowcast(self) -> None:
        apicall = Epidata.pub_nowcast(locations="ca", epiweeks=EpiRange(201201, 201301))
        data = apicall.df()

        assert len(data) > 0
        assert str(data["location"].dtype) == "string"
        assert str(data["epiweek"].dtype) == "string"
        assert str(data["value"].dtype) == "Float64"
        assert str(data["std"].dtype) == "Float64"

    def test_pub_paho_dengue(self) -> None:
        apicall = Epidata.pub_paho_dengue(regions="ca", epiweeks=EpiRange(201401, 201501))
        data = apicall.df()

        assert len(data) > 0
        assert str(data["release_date"].dtype) == "datetime64[ns]"
        assert str(data["region"].dtype) == "string"
        assert str(data["serotype"].dtype) == "string"
        assert str(data["epiweek"].dtype) == "string"
        assert str(data["issue"].dtype) == "string"
        assert str(data["lag"].dtype) == "Int64"
        assert str(data["total_pop"].dtype) == "Int64"
        assert str(data["num_dengue"].dtype) == "Int64"
        assert str(data["num_severe"].dtype) == "Int64"
        assert str(data["num_deaths"].dtype) == "Int64"
        assert str(data["incidence_rate"].dtype) == "Float64"

    @pytest.mark.skipif(not secret_quidel, reason="Quidel key not available.")
    def test_pvt_quidel(self) -> None:
        apicall = Epidata.pvt_quidel(auth=secret_quidel, locations="hhs1", epiweeks=EpiRange(201201, 202001))
        data = apicall.df()

        assert len(data) > 0
        assert str(data["location"].dtype) == "string"
        assert str(data["epiweek"].dtype) == "string"
        assert str(data["value"].dtype) == "Float64"

    @pytest.mark.skipif(not secret_sensors, reason="Sensors key not available.")
    def test_pvt_sensors(self) -> None:
        apicall = Epidata.pvt_sensors(
            auth=secret_sensors, names="sar3", locations="nat", epiweeks=EpiRange(201501, 202001)
        )
        data = apicall.df()

        assert len(data) > 0
        assert str(data["name"].dtype) == "string"
        assert str(data["location"].dtype) == "string"
        assert str(data["epiweek"].dtype) == "string"
        assert str(data["value"].dtype) == "Float64"

    @pytest.mark.skipif(not secret_twitter, reason="Twitter key not available.")
    def test_pvt_twitter(self) -> None:
        apicall = Epidata.pvt_twitter(
            auth=secret_twitter, locations="CA", time_type="week", time_values=EpiRange(201501, 202001)
        )
        data = apicall.df()

        assert len(data) > 0
        assert str(data["location"].dtype) == "string"
        assert str(data["epiweek"].dtype) == "string"
        assert str(data["num"].dtype) == "Int64"
        assert str(data["total"].dtype) == "Int64"
        assert str(data["percent"].dtype) == "Float64"

    def test_pub_wiki(self) -> None:
        apicall = Epidata.pub_wiki(articles="avian_influenza", time_type="week", time_values=EpiRange(201501, 201601))
        data = apicall.df()

        assert len(data) > 0
        assert str(data["article"].dtype) == "string"
        assert str(data["epiweek"].dtype) == "string"
        assert str(data["count"].dtype) == "Int64"
        assert str(data["total"].dtype) == "Int64"
        assert str(data["hour"].dtype) == "Int64"
        assert str(data["value"].dtype) == "Float64"
