from rest_framework import viewsets, serializers
from printOrderManager.models import RequestLabelPrint, Contact
from rest_framework.permissions import IsAuthenticated

# DJANGO REST FRAMEWORK

# Serializer for the RequestLabel Model


class RequestLabelPrintSerializer(serializers.ModelSerializer):

    class Meta:
        model = RequestLabelPrint  # Model Created
        # Needed fields of the model
        fields = ('id', 'user', 'printer', 'status')


# Viewset for the RequestLabel Model


class RequestLabelPrintViewSet(viewsets.ModelViewSet):
    """
    Example empty viewset demonstrating the standard
    actions that will be handled by a router class.

    If you're using format suffixes, make sure to also include
    the `format=None` keyword argument for each action.
    """

    queryset = RequestLabelPrint.objects.all()
    serializer_class = RequestLabelPrintSerializer
    permission_classes = [IsAuthenticated, ]  # Aqui van todos los permisos

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

# Serializer for the Contact Model


class ContactSerializer(serializers.ModelSerializer):

    class Meta:
        model = Contact  # Model Created
        # Needed fields of the model
        fields = ('id', 'phone', 'assigned_user')


# Viewset for the Contact Model


class ContactViewSet(viewsets.ModelViewSet):
    queryset = Contact.objects.all()  # All the contacts
    serializer_class = ContactSerializer  # Serializer
    permission_classes = [IsAuthenticated, ]  # Required permissions

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
