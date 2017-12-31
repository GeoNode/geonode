from django.dispatch import Signal


message_sent = Signal(providing_args=["message", "thread", "reply"])
