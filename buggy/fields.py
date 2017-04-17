from django import forms
from django.utils.datastructures import MultiValueDict


class MultipleFileInput(forms.FileInput):
    def build_attrs(self, *args, **kwargs):
        attrs = super().build_attrs(*args, **kwargs)
        attrs['multiple'] = True
        return attrs

    def value_from_datadict(self, data, files, name):
        if isinstance(files, MultiValueDict):
            return files.getlist(name)
        else:
            return files.get(name)


class MultipleFileField(forms.FileField):
    widget = MultipleFileInput

    def to_python(self, data):
        if isinstance(data, list):
            return [super(MultipleFileField, self).to_python(i) for i in data]
        elif data in self.empty_values:
            return []
        else:
            return [super().to_python(data)]
