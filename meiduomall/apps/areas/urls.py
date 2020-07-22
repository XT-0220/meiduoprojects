from django.urls import path

from . import views

urlpatterns = {

    path('areas/',views.ProvinceAreaView.as_view()),

    path('areas/<int:parentid>/',views.SubAreaView.as_view()),

}