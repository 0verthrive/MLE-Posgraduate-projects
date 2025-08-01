import aws_cdk as core
import aws_cdk.assertions as assertions

from cdk_b3.cdk_b3_stack import CdkB3Stack

# example tests. To run these tests, uncomment this file along with the example
# resource in cdk_b3/cdk_b3_stack.py
def test_sqs_queue_created():
    app = core.App()
    stack = CdkB3Stack(app, "cdk-b3")
    template = assertions.Template.from_stack(stack)

#     template.has_resource_properties("AWS::SQS::Queue", {
#         "VisibilityTimeout": 300
#     })
