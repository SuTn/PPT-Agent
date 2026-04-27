from fastapi import APIRouter, HTTPException

from ppt_agent.templates.registry import list_all_templates, load_template

router = APIRouter()


@router.get("/templates")
async def list_templates():
    return {"templates": list_all_templates()}


@router.get("/templates/{key}")
async def get_template(key: str):
    try:
        return load_template(key)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
