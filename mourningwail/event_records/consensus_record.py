from ._base import EventRecord


class ConsensusRecord(EventRecord):
    community_uri = metrics.Keyword()
