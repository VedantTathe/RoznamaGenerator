"""
URL configuration for mynewproject project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from mynewapp import views

urlpatterns = [
    path('',views.index,name='index'),
    path('fetch_and_download_pdf/', views.fetch_and_download_pdf, name='fetch_and_download_pdf'),
    # path('read_pdf_to_excel/', views.read_pdf_to_excel, name='read_pdf_to_excel'),
    # path('fill_roznama_excel/', views.fill_roznama_excel, name='fill_roznama_excel'),
    path('return_roznama/', views.return_roznama, name='return_roznama'),
    path('change_caseinfo_excelfile/', views.change_caseinfo_excelfile, name='change_caseinfo_excelfile'),

]

