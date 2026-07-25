"""ConnectXperts NMS - Reports API"""
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import Response, StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.user import User, Role
from app.services.report_service import ReportService
from app.utils.security import get_current_user, check_role_permissions
import io

router = APIRouter(prefix="/api/v1/reports", tags=["Reports"])
report_service = ReportService()


@router.get("/daily")
async def get_daily_report(
    customer_id: Optional[int] = None,
    format: str = Query("json", regex="^(json|pdf|excel|csv)$"),
    current_user: User = Depends(get_current_user),
):
    """Generate daily report."""
    if current_user.role != Role.ADMIN and customer_id != current_user.customer_id:
        customer_id = current_user.customer_id
    
    report_data = await report_service.generate_daily_report(customer_id)
    return _export_report(report_data, format, "daily")


@router.get("/weekly")
async def get_weekly_report(
    customer_id: Optional[int] = None,
    format: str = Query("json", regex="^(json|pdf|excel|csv)$"),
    current_user: User = Depends(get_current_user),
):
    """Generate weekly report."""
    report_data = await report_service.generate_weekly_report(customer_id)
    return _export_report(report_data, format, "weekly")


@router.get("/monthly")
async def get_monthly_report(
    customer_id: Optional[int] = None,
    format: str = Query("json", regex="^(json|pdf|excel|csv)$"),
    current_user: User = Depends(get_current_user),
):
    """Generate monthly report."""
    report_data = await report_service.generate_monthly_report(customer_id)
    return _export_report(report_data, format, "monthly")


@router.get("/yearly")
async def get_yearly_report(
    customer_id: Optional[int] = None,
    format: str = Query("json", regex="^(json|pdf|excel|csv)$"),
    current_user: User = Depends(get_current_user),
):
    """Generate yearly report."""
    report_data = await report_service.generate_yearly_report(customer_id)
    return _export_report(report_data, format, "yearly")


def _export_report(report_data: dict, format: str, period: str):
    """Export report in requested format."""
    if format == "json":
        return report_data
    
    elif format == "pdf":
        pdf_bytes = report_service.export_to_pdf(report_data, f"{period.title()} Report")
        return Response(
            content=pdf_bytes,
            media_type="application/pdf",
            headers={"Content-Disposition": f"attachment; filename=cnms_{period}_report.pdf"}
        )
    
    elif format == "excel":
        excel_bytes = report_service.export_to_excel(report_data)
        return Response(
            content=excel_bytes,
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={"Content-Disposition": f"attachment; filename=cnms_{period}_report.xlsx"}
        )
    
    elif format == "csv":
        csv_content = report_service.export_to_csv(report_data)
        return StreamingResponse(
            iter([csv_content]),
            media_type="text/csv",
            headers={"Content-Disposition": f"attachment; filename=cnms_{period}_report.csv"}
        )
