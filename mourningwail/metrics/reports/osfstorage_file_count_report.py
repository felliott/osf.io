from django.contrib.contenttypes.models import ContentType
from django.db.models import Q
import logging
from datetime import timedelta

from osf.models import AbstractNode, Preprint
from mourningwail.metrics.base import DailyReport


logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)


class OsfstorageFileCountReport(DailyReport):

    @classmethod
    def run_daily_report(cls, date):
        from addons.osfstorage.models import OsfStorageFile

        file_qs = OsfStorageFile.objects
        abstract_node_content_type = ContentType.objects.get_for_model(AbstractNode)
        preprint_content_type = ContentType.objects.get_for_model(Preprint)

        public_query = Q(
            target_object_id__in=AbstractNode.objects.filter(is_public=True).values('id'),
            target_content_type__in=[abstract_node_content_type, preprint_content_type],
        )

        private_query = Q(
            target_object_id__in=AbstractNode.objects.filter(is_public=False).values('id'),
            target_content_type__in=[abstract_node_content_type, preprint_content_type],
        )

        daily_query = Q(
            created__gte=date,
            created__lt=(date + timedelta(days=1)),
        )

        totals = {
            'keen': {
                # 'timestamp': timestamp_datetime.isoformat()
            },
            # OsfStorageFiles - the number of files on OsfStorage
            'osfstorage_files_including_quickfiles': {
                'total': file_qs.count(),
                'public': file_qs.filter(public_query).count(),
                'private': file_qs.filter(private_query).count(),
                'total_daily': file_qs.filter(daily_query).count(),
                'public_daily': file_qs.filter(public_query & daily_query).count(),
                'private_daily': file_qs.filter(private_query & daily_query).count(),
            },
        }

        logger.info(
            'OsfStorage Files counted. Files: {}'.format(
                totals['osfstorage_files_including_quickfiles']['total'],
            )
        )

        return [totals]
