from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional
from backend.database import get_db
from backend.models import User, Comment, CommentReaction
from backend.schemas import CommentCreate, CommentResponse, CommentReactRequest
from backend.auth import get_current_user, oauth2_scheme
from jose import jwt, JWTError
from backend.config import SECRET_KEY, ALGORITHM

router = APIRouter(prefix="/comments", tags=["Comments"])


def _enrich_comments(comments: list, db: Session, user_id: Optional[int] = None) -> list:
    """Attaches like/dislike counts and user_reaction to a list of Comment ORM objects."""
    result = []
    for c in comments:
        reactions = db.query(CommentReaction).filter(CommentReaction.comment_id == c.id).all()
        likes = sum(1 for r in reactions if r.reaction == "like")
        dislikes = sum(1 for r in reactions if r.reaction == "dislike")
        user_reaction = None
        if user_id:
            for r in reactions:
                if r.user_id == user_id:
                    user_reaction = r.reaction
                    break

        result.append({
            "id": c.id,
            "symbol": c.symbol,
            "content": c.content,
            "created_at": c.created_at,
            "parent_id": c.parent_id,
            "user": c.user,
            "likes": likes,
            "dislikes": dislikes,
            "user_reaction": user_reaction,
        })
    return result


def _get_optional_user_id(token: Optional[str], db: Session) -> Optional[int]:
    """Tries to decode user id from an optional token. Returns None if unauthenticated."""
    if not token:
        return None
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username = payload.get("sub")
        if not username:
            return None
        user = db.query(User).filter(User.username == username).first()
        return user.id if user else None
    except JWTError:
        return None


@router.get("/{symbol}", response_model=List[CommentResponse])
def get_comments(symbol: str, token: Optional[str] = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    """Fetches all comments/discussions for a given asset symbol, enriched with reaction counts."""
    user_id = _get_optional_user_id(token, db)
    comments = db.query(Comment).filter(Comment.symbol == symbol).order_by(Comment.created_at.asc()).all()
    return _enrich_comments(comments, db, user_id)


@router.post("", response_model=CommentResponse, status_code=status.HTTP_201_CREATED)
def create_comment(data: CommentCreate, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Creates a new comment or nested reply for an asset."""
    if data.parent_id is not None:
        parent = db.query(Comment).filter(Comment.id == data.parent_id).first()
        if not parent:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Parent comment not found")
        if parent.symbol != data.symbol:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Parent comment does not match the active asset symbol")

    comment = Comment(
        symbol=data.symbol,
        content=data.content,
        user_id=current_user.id,
        parent_id=data.parent_id
    )
    db.add(comment)
    db.commit()
    db.refresh(comment)
    enriched = _enrich_comments([comment], db, current_user.id)
    return enriched[0]


@router.delete("/{comment_id}", status_code=status.HTTP_200_OK)
def delete_comment(comment_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Deletes a comment. Only the owner of the comment can perform this action."""
    comment = db.query(Comment).filter(Comment.id == comment_id).first()
    if not comment:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Comment not found")
    if comment.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You are not authorized to delete this comment")

    db.delete(comment)
    db.commit()
    return {"message": "Comment successfully deleted"}


@router.post("/{comment_id}/react", status_code=status.HTTP_200_OK)
def react_to_comment(
    comment_id: int,
    data: CommentReactRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Toggle a like or dislike reaction on a comment.
    If the same reaction already exists, it will be removed (toggle off).
    If a different reaction exists, it will be replaced.
    """
    if data.reaction not in ("like", "dislike"):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="reaction must be 'like' or 'dislike'")

    comment = db.query(Comment).filter(Comment.id == comment_id).first()
    if not comment:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Comment not found")

    existing = db.query(CommentReaction).filter(
        CommentReaction.comment_id == comment_id,
        CommentReaction.user_id == current_user.id
    ).first()

    if existing:
        if existing.reaction == data.reaction:
            # Toggle off — remove reaction
            db.delete(existing)
            db.commit()
            return {"action": "removed", "reaction": data.reaction}
        else:
            # Switch reaction
            existing.reaction = data.reaction
            db.commit()
            return {"action": "switched", "reaction": data.reaction}
    else:
        new_reaction = CommentReaction(
            comment_id=comment_id,
            user_id=current_user.id,
            reaction=data.reaction
        )
        db.add(new_reaction)
        db.commit()
        return {"action": "added", "reaction": data.reaction}
