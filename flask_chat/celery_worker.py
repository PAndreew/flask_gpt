#!/usr/bin/env python
import os
from .app import celery, create_app

app = create_app()
app.app_context().push()
print(id(app))
