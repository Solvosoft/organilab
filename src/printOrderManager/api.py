from rest_framework import viewsets, serializers
from printOrderManager.models import RequestLabelPrint
from rest_framework.permissions import IsAuthenticated


class RequestLabelPrintSerializer(serializers.ModelSerializer):
    class Meta:
        model = RequestLabelPrint
        fields = ('user', 'printer', 'add_date', 'status')


class RequestLabelPrintViewSet(viewsets.ModelViewSet):
    """
    Example empty viewset demonstrating the standard
    actions that will be handled by a router class.

    If you're using format suffixes, make sure to also include
    the `format=None` keyword argument for each action.
    """

    queryset = RequestLabelPrint.objects.all()
    serializer_class = RequestLabelPrintSerializer
    permission_classes = [IsAuthenticated, ]

    """
    def list(self, request):
        pass

    def create(self, request):
        pass

    def retrieve(self, request, pk=None):
        pass

    def update(self, request, pk=None):
        pass

    def partial_update(self, request, pk=None):
        pass

    def destroy(self, request, pk=None):
        pass
    """