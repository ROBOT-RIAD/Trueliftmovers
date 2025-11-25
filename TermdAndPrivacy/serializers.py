from rest_framework import serializers
from .models import Terms , Privacy



class TermsSerialiser(serializers.ModelSerializer):
    text = serializers.CharField(required=True)

    class Meta:
        model = Terms
        fields = "__all__"

    def validate(self, attrs):
        text = attrs.get("text")
        if not text:
            raise serializers.ValidationError({"text": "Text field cannot be empty."})
        if len(text) < 200:
            raise serializers.ValidationError({"text": "Text must be at least 200 characters long."})
        return attrs




class PrivacySerializer(serializers.ModelSerializer):
    text = serializers.CharField(required=True)

    class Meta:
        model = Privacy
        fields = "__all__"

    def validate(self, attrs):
        text = attrs.get("text")
        if not text:
            raise serializers.ValidationError({"text": "Text field cannot be empty."})
        if len(text) < 200:
            raise serializers.ValidationError({"text": "Text must be at least 200 characters long."})
        return attrs
        