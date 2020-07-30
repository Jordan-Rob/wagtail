# -*- coding: utf-8 -*
from django.core.exceptions import ImproperlyConfigured
from django.test import TestCase, override_settings
from django.utils.text import slugify

from wagtail.core.models import Page
from wagtail.core.utils import (
    accepts_kwarg, camelcase_to_underscore, cautious_slugify, find_available_slug,
    get_content_languages, get_supported_content_language_variant, safe_snake_case, string_to_ascii)


class TestCamelCaseToUnderscore(TestCase):

    def test_camelcase_to_underscore(self):
        test_cases = [
            ('HelloWorld', 'hello_world'),
            ('longValueWithVarious subStrings', 'long_value_with_various sub_strings')
        ]

        for (original, expected_result) in test_cases:
            self.assertEqual(camelcase_to_underscore(original), expected_result)


class TestStringToAscii(TestCase):

    def test_string_to_ascii(self):
        test_cases = [
            (u'30 \U0001d5c4\U0001d5c6/\U0001d5c1', '30 km/h'),
            (u'\u5317\u4EB0', 'BeiJing'),
            ('ぁ あ ぃ い ぅ う ぇ', 'a a i i u u e'),
            ('Ա Բ Գ Դ Ե Զ Է Ը Թ Ժ Ի Լ Խ Ծ Կ Հ Ձ Ղ Ճ Մ Յ Ն', 'A B G D E Z E Y T\' Zh I L Kh Ts K H Dz Gh Ch M Y N'),
            ('Спорт!', 'Sport!'),
            ('Straßenbahn', 'Strassenbahn'),
            ('Hello world', 'Hello world'),
            ('Ā ā Ă ă Ą ą Ć ć Ĉ ĉ Ċ ċ Č č Ď ď Đ', 'A a A a A a C c C c C c C c D d D'),
            ('〔山脈〕', '[ShanMai]'),
        ]

        for (original, expected_result) in test_cases:
            self.assertEqual(string_to_ascii(original), expected_result)


class TestCautiousSlugify(TestCase):

    def test_behaves_same_as_slugify_for_latin_chars(self):
        test_cases = [
            ('', ''),
            ('???', ''),
            ('Hello world', 'hello-world'),
            ('Hello_world', 'hello_world'),
            ('Hellö wörld', 'hello-world'),
            ('Hello   world', 'hello-world'),
            ('   Hello world   ', 'hello-world'),
            ('Hello, world!', 'hello-world'),
            ('Hello*world', 'helloworld'),
            ('Hello☃world', 'helloworld'),
        ]

        for (original, expected_result) in test_cases:
            self.assertEqual(slugify(original), expected_result)
            self.assertEqual(cautious_slugify(original), expected_result)

    def test_escapes_non_latin_chars(self):
        test_cases = [
            ('Straßenbahn', 'straxdfenbahn'),
            ('Спорт!', 'u0421u043fu043eu0440u0442'),
            ('〔山脈〕', 'u5c71u8108'),
        ]

        for (original, expected_result) in test_cases:
            self.assertEqual(cautious_slugify(original), expected_result)


class TestSafeSnakeCase(TestCase):

    def test_strings_with_latin_chars(self):
        test_cases = [
            ('', ''),
            ('???', ''),
            ('using-Hyphen', 'using_hyphen'),
            ('en–⁠dash', 'endash'),  # unicode non-letter characters stripped
            ('  em—dash ', 'emdash'),  # unicode non-letter characters stripped
            ('horizontal―BAR', 'horizontalbar'),  # unicode non-letter characters stripped
            ('Hello world', 'hello_world'),
            ('Hello_world', 'hello_world'),
            ('Hellö wörld', 'hello_world'),
            ('Hello   world', 'hello_world'),
            ('   Hello world   ', 'hello_world'),
            ('Hello, world!', 'hello_world'),
            ('Hello*world', 'helloworld'),
            ('Screenshot_2020-05-29 Screenshot(1).png', 'screenshot_2020_05_29_screenshot1png')
        ]

        for (original, expected_result) in test_cases:
            self.assertEqual(safe_snake_case(original), expected_result)

    def test_strings_with__non_latin_chars(self):
        test_cases = [
            ('Straßenbahn Straßenbahn', 'straxdfenbahn_straxdfenbahn'),
            ('Сп орт!', 'u0421u043f_u043eu0440u0442'),
        ]

        for (original, expected_result) in test_cases:
            self.assertEqual(safe_snake_case(original), expected_result)


class TestAcceptsKwarg(TestCase):
    def test_accepts_kwarg(self):
        def func_without_banana(apple, orange=42):
            pass

        def func_with_banana(apple, banana=42):
            pass

        def func_with_kwargs(apple, **kwargs):
            pass

        self.assertFalse(accepts_kwarg(func_without_banana, 'banana'))
        self.assertTrue(accepts_kwarg(func_with_banana, 'banana'))
        self.assertTrue(accepts_kwarg(func_with_kwargs, 'banana'))


