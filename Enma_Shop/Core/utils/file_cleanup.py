from django.core.files.storage import default_storage


def delete_file(file_field):
    if not file_field:
        return
    if not file_field.name:
        return
    try:
        if default_storage.exists(file_field.name):
            default_storage.delete(file_field.name)
    except Exception:
        pass
