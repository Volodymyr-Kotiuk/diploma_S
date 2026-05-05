from pathlib import Path

from fastapi import HTTPException
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle
from sqlalchemy import desc, select
from sqlalchemy.orm import Session

from app import models
from app.config import get_settings
from app.utils.time_utils import utc_now

_FONT_NAMES: tuple[str, str] | None = None


def generate_environment_report(db: Session, environment_id: int) -> models.Report:
    env = db.get(models.Environment, environment_id)
    if not env:
        raise HTTPException(status_code=404, detail="Environment not found")
    nodes = db.scalars(select(models.Node).where(models.Node.environment_id == environment_id)).all()
    incidents = db.scalars(
        select(models.Incident)
        .join(models.Node, models.Node.id == models.Incident.node_id)
        .where(models.Node.environment_id == environment_id)
        .order_by(desc(models.Incident.started_at))
        .limit(50)
    ).all()
    recommendations = db.scalars(
        select(models.Recommendation)
        .join(models.Node, models.Node.id == models.Recommendation.node_id)
        .where(models.Node.environment_id == environment_id)
        .order_by(desc(models.Recommendation.created_at))
        .limit(50)
    ).all()
    story = _pdf_report(
        title=f"Звіт середовища: {env.name}",
        summary=f"Тип: {env.environment_type}. Статус: {env.status}. Вузлів: {len(nodes)}.",
        nodes=nodes,
        incidents=incidents,
        recommendations=recommendations,
        latest_metrics=_latest_metrics(db, nodes),
        latest_diagnostics=_latest_diagnostics(db, nodes),
        capacity_forecasts=_capacity_forecasts(db, nodes),
    )
    return _save_report(db, "environment", story, environment_id=environment_id)


def generate_node_report(db: Session, node_id: int) -> models.Report:
    node = db.get(models.Node, node_id)
    if not node:
        raise HTTPException(status_code=404, detail="Node not found")
    incidents = db.scalars(select(models.Incident).where(models.Incident.node_id == node_id).order_by(desc(models.Incident.started_at)).limit(50)).all()
    recommendations = db.scalars(select(models.Recommendation).where(models.Recommendation.node_id == node_id).order_by(desc(models.Recommendation.created_at)).limit(50)).all()
    story = _pdf_report(
        title=f"Звіт вузла: {node.name}",
        summary=f"Тип: {node.node_type}. Роль: {node.role}. Статус: {node.status}.",
        nodes=[node],
        incidents=incidents,
        recommendations=recommendations,
        latest_metrics=_latest_metrics(db, [node]),
        latest_diagnostics=_latest_diagnostics(db, [node]),
        capacity_forecasts=_capacity_forecasts(db, [node]),
    )
    return _save_report(db, "node", story, node_id=node_id)


def _save_report(db: Session, report_type: str, story: list, environment_id: int | None = None, node_id: int | None = None) -> models.Report:
    reports_dir = Path(get_settings().reports_dir)
    reports_dir.mkdir(parents=True, exist_ok=True)
    name = f"{report_type}_{environment_id or node_id}_{utc_now().strftime('%Y%m%d_%H%M%S')}.pdf"
    path = reports_dir / name
    _build_pdf(path, story)
    report = models.Report(environment_id=environment_id, node_id=node_id, report_type=report_type, file_path=str(path))
    db.add(report)
    db.commit()
    db.refresh(report)
    return report


def _latest_metrics(db: Session, nodes: list[models.Node]) -> dict[int, models.ResourceMetric]:
    result: dict[int, models.ResourceMetric] = {}
    for node in nodes:
        metric = db.scalar(select(models.ResourceMetric).where(models.ResourceMetric.node_id == node.id).order_by(desc(models.ResourceMetric.timestamp), desc(models.ResourceMetric.id)).limit(1))
        if metric:
            result[node.id] = metric
    return result


def _latest_diagnostics(db: Session, nodes: list[models.Node]) -> dict[int, models.Diagnostic]:
    result: dict[int, models.Diagnostic] = {}
    for node in nodes:
        diagnostic = db.scalar(select(models.Diagnostic).where(models.Diagnostic.node_id == node.id).order_by(desc(models.Diagnostic.created_at), desc(models.Diagnostic.id)).limit(1))
        if diagnostic:
            result[node.id] = diagnostic
    return result


