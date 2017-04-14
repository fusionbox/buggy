from django.views.generic import TemplateView


class GetFormView(TemplateView):
    form_class = None

    @property
    def is_form_submitted(self):
        return bool(self.request.GET)

    def get_form_kwargs(self):
        kwargs = {}
        if self.is_form_submitted:
            kwargs.update(data=self.request.GET)
        else:
            kwargs.update(initial=self.request.GET)
        return kwargs

    def get_form(self):
        return self.form_class(**self.get_form_kwargs())

    def get_context_data(self, **kwargs):
        kwargs = super().get_context_data(**kwargs)
        kwargs['form'] = self.form
        return kwargs

    def form_invalid(self, form):
        return self.render_to_response(self.get_context_data(form=form))

    def get(self, request, *args, **kwargs):
        self.form = self.get_form()
        if self.is_form_submitted:
            if self.form.is_valid():
                return self.form_valid(self.form)
            else:
                return self.form_invalid(self.form)
        else:
            return super().get(request, *args, **kwargs)
