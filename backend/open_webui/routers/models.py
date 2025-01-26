import logging
from typing import Optional

from open_webui.models.models import (
    ModelForm,
    ModelModel,
    ModelResponse,
    ModelUserResponse,
    Models,
)
from open_webui.constants import ERROR_MESSAGES
from fastapi import APIRouter, Depends, HTTPException, Request, status


from open_webui.utils.auth import get_admin_user, get_verified_user
from open_webui.utils.access_control import has_access, has_permission

from open_webui.env import SRC_LOG_LEVELS

log = logging.getLogger(__name__)
log.setLevel(SRC_LOG_LEVELS["MODELS"])
router = APIRouter()


###########################
# GetModels
###########################


@router.get("/", response_model=list[ModelUserResponse])
async def get_models(id: Optional[str] = None, user=Depends(get_verified_user)):
    log.debug(f"Getting models for user: {user}")
    if user.role == "admin":
        return Models.get_models()
    else:
        return Models.get_models_by_user_id(user.id)


###########################
# GetBaseModels
###########################


@router.get("/base", response_model=list[ModelResponse])
async def get_base_models(user=Depends(get_admin_user)):
    log.debug(f"Getting base models")
    return Models.get_base_models()


############################
# CreateNewModel
############################


@router.post("/create", response_model=Optional[ModelModel])
async def create_new_model(
    request: Request,
    form_data: ModelForm,
    user=Depends(get_verified_user),
):
    log.debug(f"Creating new model: {form_data}")
    if user.role != "admin" and not has_permission(
        user.id, "workspace.models", request.app.state.config.USER_PERMISSIONS
    ):
        log.debug(f"User does not have permission to create model")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=ERROR_MESSAGES.UNAUTHORIZED,
        )

    model = Models.get_model_by_id(form_data.id)
    if model:
        log.debug(f"Model id already taken: {form_data.id}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=ERROR_MESSAGES.MODEL_ID_TAKEN,
        )

    else:
        model = Models.insert_new_model(form_data, user.id)
        if model:
            log.debug(f"Model created: {model}")
            return model
        else:
            log.debug(f"Error creating model because user is not authorized")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=ERROR_MESSAGES.DEFAULT(),
            )


###########################
# GetModelById
###########################


# Note: We're not using the typical url path param here, but instead using a query parameter to allow '/' in the id
@router.get("/model", response_model=Optional[ModelResponse])
async def get_model_by_id(id: str, user=Depends(get_verified_user)):
    log.debug(f"Getting model by id: {id}")
    model = Models.get_model_by_id(id)
    if model:
        if (
            user.role == "admin"
            or model.user_id == user.id
            or has_access(user.id, "read", model.access_control)
        ):
            return model
    else:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=ERROR_MESSAGES.NOT_FOUND,
        )


############################
# ToggelModelById
############################


@router.post("/model/toggle", response_model=Optional[ModelResponse])
async def toggle_model_by_id(id: str, user=Depends(get_verified_user)):
    log.debug(f"Toggling model: {id}")
    model = Models.get_model_by_id(id)
    if model:
        if (
            user.role == "admin"
            or model.user_id == user.id
            or has_access(user.id, "write", model.access_control)
        ):
            model = Models.toggle_model_by_id(id)

            if model:
                return model
            else:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=ERROR_MESSAGES.DEFAULT("Error updating function"),
                )
        else:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=ERROR_MESSAGES.UNAUTHORIZED,
            )
    else:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=ERROR_MESSAGES.NOT_FOUND,
        )


############################
# UpdateModelById
############################


@router.post("/model/update", response_model=Optional[ModelModel])
async def update_model_by_id(
    id: str,
    form_data: ModelForm,
    user=Depends(get_verified_user),
):
    log.debug(f"Updating model: {form_data}")
    model = Models.get_model_by_id(id)

    if not model:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=ERROR_MESSAGES.NOT_FOUND,
        )

    model = Models.update_model_by_id(id, form_data)
    return model


############################
# DeleteModelById
############################


@router.delete("/model/delete", response_model=bool)
async def delete_model_by_id(id: str, user=Depends(get_verified_user)):
    model = Models.get_model_by_id(id)
    if not model:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=ERROR_MESSAGES.NOT_FOUND,
        )

    if model.user_id != user.id and user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=ERROR_MESSAGES.UNAUTHORIZED,
        )

    result = Models.delete_model_by_id(id)
    return result


@router.delete("/delete/all", response_model=bool)
async def delete_all_models(user=Depends(get_admin_user)):
    result = Models.delete_all_models()
    return result
