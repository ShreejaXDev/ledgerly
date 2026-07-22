import csv
import os
import tempfile
from datetime import datetime

from sqlalchemy.orm import Session

from app.core.logger import logger
from app.repositories.transaction_repository import TransactionRepository
from app.repositories.user_repository import UserRepository
from app.schemas.bot import TelegramMessage
from app.schemas.export import ExportFormat, ExportResponse
from app.schemas.user import UserCreate
from app.services.user_service import UserService


class ExportService:
    @staticmethod
    def _get_or_create_user(db: Session, payload: TelegramMessage):
        user = UserRepository.get_by_telegram_id(db, payload.telegram_id)
        if user is not None:
            return user

        logger.info(
            "Export user missing | telegram_id=%s registering automatically",
            payload.telegram_id,
        )
        user_data = UserCreate(
            telegram_id=payload.telegram_id,
            username=payload.username or "unknown",
            first_name=payload.first_name,
        )
        UserService.create_user(db, user_data)
        return UserRepository.get_by_telegram_id(db, payload.telegram_id)

    @staticmethod
    def _build_rows(transactions) -> list[dict[str, str]]:
        rows = []
        for transaction in transactions:
            rows.append(
                {
                    "Date": transaction.transaction_date.isoformat(),
                    "Amount": f"{float(transaction.amount):.2f}",
                    "Category": transaction.category,
                    "Description": transaction.description or "",
                    "Transaction Type": transaction.transaction_type,
                }
            )
        return rows

    @staticmethod
    def _write_csv(file_path: str, rows: list[dict[str, str]]) -> None:
        with open(file_path, "w", newline="", encoding="utf-8") as file_handle:
            writer = csv.DictWriter(
                file_handle,
                fieldnames=[
                    "Date",
                    "Amount",
                    "Category",
                    "Description",
                    "Transaction Type",
                ],
            )
            writer.writeheader()
            writer.writerows(rows)

    @staticmethod
    def _write_xlsx(file_path: str, rows: list[dict[str, str]]) -> None:
        from openpyxl import Workbook

        workbook = Workbook()
        worksheet = workbook.active
        worksheet.title = "Transactions"
        headers = ["Date", "Amount", "Category", "Description", "Transaction Type"]
        worksheet.append(headers)
        for row in rows:
            worksheet.append([row[column] for column in headers])
        workbook.save(file_path)

    @staticmethod
    def _write_pdf(file_path: str, rows: list[dict[str, str]]) -> None:
        from reportlab.lib.pagesizes import A4
        from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
        from reportlab.lib import colors
        from reportlab.lib.styles import getSampleStyleSheet

        document = SimpleDocTemplate(file_path, pagesize=A4)
        styles = getSampleStyleSheet()

        data = [["Date", "Amount", "Category", "Description", "Transaction Type"]]
        for row in rows:
            data.append([
                row["Date"],
                row["Amount"],
                row["Category"],
                row["Description"],
                row["Transaction Type"],
            ])

        table = Table(data, repeatRows=1)
        table.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1f2937")),
                    ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                    ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#d1d5db")),
                    ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                    ("FONTSIZE", (0, 0), (-1, -1), 9),
                    ("LEADING", (0, 0), (-1, -1), 11),
                    ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f9fafb")]),
                ]
            )
        )

        story = [
            Paragraph("Ledgerly Transaction Export", styles["Title"]),
            Spacer(1, 12),
            table,
        ]
        document.build(story)

    @staticmethod
    def generate_export(
        db: Session,
        payload: TelegramMessage,
        export_format: ExportFormat,
    ) -> ExportResponse | None:
        user = ExportService._get_or_create_user(db, payload)
        transactions = TransactionRepository.get_by_user(db, user.id)

        if not transactions:
            logger.info(
                "Export requested with no transactions | telegram_id=%s user_id=%s",
                payload.telegram_id,
                user.id,
            )
            return None

        rows = ExportService._build_rows(transactions)
        timestamp = datetime.utcnow().strftime("%Y%m%d%H%M%S")
        filename = f"ledgerly_transactions_{user.id}_{timestamp}.{export_format.value}"
        file_path = os.path.join(tempfile.gettempdir(), filename)

        if export_format == ExportFormat.csv:
            ExportService._write_csv(file_path, rows)
        elif export_format == ExportFormat.xlsx:
            ExportService._write_xlsx(file_path, rows)
        elif export_format == ExportFormat.pdf:
            ExportService._write_pdf(file_path, rows)
        else:
            raise ValueError(f"Unsupported export format: {export_format}")

        logger.info(
            "Export generated | telegram_id=%s user_id=%s format=%s file=%s",
            payload.telegram_id,
            user.id,
            export_format.value,
            file_path,
        )

        return ExportResponse(
            file_path=file_path,
            filename=filename,
        )