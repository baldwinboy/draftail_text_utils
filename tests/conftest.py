import pytest

from wagtail.models import Page, Site


@pytest.fixture(autouse=True)
def temporary_media_dir(settings, tmp_path: pytest.TempdirFactory):
    settings.MEDIA_ROOT = tmp_path / "media"


@pytest.fixture
def page():
    site = Site.objects.get(is_default_site=True)
    home = site.root_page.specific
    child = Page(title="Test page", slug="test-page")
    home.add_child(instance=child)
    child.save()
    return child
