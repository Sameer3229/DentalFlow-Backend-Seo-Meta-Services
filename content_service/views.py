import requests
from rest_framework.viewsets import ModelViewSet
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from rest_framework.exceptions import ValidationError
from .utils import custom_exception_handler
from core.permission import UserAuthenticated
from .serializers import (
    TopicRequestSerializer,
    TopicResponseSerializer,
    GenerateContentRequestSerializer,
    GenerateContentResponseSerializer
)
from .services.llm_service import generate_topics, generate_post
from .services.image_service import generate_image_from_post
# Create your views here.


class TopicViewSet(ModelViewSet):
    @action(detail=False, methods=['POST'], permission_classes=[UserAuthenticated])
    def create_topics(self, request):
        
        serializer = TopicRequestSerializer(data=request.data)
        try:
            serializer.is_valid(raise_exception=True)
        except ValidationError as exc:
            # Custom handler ko manually call karo
            response = custom_exception_handler(exc, context={'view': self, 'request': request})
            return Response(response.data, status=response.status_code)

        topics = generate_topics(
            serializer.validated_data["overview"],
            serializer.validated_data["category"]
        )

        return Response({
                    "status": True,
                    "message": "Success",
                    "data": topics
                }, status=status.HTTP_201_CREATED)
    
class GenerateContentViewSet(ModelViewSet):

    @action(detail=False, methods=['POST'], permission_classes=[UserAuthenticated])
    # def content(self, request):
    #     serializer = GenerateContentRequestSerializer(data=request.data)
    #     serializer.is_valid(raise_exception=True)
    #     data = serializer.validated_data

    #     content = generate_post(
    #         overview=data["overview"],
    #         category=data["category"],
    #         topics=data["topics"],
    #         platform=data["platform"],
    #         length=data["length"]
    #     )

    #     image_url = generate_image_from_post(content, data["platform"])

    #     return Response({
    #         "content": content,
    #         "image_url": image_url
    #     })
    def content(self, request):
        serializer = GenerateContentRequestSerializer(data=request.data)
        try:
            serializer.is_valid(raise_exception=True)
        except ValidationError as exc:
            response = custom_exception_handler(exc, context={'view': self, 'request': request})
            return Response(response.data, status=response.status_code)

        data = serializer.validated_data

        content = generate_post(
            overview=data["overview"],
            category=data["category"],
            topics=data["topics"],
            platform=data["platform"],
            length=data["length"]
        )

        image_url = generate_image_from_post(content, data["platform"])

        return Response({
            "status": True,
            "message": "Content Generated Successfully!",
            "data": {
                "content": content,
                "image_url": image_url
            }
        }, status=status.HTTP_201_CREATED)