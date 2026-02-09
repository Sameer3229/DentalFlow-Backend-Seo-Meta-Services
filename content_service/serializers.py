from rest_framework import serializers

class TopicRequestSerializer(serializers.Serializer):
    overview = serializers.CharField()
    category = serializers.CharField()

class TopicResponseSerializer(serializers.Serializer):
    topics = serializers.ListField(child=serializers.CharField())


class GenerateContentRequestSerializer(serializers.Serializer):
    overview = serializers.CharField()
    category = serializers.CharField()
    topics = serializers.ListField(child=serializers.CharField())
    platform = serializers.CharField()
    length = serializers.CharField()

class GenerateContentResponseSerializer(serializers.Serializer):
    content = serializers.CharField()
    image_url = serializers.CharField()
