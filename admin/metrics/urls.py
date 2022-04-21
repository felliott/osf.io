from django.conf.urls import url
from django.contrib.auth.decorators import login_required as login

from . import views

app_name = 'admin'

urlpatterns = [
    url(r'^$', login(views.MetricsView.as_view()), name='metrics'),
    url(r'^mw$', login(views.MetricsView2.as_view()), name='metrics-mw'),
]
