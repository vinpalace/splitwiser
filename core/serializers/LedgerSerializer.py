from rest_framework import serializers
from core.models import Ledger


class LedgerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Ledger
        fields = '__all__'
