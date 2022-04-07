from .events import (
    FileDownloadEvent,
    PageVisitEvent,
    SystemLogEvent,
    UiInteractionEvent,
)
from .report_results import (
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
DAILY_REPORTS = (
    AddonUsageReport,
    DownloadCountReport,
    InstitutionSummaryReport,
    NewUserDomainReport,
    NodeCountReport,
    OsfstorageFileCountReport,
    PreprintCountReport,
    UserCountReport,
)


__all__ = ('DAILY_REPORTS', 'METERED_EVENTS')
