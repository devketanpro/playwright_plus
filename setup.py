import setuptools

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setuptools.setup(
    name='playwright_plus',
    version='0.0.10',
    author='Martin Tran',
    author_email='martin.tranhoai@customore.co',
    description='A custom augmented version of the playwright library',
    long_description=long_description,
    long_description_content_type="text/markdown",
    url='https://github.com/customore-org/playwright_plus',
    project_urls = {
    },
    packages=[
        'playwright_plus',
        'playwright_plus.utils',
    ],
    install_requires=[
        'playwright==1.25.2 ',
    ],
)
