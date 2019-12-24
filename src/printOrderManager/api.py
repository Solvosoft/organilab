'''
Created by Luis Felipe Castro Sanchez
Universidad Nacional de Costa Rica 
Practica Profesional Supervisada (Julio - Noviembre 2018)
GitHub User luisfelipe7
'''

from rest_framework import viewsets, serializers
from printOrderManager.models import RequestLabelPrint, Contact, PrintObject, PaperType, Schedule, Advertisement
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
        fields = ('id', 'phone', 'assigned_user', 'state')


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


# Serializer for the Print Object Model


class PrintObjectSerializer(serializers.ModelSerializer):

    class Meta:
        model = PrintObject  # Model Created
        # Needed fields of the model
        fields = ('responsible_user', 'email', 'phone', 'location', 'geolocation', 'name', 'logo', 'qualification',
                  'creation_date', 'state', 'paperType', 'contacts', 'schedules', 'description', 'advertisements')

# Viewset for the Contact Model


class PrintObjectViewSet(viewsets.ModelViewSet):
    queryset = PrintObject.objects.all()  # All the contacts
    serializer_class = PrintObjectSerializer  # Serializer
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


# Serializer for the Paper Type Model


class PaperTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = PaperType  # Model Created
        # Needed fields of the model
        fields = ('id', 'unit_size', 'widthSize', 'longSize',
                  'name', 'grams', 'available', 'description')


# Viewset for the Paper Type Model


class PaperTypeViewSet(viewsets.ModelViewSet):
    queryset = PaperType.objects.all()  # All the paper types
    serializer_class = PaperTypeSerializer  # Serializer
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


# Serializer for the Schedule Model


class ScheduleSerializer(serializers.ModelSerializer):
    class Meta:
        model = Schedule  # Model Created
        # Needed fields of the model
        fields = ('id', 'name', 'startTime', 'closeTime',
                  'startDay', 'closeDay', 'description', 'state')


# Viewset for the Schedule Type Model


class ScheduleViewSet(viewsets.ModelViewSet):
    queryset = Schedule.objects.all()  # All the schedules
    serializer_class = ScheduleSerializer  # Serializer
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


# Serializer for the Advertisement Model


class AdvertisementSerializer(serializers.ModelSerializer):
    class Meta:
        model = Advertisement  # Model Created
        # Needed fields of the model
        fields = ('id', 'title', 'description', 'typeOfAdvertisement', 'published_date',
                  'state', 'usersNotified', 'creator')


# Viewset for the Advertisement Model


class AdvertisementViewSet(viewsets.ModelViewSet):
    queryset = Advertisement.objects.all()  # All the AdvertisementSerializer
    serializer_class = AdvertisementSerializer  # Serializer
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
