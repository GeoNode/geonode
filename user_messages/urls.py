try:
    from django.conf.urls import url, patterns
except ImportError:
    from django.conf.urls.defaults import url, patterns

urlpatterns = patterns("user_messages.views",
    url(r"^inbox/$", "inbox", name="messages_inbox"),
    url(r"^create/$", "message_create", name="message_create"),
    url(r"^create/(?P<user_id>\d+)/$", "message_create", name="message_create"),
    url(r"^thread/(?P<thread_id>\d+)/$", "thread_detail",
        name="messages_thread_detail"),
    url(r"^thread/(?P<thread_id>\d+)/delete/$", "thread_delete",
        name="messages_thread_delete"),

    url(r"^search/$", "message_search", name="message_search"),
)
