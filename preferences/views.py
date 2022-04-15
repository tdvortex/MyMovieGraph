from django.http import Http404
from rest_framework.response import Response
from rest_framework import status
from rest_framework.viewsets import GenericViewSet
from rest_framework.permissions import IsAuthenticated
from neomodel.exceptions import DoesNotExist
from .models import Ranker, Item
from .cypher import (delete_all_queued_compares, delete_direct_preference, delete_ranker_knows,
                     direct_preference_exists, get_direct_preference_count, get_direct_preferences, insert_preference,
                     insert_ranker_knows, list_queued_compares, ranker_knows_item, topological_sort, populate_queued_compares)
from .serializers import RankerSerializer, ItemSerializer

class RankerViewSet(GenericViewSet):
    queryset = Ranker.nodes
    serializer_class = RankerSerializer
    permission_classes = [IsAuthenticated]

    def get_object(self):
        try:
            obj = Ranker.nodes.get(ranker_id=self.request.user.id)
        except DoesNotExist:
            raise Http404

        self.check_object_permissions(self.request, obj)

        return obj

    def retrieve(self, request, *args, **kwargs):
        ranker = self.get_object()
        ranker_data = self.serializer_class(ranker).data

        preference_data = [[ItemSerializer(i).data, ItemSerializer(j).data]
                           for i, j in get_direct_preferences(ranker)]

        # Combine into a single JSON object
        data = {'ranker': ranker_data, 'preferences': preference_data}

        return Response(data)
        
    def get_sorted_list(self, request, *args, **kwargs):
        ranker = self.get_object()
        sorted_known_items = topological_sort(ranker)
        serializer = ItemSerializer(sorted_known_items, many=True)
        return Response(data=serializer.data)

    def get_comparisons_queue(self, request, *args, **kwargs):
        ranker = self.get_object()
        data = [[ItemSerializer(i).data, ItemSerializer(j).data]
                for i, j in list_queued_compares(ranker)]

        return Response(data)

    def reset_comparisons_queue(self, request, *args, **kwargs):
        ranker = self.get_object()
        delete_all_queued_compares(ranker)
        populate_queued_compares(ranker)
        data = [[ItemSerializer(i).data, ItemSerializer(j).data]
                for i, j in list_queued_compares(ranker)]
        return Response(data, status=status.HTTP_201_CREATED)

    def clear_comparisons_queue(self, request, *args, **kwargs):
        ranker = self.get_object()
        delete_all_queued_compares(ranker)
        return Response(status=status.HTTP_204_NO_CONTENT)

class RankerKnowsViewSet(GenericViewSet):
    permission_classes = [IsAuthenticated]
    serializer_class = ItemSerializer

    def get_ranker(self):
        try:
            ranker = Ranker.nodes.get(ranker_id=self.request.user.id)
        except DoesNotExist:
            raise Http404

        self.check_object_permissions(self.request, ranker)

        return ranker   

    def get_item(self):
        try:
            item = Item.nodes.get(item_id=self.kwargs['item_id'])
        except DoesNotExist:
            raise Http404

        self.check_object_permissions(self.request, item)

        return item

    def list(self, request, *args, **kwargs):
        ranker = self.get_ranker()
        count = get_direct_preference_count(ranker)
        return Response(data={'count': count})

    def retrieve(self, request, *args, **kwargs):
        ranker = self.get_ranker()
        item = self.get_item()

        if ranker_knows_item(ranker, item):
            return Response(data={'knows':True})
        else:
            return Response(data={'knows':False})

    def create(self, request, *args, **kwargs):
        ranker = self.get_ranker()
        item = self.get_item()
        if ranker_knows_item(ranker, item):
            return Response(data={'knows':True}, status=status.HTTP_200_OK)
        else:
            insert_ranker_knows(ranker, item)
            return Response(data={'knows':True}, status=status.HTTP_201_CREATED)

    def destroy(self, request, *args, **kwargs):
        ranker = self.get_ranker()
        item = self.get_item()
        delete_ranker_knows(ranker, item)
        return Response(data={'knows':False})


class RankerPairwiseViewSet(GenericViewSet):
    permission_classes = [IsAuthenticated]

    def get_ranker(self):
        try:
            ranker = Ranker.nodes.get(ranker_id=self.request.user.id)
        except DoesNotExist:
            raise Http404

        self.check_object_permissions(self.request, ranker)

        return ranker   

    def get_items(self):
        try:
            preferred = Item.nodes.get(item_id=self.kwargs['preferred_id'])
            nonpreferred = Item.nodes.get(item_id=self.kwargs['nonpreferred_id'])
        except DoesNotExist:
            raise Http404

        self.check_object_permissions(self.request, preferred)
        self.check_object_permissions(self.request, nonpreferred)

        return preferred, nonpreferred

    def list(self, request, *args, **kwargs):
        ranker = self.get_ranker()
        count = get_direct_preference_count(ranker)
        return Response(data={'count':count})

    def retrieve(self, request, *args, **kwargs):
        ranker = self.get_ranker()
        preferred, nonpreferred = self.get_items()
        if direct_preference_exists(ranker, preferred, nonpreferred):
            data = [ItemSerializer(preferred).data,
                    ItemSerializer(nonpreferred).data]
            return Response(data=data)
        else:
            return Response(status=status.HTTP_204_NO_CONTENT)

    def create(self, request, *args, **kwargs):
        ranker = self.get_ranker()
        preferred, nonpreferred = self.get_items()

        # Try to insert the preference, see if it works
        result = insert_preference(ranker, preferred, nonpreferred)

        # Return the appropriate response code
        if result == 'Invalid':
            return Response(status=status.HTTP_400_BAD_REQUEST,)
        else:
            data = [ItemSerializer(preferred).data,
                    ItemSerializer(nonpreferred).data]

            if result == 'Exists':
                return Response(data, status=status.HTTP_200_OK)
            else:
                return Response(data, status=status.HTTP_201_CREATED)

    def destroy(self, request, *args, **kwargs):
        ranker = self.get_ranker()
        preferred, nonpreferred = self.get_items()
        delete_direct_preference(ranker, preferred, nonpreferred)
        return Response(status=status.HTTP_204_NO_CONTENT)