def _capacity_forecasts(db: Session, nodes: list[models.Node]) -> list[models.CapacityForecast]:
    node_ids = [node.id for node in nodes]
    if not node_ids:
        return []
    rows = db.scalars(select(models.CapacityForecast).where(models.CapacityForecast.node_id.in_(node_ids)).order_by(desc(models.CapacityForecast.created_at)).limit(80)).all()
    covered = {row.node_id for row in rows}
    missing = [node for node in nodes if node.id not in covered]
    if missing:
        from app.services.capacity_planner import run_capacity_planning

        for node in missing:
            run_capacity_planning(db, node.id)
        rows = db.scalars(select(models.CapacityForecast).where(models.CapacityForecast.node_id.in_(node_ids)).order_by(desc(models.CapacityForecast.created_at)).limit(80)).all()
    return rows


def _pdf_report(
    title: str,
    summary: str,
    nodes: list[models.Node],
    incidents: list[models.Incident],
    recommendations: list[models.Recommendation],
    latest_metrics: dict[int, models.ResourceMetric],
    latest_diagnostics: dict[int, models.Diagnostic],
    capacity_forecasts: list[models.CapacityForecast],
) -> list:
    styles = _styles()
    timestamps = [metric.timestamp for metric in latest_metrics.values()]
    period = f"до {_fmt(max(timestamps))}" if timestamps else "метрики ще не зібрані"

    story: list = [
        Paragraph(title, styles["title"]),
        Paragraph(f"PDF-звіт створено {_fmt(utc_now())} UTC", styles["muted"]),
        Spacer(1, 5 * mm),
        Paragraph("Висновок", styles["section"]),
        Paragraph(summary, styles["body"]),
        Paragraph(f"Період аналізу: {period}.", styles["body"]),
        Paragraph(
            "Звіт містить вузли, основні метрики, підсумок діагностики, першопричину, інциденти, рекомендації та capacity planning.",
            styles["body"],
        ),
        Spacer(1, 5 * mm),
    ]

    story.extend(
        _table(
            "Вузли",
            ["Назва", "Тип", "Роль", "Статус", "CPU", "RAM MB"],
            [
                [
                    node.name,
                    _node_type_label(node.node_type),
                    _role_label(node.role),
                    _status_label(node.status),
                    node.allocated_cpu_cores or "—",
                    node.allocated_ram_mb or "—",
                ]
                for node in nodes
            ],
            [42 * mm, 34 * mm, 28 * mm, 28 * mm, 20 * mm, 24 * mm],
            styles,
        )
    )

    metric_rows = [
        [
            node.name,
            _fmt(metric.timestamp),
            _pct(metric.cpu_usage_percent),
            _pct(metric.ram_usage_percent),
            _pct(metric.swap_usage_percent),
            _pct(metric.disk_usage_percent),
            metric.process_count or "—",
            _num(metric.temperature_celsius),
        ]
        for node in nodes
        if (metric := latest_metrics.get(node.id))
    ]
    story.extend(
        _table(
            "Основні метрики",
            ["Вузол", "Час", "CPU", "RAM", "Підкачка", "Диск", "Процеси", "Темп. °C"],
            metric_rows,
            [34 * mm, 36 * mm, 18 * mm, 18 * mm, 24 * mm, 18 * mm, 22 * mm, 22 * mm],
            styles,
            empty_text="Метрик немає",
        )
    )

    diagnostic_rows = [
        [
            node.name,
            _root_cause_label(diagnostic.root_cause),
            _diagnosis_type_label(diagnostic.diagnosis_type),
            _severity_label(diagnostic.severity),
            _num(diagnostic.risk_score),
            _pct(diagnostic.confidence),
        ]
        for node in nodes
        if (diagnostic := latest_diagnostics.get(node.id))
    ]
    story.extend(
        _table(
            "Підсумок діагностики",
            ["Вузол", "Першопричина", "Тип діагнозу", "Рівень", "Ризик", "Впевненість"],
            diagnostic_rows,
            [36 * mm, 45 * mm, 42 * mm, 24 * mm, 18 * mm, 26 * mm],
            styles,
            empty_text="Діагнозів немає",
        )
    )

    story.extend(
        _table(
            "Інциденти",
            ["Час", "Назва", "Рівень", "Статус", "Першопричина"],
            [
                [
                    _fmt(incident.started_at),
                    incident.title,
                    _severity_label(incident.severity),
                    _status_label(incident.status),
                    _root_cause_label(incident.root_cause),
                ]
                for incident in incidents
            ],
            [34 * mm, 62 * mm, 24 * mm, 26 * mm, 48 * mm],
            styles,
            empty_text="Інцидентів немає",
        )
    )

    story.extend(
        _table(
            "Рекомендації",
            ["Назва", "Пріоритет", "Статус", "Причина", "Очікуваний ефект"],
            [
                [
                    rec.title,
                    _priority_label(rec.priority),
                    _status_label(rec.status),
                    rec.reason or "—",
                    rec.expected_effect or "—",
                ]
                for rec in recommendations
            ],
            [48 * mm, 24 * mm, 26 * mm, 58 * mm, 44 * mm],
            styles,
            empty_text="Рекомендацій немає",
        )
    )

    story.extend(
        _table(
            "Capacity planning",
            ["Вузол", "Метрика", "Поточне", "Прогноз", "Тренд", "Рекомендація"],
            [
                [
                    forecast.node_id,
                    _metric_label(forecast.metric_name),
                    _num(forecast.current_value),
                    _num(forecast.predicted_value),
                    _trend_label(forecast.trend_direction),
                    forecast.recommendation,
                ]
                for forecast in capacity_forecasts
            ],
            [18 * mm, 28 * mm, 24 * mm, 24 * mm, 28 * mm, 78 * mm],
            styles,
            empty_text="Capacity forecast ще не створено",
        )
    )
    return story


