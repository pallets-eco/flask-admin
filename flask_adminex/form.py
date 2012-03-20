from flask.ext import wtf


class AdminForm(wtf.Form):
    @property
    def has_file_field(self):
        # TODO: Optimize me
        for f in self:
            if isinstance(f, wtf.FileField):
                return True

        return False
