from sqlalchemy import text

from app.db.models import AnalysisJob  # noqa: F401
from app.db.session import Base, SessionLocal, engine


def _ensure_analysis_jobs_schema() -> None:
    expected_columns = {
        "file_type": "TEXT NOT NULL DEFAULT ''",
        "summary_json": "TEXT",
        "report_markdown": "TEXT",
    }

    with SessionLocal() as session:
        existing_columns = {
            row[1]
            for row in session.execute(text("PRAGMA table_info(analysis_jobs)")).all()
        }

        for column_name, column_sql in expected_columns.items():
            if column_name not in existing_columns:
                session.execute(
                    text(f"ALTER TABLE analysis_jobs ADD COLUMN {column_name} {column_sql}")
                )

        session.commit()


def init_db() -> None:
    Base.metadata.create_all(bind=engine)
    _ensure_analysis_jobs_schema()