def _build_pdf(path: Path, story: list) -> None:
    doc = SimpleDocTemplate(
        str(path),
        pagesize=landscape(A4),
        leftMargin=12 * mm,
        rightMargin=12 * mm,
        topMargin=12 * mm,
        bottomMargin=12 * mm,
        title=path.stem,
    )
    doc.build(story)


def _styles() -> dict[str, ParagraphStyle]:
    regular_font, bold_font = _report_fonts()
    return {
        "title": ParagraphStyle("title", fontName=bold_font, fontSize=18, leading=22, textColor=colors.HexColor("#111827"), spaceAfter=4),
        "section": ParagraphStyle("section", fontName=bold_font, fontSize=12, leading=15, textColor=colors.HexColor("#111827"), spaceBefore=8, spaceAfter=6),
        "body": ParagraphStyle("body", fontName=regular_font, fontSize=9, leading=12, textColor=colors.HexColor("#334155"), spaceAfter=4),
        "muted": ParagraphStyle("muted", fontName=regular_font, fontSize=8, leading=10, textColor=colors.HexColor("#64748b")),
        "cell": ParagraphStyle("cell", fontName=regular_font, fontSize=7.5, leading=9.2, textColor=colors.HexColor("#111827")),
        "head": ParagraphStyle("head", fontName=bold_font, fontSize=7.5, leading=9.2, textColor=colors.HexColor("#334155")),
    }


def _table(
    title: str,
    headers: list[str],
    rows: list[list],
    col_widths: list[float],
    styles: dict[str, ParagraphStyle],
    empty_text: str = "Даних немає",
) -> list:
    story: list = [Paragraph(title, styles["section"])]
    if not rows:
        story.extend([Paragraph(empty_text, styles["body"]), Spacer(1, 3 * mm)])
        return story
    data = [[Paragraph(str(header), styles["head"]) for header in headers]]
    data.extend([[Paragraph(_safe(cell), styles["cell"]) for cell in row] for row in rows])
    table = Table(data, colWidths=col_widths, repeatRows=1, hAlign="LEFT")
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#f1f5f9")),
                ("LINEBELOW", (0, 0), (-1, 0), 0.7, colors.HexColor("#cbd5e1")),
                ("LINEBELOW", (0, 1), (-1, -1), 0.35, colors.HexColor("#e2e8f0")),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("LEFTPADDING", (0, 0), (-1, -1), 5),
                ("RIGHTPADDING", (0, 0), (-1, -1), 5),
                ("TOPPADDING", (0, 0), (-1, -1), 5),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
            ]
        )
    )
    story.extend([table, Spacer(1, 5 * mm)])
    return story


