from rest_framework import serializers,status
from .models import Ad, ExchangeProposal
from django.contrib.auth.models import User


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username']


class AdSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    
    class Meta:
        model = Ad
        fields = ['user','title','description','image_url','category','condition','created_at']
        read_only_fields = ['created_at', 'user']


class ExchangeProposalSerializer(serializers.ModelSerializer):
    ad_sender = serializers.PrimaryKeyRelatedField(queryset=Ad.objects.all(),read_only=False)
    ad_receiver = serializers.PrimaryKeyRelatedField(queryset=Ad.objects.all(),read_only=False)
    
    class Meta:
        model = ExchangeProposal
        fields = ['ad_sender','ad_receiver','comment','status','created_at']
        read_only_fields = ['created_at','status']


class ExchangeProposalUpdateSerializer(serializers.ModelSerializer):
    status = serializers.ChoiceField(choices=ExchangeProposal.STATUS_CHOICES, required = True)
    class Meta:
        model = ExchangeProposal
        fields = ['status']

    def validate_status(self, value):
        if value == 'pending':
            raise serializers.ValidationError(detail="Недопустимое значение статуса",code=status.HTTP_400_BAD_REQUEST)
        return value