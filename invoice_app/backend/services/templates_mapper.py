from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class NoteField:
    key: str
    label: str
    field_type: str = "text"
    options: list[str] | None = None


SERVICE_DEFINITIONS: dict[str, dict] = {
    "Регистрация ТЗ": {
        "template": "Template_TM_1.docx",
        "notes": [
            NoteField("designation", "Обозначение"),
            NoteField("mark_type", "Тип обозначения"),
            NoteField("mktu_classes", "Классы МКТУ"),
        ],
    },
    "Поиск ТЗ": {
        "template": "Template_TM_1.docx",
        "notes": [
            NoteField("designation", "Обозначение"),
            NoteField("mark_type", "Тип обозначения"),
            NoteField("mktu_classes", "Классы МКТУ"),
        ],
    },
    "Внесение изменений в ТЗ": {
        "template": "Template_TM_2.docx",
        "notes": [NoteField("cert_number", "Номер св-ва")],
    },
    "Регистрация лицензионного Договора": {
        "template": "Template_TM_2.docx",
        "notes": [NoteField("cert_number", "Номер св-ва")],
    },
    "Регистрация отчуждения": {
        "template": "Template_TM_2.docx",
        "notes": [NoteField("cert_number", "Номер св-ва")],
    },
    "Получение дубликата св-ва": {
        "template": "Template_TM_2.docx",
        "notes": [NoteField("cert_number", "Номер св-ва")],
    },
    "Прекращение действия ТЗ": {
        "template": "Template_TM_2.docx",
        "notes": [NoteField("cert_number", "Номер св-ва")],
    },
    "Продление ТЗ": {
        "template": "Template_TM_2.docx",
        "notes": [NoteField("cert_number", "Номер св-ва")],
    },
    "Регистрация патента на ИЗ": {
        "template": "Template_Patent_1.docx",
        "notes": [
            NoteField("object_name", "Объект"),
            NoteField(
                "payment_type",
                "Тип платежа",
                field_type="select",
                options=["Авансовый платеж", "Окончательный платеж", "Полная стоимость"],
            ),
        ],
    },
    "Регистрация патента на ПО": {
        "template": "Template_Patent_1.docx",
        "notes": [
            NoteField("object_name", "Объект"),
            NoteField(
                "payment_type",
                "Тип платежа",
                field_type="select",
                options=["Авансовый платеж", "Окончательный платеж", "Полная стоимость"],
            ),
        ],
    },
    "Регистрация патента на ПМ": {
        "template": "Template_Patent_1.docx",
        "notes": [
            NoteField("object_name", "Объект"),
            NoteField(
                "payment_type",
                "Тип платежа",
                field_type="select",
                options=["Авансовый платеж", "Окончательный платеж", "Полная стоимость"],
            ),
        ],
    },
    "Поддержание в силе патента": {
        "template": "Template_Patent_2.docx",
        "notes": [
            NoteField("patent_number", "Номер патента"),
            NoteField("patent_title", "Название патента"),
            NoteField("maintenance_years", "Годы поддержания"),
        ],
    },
    "Регистрация программы ЭВМ": {
        "template": "Template_EVM_1.docx",
        "notes": [NoteField("software_title", "Название программы для ЭВМ")],
    },
}


def resolve_template_for_services(service_names: list[str]) -> str:
    templates = {SERVICE_DEFINITIONS[name]["template"] for name in service_names}
    if len(templates) != 1:
        raise ValueError("Выбранные услуги должны принадлежать одному шаблону документа.")
    return templates.pop()


def get_services_catalog() -> list[dict]:
    result: list[dict] = []
    for name, config in SERVICE_DEFINITIONS.items():
        result.append(
            {
                "name": name,
                "template": config["template"],
                "notes": [
                    {
                        "key": field.key,
                        "label": field.label,
                        "type": field.field_type,
                        "options": field.options or [],
                    }
                    for field in config["notes"]
                ],
            }
        )
    return sorted(result, key=lambda x: (x["template"], x["name"]))
