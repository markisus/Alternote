from db.schools import create_school
from env import env, BaseHandler
from forms.forms import CreateSchoolForm

class CreateSchool(BaseHandler):
    template = env.get_template("admin/create_school.template")
    
    def get(self):
        self.write(self.template.render(form=CreateSchoolForm()))
    
    def post(self):
        form = CreateSchoolForm(**self.get_params())
        if form.validate():
            #Process tags:
            tags_data = form.tags.data or ""
            tags = [t.strip() for t in tags_data.split(" ") if t.strip()]
            school_name = form.school_name.data
            create_school(school_name, tags)
        else:
            self.write(self.template.render(form=form))