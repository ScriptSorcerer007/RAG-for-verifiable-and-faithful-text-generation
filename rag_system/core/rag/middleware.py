from django.http import JsonResponse

class BlockBadRequests:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        user_agent = request.META.get("HTTP_USER_AGENT", "").lower()

        blocked_agents = ["sqlmap", "curl", "wget"]

        for bot in blocked_agents:
            if bot in user_agent:
                return JsonResponse(
                    {"error": "Blocked request"},
                    status=403
                )

        return self.get_response(request)