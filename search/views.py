from django.shortcuts import render

from accounts.serializers import PersonRowSerializer
from posts.serializers import PostSerializer
from search.queries import search as search_query
from common.web import shell, signed_in


def search(request):
    results = search_query(request.user, request.GET.get("q", ""))
    return render(request, "search/search.html", shell(
        request,
        active="search",
        query=results["query"],
        people=PersonRowSerializer(results["people"], many=True,
                                   context={"request": request}).data,
        posts=PostSerializer(results["posts"], many=True,
                             context={"request": request}).data,
    ))
