from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from backend.database import get_db
from backend.models import User, Comment
from backend.schemas import CommentCreate, CommentResponse
from backend.auth import get_current_user

router = APIRouter(prefix="/comments", tags=["Comments"])

@router.get("/{symbol}", response_model=List[CommentResponse])
def get_comments(symbol: str, db: Session = Depends(get_db)):
    """Fetches all comments/discussions for a given asset symbol."""
    comments = db.query(Comment).filter(Comment.symbol == symbol).order_by(Comment.created_at.asc()).all()
    return comments

@router.post("", response_model=CommentResponse, status_code=status.HTTP_201_CREATED)
def create_comment(data: CommentCreate, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Creates a new comment or nested reply for an asset."""
    # If it is a reply, verify parent comment exists and belongs to the same symbol
    if data.parent_id is not None:
        parent = db.query(Comment).filter(Comment.id == data.parent_id).first()
        if not parent:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Parent comment not found"
            )
        if parent.symbol != data.symbol:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Parent comment does not match the active asset symbol"
            )
            
    comment = Comment(
        symbol=data.symbol,
        content=data.content,
        user_id=current_user.id,
        parent_id=data.parent_id
    )
    db.add(comment)
    db.commit()
    db.refresh(comment)
    return comment

@router.delete("/{comment_id}", status_code=status.HTTP_200_OK)
def delete_comment(comment_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Deletes a comment. Only the owner of the comment can perform this action."""
    comment = db.query(Comment).filter(Comment.id == comment_id).first()
    if not comment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Comment not found"
        )
    if comment.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not authorized to delete this comment"
        )
        
    db.delete(comment)
    db.commit()
    return {"message": "Comment successfully deleted"}
