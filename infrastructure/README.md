## GenAI/ML Infrastructure AWS examples

This section contains examples and infrastructure-as-code (IaC) configurations for the GenAI ML Platform. The focus here is on cost-efficient and scalable infrastructure solutions to support the platform's machine learning models and associated services.

Contents
- [**Cost-Efficient Model Hosting on Amazon SageMaker using Graviton Instances**](https://github.com/aws-samples/genai-ml-platform-examples/tree/main/infrastructure/cost-efficient-model-inference-sagemaker-graviton): This example demonstrates how to set up a cost-effective hosting environment for small language models (SLMs) on Amazon SageMaker, leveraging Graviton instances.

- [**Cost-Efficient Model Hosting on Amazon EKS with Graviton**](https://github.com/aws-samples/genai-ml-platform-examples/tree/main/infrastructure/efficient%20model%20inference): This example shows how to set up a cost-efficient hosting environment for your machine learning models on Amazon Elastic Kubernetes Service (EKS), again leveraging Graviton-based instances.

- [**SageMaker Scale Down to Zero with AWS CDK**](https://github.com/aws-samples/genai-ml-platform-examples/tree/main/infrastructure/inference_component_scale_to_zero): This example demonstrates how to use AWS CDK (Cloud Development Kit) to implement a cost-saving feature for your Amazon SageMaker endpoints - the ability to scale down to zero instances when not in use. This approach helps you minimize infrastructure costs by only paying for the resources you actively use.

Feel free to explore these examples and adapt them to your specific GenAI ML Platform requirements. The infrastructure solutions presented here are designed to be cost-efficient, scalable, and easy to deploy and manage.

## Security

See [CONTRIBUTING](CONTRIBUTING.md#security-issue-notifications) for more information.

## License

This library is licensed under the MIT-0 License. See the LICENSE file.

