import mimetypes
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, status
from fastapi.responses import FileResponse, Response
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from pathlib import Path

from app.database import get_db
from app.models.attachment import Attachment
from app.models.comment import Comment
from app.models.ticket import Ticket
from app.models.user import User, UserRole
from app.schemas.attachment import AttachmentResponse
from app.services.storage import get_storage
from app.services.ticket_service import _check_ticket_access
from app.services.notification_service import notify_ticket_event
from app.utils.permissions import get_current_user
from app.redis import get_redis
from app.config import settings

router = APIRouter()

MAX_SIZE_BYTES = settings.MAX_FILE_SIZE_MB * 1024 * 1024

ALLOWED_MIME_PREFIXES = (
    "image/",
    "application/pdf",
    "application/msword",
    "application/vnd.openxmlformats",
    "application/vnd.ms-excel",
    "application/vnd.ms-powerpoint",
    "text/plain",
    "text/csv",
    "application/zip",
    "application/x-zip-compressed",
)


def _check_mime(mimetype: str) -> None:
    allowed = any(mimetype.startswith(p) for p in ALLOWED_MIME_PREFIXES)
    if not allowed:
        raise HTTPException(status_code=400, detail=f"Тип файла не разрешён: {mimetype}")


async def _get_ticket_or_404(db: AsyncSession, ticket_id: int) -> Ticket:
    ticket = await db.get(Ticket, ticket_id)
    if not ticket:
        raise HTTPException(status_code=404, detail="Заявка не найдена")
    return ticket


async def _upload(
    db: AsyncSession,
    current_user: User,
    ticket: Ticket,
    file: UploadFile,
    comment_id: int | None,
) -> Attachment:
    content = await file.read()
    if len(content) > MAX_SIZE_BYTES:
        raise HTTPException(
            status_code=400,
            detail=f"Файл превышает {settings.MAX_FILE_SIZE_MB} МБ",
        )
    await file.seek(0)

    mimetype = file.content_type or mimetypes.guess_type(file.filename or "")[0] or "application/octet-stream"
    _check_mime(mimetype)

    storage = get_storage()
    stored_path, size_bytes = await storage.save(file, ticket.id)

    attachment = Attachment(
        ticket_id=ticket.id,
        comment_id=comment_id,
        original_filename=file.filename or "file",
        stored_path=stored_path,
        size_bytes=size_bytes,
        mimetype=mimetype,
        uploaded_by=current_user.id,
    )
    db.add(attachment)
    await db.commit()
    await db.refresh(attachment)
    return attachment


def _attachment_response(att: Attachment) -> AttachmentResponse:
    storage = get_storage()
    uploader_name: str | None = None
    if att.uploader:
        uploader_name = att.uploader.full_name or att.uploader.username
    return AttachmentResponse(
        id=att.id,
        ticket_id=att.ticket_id,
        comment_id=att.comment_id,
        original_filename=att.original_filename,
        size_bytes=att.size_bytes,
        mimetype=att.mimetype,
        uploaded_by=att.uploaded_by,
        uploader_name=uploader_name,
        url=storage.get_url(att.stored_path),
        created_at=att.created_at,
    )


@router.get(
    "/tickets/{ticket_id}/attachments",
    response_model=list[AttachmentResponse],
    tags=["attachments"],
)
async def list_ticket_attachments(
    ticket_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    ticket = await _get_ticket_or_404(db, ticket_id)
    _check_ticket_access(ticket, current_user)
    result = await db.execute(
        select(Attachment)
        .where(Attachment.ticket_id == ticket_id)
        .order_by(Attachment.created_at)
    )
    return [_attachment_response(att) for att in result.scalars().all()]


@router.post(
    "/tickets/{ticket_id}/attachments",
    response_model=AttachmentResponse,
    status_code=status.HTTP_201_CREATED,
    tags=["attachments"],
)
async def upload_to_ticket(
    ticket_id: int,
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    redis=Depends(get_redis),
):
    ticket = await _get_ticket_or_404(db, ticket_id)
    _check_ticket_access(ticket, current_user)
    att = await _upload(db, current_user, ticket, file, comment_id=None)
    await notify_ticket_event(db, redis, ticket, "new_attachment", actor=current_user,
                              extra={"filename": att.original_filename})
    return _attachment_response(att)


@router.post(
    "/tickets/{ticket_id}/comments/{comment_id}/attachments",
    response_model=AttachmentResponse,
    status_code=status.HTTP_201_CREATED,
    tags=["attachments"],
)
async def upload_to_comment(
    ticket_id: int,
    comment_id: int,
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    redis=Depends(get_redis),
):
    ticket = await _get_ticket_or_404(db, ticket_id)
    _check_ticket_access(ticket, current_user)

    comment = await db.get(Comment, comment_id)
    if not comment or comment.ticket_id != ticket_id:
        raise HTTPException(status_code=404, detail="Комментарий не найден")

    att = await _upload(db, current_user, ticket, file, comment_id=comment_id)
    await notify_ticket_event(db, redis, ticket, "new_attachment", actor=current_user,
                              extra={"filename": att.original_filename})
    return _attachment_response(att)


@router.get("/attachments/{attachment_id}", tags=["attachments"])
async def download_attachment(
    attachment_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    att = await db.get(Attachment, attachment_id)
    if not att:
        raise HTTPException(status_code=404, detail="Файл не найден")

    ticket = await db.get(Ticket, att.ticket_id)
    _check_ticket_access(ticket, current_user)

    storage = get_storage()
    full_path = Path(settings.UPLOAD_PATH) / att.stored_path

    if not full_path.exists():
        raise HTTPException(status_code=404, detail="Файл не найден на диске")

    return FileResponse(
        path=str(full_path),
        filename=att.original_filename,
        media_type=att.mimetype,
    )


@router.delete("/attachments/{attachment_id}", status_code=status.HTTP_204_NO_CONTENT, tags=["attachments"])
async def delete_attachment(
    attachment_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    att = await db.get(Attachment, attachment_id)
    if not att:
        raise HTTPException(status_code=404, detail="Файл не найден")

    ticket = await db.get(Ticket, att.ticket_id)
    _check_ticket_access(ticket, current_user)

    if current_user.role != UserRole.admin and att.uploaded_by != current_user.id:
        raise HTTPException(status_code=403, detail="Нет прав на удаление файла")

    storage = get_storage()
    await storage.delete(att.stored_path)
    await db.delete(att)
    await db.commit()
