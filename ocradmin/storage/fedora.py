"""
Fedora storage backend.
"""

import io
import re
import urllib
from django import forms
from django.conf import settings
import eulfedora
import hashlib
from cStringIO import StringIO
from eulfedora.server import Repository
from eulfedora.models import DigitalObject, FileDatastream

from . import base



class ConfigForm(base.BaseConfigForm):
    root = forms.CharField(max_length=255)
    username = forms.CharField(max_length=255)
    password = forms.CharField(max_length=255, widget=forms.PasswordInput)
    image_name = forms.CharField(max_length=255)
    transcript_name = forms.CharField(max_length=255)


class FedoraDocument(base.BaseDocument):
    """Fedora document class."""
    def __init__(self, digiobj, *args, **kwargs):
        self._doc = digiobj
        super(FedoraDocument, self).__init__(self._doc.pid, *args, **kwargs)

    @property
    def pid(self):
        return self._doc.pid
    

class FedoraStorage(base.BaseStorage):
    """Fedora Commons repository storage."""

    configform = ConfigForm
    defaults = dict(
            root=getattr(settings, "FEDORA_ROOT", ""),
            username=getattr(settings, "FEDORA_USER", ""),
            password=getattr(settings, "FEDORA_PASS", ""),
            namespace=getattr(settings, "FEDORA_PIDSPACE", ""),
            image_name=getattr(settings, "FEDORA_IMAGE_NAME", ""),
            transcript_name=getattr(settings, "FEDORA_TRANSCRIPT_NAME", "")
    )

    def __init__(self, *args, **kwargs):
        super(FedoraStorage, self).__init__(*args, **kwargs)
        self.namespace = kwargs["namespace"]
        self.image_name = kwargs["image_name"]
        self.thumbnail_name = "THUMBNAIL"
        self.binary_name = "BINARY"
        self.script_name = "OCR_SCRIPT"
        self.transcript_name = kwargs["transcript_name"]

        self.repo = Repository(
                root=kwargs["root"], username=kwargs["username"],
                password=kwargs["password"])

        self.model = type("Document", (DigitalObject,), {
            "default_pidspace": kwargs["namespace"],
            "FILE_CONTENT_MODEL": "info:fedora/genrepo:File-1.0",
            "CONTENT_MODELS":     ["info:fedora/genrepo:File-1.0"],
            "image": FileDatastream(self.image_name, "Document image", defaults={
              'versionable': True,
            }),
            "binary": FileDatastream(self.binary_name, "Document image binary", defaults={
              'versionable': True,
            }),
            "thumbnail": FileDatastream(self.thumbnail_name, "Document image thumbnail", defaults={
              'versionable': True,
            }),
            "script": FileDatastream(self.script_name, "OCR Script", defaults={
                "versionable": True,
            }),
            "transcript": FileDatastream(self.transcript_name, "Document transcript", defaults={
                "versionable": True,
            }),
            "meta": FileDatastream("meta", "Document metadata", defaults={
                "versionable": False,
            }),
        })

    def read_metadata(self, doc):
        meta = doc._doc.meta.content
        if hasattr(meta, "read"):
            meta = meta.read()
        if not meta:
            return {}
        return dict([v.strip().split("=") for v in \
                meta.split("\n") if re.match("^\w+=[^=]+$", v.strip())])

    def write_metadata(self, doc, **kwargs):
        meta = self.read_metadata(doc)
        meta.update(kwargs)
        metacontent = [u"%s=%s" % (k, v) for k, v in meta.iteritems()]
        doc._doc.meta.content = "\n".join(metacontent)

    def attr_uri(self, doc, attr):
        """URI for image datastream."""
        return "%sobjects/%s/datastreams/%s/content" % (
                self.repo.fedora_root,
                urllib.quote(doc.pid),
                getattr(self, "%s_name" % attr)
        )

    def document_label(self, doc):
        """Get the document label."""
        return doc._doc.label

    def document_attr_empty(self, doc, attr):
        """Check if document attr is empty."""
        return getattr(doc._doc, attr).info.size == 0

    def document_attr_label(self, doc, attr):
        """Get label for an image type attribute."""
        return getattr(doc._doc, attr).label

    def document_attr_mimetype(self, doc, attr):
        """Get mimetype for an image type attribute."""
        return getattr(doc._doc, attr).mimetype

    def document_attr_content_handle(self, doc, attr):
        """Get content for an image type attribute."""
        handle = getattr(doc._doc, attr).content
        return StringIO() if handle is None else handle

    def document_metadata(self, doc):
        """Get document metadata. This currently
        just exposes the DC stream attributes."""                
        return self.read_metadata(doc)

    def _set_document_ds_content(self, doc, dsattr, content):
        docattr = getattr(doc._doc, dsattr)
        #checksum = hashlib.md5(content.read()).hexdigest()
        #content.seek(0)
        #docattr.checksum = checksum
        #docattr.checksum_type = "MD5"
        docattr.content = content

    def set_document_attr_content(self, doc, attr, content):
        """Set image content."""
        self._set_document_ds_content(doc, attr, content)

    def set_document_attr_mimetype(self, doc, attr, mimetype):
        """Set image mimetype."""
        getattr(doc._doc, attr).mimetype = mimetype
    
    def set_document_attr_label(self, doc, attr, label):
        """Set image label."""
        getattr(doc._doc, attr).label = label

    def set_document_label(self, doc, label):
        """Set document label."""
        doc._doc.label = label

    def set_document_metadata(self, doc, **kwargs):
        """Set arbitrary document metadata."""
        self.write_metadata(doc, kwargs)

    def save_document(self, doc):
        """Save document."""
        doc._doc.save()

    def create_document(self, label):
        """Get a new document object"""
        dobj = self.repo.get_object(type=self.model)
        dobj.label = label
        dobj.meta.label = "Document Metadata"
        dobj.meta.mimetype = "text/plain"
        doc = FedoraDocument(dobj, self)
        return doc

    def get(self, pid):
        """Get an object by id."""
        doc = self.repo.get_object(pid, type=self.model)
        if doc:
            return FedoraDocument(doc, self)

    def delete(self, doc, msg=None):
        """Delete an object."""
        self.repo.purge_object(doc.pid, log_message=msg)

    def list(self, namespace=None):
        """List documents in the repository."""
        ns = namespace if namespace is not None else self.namespace
        return [FedoraDocument(d, self) \
                for d in self.repo.find_objects("%s:*" % ns, type=self.model)]
        
    def list_pids(self, namespace=None):
        """List of pids.  This unforunately involves calling
        list(), so it not a quicker alternative."""
        return [doc.pid for doc in self.list()]

