from iommi.admin import Admin

from tests.helpers import req


def test_iommi_admin():
    class MyAdmin(Admin):
        pass

    MyAdmin.all_models().bind(request=req('get')).render_to_response()
