import os

BOT_NAME = 'rechtspraak_nl'
BOT_VERSION = 1.0

SPIDER_MODULES = ['rechtspraak_nl.spiders']
ITEM_PIPELINES = ['rechtspraak_nl.pipelines.RechtspraakNlPipeline']
NEWSPIDER_MODULE = 'rechtspraak_nl.spiders'
USER_AGENT = '%s/%s' % (BOT_NAME, BOT_VERSION)

# Autothrottling settings
AUTOTHROTTLE_ENABLED = True
AUTOTHROTTLE_DEBUG = True

# Full filesystem path to the project
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
