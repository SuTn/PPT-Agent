import os
import tempfile

from fastapi import APIRouter, File, HTTPException, UploadFile

from ppt_agent.config import settings
from ppt_agent.tools.upload import upload_and_parse

router = APIRouter()


@router.post("/sessions/{session_id}/upload")
async def upload_file(session_id: str, file: UploadFile = File(...)):
    session_dir = settings.output_dir / session_id
    if not session_dir.exists():
        raise HTTPException(status_code=404, detail="Session not found")

    suffix = file.filename or ".bin"
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        content = await file.read()
        tmp.write(content)
        tmp_path = tmp.name

    try:
        result = upload_and_parse.invoke({"file_path": tmp_path})
    finally:
        os.unlink(tmp_path)

    return {"result": result}
