# notes/signals.py
from django.dispatch import receiver
from django.db.models.signals import post_save
from .models import NoteReception
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync

@receiver(post_save, sender=NoteReception)
def send_note_notification(sender, instance, created, **kwargs):
    if created:
        channel_layer = get_channel_layer()
        group_name = f"user_{instance.destinataire.id}"
        async_to_sync(channel_layer.group_send)(
            group_name,
            {
                "type": "send_note_notification",
                "message": f"Nouvelle note reçue de {instance.note.expediteur.get_full_name()}",
            }
        )
