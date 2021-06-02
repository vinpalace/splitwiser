from rest_framework.decorators import action
from core.serializers.LedgerSerializer import LedgerSerializer
from core.models import Ledger
from rest_framework import viewsets


class LedgerViewSet(viewsets.ModelViewSet):
    queryset = Ledger.objects.all()
    serializer_class = LedgerSerializer

    # TODO: Handle User not in group case
