from dataclasses import Field, InitVar, dataclass, field, fields
from typing import (
    Any,
    Callable,
    Dict,
    Generic,
    Iterable,
    List,
    Literal,
    Mapping,
    Optional,
    OrderedDict,
    Sequence,
    Tuple,
    Union,
    overload,
    get_args,
)
from functools import cached_property
from pandas import DataFrame
from ._model import (
    EpiRangeLike,
    CALL_TYPE,
    EpidataFieldInfo,
    EpidataFieldType,
    EpiRangeParam,
    InvalidArgumentException,
)


GeoType = Literal["nation", "msa", "hrr", "hhs", "state", "county"]
TimeType = Literal["day", "week"]


@dataclass
class WebLink:
    """
    represents a web link
    """

    alt: str
    href: str


@dataclass
class DataSignalGeoStatistics:
    """
    COVIDcast signal statistics
    """

    min: float
    max: float
    mean: float
    stdev: float


def _limit_fields(data: Dict[str, Any], class_fields: Tuple[Field, ...]) -> Dict[str, Any]:
    field_names = {f.name for f in class_fields}
    return {k: v for k, v in data.items() if k in field_names}


def define_covidcast_fields() -> List[EpidataFieldInfo]:
    return [
        EpidataFieldInfo("source", EpidataFieldType.text),
        EpidataFieldInfo("signal", EpidataFieldType.text),
        EpidataFieldInfo(
            "geo_type",
            EpidataFieldType.categorical,
            categories=list(get_args(GeoType)),
        ),
        EpidataFieldInfo("geo_value", EpidataFieldType.text),
        EpidataFieldInfo("time_type", EpidataFieldType.categorical, categories=list(get_args(TimeType))),
        EpidataFieldInfo("time_value", EpidataFieldType.date_or_epiweek),
        EpidataFieldInfo("issue", EpidataFieldType.date),
        EpidataFieldInfo("lag", EpidataFieldType.int),
        EpidataFieldInfo("value", EpidataFieldType.float),
        EpidataFieldInfo("stderr", EpidataFieldType.float),
        EpidataFieldInfo("sample_size", EpidataFieldType.int),
        EpidataFieldInfo("direction", EpidataFieldType.float),
        EpidataFieldInfo("missing_value", EpidataFieldType.int),
        EpidataFieldInfo("missing_stderr", EpidataFieldType.int),
        EpidataFieldInfo("missing_sample_size", EpidataFieldType.int),
    ]


@dataclass
class DataSignal(Generic[CALL_TYPE]):
    """
    represents a COVIDcast data signal
    """

    _create_call: Callable[[Mapping[str, Union[None, EpiRangeLike, Iterable[EpiRangeLike]]]], CALL_TYPE]

    source: str
    signal: str
    signal_basename: str
    name: str
    active: bool
    short_description: str
    description: str
    time_label: str
    value_label: str
    format: Literal["per100k", "percent", "fraction", "count", "raw"] = "raw"
    category: Literal["early", "public", "late", "other"] = "other"
    high_values_are: Literal["good", "bad", "neutral"] = "neutral"
    is_smoothed: bool = False
    is_weighted: bool = False
    is_cumulative: bool = False
    has_stderr: bool = False
    has_sample_size: bool = False
    link: Sequence[WebLink] = field(default_factory=list)
    compute_from_base: bool = False
    time_type: TimeType = "day"

    geo_types: Dict[GeoType, DataSignalGeoStatistics] = field(default_factory=dict)

    def __post_init__(self) -> None:
        self.link = [WebLink(alt=l["alt"], href=l["href"]) if isinstance(l, dict) else l for l in self.link]
        stats_fields = fields(DataSignalGeoStatistics)
        self.geo_types = {
            k: DataSignalGeoStatistics(**_limit_fields(l, stats_fields)) if isinstance(l, dict) else l
            for k, l in self.geo_types.items()
        }

    @staticmethod
    def to_df(signals: Iterable["DataSignal"]) -> DataFrame:
        df = DataFrame(
            signals,
            columns=[
                "source",
                "signal",
                "name",
                "active",
                "short_description",
                "description",
                "time_type",
                "time_label",
                "value_label",
                "format",
                "category",
                "high_values_are",
                "is_smoothed",
                "is_weighted",
                "is_cumulative",
                "has_stderr",
                "has_sample_size",
            ],
        )
        df.insert(6, "geo_types", [",".join(s.geo_types.keys()) for s in signals])
        return df.set_index(["source", "signal"])

    @property
    def key(self) -> Tuple[str, str]:
        return (self.source, self.signal)

    def call(
        self,
        geo_type: GeoType,
        geo_values: Union[int, str, Iterable[Union[int, str]]],
        time_values: EpiRangeParam,
        as_of: Union[None, str, int] = None,
        issues: Optional[EpiRangeParam] = None,
        lag: Optional[int] = None,
    ) -> CALL_TYPE:
        """Fetch Delphi's COVID-19 Surveillance Streams"""
        if any((v is None for v in (geo_type, geo_values, time_values))):
            raise InvalidArgumentException("`geo_type`, `time_values`, and `geo_values` are all required")
        if issues is not None and lag is not None:
            raise InvalidArgumentException("`issues` and `lag` are mutually exclusive")

        return self._create_call(
            {
                "data_source": self.source,
                "signals": self.signal,
                "time_type": self.time_type,
                "time_values": time_values,
                "geo_type": geo_type,
                "geo_values": geo_values,
                "as_of": as_of,
                "issues": issues,
                "lag": lag,
            }
        )

    def __call__(
        self,
        geo_type: GeoType,
        geo_values: Union[int, str, Iterable[Union[int, str]]],
        time_values: EpiRangeParam,
        as_of: Union[None, str, int] = None,
        issues: Optional[EpiRangeParam] = None,
        lag: Optional[int] = None,
    ) -> CALL_TYPE:
        """Fetch Delphi's COVID-19 Surveillance Streams"""
        return self.call(geo_type, geo_values, time_values, as_of, issues, lag)