class TestFindAvailableSlug(TestCase):
    def setUp(self):
        self.root_page = Page.objects.get(depth=1)
        self.home_page = Page.objects.get(depth=2)

        self.root_page.add_child(instance=Page(title="Second homepage", slug="home-1"))

    def test_find_available_slug(self):
        with self.assertNumQueries(1):
            slug = find_available_slug(self.root_page, "unique-slug")

        self.assertEqual(slug, "unique-slug")

    def test_find_available_slug_already_used(self):
        # Even though the first two slugs are already used, this still requires only one query to find a unique one
        with self.assertNumQueries(1):
            slug = find_available_slug(self.root_page, "home")

        self.assertEqual(slug, "home-2")


@override_settings(
    USE_I18N=True,
    WAGTAIL_I18N_ENABLED=True,
    LANGUAGES=[
        ('en', 'English'),
        ('de', 'German'),
        ('de-at', 'Austrian German'),
        ('pt-br', 'Portuguese (Brazil)'),
    ],
    WAGTAIL_CONTENT_LANGUAGES=[
        ('en', 'English'),
        ('de', 'German'),
        ('de-at', 'Austrian German'),
        ('pt-br', 'Portuguese (Brazil)'),
    ],
)
class TestGetContentLanguages(TestCase):
    def test_get_content_languages(self):
        self.assertEqual(get_content_languages(), {
            'de': 'German',
            'de-at': 'Austrian German',
            'en': 'English',
            'pt-br': 'Portuguese (Brazil)'
        })

    @override_settings(
        WAGTAIL_CONTENT_LANGUAGES=[
            ('en', 'English'),
            ('de', 'German'),
        ],
    )
    def test_can_be_different_to_django_languages(self):
        self.assertEqual(get_content_languages(), {
            'de': 'German',
            'en': 'English',
        })

    @override_settings(
        WAGTAIL_CONTENT_LANGUAGES=[
            ('en', 'English'),
            ('de', 'German'),
            ('zh', 'Chinese'),
        ],
    )
    def test_must_be_subset_of_django_languages(self):
        with self.assertRaises(ImproperlyConfigured) as e:
            get_content_languages()

        self.assertEqual(e.exception.args, ("The language zh is specified in WAGTAIL_CONTENT_LANGUAGES but not LANGUAGES. WAGTAIL_CONTENT_LANGUAGES must be a subset of LANGUAGES.", ))


@override_settings(
    USE_I18N=True,
    WAGTAIL_I18N_ENABLED=True,
    LANGUAGES=[
        ('en', 'English'),
        ('de', 'German'),
        ('de-at', 'Austrian German'),
        ('pt-br', 'Portuguese (Brazil)'),
    ],
    WAGTAIL_CONTENT_LANGUAGES=[
        ('en', 'English'),
        ('de', 'German'),
        ('de-at', 'Austrian German'),
        ('pt-br', 'Portuguese (Brazil)'),
    ],
)
class TestGetSupportedContentLanguageVariant(TestCase):
    # From: https://github.com/django/django/blob/9e57b1efb5205bd94462e9de35254ec5ea6eb04e/tests/i18n/tests.py#L1481
    def test_get_supported_content_language_variant(self):
        g = get_supported_content_language_variant
        self.assertEqual(g('en'), 'en')
        self.assertEqual(g('en-gb'), 'en')
        self.assertEqual(g('de'), 'de')
        self.assertEqual(g('de-at'), 'de-at')
        self.assertEqual(g('de-ch'), 'de')
        self.assertEqual(g('pt-br'), 'pt-br')
        self.assertEqual(g('pt'), 'pt-br')
        self.assertEqual(g('pt-pt'), 'pt-br')
        with self.assertRaises(LookupError):
            g('pt', strict=True)
        with self.assertRaises(LookupError):
            g('pt-pt', strict=True)
        with self.assertRaises(LookupError):
            g('xyz')
        with self.assertRaises(LookupError):
            g('xy-zz')

    @override_settings(WAGTAIL_CONTENT_LANGUAGES=[
        ('en', 'English'),
        ('de', 'German'),
    ])
    def test_uses_wagtail_content_languages(self):
        # be sure it's not using Django's LANGUAGES
        g = get_supported_content_language_variant
        self.assertEqual(g('en'), 'en')
        self.assertEqual(g('en-gb'), 'en')
        self.assertEqual(g('de'), 'de')
        self.assertEqual(g('de-at'), 'de')
        self.assertEqual(g('de-ch'), 'de')
        with self.assertRaises(LookupError):
            g('pt-br')
        with self.assertRaises(LookupError):
            g('pt')
        with self.assertRaises(LookupError):
            g('pt-pt')
        with self.assertRaises(LookupError):
            g('xyz')
        with self.assertRaises(LookupError):
            g('xy-zz')
