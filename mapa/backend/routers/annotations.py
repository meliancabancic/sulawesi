from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from ..database import get_conn

router = APIRouter()


class AnnotationIn(BaseModel):
    lon:      float
    lat:      float
    text:     str
    username: str  = "anónimo"
    color:    str  = "#ffdd2c"


@router.get("/annotations")
def list_annotations():
    conn = get_conn()
    rows = conn.execute(
        "SELECT id, lon, lat, text, username, color, created_at "
        "FROM annotations ORDER BY created_at DESC"
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


@router.post("/annotations", status_code=201)
def create_annotation(ann: AnnotationIn):
    conn = get_conn()
    cur = conn.execute(
        "INSERT INTO annotations (lon, lat, text, username, color) VALUES (?,?,?,?,?)",
        [ann.lon, ann.lat, ann.text, ann.username, ann.color],
    )
    conn.commit()
    ann_id = cur.lastrowid
    row = conn.execute("SELECT * FROM annotations WHERE id=?", [ann_id]).fetchone()
    conn.close()
    return dict(row)


@router.delete("/annotations/{ann_id}", status_code=204)
def delete_annotation(ann_id: int):
    conn = get_conn()
    n = conn.execute("DELETE FROM annotations WHERE id=?", [ann_id]).rowcount
    conn.commit()
    conn.close()
    if n == 0:
        raise HTTPException(404, "Anotación no encontrada")
