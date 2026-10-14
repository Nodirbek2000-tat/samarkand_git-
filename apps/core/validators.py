from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.validators import FileExtensionValidator
from django.utils.deconstruct import deconstructible

IMAGE_EXTENSIONS = ["jpg", "jpeg", "png", "webp", "avif", "gif"]
DOCUMENT_EXTENSIONS = ["pdf", "doc", "docx", "xls", "xlsx", "ppt", "pptx", "zip"]
VIDEO_EXTENSIONS = ["mp4", "webm", "mov", "m4v"]


@deconstructible
class MaxFileSizeValidator:
    def __init__(self, megabytes: int):
        self.megabytes = megabytes

    def __call__(self, file):
        if file and file.size > self.megabytes * 1024 * 1024:
            raise ValidationError(f"Fayl hajmi {self.megabytes} MB dan oshmasligi kerak.")

    def __eq__(self, other):
        return isinstance(other, MaxFileSizeValidator) and other.megabytes == self.megabytes


image_validators = [
    FileExtensionValidator(IMAGE_EXTENSIONS, message="Faqat rasm fayllari: " + ", ".join(IMAGE_EXTENSIONS)),
    MaxFileSizeValidator(settings.MAX_IMAGE_SIZE_MB),
]

document_validators = [
    FileExtensionValidator(DOCUMENT_EXTENSIONS, message="Ruxsat etilgan formatlar: " + ", ".join(DOCUMENT_EXTENSIONS)),
    MaxFileSizeValidator(settings.MAX_DOCUMENT_SIZE_MB),
]

video_validators = [
    FileExtensionValidator(VIDEO_EXTENSIONS, message="Faqat video fayllari: " + ", ".join(VIDEO_EXTENSIONS)),
    MaxFileSizeValidator(settings.MAX_VIDEO_SIZE_MB),
]
