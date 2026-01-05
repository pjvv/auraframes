from pydantic import create_model, BaseModel


def create_partial_model(model: type[BaseModel]) -> type[BaseModel]:
    """Create a version of a model with all fields Optional and defaulting to None.

    This is used to create "Partial" versions of models for updates where
    only some fields may be provided.
    """
    field_definitions = {}
    for name, field_info in model.model_fields.items():
        # Make field optional with None default
        field_definitions[name] = (field_info.annotation | None, None)

    return create_model(
        f'{model.__name__}Partial',
        __base__=(model,),
        **field_definitions
    )
