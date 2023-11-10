import aws_cdk as core
import aws_cdk.assertions as assertions

from stock_analysis_cdk.stock_analysis_cdk_stack import StockAnalysisCdkStack

# example tests. To run these tests, uncomment this file along with the example
# resource in stock_analysis_cdk/stock_analysis_cdk_stack.py
def test_sqs_queue_created():
    app = core.App()
    stack = StockAnalysisCdkStack(app, "stock-analysis-cdk")
    template = assertions.Template.from_stack(stack)

#     template.has_resource_properties("AWS::SQS::Queue", {
#         "VisibilityTimeout": 300
#     })
