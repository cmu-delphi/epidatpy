import os
from epidatpy.request import Epidata, EpiRange

# Requirements to run these:
# - DELPHI_EPIDATA_KEY environment variable is set https://api.delphi.cmu.edu/epidata/admin/registration_form
# - it has access to the private endpoints being tested

auth = os.environ.get("DELPHI_EPIDATA_KEY")
secret_cdc = os.environ.get("SECRET_API_AUTH_CDC")
secret_fluview = os.environ.get("SECRET_API_AUTH_FLUVIEW")
secret_ght = os.environ.get("SECRET_API_AUTH_GHT")
secret_norostat = os.environ.get("SECRET_API_AUTH_NOROSTAT")
secret_quidel = os.environ.get("SECRET_API_AUTH_QUIDEL")
secret_sensors = os.environ.get("SECRET_API_AUTH_SENSORS")
secret_twitter = os.environ.get("SECRET_API_AUTH_TWITTER")

def test_pvt_cdc() -> None:
    apicall = Epidata.pvt_cdc(
        auth = secret_cdc,
        locations = "fl,ca",
        epiweeks = EpiRange(201501, 201601)
    )
    data = apicall.df()
    assert(len(data) > 0)

def test_pub_covid_hosp_facility_lookup() -> None:
    apicall = Epidata.pub_covid_hosp_facility_lookup(state="fl")
    data = apicall.df()
    assert(len(data) > 0)

    apicall = Epidata.pub_covid_hosp_facility_lookup(city="southlake")
    data = apicall.df()
    assert(len(data) > 0)

def test_pub_covid_hosp_facility() -> None:
    apicall = Epidata.pub_covid_hosp_facility(
        hospital_pks = "100075",
        collection_weeks = EpiRange(20200101, 20200501))
    data = apicall.df()
    assert(len(data) > 0)

    apicall = Epidata.pub_covid_hosp_facility(
        hospital_pks = "100075",
        collection_weeks = EpiRange(202001, 202005))
    data = apicall.df()
    assert(len(data) > 0) # fails

def test_pub_covid_hosp_state_timeseries() -> None:
    apicall = Epidata.pub_covid_hosp_state_timeseries(
        states = "fl",
        dates = EpiRange(20200101, 20200501))
    data = apicall.df()
    assert(len(data) > 0)

def test_pub_covidcast_meta() -> None:
    apicall = Epidata.pub_covidcast_meta()
    data = apicall.df()
    assert(len(data) > 0)

def test_pub_covidcast() -> None:
    apicall = Epidata.pub_covidcast(
        data_source = "jhu-csse",
        signals = "confirmed_7dav_incidence_prop",
        geo_type = "state",
        time_type = "day",
        geo_values = ["ca", "fl"],
        time_values = EpiRange(20200601, 20200801))
    data = apicall.df()
    assert(len(data) > 0)

    apicall = Epidata.pub_covidcast(
        data_source = "jhu-csse",
        signals = "confirmed_7dav_incidence_prop",
        geo_type = "state",
        time_type = "day",
        geo_values = "*",
        time_values = EpiRange(20200601, 20200801))
    data = apicall.df()
    assert(len(data) > 0)

def test_pub_delphi() -> None:
    apicall = Epidata.pub_delphi(
        system = "ec",
        epiweek = 201501
    )
    data = apicall.classic() # only supports classic
    assert(len(data) > 0)

def test_pub_dengue_nowcast() -> None:
    apicall = Epidata.pub_dengue_nowcast(
        locations = "pr",
        epiweeks = EpiRange(201401, 202301)
    )
    data = apicall.df()
    assert(len(data) > 0)

def test_pvt_dengue_sensors() -> None:
    apicall = Epidata.pvt_dengue_sensors(
        auth = secret_norostat,
        names = "ght",
        locations = "ag",
        epiweeks = EpiRange(201501, 202001)
    )
    data = apicall.df()
    assert(len(data) > 0)

def test_pub_ecdc_ili() -> None:
    apicall = Epidata.pub_ecdc_ili(
        regions = "austria",
        epiweeks = EpiRange(201901, 202001)
    )
    data = apicall.df(disable_date_parsing=True)
    assert(len(data) > 0)

