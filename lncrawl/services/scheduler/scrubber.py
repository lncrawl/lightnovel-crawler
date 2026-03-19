import logging
import shutil
from threading import Event

import sqlmodel as sq

from ...context import ctx
from ...dao import Job, JobStatus, UserToken
from ...dao.artifact import Artifact
from ...exceptions import AbortedException
from ...utils.file_tools import folder_size, format_size
from ...utils.time_utils import current_timestamp

logger = logging.getLogger(__name__)
_hour = 3600 * 1000
_day = 24 * _hour
_month = 30 * _day


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
        now = current_timestamp()
        size_limit = ctx.config.crawler.disk_size_limit
        if size_limit <= 0:
            return

        current_size = folder_size(ctx.config.app.output_path)
        logger.info(f"Current folder size: {format_size(current_size)}")
        if current_size < size_limit:
            return

        # Delete old artifacts to reach target disk size limit
        logger.info('Deleting artifacts to free up space')
        with ctx.db.session() as sess:
            to_delete = []
            for artifact in sess.exec(
                sq.select(Artifact)
                .where(sq.col(Artifact.created_at) < now - _month)
                .order_by(sq.col(Artifact.file_size).desc())
            ):
                if current_size < size_limit:
                    break
                if self.signal.is_set():
                    raise AbortedException()
                file_path = ctx.files.resolve(artifact.output_file)
                try:
                    current_size -= file_path.stat().st_size
                    file_path.unlink()
                except OSError:
                    pass
                to_delete.append(artifact.id)
            sess.exec(
                sq.delete(Artifact)
                .where(sq.col(Artifact.id).in_(to_delete))
            )
            sess.commit()
        logger.info(f"Current folder size: {format_size(current_size)}")

        # Delete novel data to reach target disk size limit
        logger.info('Deleting novel data to free up space')
        for folder in sorted(
            ctx.files.resolve('novels').iterdir(),
            key=lambda p: p.stat().st_mtime,
        ):
            if current_size < size_limit:
                break
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
                    # intentionally keeping top level files, such as cover image
                with ctx.db.session() as sess:
                    sess.exec(
                        sq.delete(Artifact)
                        .where(sq.col(Artifact.novel_id) == folder.name)
                    )
                    sess.commit()
                logger.debug(f'Deleted novel: {folder.name} [{format_size(size)}]')
            except Exception:
                current_size = folder_size(ctx.config.app.output_path)
                logger.info(f'Error removing: {folder.name}', exc_info=True)
        logger.info(f"Current folder size: {format_size(current_size)}")

    def delete_old_jobs(self):
        now = current_timestamp()
        with ctx.db.session() as sess:
            # find root jobs to delete
            job_ids = sess.exec(
                sq.select(Job.id)
                .where(
                    sq.col(Job.parent_job_id).is_(None),
                    Job.status != JobStatus.PENDING,
                    Job.updated_at < now - _month * 3
                )
            ).all()

            # delete child jobs
            sess.exec(
                sq.delete(Job)
                .where(
                    sq.col(Job.parent_job_id).is_not(None),
                    sq.col(Job.updated_at) < now - _day * 15
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
        now = current_timestamp()
        with ctx.db.session() as sess:
            job_ids = sess.exec(
                sq.select(Job.id)
                .where(
                    sq.col(Job.parent_job_id).is_(None),
                    Job.status == JobStatus.RUNNING,
                    Job.updated_at < now - _hour * 16
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
