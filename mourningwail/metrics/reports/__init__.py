from .addon_usage_report import AddonUsageReport
from .download_count_report import DownloadCountReport
from .institution_summary_report import InstitutionSummaryReport
from .new_user_domain_report import NewUserDomainReport
from .node_count_report import NodeCountReport
from .osfstorage_file_count_report import OsfstorageFileCountReport
from .preprint_count_report import PreprintCountReport
from .user_count_report import UserCountReport


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
