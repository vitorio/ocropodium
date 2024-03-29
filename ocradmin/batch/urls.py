from django.conf.urls.defaults import *

from ocradmin.batch import views
from django.contrib.auth.decorators import login_required

urlpatterns = patterns('',
    (r'^abort/(?P<batch_pk>\d+)/?$', login_required(views.abort_batch)),
	(r'^create/?$', login_required(views.create)),
	(r'^delete/(?P<pk>\d+)/?$', login_required(views.batchdelete)),
	(r'^export_options/(?P<batch_pk>\d+)/?$', login_required(views.export_options)),
	(r'^latest/?$', login_required(views.latest)),
	(r'^list/?$', login_required(views.batchlist)),
	(r'^new/?$', login_required(views.new)),
    (r'^results/(?P<batch_pk>\d+)/?$', login_required(views.results)),
    (r'^results/(?P<batch_pk>\d+)/(?P<page_index>\d+)/?$', login_required(views.page_results)),
    (r'^retry/(?P<batch_pk>\d+)/?$', login_required(views.retry)),
    (r'^retry_errored/(?P<batch_pk>\d+)/?$', login_required(views.retry_errored)),
    (r'^show/(?P<batch_pk>\d+)/?$', login_required(views.show)),
    (r'^test/?$', login_required(views.test)),
	(r'^upload_files/?$', login_required(views.upload_files)),
)
