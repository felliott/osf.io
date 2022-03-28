from .file_download_event import FileDownloadEvent
from .page_visit_event import PageVisitEvent
from .system_log_event import SystemLogEvent
from .ui_interaction_event import UiInteractionEvent


METERED_EVENTS = (
    FileDownloadEvent,
    PageVisitEvent,
    SystemLogEvent,
    UiInteractionEvent,
)
