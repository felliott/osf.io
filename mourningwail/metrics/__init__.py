from .events import (
    FileDownloadEvent,
    PageVisitEvent,
    SystemLogEvent,
    UiInteractionEvent,
)
from .reports import (
    AddonUsageReport,
    DailyDownloadCountReport,
    InstitutionSummaryReport,
    # NewUserDomainReport,
    # NodeCountReport,
    # OsfstorageFileCountReport,
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
    DailyDownloadCountReport,
    InstitutionSummaryReport,
    # NewUserDomainReport,
    # NodeCountReport,
    # OsfstorageFileCountReport,
    PreprintCountReport,
    UserCountReport,
)


__all__ = ('METERED_REPORTS', 'METERED_EVENTS')
