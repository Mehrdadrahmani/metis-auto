"""Which messages may use the semantic cache (PLAN E8). Conservative by design."""

from __future__ import annotations

import re

HISTORY = re.compile(r"(^|\s)(اون|آن|قبلی|همین|همون|این|بالا|it|that|this|those|previous|above)(\s|[.,؟?!]|$)", re.IGNORECASE)
TIME = re.compile(r"(امروز|الان|فردا|دیروز|هفته|ماه\s*جاری|قیمت|نرخ|موجودی|today|tomorrow|now|price|current|latest)", re.IGNORECASE)
PERSONAL = re.compile(
    r"(09\d{9}|۰۹[۰-۹]{9}|\+?98\d{10}|\b\d{10}\b|\b\d{16}\b|\b(\d{4}[- ]){3}\d{4}\b|[\w.+-]+@[\w-]+\.\w+|"
    r"(سفارش|پیگیری|کد\s*ملی|شماره\s*کارت|order|tracking)\s*[:#]?\s*[\d۰-۹]+)", re.IGNORECASE)


def is_cacheable(text: str, first_turn: bool, has_image: bool = False, uses_rag: bool = False, context_hash: str | None = None) -> tuple[bool, str]:
    if has_image:
        return False, "image"
    if uses_rag and not context_hash:
        return False, "rag"
    if PERSONAL.search(text):
        return False, "personal"
    if TIME.search(text):
        return False, "time"
    if not first_turn and HISTORY.search(text):
        return False, "history"
    return True, "ok"
