
import logging
from config import supabase

logger = logging.getLogger(__name__)

def log_qr_usage(user_id: int | str, content: str) -> None:
    if not supabase: return
    try:
        data = {"user_id": str(user_id), "content": content}
        supabase.table("qr_logs").insert(data).execute()
    except Exception as e:
        logger.error(f"QR log hatası (User: {user_id}): {e}")

def log_pdf_usage(user_id: int | str, pdf_type: str) -> None:
    if not supabase: return
    try:
        data = {"user_id": str(user_id), "type": pdf_type}
        supabase.table("pdf_logs").insert(data).execute()
    except Exception as e:
        logger.error(f"PDF log hatası (User: {user_id}): {e}")
