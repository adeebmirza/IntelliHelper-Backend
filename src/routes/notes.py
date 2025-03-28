from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import JSONResponse, StreamingResponse
from datetime import datetime, timedelta
from bson import ObjectId
from io import BytesIO
import uuid
import secrets

from src.database import notes_collection
from src.profile.token_jwt import get_current_user  # Import JWT-based authentication dependency
from src.profile.form import NoteCreate, NoteUpdate, NoteResponse  # Define these Pydantic models separately

notes_router = APIRouter(prefix="/notes", tags=["Notes"])


@notes_router.get("/", response_model=list[NoteResponse])
async def get_all_notes(user: dict = Depends(get_current_user)):
    """Fetch all notes for the authenticated user."""
    notes = await notes_collection.find({"user_id": ObjectId(user["_id"])}).to_list(None)
    return [NoteResponse(id=note["note_id"], **note) for note in notes]



@notes_router.post("/", response_model=NoteResponse)
async def create_note(note: NoteCreate, user: dict = Depends(get_current_user)):
    """Create a new note for the authenticated user."""
    note_id = str(uuid.uuid4())
    date = datetime.utcnow()
    
    header = f"<h2>{note.title}</h2><p>Date: {date.strftime('%Y-%m-%d %H:%M:%S')}</p>"
    formatted_content = header + note.formatted_content

    note_doc = {
        "user_id": ObjectId(user["_id"]),
        "note_id": note_id,
        "title": note.title,
        "content": note.content,
        "formatted_content": formatted_content,
        "created_at": date,
        "expires_at": None
    }
    
    new_note = await notes_collection.insert_one(note_doc)
    note_doc["_id"] = new_note.inserted_id
    return NoteResponse(**note_doc, id=str(new_note.inserted_id))


@notes_router.get("/{note_id}", response_model=NoteResponse)
async def view_note(note_id: str, user: dict = Depends(get_current_user)):
    """View a single note."""
    note = await notes_collection.find_one({"note_id": note_id, "user_id": ObjectId(user["_id"])})
    if not note:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Note not found")
    return NoteResponse(**note, id=str(note["_id"]))


@notes_router.put("/{note_id}", response_model=NoteResponse)
async def edit_note(note_id: str, note_data: NoteUpdate, user: dict = Depends(get_current_user)):
    """Edit an existing note."""
    update_result = await notes_collection.update_one(
        {"note_id": note_id, "user_id": ObjectId(user["_id"])},
        {"$set": note_data.dict(exclude_unset=True)}
    )

    if update_result.modified_count == 0:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Note not found")

    updated_note = await notes_collection.find_one({"note_id": note_id})
    return NoteResponse(**updated_note, id=str(updated_note["_id"]))


@notes_router.delete("/{note_id}")
async def delete_note(note_id: str, user: dict = Depends(get_current_user)):
    """Delete a note."""
    delete_result = await notes_collection.delete_one({"note_id": note_id, "user_id": ObjectId(user["_id"])})
    if delete_result.deleted_count == 0:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Note not found")
    return JSONResponse(content={"message": "Note deleted successfully"}, status_code=200)


@notes_router.get("/download/{note_id}")
async def download_note(note_id: str, user: dict = Depends(get_current_user)):
    """Download a note as a text file."""
    note = await notes_collection.find_one({"note_id": note_id, "user_id": ObjectId(user["_id"])})
    if not note:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Note not found")

    file_content = f"Title: {note['title']}\nDate: {note['created_at'].strftime('%Y-%m-%d %H:%M:%S')}\n\n{note['content']}"
    file_stream = BytesIO(file_content.encode("utf-8"))

    return StreamingResponse(file_stream, media_type="text/plain", headers={"Content-Disposition": f"attachment; filename={note['title']}.txt"})


@notes_router.get("/share/{note_id}")
async def share_note_link(note_id: str, user: dict = Depends(get_current_user)):
    """Generate a shareable link for a note."""
    note = await notes_collection.find_one({"note_id": note_id, "user_id": ObjectId(user["_id"])})
    if not note:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Note not found")

    share_token = secrets.token_urlsafe(16)
    expiration_time = datetime.utcnow() + timedelta(hours=24)

    await notes_collection.update_one(
        {"note_id": note_id},
        {"$set": {"share_token": share_token, "expires_at": expiration_time}}
    )

    share_link = f"/notes/shared/{note_id}/{share_token}"
    return {"share_link": share_link}


@notes_router.get("/shared/{note_id}/{token}")
async def view_shared_note(note_id: str, token: str):
    """View a shared note."""
    note = await notes_collection.find_one({"note_id": note_id, "share_token": token})
    if not note:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Invalid or expired link")

    if note.get("expires_at") and datetime.utcnow() > note["expires_at"]:
        await notes_collection.update_one({"note_id": note_id}, {"$unset": {"share_token": "", "expires_at": ""}})
        raise HTTPException(status_code=status.HTTP_410_GONE, detail="The link has expired")

    return NoteResponse(**note, id=str(note["_id"]))
