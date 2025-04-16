from rest_framework import viewsets, permissions, filters, mixins
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.pagination import PageNumberPagination
from rest_framework.exceptions import PermissionDenied, ParseError
from django_filters.rest_framework import DjangoFilterBackend
from .models import Ad, ExchangeProposal
from .serializers import AdSerializer, ExchangeProposalSerializer, ExchangeProposalUpdateSerializer
from .filters import AdFilter


class StandardPagination(PageNumberPagination):
    page_size = 10
    page_size_query_param = 'page_size'
    max_page_size = 100


class AdViewSet(mixins.CreateModelMixin,
                   mixins.UpdateModelMixin,
                   mixins.DestroyModelMixin,
                   mixins.ListModelMixin,
                   viewsets.GenericViewSet):
    """
    ViewSet для работы с объявлениями.
    Поддерживает создание, просмотр, обновление, удаление, поиск и фильтрацию.
    """
    queryset = Ad.objects.select_related('user').all()
    serializer_class = AdSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    pagination_class = StandardPagination
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    filterset_class = AdFilter
    search_fields = ['title', 'description']

    def perform_create(self, serializer):
        """Автоматически устанавливаем пользователя при создании объявления"""
        serializer.save(user=self.request.user)

    def perform_update(self, serializer):
        """Проверка авторства перед обновлением"""
        if serializer.instance.user != self.request.user:
            raise PermissionDenied("Вы не являетесь автором этого объявления")
        serializer.save()

    def perform_destroy(self, instance):
        """Проверка авторства перед удалением"""
        if instance.user != self.request.user:
            raise PermissionDenied("Вы не являетесь автором этого объявления")
        instance.delete()


class ExchangeProposalViewSet(mixins.CreateModelMixin,
                   mixins.ListModelMixin,
                   viewsets.GenericViewSet):
    """
    ViewSet для работы с предложениями обмена.
    Поддерживает создание, просмотр, обновление статуса, фильтрацию.
    """
    queryset = ExchangeProposal.objects.select_related('ad_sender__user','ad_receiver__user').all()
    serializer_class = ExchangeProposalSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    pagination_class = StandardPagination
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['status', 'ad_sender', 'ad_receiver']

    def get_serializer_class(self):
        if self.request.method in ["GET", "POST"]:
            return super().get_serializer_class()
        else:
            return ExchangeProposalUpdateSerializer

    def perform_create(self, serializer):
        """Создание предложения об обмене"""
        ad_sender = serializer.validated_data['ad_sender']
        if ad_sender.user != self.request.user:
            raise PermissionDenied("Вы не владелец объявления-отправителя")
        serializer.save()
        
    @action(detail=True, methods=['put'], url_path='update', url_name='update')
    def update_status(self, request, pk=None):
        """Обновление статуса предложения"""
        proposal = self.get_object()
        serializer = self.get_serializer(proposal, data=request.data)
        serializer.is_valid(raise_exception=True)
        new_status = serializer.validated_data['status']
        req_user = request.user

        if (req_user != proposal.ad_sender.user and req_user != proposal.ad_receiver.user) or proposal.status != 'pending':
            raise PermissionDenied("Вы не владелец объявления-отправителя")

        if (req_user == proposal.ad_sender.user and new_status != 'rejected'):
            raise ParseError("Недопустимый статус для обновления")

        proposal.status = new_status
        proposal.save()
        return Response({'status': 'Статус успешно обновлен'})