def test_pub_flusurv() -> None:
    apicall = Epidata.pub_flusurv(
        locations = "CA",
        epiweeks = EpiRange(201701, 201801)
    )
    data = apicall.df(disable_date_parsing=True)
    assert(len(data) > 0)

def test_pub_fluview_clinical() -> None:
    apicall = Epidata.pub_fluview_clinical(
        regions = "nat",
        epiweeks = EpiRange(201601, 201701)
    )
    data = apicall.df(disable_date_parsing=True)
    assert(len(data) > 0)

def test_pub_fluview_meta() -> None:
    apicall = Epidata.pub_fluview_meta()
    data = apicall.df(disable_date_parsing=True)
    assert(len(data) > 0)

def test_pub_fluview() -> None:
    apicall = Epidata.pub_fluview(
        regions = "nat",
        epiweeks = EpiRange(201201, 202005)
    )
    data = apicall.df(disable_date_parsing=True)
    assert(len(data) > 0)

def test_pub_gft() -> None:
    apicall = Epidata.pub_gft(
        locations = "hhs1",
        epiweeks = EpiRange(201201, 202001)
    )
    data = apicall.df()
    assert(len(data) > 0)

def test_pvt_ght() -> None:
    apicall = Epidata.pvt_ght(
        auth = secret_ght,
        locations = "ma",
        epiweeks = EpiRange(199301, 202304),
        query = "how to get over the flu"
    )
    data = apicall.df()
    assert(len(data) > 0)

def test_pub_kcdc_ili() -> None:
    apicall = Epidata.pub_kcdc_ili(
        regions = "ROK",
        epiweeks = 200436
    )
    data = apicall.df(disable_date_parsing=True)
    assert(len(data) > 0)

def test_pvt_meta_norostat() -> None:
    apicall = Epidata.pvt_meta_norostat(
        auth = secret_norostat
    )
    data = apicall.classic()
    assert(len(data) > 0)

def test_pub_meta() -> None:
    apicall = Epidata.pub_meta()
    data = apicall.classic() # only supports classic
    assert(len(data) > 0)

def test_pub_nidss_dengue() -> None:
    apicall = Epidata.pub_nidss_dengue(
        locations = "taipei",
        epiweeks = EpiRange(201201, 201301)
    )
    data = apicall.df()
    assert(len(data) > 0)

def test_pub_nidss_flu() -> None:
    apicall = Epidata.pub_nidss_flu(
        regions = "taipei",
        epiweeks = EpiRange(201501, 201601)
    )
    data = apicall.df(disable_date_parsing=True)
    assert(len(data) > 0)

def test_pvt_norostat() -> None:
    apicall = Epidata.pvt_norostat(
        auth = secret_norostat,
        location = "1",
        epiweeks = 201233
    )
    data = apicall.df()
    # TODO: Norostat is known to not return data
    # assert(len(data) > 0)

def test_pub_nowcast() -> None:
    apicall = Epidata.pub_nowcast(
        locations = "ca",
        epiweeks = EpiRange(201201, 201301)
    )
    data = apicall.df()
    assert(len(data) > 0)

def test_pub_paho_dengue() -> None:
    apicall = Epidata.pub_paho_dengue(
        regions = "ca",
        epiweeks = EpiRange(201401, 201501)
    )
    data = apicall.df(disable_date_parsing=True)
    assert(len(data) > 0)

def test_pvt_quidel() -> None:
    apicall = Epidata.pvt_quidel(
        auth = secret_quidel,
        locations = "hhs1",
        epiweeks = EpiRange(201201, 202001)
    )
    data = apicall.df()
    assert(len(data) > 0)

def test_pvt_sensors() -> None:
    apicall = Epidata.pvt_sensors(
        auth = secret_sensors,
        names = "sar3",
        locations = "nat",
        epiweeks = EpiRange(201501, 202001)
    )
    data = apicall.df()
    assert(len(data) > 0)

def test_pvt_twitter() -> None:
    apicall = Epidata.pvt_twitter(
        auth = secret_twitter,
        locations = "CA",
        time_type = "week",
        time_values = EpiRange(201501, 202001)
    )
    data = apicall.df()
    assert(len(data) > 0)

def test_pub_wiki() -> None:
    apicall = Epidata.pub_wiki(
        articles = "avian_influenza",
        time_type = "week",
        time_values = EpiRange(201501, 201601)
    )
    data = apicall.df()
    assert(len(data) > 0)
