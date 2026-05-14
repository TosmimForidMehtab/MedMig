from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from typing import List
from uuid import UUID

from app.api import deps
from app.models.user import User
from app.models.family_member import FamilyMember
from app.schemas.family_member import FamilyMember as FamilyMemberSchema, FamilyMemberCreate, FamilyMemberUpdate
from app.config import settings

router = APIRouter()

@router.post("/", response_model=FamilyMemberSchema)
async def create_family_member(
    member_in: FamilyMemberCreate,
    db: AsyncSession = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user)
):
    # Check limit
    result = await db.execute(select(FamilyMember).where(FamilyMember.user_id == current_user.id))
    members = result.scalars().all()
    if len(members) >= settings.MAX_FAMILY_MEMBERS:
        raise HTTPException(
            status_code=400,
            detail=f"Maximum limit of {settings.MAX_FAMILY_MEMBERS} family members reached."
        )
    
    db_obj = FamilyMember(
        user_id=current_user.id,
        **member_in.model_dump()
    )
    db.add(db_obj)
    await db.commit()
    await db.refresh(db_obj)
    return db_obj

@router.get("/", response_model=List[FamilyMemberSchema])
async def list_family_members(
    db: AsyncSession = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user)
):
    result = await db.execute(select(FamilyMember).where(FamilyMember.user_id == current_user.id))
    return result.scalars().all()

@router.get("/{member_id}", response_model=FamilyMemberSchema)
async def get_family_member(
    member_id: UUID,
    db: AsyncSession = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user)
):
    result = await db.execute(
        select(FamilyMember)
        .where(FamilyMember.id == member_id, FamilyMember.user_id == current_user.id)
    )
    member = result.scalars().first()
    if not member:
        raise HTTPException(status_code=404, detail="Family member not found")
    return member

@router.put("/{member_id}", response_model=FamilyMemberSchema)
async def update_family_member(
    member_id: UUID,
    member_in: FamilyMemberUpdate,
    db: AsyncSession = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user)
):
    result = await db.execute(
        select(FamilyMember)
        .where(FamilyMember.id == member_id, FamilyMember.user_id == current_user.id)
    )
    member = result.scalars().first()
    if not member:
        raise HTTPException(status_code=404, detail="Family member not found")
    
    update_data = member_in.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(member, field, value)
    
    await db.commit()
    await db.refresh(member)
    return member

@router.delete("/{member_id}")
async def delete_family_member(
    member_id: UUID,
    db: AsyncSession = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user)
):
    result = await db.execute(
        select(FamilyMember)
        .where(FamilyMember.id == member_id, FamilyMember.user_id == current_user.id)
    )
    member = result.scalars().first()
    if not member:
        raise HTTPException(status_code=404, detail="Family member not found")
    
    await db.delete(member)
    await db.commit()
    return {"message": "Family member deleted successfully"}
