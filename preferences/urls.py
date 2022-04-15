from django.urls import path
from . import views

urlpatterns = [
    path('',
         views.RankerViewSet.as_view({'get': 'retrieve'})),
    path('knows/',
         views.RankerKnowsViewSet.as_view({'get': 'list'})),
    path('knows/<str:item_id>/',
         views.RankerKnowsViewSet.as_view({'get': 'retrieve',
                                           'post': 'create',
                                           'delete': 'destroy'})),
    path('prefers/<str:preferred_id>/<str:nonpreferred_id>/',
         views.RankerPairwiseViewSet.as_view({'get': 'retrieve',
                                              'post': 'create',
                                              'delete': 'destroy'})),
    path('prefers/',
         views.RankerPairwiseViewSet.as_view({'get': 'list'})),
    path('prefers/<str:preferred_id>/<str:nonpreferred_id>/',
         views.RankerPairwiseViewSet.as_view({'get': 'retrieve',
                                              'post': 'create',
                                              'delete': 'destroy'})),
    path('sort/',
         views.RankerViewSet.as_view({'get': 'get_sorted_list'})),
    path('queue/',
         views.RankerViewSet.as_view({'get': 'get_comparisons_queue',
                                      'post': 'reset_comparisons_queue',
                                      'delete': 'clear_comparisons_queue'}))
]
