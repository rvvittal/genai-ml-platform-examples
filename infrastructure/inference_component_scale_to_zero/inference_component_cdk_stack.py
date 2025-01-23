import aws_cdk
from aws_cdk import (
    Stack,
    aws_applicationautoscaling as appscaling,
    aws_cloudwatch as cloudwatch,
    aws_cloudwatch_actions as cloudwatch_actions,
    aws_iam as iam,
    aws_sagemaker as sagemaker
)
from constructs import Construct

class InferenceComponentCdkStack(Stack):

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        ecr_image = aws_cdk.CfnParameter(
            self,
            'ECRImage',
            default='763104351884.dkr.ecr.us-east-1.amazonaws.com/djl-inference:0.31.0-lmi13.0.0-cu124'
        ).value_as_string

        s3_model_data = aws_cdk.CfnParameter(
            self,
            'ModelData',
            default="s3://jumpstart-private-cache-prod-us-east-1/meta-textgeneration/meta-textgeneration-llama-3-8b/artifacts/inference-prepack/v1.1.0/"
        ).value_as_string

        instance_type = aws_cdk.CfnParameter(
            self,
            'InstanceType',
            default='ml.g5.12xlarge'
        ).value_as_string


        role = iam.Role(
            self,
            'SageMakerRole',
            assumed_by=iam.ServicePrincipal('sagemaker.amazonaws.com')
        )
        role.add_managed_policy(iam.ManagedPolicy.from_aws_managed_policy_name('AmazonSageMakerFullAccess'))
        execution_role=role.role_arn


        model = sagemaker.CfnModel(
            self,
            'LlamaModel',
            execution_role_arn=execution_role,
            primary_container=sagemaker.CfnModel.ContainerDefinitionProperty(
                image=ecr_image,
                environment={
                'ENDPOINT_SERVER_TIMEOUT': "3600",
                "HF_MODEL_ID": "/opt/ml/model",
                "MODEL_CACHE_ROOT": "/opt/ml/model",
                "OPTION_GPU_MEMORY_UTILIZATION": "0.85",
                "OPTION_TENSOR_PARALLEL_DEGREE": "4",
                "SAGEMAKER_ENV": "1",
                "SAGEMAKER_MODEL_SERVER_WORKERS": "1",
                "SAGEMAKER_PROGRAM": "inference.py"
                },
                mode='SingleModel',
                model_data_source=sagemaker.CfnModel.ModelDataSourceProperty(
                    s3_data_source=sagemaker.CfnModel.S3DataSourceProperty(
                        compression_type='None',
                        s3_data_type='S3Prefix',
                        s3_uri=s3_model_data,
                        model_access_config=sagemaker.CfnModel.ModelAccessConfigProperty(
                            accept_eula=True
                        )
                    )
                )
            )
        )

        endpoint_config = sagemaker.CfnEndpointConfig(
            self,
            'LlamaEndpointConfig',
            execution_role_arn=execution_role,
            production_variants=[sagemaker.CfnEndpointConfig.ProductionVariantProperty(
                variant_name='variant-0',
                instance_type=instance_type,
                initial_instance_count=1,
                model_data_download_timeout_in_seconds=3600,
                container_startup_health_check_timeout_in_seconds=3600,
                managed_instance_scaling=sagemaker.CfnEndpointConfig.ManagedInstanceScalingProperty(
                    status='ENABLED',
                    min_instance_count=0,
                    max_instance_count=2
                ),
                routing_config=sagemaker.CfnEndpointConfig.RoutingConfigProperty(
                    routing_strategy='LEAST_OUTSTANDING_REQUESTS'
                )
            )]
        )

        endpoint = sagemaker.CfnEndpoint(
            self,
            'LlamaEndpoint',
            endpoint_config_name=endpoint_config.attr_endpoint_config_name
        )

        inference_component = sagemaker.CfnInferenceComponent(
            self,
            'LlamaInferenceComponent',
            variant_name='variant-0',
            inference_component_name='llama-inference-component',
            endpoint_name=endpoint.attr_endpoint_name,
            specification=sagemaker.CfnInferenceComponent.InferenceComponentSpecificationProperty(
                model_name=model.attr_model_name,
                startup_parameters=sagemaker.CfnInferenceComponent.InferenceComponentStartupParametersProperty(
                    model_data_download_timeout_in_seconds=3600,
                    container_startup_health_check_timeout_in_seconds=3600
                ),
                compute_resource_requirements=sagemaker.CfnInferenceComponent.InferenceComponentComputeResourceRequirementsProperty(
                    min_memory_required_in_mb=104096,
                    number_of_accelerator_devices_required=4
                )
            ),
            runtime_config=sagemaker.CfnInferenceComponent.InferenceComponentRuntimeConfigProperty(
                copy_count=1
            )
        )

        scalable_target = appscaling.ScalableTarget(
            self,
            'SageMakerScalableTarget',
            service_namespace=appscaling.ServiceNamespace.SAGEMAKER,
            min_capacity=0,
            max_capacity=2,
            scalable_dimension='sagemaker:inference-component:DesiredCopyCount',
            resource_id=f"inference-component/{inference_component.inference_component_name}"
        )

        scalable_target.scale_to_track_metric(
            'SageMakerScalingSetup',
            target_value=1,
            predefined_metric=appscaling.PredefinedMetric.SAGEMAKER_INFERENCE_COMPONENT_INVOCATIONS_PER_COPY
        )

        scaling_alarm = cloudwatch.Alarm(
            self,
            'InferenceComponentScalingAlarm',
            comparison_operator=cloudwatch.ComparisonOperator.GREATER_THAN_OR_EQUAL_TO_THRESHOLD,
            threshold=1,
            evaluation_periods=1,
            metric= cloudwatch.Metric(
                namespace='AWS/SageMaker',
                period=aws_cdk.Duration.seconds(30),
                metric_name='NoCapacityInvocationFailures',
                dimensions_map={ 'InferenceComponentName': inference_component.inference_component_name }
            )
        )

        scale_from_zero_action = appscaling.StepScalingAction(
            self,
            'ScaleFromZero',
            scaling_target=scalable_target,
            adjustment_type=appscaling.AdjustmentType.CHANGE_IN_CAPACITY,
            metric_aggregation_type=appscaling.MetricAggregationType.MAXIMUM,
            cooldown=aws_cdk.Duration.seconds(60)
        )

        scale_from_zero_action.add_adjustment(adjustment=1, lower_bound=0)

        application_scaling_action = cloudwatch_actions.ApplicationScalingAction(scale_from_zero_action)

        scaling_alarm.add_alarm_action(application_scaling_action)

        scalable_target.node.add_dependency(inference_component)

        aws_cdk.CfnOutput()