def _report_fonts() -> tuple[str, str]:
    global _FONT_NAMES
    if _FONT_NAMES:
        return _FONT_NAMES

    candidates = [
        ("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"),
        ("/usr/share/fonts/dejavu/DejaVuSans.ttf", "/usr/share/fonts/dejavu/DejaVuSans-Bold.ttf"),
        ("/System/Library/Fonts/Supplemental/Arial.ttf", "/System/Library/Fonts/Supplemental/Arial Bold.ttf"),
        ("/Library/Fonts/Arial Unicode.ttf", "/Library/Fonts/Arial Unicode.ttf"),
        ("/System/Library/Fonts/Supplemental/Arial Unicode.ttf", "/System/Library/Fonts/Supplemental/Arial Unicode.ttf"),
    ]
    for regular_path, bold_path in candidates:
        regular = Path(regular_path)
        bold = Path(bold_path)
        if regular.exists():
            if "ReportFont" not in pdfmetrics.getRegisteredFontNames():
                pdfmetrics.registerFont(TTFont("ReportFont", str(regular)))
            if "ReportFontBold" not in pdfmetrics.getRegisteredFontNames():
                pdfmetrics.registerFont(TTFont("ReportFontBold", str(bold if bold.exists() else regular)))
            _FONT_NAMES = ("ReportFont", "ReportFontBold")
            return _FONT_NAMES

    _FONT_NAMES = ("Helvetica", "Helvetica-Bold")
    return _FONT_NAMES


def _safe(value) -> str:
    if value is None:
        return "—"
    return str(value).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def _fmt(value) -> str:
    if value is None:
        return "—"
    return str(value).split(".")[0]


def _num(value) -> str:
    if value is None:
        return "—"
    if isinstance(value, float):
        return f"{value:.1f}"
    return str(value)


def _pct(value) -> str:
    if value is None:
        return "—"
    return f"{float(value):.1f}%"


def _node_type_label(value: str | None) -> str:
    return {"remote_agent": "Вузол агента", "virtual_node": "Віртуальний вузол", "simulated_vm": "Віртуальна VM"}.get(value or "", value or "—")


def _role_label(value: str | None) -> str:
    return {"server": "Сервер", "service": "Сервіс/API", "database": "База даних", "other": "Інше", "unknown": "Не вказано"}.get(value or "", value or "—")


def _status_label(value: str | None) -> str:
    return {
        "waiting": "очікує",
        "online": "онлайн",
        "offline": "офлайн",
        "healthy": "справний",
        "warning": "попередження",
        "critical": "критичний",
        "open": "відкритий",
        "acknowledged": "підтверджений",
        "resolved": "закритий",
        "new": "нова",
        "accepted": "прийнята",
        "ignored": "проігнорована",
    }.get(value or "", value or "—")


def _severity_label(value: str | None) -> str:
    return {"low": "низький", "medium": "середній", "high": "високий", "critical": "критичний"}.get(value or "", value or "—")


def _priority_label(value: str | None) -> str:
    return _severity_label(value)


def _diagnosis_type_label(value: str | None) -> str:
    return {
        "cpu_saturation": "Перевантаження CPU",
        "memory_pressure": "Нестача пам’яті",
        "swap_pressure": "Навантаження підкачки",
        "disk_io_bottleneck": "Обмеження дискових операцій",
        "network_pressure": "Навантаження мережі",
        "thermal_risk": "Температурний ризик",
        "resource_overcommit": "Перевиділення ресурсів",
        "underutilization": "Недовикористання ресурсів",
        "service_degradation": "Деградація сервісу",
        "unknown_degradation": "Невизначена деградація",
    }.get(value or "", value or "—")


def _root_cause_label(value: str | None) -> str:
    return {
        "CPU saturation": "Перевантаження CPU",
        "Memory pressure": "Нестача оперативної пам’яті",
        "Swap pressure": "Надмірне використання підкачки",
        "Disk I/O bottleneck": "Обмеження дискових операцій",
        "Network pressure": "Навантаження мережі",
        "Thermal risk": "Температурний ризик",
        "Resource overcommit": "Перевиділення ресурсів",
        "Underutilization": "Недовикористання ресурсів",
        "Service degradation": "Деградація сервісу",
        "Unknown degradation": "Невизначена деградація",
    }.get(value or "", value or "—")


def _metric_label(value: str | None) -> str:
    return {"cpu_usage_percent": "CPU", "ram_usage_percent": "RAM", "disk_usage_percent": "Диск"}.get(value or "", value or "—")


def _trend_label(value: str | None) -> str:
    return {"increasing": "зростає", "decreasing": "спадає", "stable": "стабільний"}.get(value or "", value or "—")
