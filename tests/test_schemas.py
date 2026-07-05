from moosey_cms.schemas import (
    schema_article, schema_breadcrumbs, schema_faqpage, schema_howto,
    schema_localbusiness, schema_product, schema_event, schema_organization,
    schema_website, schema_person, json_ld,
)


class TestSchemaArticle:
    def test_minimal(self):
        r = schema_article("Test")
        assert r["@context"] == "https://schema.org"
        assert r["@type"] == "Article"
        assert r["headline"] == "Test"
        assert len(r) == 3

    def test_original_fields(self):
        r = schema_article(
            "T", description="D", image="i.jpg", author="Alice",
            date_published="2024-01-01", date_modified="2024-01-02",
            url="https://x.com",
        )
        assert r["description"] == "D"
        assert r["image"] == "i.jpg"
        assert r["author"] == {"@type": "Person", "name": "Alice"}
        assert r["datePublished"] == "2024-01-01"
        assert r["dateModified"] == "2024-01-02"
        assert r["mainEntityOfPage"] == {"@type": "WebPage", "@id": "https://x.com"}

    def test_publisher_string(self):
        r = schema_article("T", publisher="My Site")
        assert r["publisher"] == {"@type": "Organization", "name": "My Site"}

    def test_publisher_dict(self):
        r = schema_article("T", publisher={"name": "X", "logo": "/l.png"})
        assert r["publisher"] == {"@type": "Organization", "name": "X", "logo": "/l.png"}

    def test_word_count_auto(self):
        r = schema_article("T", article_body="one two three four five")
        assert r["wordCount"] == 5

    def test_word_count_explicit(self):
        r = schema_article("T", article_body="one two three", word_count=99)
        assert r["wordCount"] == 99

    def test_keywords_list(self):
        r = schema_article("T", keywords=["python", "cms"])
        assert r["keywords"] == "python, cms"

    def test_keywords_string(self):
        r = schema_article("T", keywords="python, cms")
        assert r["keywords"] == "python, cms"

    def test_speakable(self):
        r = schema_article("T", speakable=["#headline", ".summary"])
        assert r["speakable"] == {
            "@type": "SpeakableSpecification",
            "cssSelector": ["#headline", ".summary"],
        }

    def test_is_part_of(self):
        r = schema_article("T", is_part_of={"name": "Series", "url": "/s/1"})
        assert r["isPartOf"] == {"@type": "WebPage", "name": "Series", "url": "/s/1"}

    def test_is_accessible_for_free(self):
        r = schema_article("T", is_accessible_for_free=True)
        assert r["isAccessibleForFree"] is True

    def test_false_is_included_explicitly(self):
        r = schema_article("T", is_accessible_for_free=False)
        assert r["isAccessibleForFree"] is False

    def test_omitted_when_none(self):
        r = schema_article("T")
        assert "isAccessibleForFree" not in r

    def test_copyright_holder_string(self):
        r = schema_article("T", copyright_holder="ACME")
        assert r["copyrightHolder"] == {"@type": "Organization", "name": "ACME"}

    def test_copyright_holder_dict(self):
        r = schema_article("T", copyright_holder={"name": "Alice", "url": "/about"})
        assert r["copyrightHolder"] == {"@type": "Person", "name": "Alice", "url": "/about"}

    def test_about_list(self):
        r = schema_article("T", about=["AI", "ML"])
        assert r["about"] == "AI, ML"

    def test_genre_list(self):
        r = schema_article("T", genre=["tech", "science"])
        assert r["genre"] == "tech, science"

    def test_all_new_fields(self):
        r = schema_article(
            "Title",
            keywords=["k1"], in_language="en", article_section="Tech",
            article_body="body", word_count=1, speakable=[".h"],
            backstory="why", date_created="2024-01-01", publisher="Pub",
            comment_count=5, about="subj", abstract="abs",
            alternative_headline="Alt", genre="g", license="MIT",
            is_part_of={"name": "S"}, is_accessible_for_free=True,
            copyright_year=2024, copyright_holder="C", discussion_url="/comments",
        )
        assert r["@context"] == "https://schema.org"
        assert r["@type"] == "Article"
        assert r["headline"] == "Title"
        assert r["keywords"] == "k1"
        assert r["inLanguage"] == "en"
        assert r["articleSection"] == "Tech"
        assert r["articleBody"] == "body"
        assert r["wordCount"] == 1
        assert r["speakable"] == {"@type": "SpeakableSpecification", "cssSelector": [".h"]}
        assert r["backstory"] == "why"
        assert r["dateCreated"] == "2024-01-01"
        assert r["publisher"] == {"@type": "Organization", "name": "Pub"}
        assert r["commentCount"] == 5
        assert r["about"] == "subj"
        assert r["abstract"] == "abs"
        assert r["alternativeHeadline"] == "Alt"
        assert r["genre"] == "g"
        assert r["license"] == "MIT"
        assert r["isPartOf"] == {"@type": "WebPage", "name": "S"}
        assert r["isAccessibleForFree"] is True
        assert r["copyrightYear"] == 2024
        assert r["copyrightHolder"] == {"@type": "Organization", "name": "C"}
        assert r["discussionUrl"] == "/comments"


class TestOtherSchemas:
    def test_breadcrumbs(self):
        items = [{"name": "Home", "url": "/"}, {"name": "Blog", "url": "/blog"}]
        r = schema_breadcrumbs(items)
        assert r["@type"] == "BreadcrumbList"
        assert len(r["itemListElement"]) == 2
        assert r["itemListElement"][0]["position"] == 1

    def test_faqpage(self):
        faqs = [{"question": "Q?", "answer": "A!"}]
        r = schema_faqpage(faqs)
        assert r["@type"] == "FAQPage"
        assert r["mainEntity"][0]["acceptedAnswer"]["text"] == "A!"

    def test_howto(self):
        steps = [{"name": "Step 1", "text": "Do X"}]
        r = schema_howto("How to X", steps, description="A guide")
        assert r["@type"] == "HowTo"
        assert r["step"][0]["text"] == "Do X"

    def test_localbusiness(self):
        r = schema_localbusiness("ACME", "https://acme.com", telephone="555")
        assert r["@type"] == "LocalBusiness"
        assert r["telephone"] == "555"

    def test_product(self):
        r = schema_product("Gadget", price=9.99, currency="USD")
        assert r["@type"] == "Product"
        assert r["offers"]["price"] == "9.99"

    def test_event(self):
        r = schema_event("Concert", "2024-06-15")
        assert r["@type"] == "Event"
        assert r["startDate"] == "2024-06-15"

    def test_org(self):
        r = schema_organization("ACME", "https://acme.com", logo="/logo.png")
        assert r["@type"] == "Organization"
        assert r["logo"]["url"] == "/logo.png"

    def test_website(self):
        r = schema_website("My Site", "https://example.com")
        assert r["@type"] == "WebSite"

    def test_person(self):
        r = schema_person("Alice", job_title="Engineer")
        assert r["@type"] == "Person"
        assert r["jobTitle"] == "Engineer"


class TestJsonLd:
    def test_renders_script_tag(self):
        r = schema_article("Test", description="Hello")
        html = json_ld(r)
        assert 'application/ld+json' in html
        assert "headline" in html
        assert "Hello" in html

    def test_escapes_script_close(self):
        html = json_ld({"foo": "</script>"})
        assert "<\\/script>" in html

    def test_empty_on_non_dict(self):
        assert json_ld(None) == ""
        assert json_ld("str") == ""
        assert json_ld(42) == ""
        assert json_ld([]) == ""
