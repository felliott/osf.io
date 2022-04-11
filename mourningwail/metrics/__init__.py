from .events import (
    FileDownloadEvent,
    PageVisitEvent,
    SystemLogEvent,
    UiInteractionEvent,
)
from .reports import (
    AddonUsageReport,
    DownloadCountReport,
    InstitutionSummaryReport,
    NewUserDomainReport,
    NodeCountReport,
    OsfstorageFileCountReport,
    PreprintCountReport,
    UserCountReport,
)


METERED_EVENTS = (
    FileDownloadEvent,
    PageVisitEvent,
    SystemLogEvent,
    UiInteractionEvent,
)
METERED_REPORTS = (
    AddonUsageReport,
    DownloadCountReport,
    InstitutionSummaryReport,
    NewUserDomainReport,
    NodeCountReport,
    OsfstorageFileCountReport,
    PreprintCountReport,
    UserCountReport,
)


__all__ = ('METERED_REPORTS', 'METERED_EVENTS')
