from django import forms

from .models import BagImage


class MultiFileUploadForm(forms.Form):
    files = forms.FileField(
        widget=forms.FileInput(),
        label='Upload files'
    )