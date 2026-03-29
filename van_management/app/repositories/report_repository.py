from sqlalchemy.orm import Session

from app.models.report import Report


class ReportRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def create(self, report: Report) -> Report:
        self.db.add(report)
        self.db.commit()
        self.db.refresh(report)
        return report

    def get_by_id(self, report_id: str) -> Report | None:
        return self.db.query(Report).filter(Report.id == report_id).first()

    def get_all(self, skip: int = 0, limit: int = 50) -> list[Report]:
        return (
            self.db.query(Report)
            .order_by(Report.created_at.desc())
            .offset(skip)
            .limit(limit)
            .all()
        )

    def count(self) -> int:
        return self.db.query(Report).count()
