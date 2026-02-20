#!/usr/bin/env python3
"""AWS CDK App entry point for Word-to-JATS platform."""
import os
import aws_cdk as cdk
from cdk_stack import WordToJatsStack

app = cdk.App()
WordToJatsStack(app, "WordToJatsStack", env=cdk.Environment(
    account=os.environ.get("CDK_DEFAULT_ACCOUNT"),
    region=os.environ.get("CDK_DEFAULT_REGION"),
))
app.synth()
