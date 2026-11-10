import json

from django.contrib.auth import get_user_model
from django.http import HttpResponse
from oauth2_provider.views.introspect import IntrospectTokenView

from geonode.base.oauth2_validators import get_user_groups_and_roles


class GeoNodeIntrospectTokenView(IntrospectTokenView):
    @staticmethod
    def get_token_response(token_value=None):
        response = IntrospectTokenView.get_token_response(token_value)
        if response.status_code != 200:
            return response

        data = json.loads(response.content)
        if not data.get("active") or "username" not in data:
            return response

        user = get_user_model().objects.filter(username=data["username"]).first()
        if not user:
            return response

        data["groups"], data["roles"] = get_user_groups_and_roles(user)
        return HttpResponse(content=json.dumps(data), status=200, content_type="application/json")
