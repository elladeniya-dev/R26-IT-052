from datetime import date

from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert as pg_insert

from app.models import DroppedRecord, ScrapeRun
from app.repositories.base import BaseRepository


class RunRepository(BaseRepository):
    def record_run(
        self, *, run_date: date, brand_id: int, status: str, products_seen: int,
        products_kept: int, duration_ms: int | None = None, error_message: str | None = None,
    ) -> ScrapeRun:
        """Upserts on (run_date, brand_id) — a re-run for the same brand/day
        (e.g. a manual retry after a failure) replaces the prior row rather
        than creating a duplicate."""
        stmt = pg_insert(ScrapeRun).values(
            run_date=run_date, brand_id=brand_id, status=status, products_seen=products_seen,
            products_kept=products_kept, duration_ms=duration_ms, error_message=error_message,
        )
        stmt = stmt.on_conflict_do_update(
            index_elements=["run_date", "brand_id"],
            set_=dict(
                status=stmt.excluded.status, products_seen=stmt.excluded.products_seen,
                products_kept=stmt.excluded.products_kept, duration_ms=stmt.excluded.duration_ms,
                error_message=stmt.excluded.error_message,
            ),
        ).returning(ScrapeRun)
        run = self.db.scalar(stmt)
        self.db.commit()
        return run

    def log_dropped(
        self, *, run_date: date, brand_id: int | None, reason: str,
        raw_title: str | None = None, raw_payload: dict | None = None,
    ) -> None:
        self.db.add(DroppedRecord(
            run_date=run_date, brand_id=brand_id, reason=reason,
            raw_title=raw_title, raw_payload=raw_payload,
        ))

    def get_runs(self, run_date: date | None = None) -> list[ScrapeRun]:
        stmt = select(ScrapeRun).order_by(ScrapeRun.run_date.desc(), ScrapeRun.brand_id)
        if run_date:
            stmt = stmt.where(ScrapeRun.run_date == run_date)
        return list(self.db.scalars(stmt).all())

    def get_dropped(self, run_date: date | None = None) -> list[DroppedRecord]:
        stmt = select(DroppedRecord).order_by(DroppedRecord.id.desc())
        if run_date:
            stmt = stmt.where(DroppedRecord.run_date == run_date)
        return list(self.db.scalars(stmt).all())

    def get_brand_coverage(self, brand_id: int, days: int = 30) -> list[ScrapeRun]:
        stmt = (
            select(ScrapeRun)
            .where(ScrapeRun.brand_id == brand_id)
            .order_by(ScrapeRun.run_date.desc())
            .limit(days)
        )
        return list(self.db.scalars(stmt).all())
