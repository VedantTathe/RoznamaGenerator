from django import forms


class ChangeExcel(forms.Form):
    file = forms.FileField(label='Select an Excel File')

    def clean_file(self):
        file = self.cleaned_data.get('file')
        if not file:
            raise forms.ValidationError("No file uploaded!")
        if not file.name.endswith(('.xls', '.xlsx')):
            raise forms.ValidationError("File is not an Excel file!")
        if file.content_type not in ['application/vnd.ms-excel', 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet']:
            raise forms.ValidationError("File is not an Excel file!")
        return file