# forms.py
from django import forms

class ImportExcelForm(forms.Form):
    excel_file = forms.FileField()
