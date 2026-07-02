from __future__ import annotations

import json

from fastapi import APIRouter, File, HTTPException, UploadFile

from app.db.models import AnalysisJob
from app.db.session import SessionLocal
from app.services.pipeline import analyze_file

router = APIRouter()


@router.post("/explore")
async def explore_data(file: UploadFile = File(...)) -> dict:
    content = await file.read()
    if not content:
        raise HTTPException(status_code=400, detail="업로드된 파일이 비어 있습니다.")

    try:
        result = analyze_file(file.filename or "uploaded_file", content)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"분석 처리 중 오류가 발생했습니다: {exc}") from exc

    with SessionLocal() as session:
        job = AnalysisJob(
            source_name=file.filename or "uploaded_file",
            file_type=result.file_type,
            status="completed",
            summary_json=json.dumps(result.exploration["summary"], ensure_ascii=False),
            report_markdown=result.report_markdown,
        )
        session.add(job)
        session.commit()
        session.refresh(job)

    return {
        "job_id": job.id,
        "source_name": result.source_name,
        "file_type": result.file_type,
        "exploration": result.exploration,
        "preprocessing": result.preprocessing,
        "eda": result.eda,
        "visualization": result.visualization,
        "insights": result.insights,
        "report_markdown": result.report_markdown,
    }