@dataclass
class DataSource(Generic[CALL_TYPE]):
    """
    represents a COVIDcast data source
    """

    _create_call: InitVar[Callable[[Mapping[str, Union[None, EpiRangeLike, Iterable[EpiRangeLike]]]], CALL_TYPE]]

    source: str
    db_source: str
    name: str
    description: str
    reference_signal: str
    license: Optional[str] = None
    link: Sequence[WebLink] = field(default_factory=list)
    dua: Optional[str] = None

    signals: Sequence[DataSignal] = field(default_factory=list)

    def __post_init__(
        self, _create_call: Callable[[Mapping[str, Union[None, EpiRangeLike, Iterable[EpiRangeLike]]]], CALL_TYPE]
    ) -> None:
        self.link = [WebLink(alt=l["alt"], href=l["href"]) if isinstance(l, dict) else l for l in self.link]
        signal_fields = fields(DataSignal)
        self.signals = [
            DataSignal(_create_call=_create_call, **_limit_fields(s, signal_fields)) if isinstance(s, dict) else s
            for s in self.signals
        ]

    @staticmethod
    def to_df(sources: Iterable["DataSource"]) -> DataFrame:
        df = DataFrame(
            sources,
            columns=["source", "name", "description", "reference_signal", "license", "dua"],
        )
        df["signals"] = [",".join(ss.signal for ss in s.signals) for s in sources]
        return df.set_index("source")

    def get_signal(self, signal: str) -> Optional[DataSignal]:
        return next((s for s in self.signals if s.signal == signal), None)

    @cached_property
    def signal_df(self) -> DataFrame:
        return DataSignal.to_df(self.signals)


