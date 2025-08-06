import random
import string

from django.contrib.auth import get_user_model
from django.db import models
from django.db.models.signals import pre_save
from django.dispatch import receiver

# Core Model for the application
User = get_user_model()


class CoreModel(models.Model):
    dtm_created = models.DateTimeField(auto_now_add=True)
    dtm_updated = models.DateTimeField(auto_now=True)
    slug = models.CharField(max_length=12, unique=True)
    updated_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name="updated_%(class)s",
    )

    def generate_slug(self):
        while True:
            slug_candidate = random.choice(string.ascii_letters) + "".join(
                random.choices(string.ascii_letters + string.digits, k=11)
            )
            if not self.__class__.objects.filter(slug=slug_candidate).exists():
                return slug_candidate

    class Meta:
        abstract = True


@receiver(pre_save)
def ensure_slug(sender, instance, **kwargs):
    if isinstance(instance, CoreModel) and not instance.slug:
        instance.slug = instance.generate_slug()
