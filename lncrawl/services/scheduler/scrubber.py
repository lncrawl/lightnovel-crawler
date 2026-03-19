import logging
import shutil
from threading import Event

import sqlmodel as sq

from ...context import ctx
from ...dao import Job, JobStatus, UserToken
from ...exceptions import AbortedException
from ...utils.file_tools import folder_size, format_size
from ...utils.time_utils import current_timestamp

logger = logging.getLogger(__name__)


class Scrubber:
    def __init__(self, signal=Event()) -> None:
        self.signal = signal

    @staticmethod
    def run(signal: Event):
        scrubber = Scrubber(signal)
        scrubber.free_disk_size()
        scrubber.delete_old_jobs()
        scrubber.cancel_long_jobs()
        scrubber.delete_expired_tokens()

    def free_disk_size(self):
        size_limit = ctx.config.crawler.disk_size_limit
        if size_limit <= 0:
            return

        current_size = folder_size(ctx.config.app.output_path)
        logger.info(f"Current folder size: {format_size(current_size)}")
        if current_size < size_limit:
            return

        # Keep deleting novels to reach target disk size limit
        logger.debug('Deleting novels to free up space')
        for folder in sorted(
            ctx.files.resolve('novels').iterdir(),
            key=lambda p: p.stat().st_mtime,
        ):
            if self.signal.is_set():
                raise AbortedException()
            if not folder.is_dir():
                continue
            try:
                size = folder_size(folder)
                current_size -= size
                for file in folder.iterdir():
                    if file.is_dir():
                        shutil.rmtree(file, ignore_errors=True)
                logger.info(f'Deleted novel: {folder.name} [{format_size(size)}]')
            except Exception:
                current_size = folder_size(ctx.config.app.output_path)
                logger.info(f'Error removing: {folder.name}', exc_info=True)
            finally:
                if current_size < size_limit:
                    break

        logger.info(f"Current folder size: {format_size(current_size)}")

    def delete_old_jobs(self):
        day = 24 * 3600 * 1000
        now = current_timestamp()
        with ctx.db.session() as sess:
            # find root jobs to delete
            job_ids = sess.exec(
                sq.select(Job.id)
                .where(
                    sq.col(Job.parent_job_id).is_(None),
                    Job.status != JobStatus.PENDING,
                    Job.updated_at < now - 90 * day
                )
            ).all()

            # delete child jobs
            sess.exec(
                sq.delete(Job)
                .where(
                    sq.col(Job.parent_job_id).is_not(None),
                    sq.col(Job.updated_at) < now - 15 * day
                )
            )
            sess.commit()

        if len(job_ids) > 0:
            logger.info(f"Deleting {len(job_ids)} jobs")
            for job_id in job_ids:
                if self.signal.is_set():
                    return
                ctx.jobs.delete(job_id)

    def cancel_long_jobs(self):
        hour = 3600 * 1000
        now = current_timestamp()
        with ctx.db.session() as sess:
            job_ids = sess.exec(
                sq.select(Job.id)
                .where(
                    sq.col(Job.parent_job_id).is_(None),
                    Job.status == JobStatus.RUNNING,
                    Job.updated_at < now - 16 * hour
                )
            ).all()

        if len(job_ids) > 0:
            logger.info(f"Canceling {len(job_ids)} jobs")
            for job_id in job_ids:
                if self.signal.is_set():
                    return
                ctx.jobs.cancel(job_id)

    def delete_expired_tokens(self):
        now = current_timestamp()
        with ctx.db.session() as sess:
            sess.exec(
                sq.delete(UserToken)
                .where(sq.col(UserToken.expires_at) < now)
            )
            sess.commit()