@dataclass
class CovidcastDataSources(Generic[CALL_TYPE]):
    """
    COVIDcast data source helper.
    """

    sources: Sequence[DataSource[CALL_TYPE]]
    _source_by_name: Dict[str, DataSource[CALL_TYPE]] = field(init=False, default_factory=dict)
    _signals_by_key: OrderedDict[Tuple[str, str], DataSignal[CALL_TYPE]] = field(
        init=False, default_factory=OrderedDict
    )

    _create_call: Callable[[Mapping[str, Union[None, EpiRangeLike, Iterable[EpiRangeLike]]]], CALL_TYPE]

    def __post_init__(self) -> None:
        self._source_by_name = {s.source: s for s in self.sources}
        for source in self.sources:
            for signal in source.signals:
                self._signals_by_key[signal.key] = signal

    def get_source(self, source: str) -> Optional[DataSource[CALL_TYPE]]:
        return self._source_by_name.get(source)

    @property
    def source_names(self) -> Iterable[str]:
        return (s.source for s in self.sources)

    @cached_property
    def source_df(self) -> DataFrame:
        """Fetch metadata about available covidcast sources.

        Obtains a data frame of source metadata describing all publicly available data
        streams from the covidcast API.

        :returns: A data frame containing one row per available source, with the
          following columns:

          ``source``
            Data source name.

          ``signal``
            Signal name.

          ``description``
            Description of the signal.

          ``reference_signal``
            Geographic level for which this signal is available, such as county,
            state, msa, hss, hrr, or nation. Most signals are available at multiple geographic
            levels and will hence be listed in multiple rows with their own
            metadata.

          ``license``
            The license

          ``dua``
            Link to the Data Use Agreement.
        """
        return DataSource.to_df(self.sources)

    @property
    def signals(self) -> Iterable[DataSignal[CALL_TYPE]]:
        return self._signals_by_key.values()

    @cached_property
    def signal_df(self) -> DataFrame:
        """Fetch metadata about available covidcast signals.

        Obtains a data frame of metadata describing all publicly available data
        streams from the COVIDcast API. See the `data source and signals documentation
        <https://cmu-delphi.github.io/delphi-epidata/api/covidcast_signals.html>`_
        for descriptions of the available sources.

        :returns: A data frame containing one row per available signal, with the
          following columns:

          ``data_source``
            Data source name.

          ``signal``
            Signal name.

          ``name``
            Name of signal.

          ``active``
            Whether the signal is currently not updated or not. Signals may be inactive
            because the sources have become unavailable, other sources have replaced
            them, or additional work is required for us to continue updating them.

          ``short_description``
            Brief description of the signal.

          ``description``
            Full description of the signal.

          ``geo_types``
            Spatial resolution of the signal (e.g., `county`, `hrr`, `msa`, `dma`, `state`).
            More detail about all `geo_types` is given in the `geographic coding documentation
            <https://cmu-delphi.github.io/delphi-epidata/api/covidcast_geography.html>`_.

          ``time_type``
            Temporal resolution of the signal (e.g., day, week; see
            `date coding details <https://cmu-delphi.github.io/delphi-epidata/api/covidcast_times.html>`_).

          ``time_label``
            The time label ("Date", "Week").

          ``value_label``
            The value label ("Value", "Percentage", "Visits", "Visits per 100,000 people").

          ``format``
            The value format ("per100k", "percent", "fraction", "count", "raw").

          ``category``
            The signal category ("early", "public", "late", "other").

          ``high_values_are``
            What the higher value of signal indicates ("good", "bad", "neutral").

          ``is_smoothed``
            Whether the signal is smoothed.

          ``is_weighted``
            Whether the signal is weighted.

          ``is_cumulative``
            Whether the signal is cumulative.

          ``has_stderr``
            Whether the signal has `stderr` statistic.

          ``has_sample_size``
            Whether the signal has `sample_size` statistic.
        """
        return DataSignal.to_df(self.signals)

    def get_signal(self, source: str, signal: str) -> Optional[DataSignal[CALL_TYPE]]:
        return self._signals_by_key.get((source, signal))

    @property
    def signal_names(self) -> Iterable[Tuple[str, str]]:
        return self._signals_by_key.keys()

    def __iter__(self) -> Iterable[DataSource[CALL_TYPE]]:
        return iter(self.sources)

    @overload
    def __getitem__(self, source: str) -> DataSource[CALL_TYPE]:
        ...

    @overload
    def __getitem__(self, source_signal: Tuple[str, str]) -> DataSignal[CALL_TYPE]:
        ...

    def __getitem__(
        self, source_signal: Union[str, Tuple[str, str]]
    ) -> Union[DataSource[CALL_TYPE], DataSignal[CALL_TYPE]]:
        if isinstance(source_signal, str):
            r = self.get_source(source_signal)
            assert r is not None
            return r
        s = self.get_signal(source_signal[0], source_signal[1])
        assert s is not None
        return s

    @staticmethod
    def create(
        meta: List[Dict],
        create_call: Callable[[Mapping[str, Union[None, EpiRangeLike, Iterable[EpiRangeLike]]]], CALL_TYPE],
    ) -> "CovidcastDataSources":
        source_fields = fields(DataSource)
        sources = [DataSource(_create_call=create_call, **_limit_fields(k, source_fields)) for k in meta]
        return CovidcastDataSources(sources, create_call)
